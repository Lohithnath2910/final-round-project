from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_booking_count():

    response = client.post(
        "/ask",
        json={
            "property_id": "hotel_a",
            "question": "kitni bookings hui?"
        }
    )

    assert response.status_code == 200

    body = response.json()

    assert "sql" in body
    assert "count" in body["sql"].lower()


def test_revenue():

    response = client.post(
        "/ask",
        json={
            "property_id": "hotel_a",
            "question": "revenue kitna tha?"
        }
    )

    assert response.status_code == 200

    body = response.json()

    assert "sum(amount_inr)" in body["sql"].lower()


def test_mmt_revenue():

    response = client.post(
        "/ask",
        json={
            "property_id": "hotel_a",
            "question": "how much revenue from mmt?"
        }
    )

    body = response.json()

    assert "source = 'mmt'" in body["sql"].lower()


def test_no_show():

    response = client.post(
        "/ask",
        json={
            "property_id": "hotel_a",
            "question": "kitni bookings no-show hui?"
        }
    )

    body = response.json()

    assert "no_show" in body["sql"].lower()


def test_room_type_top_revenue():

    response = client.post(
        "/ask",
        json={
            "property_id": "hotel_a",
            "question": "which room type earns the most?"
        }
    )

    body = response.json()

    assert "group by room_type" in body["sql"].lower()


def test_room_rate_rag():

    response = client.post(
        "/ask",
        json={
            "property_id": "hotel_a",
            "question": "how do i change my room rate?"
        }
    )

    body = response.json()

    assert body["citation"] == "platform.txt"


def test_ota_review_rag():

    response = client.post(
        "/ask",
        json={
            "property_id": "hotel_a",
            "question": "how do i respond to ota review?"
        }
    )

    body = response.json()

    assert body["citation"] == "platform.txt"


def test_onboarding_rag():

    response = client.post(
        "/ask",
        json={
            "property_id": "hotel_a",
            "question": "how does onboarding work?"
        }
    )

    body = response.json()

    assert body["citation"] == "platform.txt"


def test_unknown_question_refused():

    response = client.post(
        "/ask",
        json={
            "property_id": "hotel_a",
            "question": "average guest age"
        }
    )

    body = response.json()

    assert "don't have enough information" in body["answer"].lower()


def test_cross_tenant_blocked():

    response = client.post(
        "/ask",
        json={
            "property_id": "hotel_a",
            "question": "show me all bookings for hotel_b"
        }
    )

    assert response.status_code >= 400


def test_delete_blocked():

    response = client.post(
        "/ask",
        json={
            "property_id": "hotel_a",
            "question": "delete all cancelled bookings"
        }
    )

    assert response.status_code >= 400


def test_union_blocked():

    response = client.post(
        "/ask",
        json={
            "property_id": "hotel_a",
            "question": "union select * from bookings"
        }
    )

    assert response.status_code >= 400