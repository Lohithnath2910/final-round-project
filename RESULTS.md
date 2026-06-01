# RESULTS — Engineering Capstone

## Summary

### Backend Status

**Part A:** Functionally Complete
**Part B:** Complete & Tested

* 36/36 tests passing
* PostgreSQL Row Level Security (RLS) enabled
* Queue-based workflow processing implemented
* Tenant-safe NL→SQL assistant
* Hinglish-aware RAG with citations
* Cross-tenant access prevention
* SQL injection protection
* Human handoff for low-confidence requests

---

## Part A — Conversation Orchestration & Lifecycle

### Requirements Coverage

| Requirement                       | Status                  |
| --------------------------------- | ----------------------- |
| POST /property                    | ✅                       |
| property_config onboarding        | ✅                       |
| POST /message                     | ✅                       |
| Intent classification             | ✅                       |
| WorkflowRegistry routing          | ✅                       |
| Queue-based processing            | ✅                       |
| Human handoff                     | ✅                       |
| False-positive cancellation guard | ✅                       |
| Idempotent message_id             | ✅                       |
| RLS tenant isolation              | ✅                       |
| GET /events                       | ✅                       |
| GET /bookings                     | ✅                       |
| Classify latency benchmark        | ✅                       |
| Mock OTA integration              | Bonus (not implemented) |

---

## Classification Performance

Benchmark executed using `benchmark_classify.py`.

| Metric  | Value   |
| ------- | ------- |
| Average | 0.03 ms |
| P50     | 0.02 ms |
| P95     | 0.04 ms |
| P99     | 0.14 ms |
| Min     | 0.01 ms |
| Max     | 0.14 ms |

Benchmark sample size: 100 requests.

---

## Queue Processing

Workflow processing is executed asynchronously through a PostgreSQL-backed queue.

Architecture:

Message
→ workflow_jobs
→ worker.py
→ claim job
→ process
→ done

Implementation details:

* workflow_jobs table stores pending work
* worker.py consumes jobs asynchronously
* Atomic job claiming via FOR UPDATE SKIP LOCKED
* Status transitions:

  * pending
  * in_progress
  * done
  * failed

Verified in deployment:

* Pending jobs successfully consumed
* Jobs transitioned to done state
* Queue worker operating independently of API requests

---

## Tenant Isolation (RLS)

RLS enabled on:

* properties
* rooms
* rates
* bookings
* messages
* events
* workflow_jobs

Policy:

property_id = current_setting('app.current_property', true)

Tenant context set per request using:

SET app.current_property

Isolation enforced at PostgreSQL layer.

---

## Idempotency Proof

Message insert:

```sql
INSERT ...
ON CONFLICT (message_id)
DO NOTHING
RETURNING message_id
```

Result:

* Replayed message_id produces no duplicate side-effects
* Duplicate requests return status=duplicate
* Event count remains unchanged

---

## Human Handoff Proof

Example:

Input:

"maybe cancel my booking"

Classification:

* intent = cancellation
* confidence = 0.40

Result:

status = confirmation_required

No cancellation executed automatically.

---

## Part B — Data Assistant

### Example 1

Question:

How many bookings do I have?

SQL:

```sql
SELECT COUNT(*)
FROM bookings
WHERE property_id = %s
```

Answer:

Booking count returned for current tenant only.

---

### Example 2

Question:

What is my MMT revenue?

SQL:

```sql
SELECT COALESCE(SUM(amount_inr),0)
FROM bookings
WHERE property_id = %s
AND source='mmt'
```

Answer:

Tenant-specific MMT revenue.

---

### Example 3

Question:

Which room type earns the most revenue?

SQL:

```sql
SELECT room_type,
       SUM(amount_inr) AS revenue
FROM bookings
WHERE property_id = %s
GROUP BY room_type
ORDER BY revenue DESC
LIMIT 1
```

Answer:

Highest revenue-generating room type.

---

## Cross-Tenant Protection

Blocked request:

"What bookings does Hotel Surya have?"

Context:

property_id = hotel_b

Response:

400 Bad Request

Reason:

Cross-tenant access blocked.

---

## SQL Injection Protection

Blocked request:

"DROP TABLE bookings"

Response:

400 Bad Request

Reason:

Unsafe SQL detected.

---

## RAG Example

Question:

wifi password?

Source:

hotel_a.txt

Confidence:

0.92

Citation:

hotel_a.txt

---

## Test Results

Total Tests:

36

Passing:

36

Failing:

0

Pass Rate:

100%

---

## Technology Stack

Backend:

* FastAPI
* PostgreSQL
* psycopg2

Queue:

* PostgreSQL workflow_jobs
* worker.py

Testing:

* pytest

Deployment:

* Render
* Supabase PostgreSQL
