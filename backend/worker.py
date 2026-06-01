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
            RETURNING w.job_id, w.payload
            """
        )
        row = cur.fetchone()
        if row:
            conn.commit()
            return row[0], row[1]
        conn.commit()
        return None
    finally:
        cur.close()


def mark_done(conn, job_id):
    cur = conn.cursor()
    try:
        cur.execute(
            "UPDATE workflow_jobs SET status = 'done' WHERE job_id = %s",
            (job_id,)
        )
        conn.commit()
    finally:
        cur.close()


def process_payload(payload):
    # For the capstone, we simulate processing. In real life, implement OTA calls.
    print('Processing payload:', payload)
    time.sleep(PROCESS_SLEEP)


def main_loop():
    print('worker started')
    conn = get_conn()
    try:
        while True:
            claimed = claim_one_job(conn)
            if not claimed:
                time.sleep(0.5)
                continue

            job_id, payload = claimed
            try:
                process_payload(payload)
                mark_done(conn, job_id)
            except Exception as e:
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
