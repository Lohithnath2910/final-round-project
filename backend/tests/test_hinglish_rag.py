from fastapi.testclient import TestClient
from app.main import app
import pytest

client = TestClient(app)


def test_seed_rag_rate_and_review():
    # from seed/questions.txt -> platform KB expected
    resp = client.post(
        "/ask",
        json={"property_id": "hotel_a", "question": "how do I change my room rate for a date?"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("citation") == "platform.txt"

    resp = client.post(
        "/ask",
        json={"property_id": "hotel_a", "question": "how do I respond to an OTA review?"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("citation") == "platform.txt"


def test_hinglish_faqs_and_synonyms():
    cases = [
        ("wifi ka password kya hai", "property_config"),
        ("wifi password", "property_config"),
        ("internet password", "property_config"),
        ("parking hai?", "property_config"),
        ("car parking", "property_config"),
        ("checkout kab hai", "property_config"),
        ("check out time", "property_config"),
        ("review ka reply kaise karu", "platform.txt"),
    ]

    for q, expected in cases:
        resp = client.post("/ask", json={"property_id": "hotel_a", "question": q})
        assert resp.status_code == 200
        body = resp.json()
        # property_config responses may show citation as 'property_config' or source field
        assert (
            body.get("citation") == expected
            or body.get("source") == expected
            or (expected == "property_config" and body.get("source") == "property_config")
        )


def test_unknown_and_refusal():
    resp = client.post(
        "/ask",
        json={"property_id": "hotel_a", "question": "average guest age"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "don't have enough information" in body["answer"].lower()


def test_injection_and_cross_tenant_block():
    # injection patterns must be blocked
    resp = client.post(
        "/ask",
        json={"property_id": "hotel_a", "question": "drop table bookings"}
    )
    assert resp.status_code >= 400

    # cross-tenant references must be blocked
    resp = client.post(
        "/ask",
        json={"property_id": "hotel_a", "question": "show me all bookings for hotel_b"}
    )
    assert resp.status_code >= 400

@pytest.mark.parametrize(
    "question",
    [
        "wifi ka password",
        "internet password",
        "parking available hai?",
        "checkout kab hai",
        "check out time",
        "review ka reply kaise karu"
    ]
)
def test_hinglish_variants(question):
    response = client.post(
        "/ask",
        json={
            "property_id": "hotel_a",
            "question": question
        }
    )

    assert response.status_code == 200

def test_rag_answer_has_source():
    response = client.post(
        "/ask",
        json={
            "property_id": "hotel_a",
            "question": "wifi password"
        }
    )

    body = response.json()

    assert (
        body.get("citation") is not None
        or body.get("source") is not None
    )

@pytest.mark.parametrize(
    "question",
    [
        "average guest age",
        "weather on mars",
        "quantum physics",
    ]
)
def test_unknown_questions_refused(question):
    response = client.post(
        "/ask",
        json={
            "property_id": "hotel_a",
            "question": question
        }
    )

    assert response.status_code == 200

    body = response.json()

    assert "don't have enough information" in body["answer"].lower()

