import json
import os
import re
from app.db import get_conn

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
KB_DIR = os.path.join(BACKEND_DIR, "kb")
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
    "ka",
    "ke",
    "ki",
    "hai",
    "hain",
    "ho",
    "kya",
    "kab",
    "kaise",
    "karu",
    "karna",
    "kar",
    "mein",
    "me",
    "se",
    "par",
    "pe",
    "mujhe",
    "mera",
    "meri",
    "mere",
    "work",
    "work?",
}

SYNONYMS = {
    "wifi": [
        "wifi",
        "internet",
        "net",
    ],
    "parking": [
        "parking",
        "car parking",
        "vehicle parking",
    ],
    "checkout": [
        "checkout",
        "check out",
        "room vacate",
    ],
    "review": [
        "review",
        "rating",
        "feedback",
    ],
    "rate": [
        "rate",
        "price",
        "pricing",
        "room rate",
    ],
    "food": [
        "food",
        "mess",
        "meal",
    ],
    "shuttle": [
        "shuttle",
        "airport shuttle",
        "airport pickup",
    ],
    "onboarding": [
        "onboarding",
        "setup",
        "setup process",
        "add property",
    ],
    "deposit": [
        "deposit",
        "security deposit",
        "advance",
    ],
    "rent": [
        "rent",
        "monthly rent",
        "rent price",
    ],
    "booking": [
        "booking",
        "bookings",
        "reservation",
    ],
    "revenue": [
        "revenue",
        "income",
        "earnings",
    ],
}

QUERY_NORMALIZATIONS = {
    "wifi password": [
        "wifi ka password",
        "internet password",
        "net password",
    ],
    "parking": [
        "car parking",
        "vehicle parking",
    ],
    "checkout": [
        "checkout kab hai",
        "check out time",
        "room kab khali karna hai",
    ],
    "rate update": [
        "rate kaise change karu",
        "price update",
        "room rate update",
    ],
    "review response": [
        "review ka reply kaise karu",
        "ota review response",
    ],
    "onboarding": [
        "how does onboarding work",
        "onboarding takes",
        "how to add property",
    ],
    "shuttle": [
        "airport shuttle",
        "do you have airport shuttle",
        "airport pickup available",
    ],
    "deposit": [
        "deposit",
        "security deposit",
        "deposit refundable",
    ],
    "rent": [
        "monthly rent",
        "rent price",
    ],
}

FAQ_CONFIDENCE_THRESHOLD = 0.35
KB_CONFIDENCE_THRESHOLD = 0.30
PLATFORM_CONFIDENCE_THRESHOLD = 0.30

SQL_BLOCKED_PATTERNS = [
    "drop",
    "delete",
    "update",
    "insert",
    "alter",
    ";",
    "--",
    "union",
    "information_schema",
    "pg_catalog",
]

QUESTION_BLOCKED_PATTERNS = [
    "drop",
    "delete",
    "insert",
    "alter",
    ";",
    "--",
    "union",
    "information_schema",
    "pg_catalog",
]


def normalize_text(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def _replace_phrase(text: str, phrase: str, replacement: str) -> str:
    pattern = r"\b" + re.escape(phrase) + r"\b"
    return re.sub(pattern, replacement, text)


def normalize_query(question: str) -> str:
    normalized = normalize_text(question)

    for canonical, variants in sorted(
        QUERY_NORMALIZATIONS.items(),
        key=lambda item: (-len(item[0]), len(item[1])),
    ):
        for variant in sorted(variants, key=len, reverse=True):
            normalized = _replace_phrase(normalized, normalize_text(variant), canonical)

    return re.sub(r"\\s+", " ", normalized).strip()


def token_set(text: str) -> set[str]:
    tokens = [token for token in normalize_query(text).split() if len(token) > 1]
    return {token for token in tokens if token not in STOPWORDS}


def expand_query_terms(question: str) -> set[str]:
    normalized = normalize_query(question)
    terms = token_set(normalized)

    for canonical, variants in SYNONYMS.items():
        canonical_terms = token_set(canonical)
        if terms & canonical_terms:
            terms.update(canonical_terms)
            for variant in variants:
                terms.update(token_set(variant))
            continue

        for variant in variants:
            variant_terms = token_set(variant)
            if variant_terms and variant_terms <= terms:
                terms.update(canonical_terms)
                terms.update(variant_terms)
                break

    return terms


def split_chunks(text: str) -> list[str]:
    chunks = [chunk.strip() for chunk in re.split(r"\n\s*\n+", text) if chunk.strip()]
    if chunks:
        return chunks
    stripped = text.strip()
    return [stripped] if stripped else []


def score_overlap(question_terms: set[str], candidate_text: str) -> float:
    candidate_terms = token_set(candidate_text)
    if not question_terms or not candidate_terms:
        return 0.0

    overlap = len(question_terms & candidate_terms)
    if overlap == 0:
        return 0.0

    coverage = overlap / max(1, len(question_terms))
    density = overlap / max(1, len(candidate_terms))
    return round((coverage * 0.75) + (density * 0.25), 4)


def best_chunk_match(question: str, chunks: list[str], threshold: float):
    question_terms = expand_query_terms(question)
    normalized_question = normalize_query(question)

    best_score = 0.0
    best_chunk = None

    for chunk in chunks:
        candidate = chunk.strip()
        if not candidate:
            continue

        normalized_candidate = normalize_query(candidate)
        if normalized_candidate and (
            normalized_candidate in normalized_question
            or normalized_question in normalized_candidate
        ):
            return candidate, 1.0

        score = score_overlap(question_terms, candidate)
        if score > best_score:
            best_score = score
            best_chunk = candidate

    if best_chunk is not None and best_score >= threshold:
        return best_chunk, best_score

    return None, 0.0


def score_custom_faq(question: str, faq_question: str) -> float:
    question_terms = expand_query_terms(question)
    faq_terms = token_set(faq_question)
    if not question_terms or not faq_terms:
        return 0.0

    overlap = len(question_terms & faq_terms)
    if overlap == 0:
        return 0.0

    coverage = overlap / max(1, len(question_terms))
    density = overlap / max(1, len(faq_terms))
    return round((coverage * 0.75) + (density * 0.25), 4)


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

    best_score = 0.0
    best_match = None

    for faq in faqs:
        if not isinstance(faq, dict):
            continue

        faq_question = str(faq.get("q", "")).strip()
        faq_answer = faq.get("a")
        if not faq_question or not faq_answer:
            continue

        faq_text = normalize_query(faq_question)
        question_text = normalize_query(question)
        if faq_text and (
            faq_text in question_text
            or question_text in faq_text
        ):
            return {
                "answer": faq_answer,
                "citation": "property_config",
                "source": "property_config",
                "confidence": 1.0,
            }

        score = score_custom_faq(question, faq_question)

        if score > best_score:
            best_score = score
            best_match = faq_answer

    if best_match is not None and best_score >= FAQ_CONFIDENCE_THRESHOLD:
        return {
            "answer": best_match,
            "citation": "property_config",
            "source": "property_config",
            "confidence": best_score,
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
        or "no_show" in q
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

    for word in SQL_BLOCKED_PATTERNS:
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

    path = os.path.join(KB_DIR, f"{property_id}.txt")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            chunks = split_chunks(f.read())

        chunk_match, confidence = best_chunk_match(question, chunks, KB_CONFIDENCE_THRESHOLD)
        if chunk_match:
            return {
                "answer": chunk_match,
                "citation": f"{property_id}.txt",
                "source": f"{property_id}.txt",
                "confidence": confidence,
            }

    platform_path = os.path.join(KB_DIR, "platform.txt")
    if os.path.exists(platform_path):
        with open(platform_path, "r", encoding="utf-8") as f:
            chunks = split_chunks(f.read())

        chunk_match, confidence = best_chunk_match(question, chunks, PLATFORM_CONFIDENCE_THRESHOLD)
        if chunk_match:
            return {
                "answer": chunk_match,
                "citation": "platform.txt",
                "source": "platform.txt",
                "confidence": confidence,
            }

    return None

def detect_cross_tenant(question, property_id):

    q = normalize_query(question)
    # Under RLS, enumerating properties via DB may return no rows for non-privileged
    # sessions. Use the seed properties as authoritative for cross-tenant name checks.

    # tokenized question for robust matching
    q_tokens = token_set(question)

    GENERIC_TOKENS = {"hotel", "stay", "pg", "inn", "residence", "property"}

    for seed_record in load_seed_properties():
        tenant = seed_record.get("property_id")
        if not tenant or tenant == property_id:
            continue

        # direct property_id mention (normalized)
        if normalize_text(str(tenant)) in q:
            raise ValueError("Cross-tenant access blocked")

        tenant_name = seed_record.get("name", "")
        if not tenant_name:
            continue

        name_tokens = token_set(tenant_name)
        if not name_tokens:
            continue

        intersect = name_tokens & q_tokens
        if not intersect:
            continue

        # block only if intersecting tokens contain at least one non-generic token
        if any(tok not in GENERIC_TOKENS for tok in intersect):
            raise ValueError("Cross-tenant access blocked")

    return True

def detect_injection(question: str):

    q = question.lower()

    for pattern in QUESTION_BLOCKED_PATTERNS:
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