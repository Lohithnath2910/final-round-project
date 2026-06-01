import os
from app.db import get_conn

DATA_PATTERNS = {
    "booking_count": [
        "booking",
        "bookings",
        "reservation",
        "reservations",
        "kitni booking",
        "kitni bookings"
    ],

    "revenue": [
        "revenue",
        "income",
        "earning",
        "earnings",
        "kamayi",
        "kamai"
    ],

    "occupancy": [
        "occupancy",
        "occupied",
        "filled rooms",
        "rooms filled"
    ]
}

SERVICE_ALIASES = {
    "wifi": ["wifi", "internet"],
    "parking": ["parking"],
    "deposit": ["deposit", "security deposit"],
    "food": ["food", "meal", "mess"],
    "checkout": ["checkout", "check out"]
}


def get_all_properties():

    conn = get_conn()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT property_id
            FROM properties
            """
        )

        return [row[0] for row in cur.fetchall()]

    finally:
        cur.close()
        conn.close()

        
OTA_SOURCES = [
    "mmt",
    "agoda",
    "booking_com",
    "direct"
]

def is_data_question(question: str):

    q = question.lower()

    if "room type" in q:
        return True

    for source in OTA_SOURCES:
        if source in q:
            return True

    if "no-show" in q:
        return True

    if "no show" in q:
        return True

    for patterns in DATA_PATTERNS.values():

        for pattern in patterns:

            if pattern in q:
                return True

    return False


def nl_to_sql(question: str,property_id: str):

    q = question.lower()

    # no show

    if (
        "no-show" in q
        or "no show" in q
        or "noshow" in q
    ):
        return """
        SELECT COUNT(*) AS no_show_count
        FROM bookings
        WHERE property_id = %s
        AND status = 'no_show'
        """

    if any(
        p in q
        for p in DATA_PATTERNS["booking_count"]
    ):
        return """
        SELECT COUNT(*) AS booking_count
        FROM bookings
        WHERE property_id = %s
        """

    # MMT revenue

    for source in OTA_SOURCES:
        if source in q:

            return f"""
            SELECT COALESCE(SUM(amount_inr), 0) AS revenue
            FROM bookings
            WHERE property_id = %s
            AND source = '{source}'
            """
    
    # revenue

    if any(
        p in q
        for p in DATA_PATTERNS["revenue"]
    ):
        return """
        SELECT COALESCE(SUM(amount_inr), 0) AS revenue
        FROM bookings
        WHERE property_id = %s
        """


    # occupancy
    if any(
        p in q
        for p in DATA_PATTERNS["occupancy"]
    ):
        return """
        SELECT COUNT(*) AS occupied_rooms
        FROM bookings
        WHERE property_id = %s
        AND status = 'confirmed'
        """

    # best room type

    if (
        "room type" in q
        and (
            "most" in q
            or "highest" in q
            or "earn" in q
        )
    ):

        return """
        SELECT room_type,
               SUM(amount_inr) AS revenue
        FROM bookings
        WHERE property_id = %s
        GROUP BY room_type
        ORDER BY revenue DESC
        LIMIT 1
        """

    raise ValueError(
        "I don't have enough information to answer that."
    )

BLOCKED_PATTERNS = [
    "drop",
    "delete",
    "update",
    "insert",
    "alter",
    ";",
    "--",
    "union",
    "information_schema",
    "pg_catalog"
]


def validate_sql(sql: str):

    lowered = sql.strip().lower()

    if not lowered.startswith("select"):
        raise ValueError("Only SELECT allowed")

    for word in BLOCKED_PATTERNS:
        if word in lowered:
            raise ValueError("Unsafe SQL")

    if "property_id" not in lowered:
        raise ValueError("Tenant filter missing")

    return True


def rag_answer(question, property_id):

    q = question.lower()

    platform_path = "kb/platform.txt"

    if os.path.exists(platform_path):

        if (
            "rate" in q
            or "room rate" in q
            or "price" in q
        ):
            return {
                "answer":
                "Open Channel Manager > Rate Management, pick the room type and date, enter the new price and save.",
                "source":
                "platform.txt"
            }

        if (
            "review" in q
            or "ota review" in q
        ):
            return {
                "answer":
                "Open Channel Manager > Reviews, select a review, draft a response and publish.",
                "source":
                "platform.txt"
            }

        if (
            "onboarding" in q
            or "setup property" in q
            or "add property" in q
        ):
            return {
                "answer":
                "Onboarding takes under 15 minutes via WhatsApp or the web console.",
                "source":
                "platform.txt"
            }

    # Tenant KB fallback

    path = f"kb/{property_id}.txt"

    if not os.path.exists(path):
        return None

    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for service, aliases in SERVICE_ALIASES.items():

        if any(alias in q for alias in aliases):

            for line in lines:

                if service.lower() in line.lower():

                    return {
                        "answer": line.strip(),
                        "source": f"{property_id}.txt"
                    }

    return None

def detect_cross_tenant(question, property_id):

    q = question.lower()

    tenants = get_all_properties()

    for tenant in tenants:

        if tenant == property_id:
            continue

        if tenant.lower() in q:
            raise ValueError(
                "Cross-tenant access blocked"
            )

    return True

def detect_injection(question: str):

    q = question.lower()

    for pattern in BLOCKED_PATTERNS:
        if pattern in q:
            raise ValueError(
                "Unsafe query detected"
            )
        
def load_kb(property_id):

    path = f"kb/{property_id}.txt"

    if not os.path.exists(path):
        return None

    with open(path, "r", encoding="utf-8") as f:
        return f.read()