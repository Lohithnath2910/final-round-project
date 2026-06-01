# TESTING — strategy

> Tell us how you think about correctness. This doc is read closely.

## How to run
```bash
cd backend
python -m pytest -v  # All 36 tests
python -m pytest backend/tests/test_part_a.py -v  # Part A only (19 tests)
python -m pytest backend/tests/test_part_b.py -v  # Part B only (13 tests)
python -m pytest backend/tests/test_hinglish_rag.py -v  # RAG coverage (4 tests)
```

## Test strategy

### What I chose to test and **why**:
- **Message classification** (rules-based, deterministic): intent accuracy + confidence scoring for booking/cancellation/faq/complaint/wakeup
- **Tenant isolation**: RLS row-level security enforced at the database layer via `app.current_property` session variable; tests verify property A cannot see property B's data
- **Idempotency**: replaying the same `message_id` results in exactly one database insert (ON CONFLICT DO NOTHING)
- **Intent routing & queuing**: messages are classified, queued to `workflow_jobs`, and events recorded; all under RLS
- **Cross-tenant blocking**: questions mentioning other properties' names are rejected outright (tokenized matching, excludes generic tokens)
- **NL→SQL safety**: deterministic templates with parameterized tenant scope (`WHERE property_id = %s`), no LLM SQL execution
- **RAG with citations**: Hinglish normalization + token-overlap scoring yields deterministic chunk matches with confidence scores and KB file citations
- **Injection & destructive SQL blocking**: patterns like DROP, DELETE, UPDATE, UNION, semicolons are blocked before execution

### Unit vs integration vs e2e split:
- **Unit** (5 tests): Hinglish normalization, synonym expansion, token overlap scoring, custom FAQ matching, KB chunk selection
- **Integration** (19 tests Part A): Full message pipeline — classify → store → queue → verify events + RLS isolation
- **Integration** (13 tests Part B): NL→SQL execution + RAG fallback; data accuracy and safety checks
- **E2E** (36 total): All tests hit the live FastAPI endpoints via TestClient; database is real (not mocked)

### Negative / adversarial cases I prioritised (and why):
1. **Ambiguous cancellation** (confidence 0.40) → routed to human, NOT auto-executed
2. **Cross-tenant name mention** (`question="How many bookings does Hotel Surya have?"` from hotel_b property) → rejected
3. **Injection attempts** (`question="drop table messages; select * from properties"`) → blocked before parsing
4. **Unknown questions** (no FAQ match, no KB match) → return refusal, not hallucination
5. **Duplicate message_id** → second POST returns `"status": "duplicate"`, no double side-effect
6. **Tenant scope in NL→SQL** → verified by fetching SQL and checking `WHERE property_id = %s` is present
7. **Hinglish variants** (`wifi ka password`, `internet password`) → all normalized to same canonical form

## Guard coverage (must address each)
| Guard | How I test it | Covered? |
|---|---|---|
| **Tenant isolation (A can't read B)** | `test_bookings_tenant_scope_hotel_a`, `_hotel_b`, `test_no_hotel_b_booking_in_hotel_a_response` | ✅ RLS at DB layer + app-level verification |
| **Idempotency (replay = 1 effect)** | `test_duplicate_message`, `test_duplicate_message_is_atomic_and_single_effect` | ✅ ON CONFLICT DO NOTHING + unique constraint |
| **False-positive guard (ambiguous → no auto-cancel)** | `test_ambiguous_cancel_goes_human` | ✅ Routes to human, returns `status: confirmation_required` |
| **NL→SQL cross-tenant blocked** | `test_cross_tenant_blocked` (in Part B) | ✅ Tokenized name-matching rejects attempt |
| **NL→SQL destructive/injection blocked** | `test_delete_blocked`, `test_union_blocked` | ✅ Pattern matching + require `SELECT` + require `property_id` |
| **RAG citation present / unanswerable refused** | `test_room_rate_rag`, `test_unknown_question_refused` | ✅ Citation in response + refusal on no match |
| **Console renders + handles error/empty** | (Part C — React app, not included in backend tests) | 🚧 Frontend scope |

## What I'd add with more time
- Concurrent message handling (load test with 100+ simultaneous messages)
- OTA mock server resilience (retry/backoff for 429/500 responses)
- Worker job backoff + short-circuit after N failures
- LLM fallback for intent classification (currently rules-only)
- Semantic RAG scoring (embeddings-based vs. token overlap)
- Custom FAQ edge cases (fuzzy matching, partial matches)
- Multi-language classification (Hinglish, Tamil, Telugu)
- Realtime event subscriptions (WebSocket or Supabase Realtime)

## How I'd structure QA for 100 real hotels
- **Regression Suite**: Keep the 36 tests; add new test per P1 bug or new feature
- **Load Testing**: Locust/k6 simulation with realistic message volume per property
- **Multi-tenant edge cases**: race conditions (concurrent message_id), RLS bypass attempts, time-zone edge cases
- **Monitoring**: Track intent accuracy by property, classify latency P99, queue throughput, failed job rates
- **CI Gating**: Block deploys if test suite < 100%, classify P95 > 500ms, or RLS checks fail
- **Audit Logging**: Log all cross-tenant block attempts + injection attempts for forensics
- **Compliance**: GDPR data deletion tests, PII scrubbing in logs, tenant data isolation audits


# TESTING

## Running Tests

Execute the entire test suite:

```bash
pytest -v
```

Current status:

* 36 tests passing
* 0 failures

---

## Test Coverage

### Part A — Conversation Lifecycle

Coverage:

* Intent classification
* Workflow routing
* Human handoff
* Ambiguous cancellation protection
* Tenant isolation
* Idempotency
* Property onboarding
* Queue creation
* Events retrieval
* Bookings retrieval

---

### Part B — Data Assistant

Coverage:

* NL→SQL generation
* Revenue analytics
* Booking analytics
* No-show analytics
* RAG retrieval
* Citation generation
* Refusal handling

---

### Security Coverage

Verified:

* Cross-tenant blocking
* SQL injection blocking
* DELETE blocking
* UNION blocking
* Unsafe SQL blocking

---

### Hinglish Coverage

Verified:

* Query normalization
* Synonym expansion
* FAQ retrieval
* Citation generation
* Refusal behavior

---

## End-to-End Validation

### Property Creation

```bash
POST /property
```

Expected:

* Property created
* property_config stored

---

### Message Flow

```bash
POST /message
```

Expected:

* Intent classified
* Event generated
* Workflow job queued

---

### Queue Processing

Worker:

```bash
python worker.py
```

Expected:

* Pending jobs claimed
* Status updated to done

---

### Analytics

```bash
POST /ask
```

Expected:

* Read-only SQL generated
* Tenant-scoped answer returned

---

### Product Help

```bash
POST /ask
```

Expected:

* KB retrieval
* Citation returned

---

## Verification Checklist

* [x] Tenant isolation
* [x] RLS policies
* [x] Idempotency
* [x] Human handoff
* [x] Queue processing
* [x] Cross-tenant protection
* [x] Injection protection
* [x] RAG citations
* [x] Refusal behavior
* [x] Hinglish support
