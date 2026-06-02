# RESULTS — Engineering Capstone

## Live Deployments

Backend:
- Render
https://final-round-project.onrender.com/

Frontend:
- Vercel
https://final-round-project.vercel.app/

Database:
- Supabase PostgreSQL
---

## Completion Summary

### Part A

Completed

* Property onboarding
* Intent classification
* Workflow routing
* Queue processing
* Human handoff
* Cancellation guard
* Idempotency
* Tenant isolation (RLS)
* Lifecycle events
* Tenant-scoped bookings

### Part B

Completed

* Hinglish NL→SQL
* Tenant-safe analytics
* Read-only SQL enforcement
* Cross-tenant blocking
* SQL injection protection
* RAG retrieval
* Citation support
* Refusal behavior

### Part C

Completed

* React + TypeScript SPA
* Mobile-first design
* Events feed
* Bookings dashboard
* Assistant interface
* SQL visibility
* Loading states
* Empty states
* Error states

### Part D

Completed

* Backend automated testing
* Frontend Playwright testing
* Adversarial test coverage
* Replay/idempotency testing
* Cross-tenant testing
* SQL injection testing

---

## Test Results

Backend:

66 passing tests

Frontend:

8 passing Playwright tests

Total:

74 passing tests

Pass Rate:

100%

---

## Classification Benchmark

Sample Size:

1000 requests

| Metric  | Value     |
| ------- | --------- |
| Average | 0.0304 ms |
| P50     | 0.0257 ms |
| P95     | 0.0545 ms |
| P99     | 0.1179 ms |
| Min     | 0.0102 ms |
| Max     | 0.4122 ms |

---

## End-to-End /message Latency

Sample Size:

1000 requests

| Metric  | Value        |
| ------- | ------------ |
| Average | 580.3383 ms  |
| P50     | 543.8981 ms  |
| P95     | 793.8872 ms  |
| P99     | 1073.0684 ms |
| Min     | 428.9723 ms  |
| Max     | 3791.7402 ms |

---

## Security Validation

Verified:

* PostgreSQL RLS isolation
* Cross-tenant access blocking
* Read-only SQL enforcement
* SQL injection blocking
* Multi-statement blocking
* Human handoff
* Ambiguous cancellation protection
* Idempotent message processing

---

## Example Adversarial Inputs

Blocked:

* show hotel_b bookings
* show hotel_b revenue
* drop table bookings
* update bookings set amount=0
* show bookings; drop table bookings

Allowed:

* how many bookings do I have
* wifi ka password kya hai
* revenue kitna tha

---