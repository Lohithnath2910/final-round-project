# Multi-Tenant Hospitality Management Assistant

A multi-tenant Hospitality Management System (HMS) assistant built for the Engineering Capstone.

# Live Deployments

Frontend

https://final-round-project.vercel.app/

Backend

https://final-round-project.onrender.com/

The platform combines:

- Conversation orchestration and lifecycle management
- Tenant-safe analytics through NL→SQL
- Hinglish-aware Retrieval-Augmented Generation (RAG)
- PostgreSQL Row Level Security (RLS)
- Queue-based workflow processing
- Multi-tenant knowledge bases

The primary focus of the project is correctness, tenant isolation, idempotency, SQL safety, and reproducibility.

---

# Architecture Overview

```text
Guest Message
      │
      ▼
POST /message
      │
      ▼
Intent Classification
      │
      ▼
Workflow Registry
      │
      ▼
workflow_jobs Queue
      │
      ▼
worker.py
      │
      ▼
Events / Side Effects


Owner Question
      │
      ▼
POST /ask
      │
      ├── Data Question
      │      ▼
      │   NL→SQL
      │      ▼
      │   PostgreSQL
      │
      └── Product Question
             ▼
             RAG
             ▼
      property_config
             ▼
         Tenant KB
             ▼
        platform KB
```

---

# Features

## Part A — Conversation Orchestration & Lifecycle

### Property Onboarding

```http
POST /property
```

Registers a new tenant property and stores:

- property metadata
- language preferences
- custom FAQs
- property-specific configuration

Property configuration is stored as JSONB and used by the assistant for tenant-specific responses.

---

### Guest Message Processing

```http
POST /message
```

Input:

```json
{
  "property_id": "hotel_a",
  "guest_id": "guest_001",
  "message_id": "msg_123",
  "text": "I'd like to book a room"
}
```

Supported intents:

- booking
- cancellation
- faq
- complaint
- wakeup

Workflow:

```text
Message
→ classify
→ route
→ create event
→ enqueue workflow job
→ worker processes asynchronously
```

---

### Intent Classification

Current implementation uses:

- deterministic rule-based classification
- confidence scoring
- human handoff for uncertain requests
- cancellation confirmation protection

Supported classifications:

| Intent | Example |
|----------|----------|
| booking | "I'd like to book a room" |
| cancellation | "Cancel my booking" |
| faq | "What's the wifi password?" |
| complaint | "The room is dirty" |
| wakeup | "Wake me up at 6am" |

Low-confidence requests are routed to a human workflow.

---

### Human Handoff

Requests below the configured confidence threshold are not automatically executed.

Example:

```text
maybe cancel my booking
```

Result:

```json
{
  "status": "confirmation_required"
}
```

This prevents accidental cancellations.

---

### False-Positive Protection

Cancellation workflows require higher confidence before execution.

Ambiguous cancellation requests:

```text
maybe cancel
thinking of cancelling
might cancel later
```

are routed to human review instead of automatic execution.

---

### Queue-Based Processing

Workflow side effects are processed asynchronously.

Architecture:

```text
POST /message
      │
      ▼
workflow_jobs
      │
      ▼
worker.py
      │
      ▼
done
```

Features:

- PostgreSQL-backed queue
- Atomic job claiming
- Background worker processing
- Durable storage
- Retry-ready architecture

Queue implementation:

```sql
FOR UPDATE SKIP LOCKED
```

ensures a job can only be claimed by one worker.

Job states:

- pending
- in_progress
- done
- failed

---

### Idempotency

Messages are idempotent using:

```sql
ON CONFLICT (message_id)
DO NOTHING
```

Benefits:

- Duplicate requests do not create duplicate side effects
- Safe retries
- Replay protection

---

### Lifecycle Events

```http
GET /events
```

Returns tenant-scoped lifecycle activity.

Examples:

- booking_requested
- cancellation_requested
- faq_received
- complaint_received
- wakeup_requested
- needs_human

---

### Bookings API

```http
GET /bookings
```

Returns bookings for the currently selected tenant only.

---

## Part B — Data Assistant

### Natural Language Analytics

```http
POST /ask
```

Example questions:

```text
How many bookings do I have?

What's my total revenue?

How much revenue came from MMT?

How many no-shows do I have?

Which room type earns the most revenue?
```

---

### NL→SQL

Questions are converted into safe, read-only SQL.

Properties:

- tenant-scoped
- parameterized
- schema-grounded
- deterministic
- read-only

No generated SQL is executed without validation.

---

### SQL Safety

The assistant blocks:

- DELETE
- UPDATE
- DROP
- ALTER
- UNION
- Multi-statement execution

Only safe SELECT queries are permitted.

---

### Cross-Tenant Protection

Example:

Tenant:

```text
hotel_b
```

Question:

```text
How many bookings does Hotel Surya have?
```

Response:

```json
{
  "detail": "Cross-tenant access blocked"
}
```

Cross-property access is rejected before query execution.

---

### Example Analytics Queries

#### Booking Count

Question:

```text
How many bookings do I have?
```

SQL:

```sql
SELECT COUNT(*)
FROM bookings
WHERE property_id = %s
```

---

#### Revenue

Question:

```text
What is my total revenue?
```

SQL:

```sql
SELECT COALESCE(SUM(amount_inr), 0)
FROM bookings
WHERE property_id = %s
```

---

#### MMT Revenue

Question:

```text
What's my MMT revenue?
```

SQL:

```sql
SELECT COALESCE(SUM(amount_inr), 0)
FROM bookings
WHERE property_id = %s
AND source = 'mmt'
```

---

### Hinglish-Aware RAG

The assistant supports mixed Hindi-English queries.

Examples:

```text
wifi ka password kya hai

parking hai kya

deposit kitna hai

rates kaise update karu

review ka reply kaise karu
```

---

### Retrieval Pipeline

RAG retrieval follows a strict priority order:

```text
property_config
        │
        ▼
Tenant Knowledge Base
        │
        ▼
Platform Knowledge Base
        │
        ▼
Refusal
```

Property-specific information always overrides platform-wide information.

---

### Knowledge Base Structure

```text
kb/
├── hotel_a.txt
├── hotel_b.txt
└── platform.txt
```

---

### Retrieval Strategy

Implementation uses:

- normalization
- synonym expansion
- token overlap scoring
- confidence thresholds
- paragraph chunking

No embeddings are used.

No vector database is used.

No external retrieval service is used.

---

### Citations

Every RAG answer includes a source citation.

Example:

```json
{
  "answer": "Free WiFi is available throughout the property.",
  "citation": "hotel_a.txt"
}
```

---

### Refusal Behavior

Unknown questions are refused rather than fabricated.

Example:

Question:

```text
Quantum physics on Mars
```

Response:

```text
I don't have enough information to answer that.
```
---
# Part C — Owner Console

The Owner Console is a mobile-first React + TypeScript SPA that provides operational visibility into property activity and exposes the Data Assistant.

Features:

- Live-ish lifecycle feed
- Bookings dashboard
- Ask Assistant interface
- SQL visibility for analytics queries
- Loading states
- Empty states
- Error states

The frontend contains no business logic.

All orchestration, analytics, security checks, and tenant isolation remain in the backend.

### Frontend Stack

- React
- TypeScript
- Vite
- Tailwind CSS
- Playwright

---

# Part D — Testing & QA

Testing was designed around the highest-risk failure modes:

- cross-tenant leakage
- unsafe SQL execution
- incorrect workflow automation
- duplicate processing
- hallucinated assistant responses

### Test Results

Backend Tests:

66 passing

Frontend E2E Tests:

8 passing

Total:

74 passing tests

Pass Rate:

100%
---

# Multi-Tenant Isolation

Tenant isolation is enforced using PostgreSQL Row Level Security (RLS).

Protected tables:

- properties
- rooms
- rates
- bookings
- messages
- events
- workflow_jobs

Tenant context:

```sql
SET app.current_property
```

Policy:

```sql
property_id =
current_setting(
    'app.current_property',
    true
)
```

Tenant isolation is enforced at the database layer.

---

# Security Guards

| Guard | Implementation |
|---------|---------|
| Tenant isolation | PostgreSQL RLS |
| Idempotency | ON CONFLICT(message_id) |
| Human handoff | Confidence threshold |
| Cancellation guard | Confirmation required |
| Cross-tenant block | Property-name detection |
| SQL injection block | Pattern validation |
| Destructive SQL block | Read-only SQL enforcement |
| RAG citation | Mandatory source citation |
| Hallucination prevention | Refusal on low confidence |

---

# Performance

Classification Benchmark

1000 requests

| Metric | Value |
|----------|----------|
| Average | 0.0304 ms |
| P50 | 0.0257 ms |
| P95 | 0.0545 ms |
| P99 | 0.1179 ms |
| Min | 0.0102 ms |
| Max | 0.4122 ms |

---

/message End-to-End Latency

1000 requests

| Metric | Value |
|----------|----------|
| Average | 580.3383 ms |
| P50 | 543.8981 ms |
| P95 | 793.8872 ms |
| P99 | 1073.0684 ms |
| Min | 428.9723 ms |
| Max | 3791.7402 ms |


---

# Testing

74 tests passing (66 backend + 8 Playwright E2E)

Backend:

66 passing

Frontend:

8 Playwright E2E tests passing

Coverage:

- intent classification
- workflow routing
- queue processing
- tenant isolation
- RLS enforcement
- idempotency
- cross-tenant protection
- SQL injection blocking
- destructive SQL blocking
- Hinglish RAG
- citation generation
- refusal behavior
- frontend analytics flow
- frontend RAG flow
- frontend property switching
Run:

```bash
python -m pytest -v (in backend folder)
npx playwright test --header (in frontend folder)
```

---

# Technology Stack

Backend

- FastAPI
- PostgreSQL
- psycopg2

Frontend

- React
- TypeScript
- Vite
- Tailwind CSS
- Playwright

Security

- PostgreSQL Row Level Security
- Parameterized SQL
- Input validation

Queue

- workflow_jobs
- worker.py
- FOR UPDATE SKIP LOCKED

Testing

- pytest

Deployment

- Backend: Render
- Frontend: Vercel
- Database: Supabase PostgreSQL

---

# Repository Structure

```text
backend/
├── app/
│   ├── main.py
│   ├── assistant.py
│   └── db.py
│
├── worker.py
├── benchmark_classify.py
├── tests/
└── kb/

frontend/
├── src/
├── tests/
└── playwright.config.ts

seed/
├── schema.sql
├── data.sql
├── seed_with_rls.sql
└── properties.json

kb/
├── hotel_a.txt
├── hotel_b.txt
└── platform.txt
```

---

# Current Status

## Part A

Complete

## Part B

Complete

## Part C

Complete

## Part D

Complete

### Implemented

- Multi-tenant RLS isolation
- Workflow orchestration
- Queue processing
- Human handoff
- Idempotency
- Tenant-safe analytics
- Hinglish RAG
- Citations
- React Owner Console
- Automated backend testing
- Automated frontend E2E testing

### Not Implemented

- OTA integration
- OTA retry/backoff
- LLM fallback classifier

---