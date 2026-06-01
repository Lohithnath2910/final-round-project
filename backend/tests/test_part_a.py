from fastapi.testclient import TestClient
from app.main import app
from app.db import get_conn
import uuid

client = TestClient(app)


def msg_id():
    return str(uuid.uuid4())


def count_rows_like(table_name: str, needle: str) -> int:
    conn = get_conn()
    cur = conn.cursor()
    try:
        if table_name == "messages":
            cur.execute(
                "SELECT COUNT(*) FROM messages WHERE message_id = %s",
                (needle,),
            )
        else:
            cur.execute(
                f"SELECT COUNT(*) FROM {table_name} WHERE payload::text LIKE %s",
                (f"%{needle}%",),
            )
        return cur.fetchone()[0]
    finally:
        cur.close()
        conn.close()


# -------------------------
# HEALTH
# -------------------------

def test_health():

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["ok"] is True


# -------------------------
# CLASSIFICATION
# -------------------------

def test_booking_message():

    response = client.post(
        "/message",
        json={
            "property_id": "hotel_a",
            "guest_id": "test_guest",
            "message_id": msg_id(),
            "text": "book a room tomorrow"
        }
    )

    body = response.json()

    assert response.status_code == 200
    assert body["intent"] == "booking"
    assert body["status"] == "queued"


def test_faq_message():

    response = client.post(
        "/message",
        json={
            "property_id": "hotel_a",
            "guest_id": "test_guest",
            "message_id": msg_id(),
            "text": "wifi password"
        }
    )

    body = response.json()

    assert body["intent"] == "faq"
    assert body["status"] == "queued"


def test_complaint_message():

    response = client.post(
        "/message",
        json={
            "property_id": "hotel_a",
            "guest_id": "test_guest",
            "message_id": msg_id(),
            "text": "AC not working"
        }
    )

    body = response.json()

    assert body["intent"] == "complaint"
    assert body["status"] == "queued"


def test_wakeup_message():

    response = client.post(
        "/message",
        json={
            "property_id": "hotel_a",
            "guest_id": "test_guest",
            "message_id": msg_id(),
            "text": "wake me up at 6am"
        }
    )

    body = response.json()

    assert body["intent"] == "wakeup"
    assert body["status"] == "queued"


# -------------------------
# HUMAN HANDOFF
# -------------------------

def test_unknown_message_goes_human():

    response = client.post(
        "/message",
        json={
            "property_id": "hotel_a",
            "guest_id": "test_guest",
            "message_id": msg_id(),
            "text": "asdfghjkl qwerty zxcvbn"
        }
    )

    body = response.json()

    assert body["status"] == "needs_human"


# -------------------------
# CANCELLATION SAFETY
# -------------------------

def test_ambiguous_cancel_goes_human():

    response = client.post(
        "/message",
        json={
            "property_id": "hotel_a",
            "guest_id": "test_guest",
            "message_id": msg_id(),
            "text": "maybe cancel my booking"
        }
    )

    body = response.json()

    assert body["status"] == "needs_human"


def test_clear_cancellation_queues():

    response = client.post(
        "/message",
        json={
            "property_id": "hotel_a",
            "guest_id": "test_guest",
            "message_id": msg_id(),
            "text": "cancel my booking"
        }
    )

    body = response.json()

    assert body["intent"] == "cancellation"
    assert body["status"] == "queued"


# -------------------------
# IDEMPOTENCY
# -------------------------

def test_duplicate_message():

    duplicate_id = "pytest_duplicate_message"

    payload = {
        "property_id": "hotel_a",
        "guest_id": "test_guest",
        "message_id": duplicate_id,
        "text": "wifi password"
    }

    client.post("/message", json=payload)

    response = client.post("/message", json=payload)

    body = response.json()

    assert body["status"] == "duplicate"


# -------------------------
# TENANT ISOLATION
# -------------------------

def test_bookings_tenant_scope_hotel_a():

    response = client.get(
        "/bookings",
        params={"property_id": "hotel_a"}
    )

    assert response.status_code == 200

    data = response.json()

    for booking in data["items"]:
        assert booking["property_id"] == "hotel_a"


def test_bookings_tenant_scope_hotel_b():

    response = client.get(
        "/bookings",
        params={"property_id": "hotel_b"}
    )

    assert response.status_code == 200

    data = response.json()

    for booking in data["items"]:
        assert booking["property_id"] == "hotel_b"


def test_events_tenant_scope_hotel_a():

    response = client.get(
        "/events",
        params={"property_id": "hotel_a"}
    )

    assert response.status_code == 200

    data = response.json()

    for event in data["events"]:
        assert event["property_id"] == "hotel_a"


def test_events_tenant_scope_hotel_b():

    response = client.get(
        "/events",
        params={"property_id": "hotel_b"}
    )

    assert response.status_code == 200

    data = response.json()

    for event in data["events"]:
        assert event["property_id"] == "hotel_b"


# -------------------------
# CROSS TENANT LEAK CHECKS
# -------------------------

def test_no_hotel_b_booking_in_hotel_a_response():

    response = client.get(
        "/bookings",
        params={"property_id": "hotel_a"}
    )

    data = response.json()

    for booking in data["items"]:
        assert booking["property_id"] != "hotel_b"


def test_no_hotel_a_booking_in_hotel_b_response():

    response = client.get(
        "/bookings",
        params={"property_id": "hotel_b"}
    )

    data = response.json()

    for booking in data["items"]:
        assert booking["property_id"] != "hotel_a"


# -------------------------
# LATENCY
# -------------------------

def test_latency_present():

    response = client.post(
        "/message",
        json={
            "property_id": "hotel_a",
            "guest_id": "test_guest",
            "message_id": msg_id(),
            "text": "book room tomorrow"
        }
    )

    body = response.json()

    assert "latency_ms" in body
    assert body["latency_ms"] >= 0


def test_property_config_onboarding_and_faq_lookup():
    property_id = f"pytest_property_{uuid.uuid4().hex[:8]}"

    create_response = client.post(
        "/property",
        json={
            "property_id": property_id,
            "name": "Pytest Hotel",
            "city": "Pune",
            "total_rooms": 10,
            "property_config": {
                "language": "hi",
                "custom_faqs": [
                    {"q": "checkout time", "a": "11 AM"},
                    {"q": "wifi", "a": "Free WiFi, password at reception"},
                ],
            },
        },
    )

    assert create_response.status_code == 200
    assert create_response.json()["stored"] is True

    ask_response = client.post(
        "/ask",
        json={
            "property_id": property_id,
            "question": "what is the checkout time?",
        },
    )

    body = ask_response.json()

    assert ask_response.status_code == 200
    assert body["citation"] == "property_config"
    assert body["answer"] == "11 AM"


def test_duplicate_message_is_atomic_and_single_effect():
    duplicate_id = f"pytest_duplicate_atomic_{uuid.uuid4().hex}"

    payload = {
        "property_id": "hotel_a",
        "guest_id": "test_guest",
        "message_id": duplicate_id,
        "text": "book a room tomorrow",
    }

    first_response = client.post("/message", json=payload)
    second_response = client.post("/message", json=payload)

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert second_response.json()["status"] == "duplicate"
    assert count_rows_like("messages", duplicate_id) == 1
    assert count_rows_like("events", duplicate_id) == 1


def test_cross_tenant_block_by_property_name():
    response = client.post(
        "/ask",
        json={
            "property_id": "hotel_b",
            "question": "How many bookings does Hotel Surya have?",
        },
    )

    assert response.status_code >= 400