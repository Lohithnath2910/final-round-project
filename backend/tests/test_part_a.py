from fastapi.testclient import TestClient
from app.main import app
import uuid

client = TestClient(app)


def msg_id():
    return str(uuid.uuid4())


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