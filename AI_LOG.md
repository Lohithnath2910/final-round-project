# AI_LOG — Engineering Capstone

## Tools used
-
## Most useful prompts
-
## Where AI was WRONG / gave broken output, and how you caught it
- (be specific per part: inline side-effects? RLS missed? LLM SQL without tenant filter? hallucinated column? desktop-only UI?)
## Design decisions (2-3 lines each, why)
- Intent classifier:
- Tenant isolation (RLS):
- Idempotency + queue:
- NL->SQL guardrails:
- RAG + citation:
- Console realtime + states:


# AI_LOG

## AI Tools Used

### GitHub Copilot

Used for:

* FastAPI scaffolding
* Test generation
* SQL query generation
* Refactoring
* Documentation drafts

### ChatGPT

Used for:

* Architecture review
* Security review
* RLS validation
* Multi-tenant design review
* Queue design review
* RAG design review
* Evaluation-readiness audits

---

## Major Design Decisions

### Multi-Tenancy

Decision:

Use PostgreSQL Row Level Security.

Reason:

Tenant isolation enforced at database layer rather than relying solely on application code.

---

### Queue Architecture

Decision:

Use PostgreSQL workflow_jobs table.

Reason:

Simple, durable, and sufficient for capstone requirements.

Implementation:

workflow_jobs
+
worker.py
+
FOR UPDATE SKIP LOCKED

---

### RAG

Decision:

Deterministic retrieval.

Reason:

Reproducible results without external dependencies.

Implementation:

property_config
→ tenant KB
→ platform KB
→ refusal

---

### NL→SQL

Decision:

Template-driven SQL generation.

Reason:

Prevents hallucinated SQL and simplifies security validation.

---

## Mistakes Found During Development

### RLS Not Present In Repository

Problem:

Policies existed only in Supabase.

Impact:

Fresh database setup would not reproduce tenant isolation.

Resolution:

Added all RLS policies and ALTER TABLE ENABLE ROW LEVEL SECURITY statements to schema.sql.

---

### Non-Atomic Idempotency

Problem:

Initial implementation used read-before-write checks.

Impact:

Potential race conditions.

Resolution:

Replaced with:

```sql
ON CONFLICT (message_id)
DO NOTHING
```

---

### Cross-Tenant Detection

Problem:

Original approach depended on database lookups.

Impact:

Could fail under strict RLS.

Resolution:

Switched to deterministic property-name detection and validation before query execution.

---

### RAG Retrieval

Problem:

Initial retrieval relied on simple keyword checks.

Impact:

Weak support for Hinglish phrasing.

Resolution:

Added:

* normalization
* synonym expansion
* token overlap scoring
* confidence thresholds

---

## AI Suggestions Rejected

### External Embeddings

Rejected because:

* unnecessary complexity
* external dependencies
* reduced reproducibility

---

### Vector Database

Rejected because:

* not required
* deterministic local retrieval sufficient

---

### Redis/Celery Queue

Rejected because:

* workflow_jobs already satisfied requirements
* increased operational complexity

---

## Final Architecture

Frontend:

* React (planned)

Backend:

* FastAPI

Database:

* PostgreSQL with RLS

Queue:

* workflow_jobs + worker.py

Assistant:

* NL→SQL
* Deterministic Hinglish RAG

Testing:

* pytest

Deployment:

* Render
* Supabase PostgreSQL

