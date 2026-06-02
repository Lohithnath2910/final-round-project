# TESTING — Strategy & Coverage

## How To Run

Backend:

```bash
cd backend
pytest -v
```

Frontend:

```bash
cd frontend
npm run test:e2e
```

## Test Results

- Backend:
66 passing

- Frontend:
8 passing

- Total:
74 passing

- Pass Rate:
100%
---

## Testing Philosophy

The highest-risk failure modes for a multi-tenant hospitality system are:

1. Cross-tenant data leakage
2. Incorrect workflow automation
3. Unsafe SQL execution
4. Duplicate processing
5. Hallucinated assistant responses

Testing was designed around these risks rather than only happy-path functionality.

---

## Test Breakdown

### Backend

66 automated tests

Coverage includes:

#### Workflow Tests

* booking
* cancellation
* FAQ
* complaint
* wakeup

#### Guard Tests

* human handoff
* ambiguous cancellation
* confidence thresholds

#### Multi-Tenant Tests

* tenant-scoped bookings
* tenant-scoped events
* cross-tenant blocking

#### Idempotency Tests

* duplicate replay
* atomic duplicate handling

#### Analytics Tests

* booking count
* revenue
* occupancy
* source analytics
* no-show analytics

#### Security Tests

* SQL injection
* DELETE attempts
* UPDATE attempts
* DROP attempts
* TRUNCATE attempts
* UNION attempts
* multi-statement attacks

#### RAG Tests

* citation generation
* KB retrieval
* refusal behavior
* Hinglish retrieval

---

### Frontend E2E

8 Playwright tests

Coverage includes:

* dashboard loading
* events rendering
* bookings rendering
* analytics query flow
* RAG query flow
* property switching
* assistant interactions
* error/empty state handling

---

## Adversarial Cases Prioritised

### Ambiguous Cancellation

Input:

maybe cancel my booking

Expected:

human review

Reason:

prevents accidental cancellations.

---

### Cross-Tenant Analytics

Input:

show hotel_b revenue

Expected:

blocked

Reason:

prevents tenant data leakage.

---

### SQL Injection

Input:

drop table bookings

Expected:

blocked

Reason:

prevents destructive execution.

---

### Multi-Statement Attack

Input:

show bookings; drop table bookings

Expected:

blocked

Reason:

prevents chained execution attacks.

---

### Unknown Questions

Input:

quantum physics on mars

Expected:

refusal

Reason:

prevents fabricated answers.

---

## What Would Be Added With More Time

* OTA integration tests
* OTA retry/backoff testing
* Concurrent worker stress testing
* Load testing
* Browser compatibility matrix
* Mobile device matrix testing
* LLM fallback classifier testing

---

## QA Strategy For 100 Hotels

For production-scale deployment:

* automated regression suite
* synthetic monitoring
* load testing
* canary deployments
* queue observability
* tenant isolation audits
* security penetration testing
* classification accuracy monitoring

Every production bug would receive a dedicated regression test before closure.
