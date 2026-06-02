#!/usr/bin/env python3
"""
Minimal workflow_jobs worker.
Claims one pending job atomically and marks it done after "processing".
This is intentionally simple for capstone acceptance: demonstrates queue processing,
visibility/claim semantics and jobs being transitioned from pending -> in_progress -> done.

Usage: python worker.py
"""
import time
from app.db import get_conn
import json

import requests
import uuid

PROCESS_SLEEP = 1.0


def claim_one_job(conn):
    cur = conn.cursor()
    try:
        # Atomically claim a pending job using UPDATE ... FROM (SELECT ... FOR UPDATE SKIP LOCKED)
        cur.execute(
            """
            WITH cte AS (
                SELECT job_id FROM workflow_jobs
                WHERE status = 'pending'
                ORDER BY created_at
                FOR UPDATE SKIP LOCKED
                LIMIT 1
            )
            UPDATE workflow_jobs w
            SET status = 'in_progress'
            FROM cte
            WHERE w.job_id = cte.job_id
            RETURNING
                w.job_id,
                w.property_id,
                w.job_type,
                w.payload
            """
        )
        row = cur.fetchone()
        if row:
            conn.commit()
            return row[0], row[1], row[2], row[3]
        conn.commit()
        return None
    finally:
        cur.close()


def mark_done(conn, job_id):

    cur = conn.cursor()

    try:

        cur.execute(
            """
            UPDATE workflow_jobs
            SET status = 'done'
            WHERE job_id = %s
            RETURNING property_id, job_type, payload
            """,
            (job_id,)
        )

        row = cur.fetchone()

        if row:

            property_id, job_type, payload = row

            cur.execute(
                """
                INSERT INTO events(
                    event_id,
                    property_id,
                    event_type,
                    payload
                )
                VALUES(
                    gen_random_uuid()::text,
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    property_id,
                    f"{job_type}_completed",
                    json.dumps(payload)
                )
            )

        conn.commit()

    finally:
        cur.close()

def process_payload(payload):
    # For the capstone, we simulate processing. In real life, implement OTA calls.
    print('Processing payload:', payload)
    time.sleep(PROCESS_SLEEP)


def push_availability_to_ota(property_id):

    push_id = str(uuid.uuid4())

    for attempt in range(5):

        try:

            response = requests.post(
                "http://localhost:9000/availability",
                json={
                    "push_id": push_id,
                    "property_id": property_id
                },
                timeout=5
            )

            if response.status_code == 200:
                return True

            if response.status_code in [429, 500]:
                time.sleep(2 ** attempt)
                continue

        except Exception:
            time.sleep(2 ** attempt)

    return False

def main_loop():
    print('worker started')
    conn = get_conn()
    try:
        while True:
            claimed = claim_one_job(conn)
            if not claimed:
                time.sleep(0.5)
                continue

            job_id, property_id, job_type, payload = claimed
            try:
                process_payload(payload)

                if job_type == "booking":

                    success = push_availability_to_ota(
                        property_id
                    )

                    print(
                        "OTA PUSH:",
                        success
                    )

                mark_done(conn, job_id)
            except Exception as e:
                cur = conn.cursor()

                cur.execute(
                    """
                    UPDATE workflow_jobs
                    SET status = 'failed'
                    WHERE job_id = %s
                    RETURNING property_id, job_type
                    """,
                    (job_id,)
                )

                row = cur.fetchone()

                if row:
                    property_id, job_type = row

                    cur.execute(
                        """
                        INSERT INTO events(
                            event_id,
                            property_id,
                            event_type,
                            payload
                        )
                        VALUES(
                            gen_random_uuid(),
                            %s,
                            %s,
                            %s
                        )
                        """,
                        (
                            property_id,
                            f"{job_type}_failed",
                            '{"reason":"worker_exception"}'
                        )
                    )

                conn.commit()
                cur.close()
                print('job failed', job_id, e)
                # For minimal worker we mark failed and continue; improvements: retry_count/backoff
                cur = conn.cursor()
                cur.execute("UPDATE workflow_jobs SET status = 'failed' WHERE job_id = %s", (job_id,))
                conn.commit()
                cur.close()

    finally:
        conn.close()


if __name__ == '__main__':
    main_loop()
