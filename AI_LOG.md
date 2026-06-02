# AI_LOG — Engineering Capstone

## Tools Used

### ChatGPT

Used for:

* Architecture review
* Security review
* RLS validation
* Queue design review
* Testing strategy
* Playwright E2E test planning
* Documentation drafting
* Rubric audits
* Bug investigation and fixes

### GitHub Copilot

Used for:

* FastAPI scaffolding assistance
* Refactoring assistance
* Test generation assistance
* Codebase navigation
* Boilerplate generation

### Stitch AI

Used only as visual inspiration for portions of the frontend design.

No generated application logic was used.

---

## Most Useful AI-Assisted Tasks

### Security Review

AI helped identify:

* cross-tenant leakage risks
* missing SQL guard cases
* idempotency race-condition risks
* ambiguous cancellation edge cases

### Testing Strategy

AI helped expand coverage from basic happy-path tests to:

* adversarial tests
* replay/idempotency tests
* SQL injection tests
* cross-tenant tests
* Playwright frontend E2E tests

### Documentation

AI assisted in:

* benchmark reporting
* architecture explanations
* testing strategy documentation
* deployment documentation

---

## Where AI Was Wrong And How It Was Caught

### Initial Frontend E2E Tests

Problem:

Playwright tests assumed UI elements that did not actually exist.

Examples:

* assumed native select element
* incorrect button selectors
* incorrect dashboard labels

How It Was Caught:

Tests failed during execution.

Resolution:

Selectors were rewritten against the actual React components and verified against the live UI.

---

### SQL Guard Coverage

Problem:

Initial suggestions focused on DROP and DELETE protection.

How It Was Caught:

Additional adversarial tests revealed UPDATE and TRUNCATE were not explicitly blocked.

Resolution:

Added broader destructive-SQL detection and corresponding tests.

---

### Documentation Drift

Problem:

Earlier documentation still referenced:

* 36 tests
* backend-only completion
* outdated benchmarks

How It Was Caught:

Final repository audit before submission.

Resolution:

Documentation updated to reflect deployed frontend, expanded test coverage, and final benchmark results.

---

## Design Decisions

### Intent Classifier

Decision:

Deterministic rule-based classifier with confidence scoring.

Why:

Predictable behavior was prioritized over LLM variability.

The classifier supports:

* booking
* cancellation
* FAQ
* complaint
* wakeup

Low-confidence requests are routed to human review.

---

### Tenant Isolation (RLS)

Decision:

PostgreSQL Row Level Security.

Why:

Tenant isolation is enforced at the database layer rather than relying solely on application code.

Additional application-level checks exist as defense in depth.

---

### Idempotency + Queue

Decision:

workflow_jobs queue with worker consumer.

Why:

Separates request handling from side effects.

Messages use:

ON CONFLICT(message_id) DO NOTHING

to prevent duplicate processing.

---

### NL→SQL Guardrails

Decision:

Template-driven SQL generation.

Why:

Provides deterministic behavior and prevents unsafe generated SQL.

Safety guarantees:

* SELECT only
* tenant-scoped
* parameterized
* cross-tenant blocked

---

### RAG + Citation

Decision:

Deterministic retrieval using token matching and confidence scoring.

Why:

Simple, reproducible, and easy to validate.

Retrieval order:

property_config
→ tenant KB
→ platform KB
→ refusal

All successful retrievals include citations.

---

### Console Design

Decision:

Mobile-first React + TypeScript SPA.

Why:

Simple operational dashboard focused on:

* lifecycle visibility
* booking visibility
* assistant access

Loading, empty, and error states were prioritized over visual complexity.

---

## AI Suggestions Rejected

### Vector Database

Rejected because:

* unnecessary for project scope
* deterministic retrieval was sufficient

### External Embeddings

Rejected because:

* increased complexity
* introduced additional dependencies

### Redis/Celery Queue

Rejected because:

workflow_jobs + worker.py satisfied project requirements with lower operational overhead.

---

