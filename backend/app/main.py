"""
Engineering Capstone — backend skeleton (Part A + Part B). Fill the TODOs.
TS/Deno equivalent is fine — mirror these contracts. The grade is in the guards.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid
import json
from app.db import get_conn

app = FastAPI(title="Engineering Capstone")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

INTENTS = ["booking", "cancellation", "faq", "complaint", "wakeup"]
CONFIDENCE_THRESHOLD = 0.6

class PropertyCreate(BaseModel):
    property_id: str
    name: str
    city: str
    total_rooms: int

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
@app.post("/property")
def create_property(config: PropertyCreate):
    conn = get_conn()
    cur = conn.cursor()

    try:
        # Insert property
        cur.execute(
            """
            INSERT INTO properties (
                property_id,
                name,
                city,
                total_rooms
            )
            VALUES (%s, %s, %s, %s)
            """,
            (
                config.property_id,
                config.name,
                config.city,
                config.total_rooms
            )
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


def classify(text: str, cfg: dict) -> tuple[str, float]:
    """2-stage: rules → LLM fallback. Return (intent, confidence). TODO."""
    return ("faq", 0.0)


@app.post("/message")
def handle_message(m: Message):
    """
    idempotent on message_id · classify · low-confidence→needs_human ·
    cancellation+low-confidence→confirm (no destructive effect) ·
    else WorkflowRegistry → ENQUEUE side-effect (not inline). All tenant-scoped. TODO.
    """
    return {"message_id": m.message_id, "intent": None, "status": "not_implemented"}


@app.get("/events")
def events(property_id: str):
    conn = get_conn()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT *
            FROM events
            WHERE property_id = %s
            ORDER BY created_at DESC
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
def nl_to_sql(question: str, property_id: str) -> str:
    """Guarded: force property_id filter in code; single read-only SELECT only;
    validate tables/columns vs schema. Raise to block. TODO."""
    raise NotImplementedError


def rag_answer(question: str) -> dict:
    """Retrieve from kb/, answer with {answer, source}. TODO."""
    return {"answer": None, "source": None}


@app.post("/ask")
def ask(req: Ask):
    """product-help→rag; else guarded nl_to_sql→read-only tenant-scoped run→{answer,sql,rows}.
    unanswerable→refuse, don't fabricate. TODO."""
    return {"answer": None, "sql": None, "rows": [], "note": "not_implemented"}
