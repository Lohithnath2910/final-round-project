import json
import os
import re
from app.db import get_conn

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SEED_PROPERTIES_PATH = os.path.join(ROOT_DIR, "seed", "properties.json")
_SEED_PROPERTIES_CACHE = None

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

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "at",
    "be",
    "can",
    "do",
    "for",
    "from",
    "have",
    "how",
    "i",
    "is",
    "it",
    "my",
    "of",
    "on",
    "or",
    "please",
    "the",
    "to",
    "us",
    "we",
    "what",
    "when",
    "where",
    "which",
    "who",
    "why",
    "with",
    "work",
    "work?",
}


def normalize_text(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def token_set(text: str) -> set[str]:
    tokens = [token for token in normalize_text(text).split() if len(token) > 1]
    return {token for token in tokens if token not in STOPWORDS}


def load_seed_properties():
    global _SEED_PROPERTIES_CACHE

    if _SEED_PROPERTIES_CACHE is not None:
        return _SEED_PROPERTIES_CACHE

    if not os.path.exists(SEED_PROPERTIES_PATH):
        _SEED_PROPERTIES_CACHE = []
        return _SEED_PROPERTIES_CACHE

    with open(SEED_PROPERTIES_PATH, "r", encoding="utf-8") as f:
        _SEED_PROPERTIES_CACHE = json.load(f)

    return _SEED_PROPERTIES_CACHE


def get_property_context(property_id: str):
    conn = get_conn()
    cur = conn.cursor()

    try:
        cur.execute(
            "SELECT set_config('app.current_property', %s, false)",
            (property_id,),
        )
        cur.execute(
            """
            SELECT name, COALESCE(property_config, '{}'::jsonb)
            FROM properties
            WHERE property_id = %s
            """,
            (property_id,),
        )
        row = cur.fetchone()

        if row:
            property_config = row[1] or {}
            if isinstance(property_config, str):
                try:
                    property_config = json.loads(property_config)
                except json.JSONDecodeError:
                    property_config = {}

            seed_record = next(
                (item for item in load_seed_properties() if item.get("property_id") == property_id),
                {},
            )
            merged_config = dict(seed_record)
            merged_config.update(property_config if isinstance(property_config, dict) else {})

            return {
                "property_id": property_id,
                "name": row[0],
                "property_config": merged_config,
            }

        seed_record = next(
            (item for item in load_seed_properties() if item.get("property_id") == property_id),
            None,
        )
        if seed_record:
            return {
                "property_id": property_id,
                "name": seed_record.get("name", property_id),
                "property_config": seed_record,
            }

        return {
            "property_id": property_id,
            "name": property_id,
            "property_config": {},
        }

    finally:
        cur.close()
        conn.close()


def best_line_match(question: str, lines: list[str]):
    question_text = normalize_text(question)
    question_tokens = token_set(question)

    best_score = 0.0
    best_line = None

    for line in lines:
        candidate = line.strip()
        if not candidate or candidate.startswith("#"):
            continue

        candidate_text = normalize_text(candidate)
        if candidate_text in question_text or question_text in candidate_text:
            return candidate

        candidate_tokens = token_set(candidate)
        if not candidate_tokens or not question_tokens:
            continue

        overlap = len(question_tokens & candidate_tokens)
        score = overlap / max(1, len(question_tokens))

        if score > best_score:
            best_score = score
            best_line = candidate

    if best_score >= 0.34:
        return best_line

    return None


def match_custom_faq(question: str, property_config: dict):
    faqs = property_config.get("custom_faqs") if isinstance(property_config, dict) else None
    if not isinstance(faqs, list):
        return None

    question_text = normalize_text(question)
    question_tokens = token_set(question)

    best_score = 0.0
    best_answer = None

    for faq in faqs:
        if not isinstance(faq, dict):
            continue

        faq_question = str(faq.get("q", "")).strip()
        faq_answer = faq.get("a")
        if not faq_question or not faq_answer:
            continue

        faq_text = normalize_text(faq_question)
        if faq_text in question_text or question_text in faq_text:
            return {
                "answer": faq_answer,
                "source": "property_config",
            }

        faq_tokens = token_set(faq_question)
        if not faq_tokens or not question_tokens:
            continue

        overlap = len(question_tokens & faq_tokens)
        score = overlap / max(1, len(faq_tokens))

        if score > best_score:
            best_score = score
            best_answer = faq_answer

    if best_answer is not None and best_score >= 0.5:
        return {
            "answer": best_answer,
            "source": "property_config",
        }

    return None


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

    context = get_property_context(property_id)

    custom_faq_match = match_custom_faq(question, context.get("property_config", {}))
    if custom_faq_match:
        return custom_faq_match

    path = f"kb/{property_id}.txt"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        line_match = best_line_match(question, lines)
        if line_match:
            return {
                "answer": line_match,
                "source": f"{property_id}.txt",
            }

    platform_path = "kb/platform.txt"
    if os.path.exists(platform_path):
        with open(platform_path, "r", encoding="utf-8") as f:
            platform_lines = f.readlines()

        line_match = best_line_match(question, platform_lines)
        if line_match:
            return {
                "answer": line_match,
                "source": "platform.txt",
            }

    return None

def detect_cross_tenant(question, property_id):

    q = normalize_text(question)

    seen_aliases = set()

    for tenant in get_all_properties():
        if tenant == property_id:
            continue

        seen_aliases.add(normalize_text(tenant))

        context = get_property_context(tenant)
        tenant_name = context.get("name")
        if tenant_name:
            seen_aliases.add(normalize_text(str(tenant_name)))

    for seed_record in load_seed_properties():
        tenant = seed_record.get("property_id")
        if tenant == property_id:
            continue

        if tenant:
            seen_aliases.add(normalize_text(str(tenant)))

        tenant_name = seed_record.get("name")
        if tenant_name:
            seen_aliases.add(normalize_text(str(tenant_name)))

    for alias in seen_aliases:
        if alias and alias in q:
            raise ValueError("Cross-tenant access blocked")

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