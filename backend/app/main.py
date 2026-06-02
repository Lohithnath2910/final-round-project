"""
Engineering Capstone — backend skeleton (Part A + Part B). Fill the TODOs.
TS/Deno equivalent is fine — mirror these contracts. The grade is in the guards.
"""
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid
import time
import json
from typing import Any
from app.db import get_conn

from app.assistant import (
    is_data_question,
    nl_to_sql,
    validate_sql,
    rag_answer,
    detect_cross_tenant,
    detect_injection
)

app = FastAPI(title="Engineering Capstone")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

INTENTS = ["booking", "cancellation", "faq", "complaint", "wakeup"]
CONFIDENCE_THRESHOLD = 0.6

class PropertyCreate(BaseModel):
    property_id: str
    name: str
    city: str
    total_rooms: int
    property_config: dict[str, Any] | None = None

class Message(BaseModel):
    property_id: str
    guest_id: str
    message_id: str
    text: str


class Ask(BaseModel):
    property_id: str
    question: str


@app.get("/health")
def health():
    try:
        conn = get_conn()
        cur = conn.cursor()

        cur.execute("SELECT 1")
        cur.fetchone()

        cur.close()
        conn.close()

        return {
            "ok": True,
            "database": True
        }

    except Exception as e:
        return {
            "ok": False,
            "database": False,
            "error": str(e)
        }


# ---------- Part A: orchestration ----------
WORKFLOW_REGISTRY = {
    "booking": "booking_requested",
    "cancellation": "cancellation_requested",
    "complaint": "complaint_received",
    "wakeup": "wakeup_requested",
    "faq": "faq_received"
}



def set_tenant(cur, property_id):
    cur.execute(
        "SELECT set_config('app.current_property', %s, false)",
        (property_id,)
    )


def ensure_schema_compatibility(conn):
    cur = conn.cursor()
    try:
        cur.execute("ALTER TABLE properties ADD COLUMN IF NOT EXISTS property_config JSONB")
        cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS messages_message_id_uidx ON messages(message_id)")
        conn.commit()
    finally:
        cur.close()


@app.on_event("startup")
def startup_checks():
    conn = get_conn()
    try:
        ensure_schema_compatibility(conn)
    finally:
        conn.close()

@app.post("/property")
def create_property(config: PropertyCreate):
    conn = get_conn()
    cur = conn.cursor()
    set_tenant(cur, config.property_id)
    try:
        property_config = json.dumps(config.property_config or {})
        cur.execute(
            """
            INSERT INTO properties (
                property_id,
                name,
                city,
                total_rooms,
                property_config
            )
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (property_id)
            DO UPDATE SET
                name = EXCLUDED.name,
                city = EXCLUDED.city,
                total_rooms = EXCLUDED.total_rooms,
                property_config = EXCLUDED.property_config
            """,
            (
                config.property_id,
                config.name,
                config.city,
                config.total_rooms,
                property_config,
            ),
        )

        # Create lifecycle event
        cur.execute(
            """
            INSERT INTO events (
                event_id,
                property_id,
                event_type,
                payload
            )
            VALUES (%s, %s, %s, %s)
            """,
            (
                str(uuid.uuid4()),
                config.property_id,
                "property_created",
                json.dumps({
                    "name": config.name,
                    "city": config.city
                })
            )
        )

        conn.commit()

        return {
            "stored": True,
            "property_id": config.property_id
        }

    except Exception as e:
        conn.rollback()
        return {
            "stored": False,
            "error": str(e)
        }

    finally:
        cur.close()
        conn.close()


def classify(text: str, cfg: dict = None):

    text = text.lower()

    if any(word in text for word in ["wake up", "wake me", "morning call"]):
        return ("wakeup", 0.95)

    if any(word in text for word in ["dirty", "not working", "bad service", "cold food", "complaint"]):
        return ("complaint", 0.95)

    if any(word in text for word in ["wifi", "checkin", "check-in", "checkout", "check-out", "parking"]):
        return ("faq", 0.95)

    if any(word in text for word in ["cancel"]):

        if any(word in text for word in [
            "maybe",
            "not sure",
            "thinking",
            "change",
            "might",
            "thinking of",
            "can i",
            "should i",
        ]):
            return ("cancellation", 0.40)

        return ("cancellation", 0.95)

    if any(word in text for word in [
        "book",
        "booking",
        "reserve",
        "room available",
        "room for"
    ]):
        return ("booking", 0.95)

    return ("faq", 0.30)


@app.post("/message")
def handle_message(m: Message):

    conn = get_conn()
    cur = conn.cursor()

    set_tenant(cur, m.property_id)

    try:
        # --------------------
        # CLASSIFICATION
        # --------------------
        start = time.perf_counter()
        intent, confidence = classify(m.text)
        latency_ms = (time.perf_counter() - start) * 1000
        # --------------------
        # STORE MESSAGE
        # --------------------

        cur.execute(
            """
            INSERT INTO messages(
                message_id,
                property_id,
                guest_id,
                text,
                intent,
                confidence,
                status
            )
            VALUES(%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (message_id) DO NOTHING
            RETURNING message_id
            """,
            (
                m.message_id,
                m.property_id,
                m.guest_id,
                m.text,
                intent,
                confidence,
                "received"
            )
        )

        if cur.fetchone() is None:
            conn.rollback()
            return {
                "message_id": m.message_id,
                "status": "duplicate"
            }

        # --------------------
        # HUMAN HANDOFF
        # --------------------

        if confidence < CONFIDENCE_THRESHOLD:

            cur.execute(
                """
                INSERT INTO events(
                    event_id,
                    property_id,
                    event_type,
                    payload
                )
                VALUES(%s,%s,%s,%s)
                """,
                (
                    str(uuid.uuid4()),
                    m.property_id,
                    "needs_human",
                    json.dumps({
                        "message_id": m.message_id,
                        "text": m.text,
                        "latency_ms": latency_ms
                    })
                )
            )

            conn.commit()

            return {
                "message_id": m.message_id,
                "intent": intent,
                "status": "needs_human",
                "latency_ms": latency_ms
            }

        # --------------------
        # CANCELLATION GUARD
        # --------------------

        if (
            intent == "cancellation"
            and confidence < 0.8
        ):

            cur.execute(
                """
                INSERT INTO events(
                    event_id,
                    property_id,
                    event_type,
                    payload
                )
                VALUES(%s,%s,%s,%s)
                """,
                (
                    str(uuid.uuid4()),
                    m.property_id,
                    "confirmation_required",
                    json.dumps({
                        "message_id": m.message_id,
                        "latency_ms": latency_ms
                    })
                )
            )

            conn.commit()

            return {
                "message_id": m.message_id,
                "intent": intent,
                "status": "confirmation_required",
                "latency_ms": latency_ms
            }

        # --------------------
        # QUEUE JOB
        # --------------------

        cur.execute(
            """
            INSERT INTO workflow_jobs(
                job_id,
                property_id,
                job_type,
                status,
                payload
            )
            VALUES(%s,%s,%s,%s,%s)
            """,
            (
                str(uuid.uuid4()),
                m.property_id,
                intent,
                "pending",
                json.dumps({
                    "message_id": m.message_id,
                    "guest_id": m.guest_id,
                    "text": m.text,
                    "latency_ms": latency_ms
                })
            )
        )

        # --------------------
        # EVENT TYPE
        # --------------------

        cur.execute(
            """
            INSERT INTO events(
                event_id,
                property_id,
                event_type,
                payload
            )
            VALUES(%s,%s,%s,%s)
            """,
            (
                str(uuid.uuid4()),
                m.property_id,
                WORKFLOW_REGISTRY[intent],
                json.dumps({
                    "message_id": m.message_id,
                    "latency_ms": latency_ms
                })
            )
        )

        conn.commit()

        return {
            "message_id": m.message_id,
            "intent": intent,
            "confidence": confidence,
            "status": "queued",
            "latency_ms": latency_ms
        }

    except Exception as e:

        conn.rollback()

        return {
            "error": str(e)
        }

    finally:

        cur.close()
        conn.close()


@app.get("/events")
def events(property_id: str):
    conn = get_conn()
    cur = conn.cursor()
    set_tenant(cur, property_id)
    try:
        cur.execute(
            """
            SELECT *
            FROM events
            WHERE property_id = %s
            ORDER BY created_at DESC
            LIMIT 20
            """,
            (property_id,)
        )

        rows = cur.fetchall()

        items = []

        for row in rows:
            items.append({
                "event_id": row[0],
                "property_id": row[1],
                "event_type": row[2],
                "payload": row[3],
                "created_at": str(row[4])
            })

        return {
            "property_id": property_id,
            "events": items
        }

    finally:
        cur.close()
        conn.close()


@app.get("/bookings")
def bookings(property_id: str):
    conn = get_conn()
    cur = conn.cursor()
    set_tenant(cur, property_id)
    try:
        cur.execute(
            """
            SELECT *
            FROM bookings
            WHERE property_id = %s
            ORDER BY checkin DESC
            """,
            (property_id,)
        )

        rows = cur.fetchall()

        items = []

        for row in rows:
            items.append({
                "booking_id": row[0],
                "property_id": row[1],
                "room_type": row[2],
                "checkin": str(row[3]),
                "checkout": str(row[4]),
                "status": row[5],
                "amount_inr": row[6],
                "source": row[7]
            })

        return {
            "property_id": property_id,
            "items": items
        }

    finally:
        cur.close()
        conn.close()


# ---------- Part B: Data Assistant ----------
@app.post("/ask")
def ask(req: Ask):
    conn = None
    cur = None
    try:
        detect_injection(req.question)
        detect_cross_tenant(req.question, req.property_id)

        if is_data_question(req.question):

            sql = nl_to_sql(req.question, req.property_id)

            validate_sql(sql)

            conn = get_conn()
            cur = conn.cursor()

            set_tenant(cur, req.property_id)

            cur.execute(
                sql,
                (req.property_id,)
            )

            rows = cur.fetchall()

            if rows:
                if(len(rows[0]) == 1):
                    answer = str(rows[0][0])
                else:
                    answer = str(rows[0])

            else:
                answer = "No matching records found."
            return {
                "answer": answer,
                "sql": sql,
                "rows": rows
            }

        rag = rag_answer(
            req.question,
            req.property_id
        )

        if rag:

            return {
                "answer": rag["answer"],
                "sql": None,
                "rows": [],
                "citation": rag.get("citation", rag.get("source")),
                "confidence": rag.get("confidence")
            }

        return {
            "answer": "I don't have enough information to answer that.",
            "sql": None,
            "rows": []
        }

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    finally:
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()
