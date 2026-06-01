# Mock OTA Integration Analysis

## Question 1: Is mock_ota integration mandatory or bonus?

**Answer: BONUS (not mandatory)**

From `README.md`:
```
## Part A — Conversation Orchestration + Lifecycle (backend)
...
**Must:** tenant isolation via RLS ... idempotent on message_id ... false-positive guard ... human-handoff ... report classify P95.

**Bonus (resilience):** the booking workflow pushes availability to the mock OTA...
```

- **MUST requirements** (Part A): Intent classification ✅ | Intent routing ✅ | Queue/event ✅ | Tenant isolation ✅ | Idempotency ✅ | Human handoff ✅ | Classify P95 ✅
- **BONUS requirement**: Mock OTA integration ❌

---

## Question 2: If I submit without mock_ota integration, how much of Part A remains incomplete?

**Answer: 0% of MUST requirements. 1 BONUS feature missing.**

### Current Status (as of now):

| Feature | Status | Mandatory? | Impact |
|---------|--------|-----------|--------|
| Intent Classification | ✅ DONE | 🔴 YES | Scoring element |
| Intent Routing (WORKFLOW_REGISTRY) | ✅ DONE | 🔴 YES | Core feature |
| Queue/Event side-effects | ✅ DONE | 🔴 YES | Core feature |
| Tenant isolation (RLS + code) | ✅ DONE | 🔴 YES | Critical guard |
| Idempotency on message_id | ✅ DONE | 🔴 YES | Data guard |
| Human handoff (low confidence) | ✅ DONE | 🔴 YES | Safety guard |
| Cancellation confirmation guard | ✅ DONE | 🔴 YES | Safety guard |
| Classify P95 measurement | ✅ DONE | 🔴 YES | Metrics reporting |
| **Mock OTA integration** | ❌ NOT | 🟡 BONUS | Resilience demo |

**Verdict**: You can submit Part A with 0% impact on evaluation if you skip mock_ota. It's pure bonus.

---

## Question 3: What is the smallest acceptable implementation?

**Answer: Replace `process_payload()` in `worker.py` with OTA POST call.**

**Current** (lines 59-61):
```python
def process_payload(payload):
    # For the capstone, we simulate processing. In real life, implement OTA calls.
    print('Processing payload:', payload)
    time.sleep(PROCESS_SLEEP)
```

**Smallest impl** (add 40-50 lines):
```python
import requests
import hashlib
import json

def process_booking_job(payload, max_retries=3):
    """
    For booking jobs: generate idempotent push_id, call OTA /availability, retry on 429/500.
    """
    job_data = json.loads(payload) if isinstance(payload, str) else payload
    message_id = job_data.get("message_id")
    
    # Generate idempotent push_id from message_id (deterministic)
    push_id = f"booking_{message_id}_{int(time.time()) // 600}"  # 10-min window
    
    ota_url = "http://localhost:9000/availability"
    
    for attempt in range(max_retries):
        try:
            response = requests.post(
                ota_url,
                json={"push_id": push_id},
                timeout=5
            )
            
            if response.status_code == 200:
                print(f"✓ OTA push accepted: {push_id}")
                return True
            
            elif response.status_code == 429:
                wait_sec = int(response.headers.get("Retry-After", 2))
                print(f"OTA rate limited, retry {attempt + 1}/{max_retries} after {wait_sec}s")
                time.sleep(wait_sec)
                continue
            
            elif 500 <= response.status_code < 600:
                print(f"OTA error {response.status_code}, retry {attempt + 1}/{max_retries}")
                time.sleep(2 ** attempt)  # Exponential backoff
                continue
            
            else:
                print(f"OTA unexpected status {response.status_code}")
                return False
        
        except requests.RequestException as e:
            print(f"OTA call failed: {e}, retry {attempt + 1}/{max_retries}")
            time.sleep(2 ** attempt)
            continue
    
    print(f"✗ OTA push failed after {max_retries} retries: {push_id}")
    return False

def process_payload(payload):
    """Route job by type and process."""
    try:
        data = json.loads(payload) if isinstance(payload, str) else payload
        job_type = data.get("job_type") or "booking"  # Default to booking
        
        if job_type == "booking":
            process_booking_job(data)
        else:
            print(f"Processing {job_type} job")  # Other intents don't need OTA
    
    except Exception as e:
        print(f"Process error: {e}")
        raise
```

**Total new code**: ~50 lines | **Risk**: Low (optional feature) | **Effort**: 30 min

---

## Question 4: Can workflow_jobs be used as the retry queue?

**Answer: YES, perfectly. It already has the columns needed.**

### Current schema (from `seed/schema.sql`, line 55):
```sql
CREATE TABLE IF NOT EXISTS workflow_jobs (
  job_id TEXT PRIMARY KEY,
  property_id TEXT REFERENCES properties(property_id),
  job_type TEXT NOT NULL,
  status TEXT,
  retry_count INT DEFAULT 0,          -- ✅ For tracking retries
  payload JSONB,                      -- ✅ Can store push_id attempt count
  created_at TIMESTAMP DEFAULT NOW()
);
```

### What's already there:
- ✅ `status` field: pending, in_progress, done, failed
- ✅ `retry_count` field: counts retries
- ✅ `payload` field: can store push_id + attempt info
- ✅ Atomic claim with FOR UPDATE SKIP LOCKED (no duplicate claim)

### What you'd add:
1. In `worker.py`: check `retry_count < MAX_RETRIES` before processing
2. On OTA failure: increment `retry_count`, set status back to `pending`
3. On success: set status to `done`

**Nothing new needed in schema.** workflow_jobs is already a first-class retry queue.

---

## Question 5: Should a worker process: booking jobs, create push_id, call POST /availability, retry on 429/500, mark completed?

**Answer: YES. Exactly that flow.**

### Recommended workflow:

```
Worker loop:
  1. Claim job (FOR UPDATE SKIP LOCKED) → status = in_progress
  2. Check job_type:
     - If "booking": call process_booking_job()
     - If "cancellation"/"faq"/etc.: just mark done (no OTA needed)
  3. On success:
     - status = done
     - completed_at = NOW()
  4. On OTA 429/500:
     - Increment retry_count
     - status = pending (will be re-claimed)
  5. On max retries exceeded:
     - status = failed
     - Log error message
```

### Push ID strategy (idempotent):

The mock OTA requires `push_id` to be idempotent. If you replay the same `push_id`, it returns "duplicate_ignored" (no side effect).

**Best approach**: Use deterministic hash:
```python
push_id = f"msg_{message_id}"  # Simple but message_id is unique anyway

# OR if you need to track attempts:
push_id = f"msg_{message_id}_attempt_{retry_count}"
# First attempt: msg_uuid_attempt_0
# Retry 1:       msg_uuid_attempt_1
# Each is unique but linked to original message
```

---

## Question 6: Simplest implementation satisfying idempotent push_id, retry/backoff, workflow_jobs based?

**Answer: 50-60 lines in `worker.py`. No schema changes.**

### Complete minimal implementation:

```python
#!/usr/bin/env python3
"""
Enhanced worker with OTA integration for booking jobs.
"""
import time
import json
import requests
from app.db import get_conn

PROCESS_SLEEP = 1.0
MAX_RETRIES = 3
OTA_URL = "http://localhost:9000/availability"


def claim_one_job(conn):
    """Atomically claim next pending job."""
    cur = conn.cursor()
    try:
        cur.execute(
            """
            WITH cte AS (
                SELECT job_id FROM workflow_jobs
                WHERE status = 'pending'
                ORDER BY created_at
                FOR UPDATE SKIP LOCKED
                LIMIT 1
            )
            UPDATE workflow_jobs w
            SET status = 'in_progress'
            FROM cte
            WHERE w.job_id = cte.job_id
            RETURNING w.job_id, w.job_type, w.payload, w.retry_count
            """
        )
        row = cur.fetchone()
        if row:
            conn.commit()
            return row
        conn.commit()
        return None
    finally:
        cur.close()


def push_to_ota(message_id, retry_count=0):
    """Call mock OTA /availability with idempotent push_id and retry logic."""
    # Idempotent push_id: ties attempts to message_id
    push_id = f"booking_{message_id}"
    
    for attempt in range(MAX_RETRIES - retry_count):
        try:
            response = requests.post(
                OTA_URL,
                json={"push_id": push_id},
                timeout=5
            )
            
            if response.status_code == 200:
                return True, f"OTA accepted: {push_id}"
            
            elif response.status_code == 429:
                wait = int(response.headers.get("Retry-After", 2))
                print(f"  OTA 429, waiting {wait}s (attempt {attempt + 1}/{MAX_RETRIES - retry_count})")
                time.sleep(wait)
            
            elif 500 <= response.status_code < 600:
                print(f"  OTA {response.status_code}, backoff (attempt {attempt + 1})")
                time.sleep(2 ** attempt)
            
            else:
                return False, f"OTA error {response.status_code}"
        
        except requests.RequestException as e:
            print(f"  OTA request failed: {e}")
            time.sleep(2 ** attempt)
    
    return False, "OTA max retries exceeded"


def process_job(conn, job_id, job_type, payload, retry_count):
    """Process job, retry on OTA failure, mark done/failed."""
    cur = conn.cursor()
    
    try:
        data = json.loads(payload) if isinstance(payload, str) else payload
        message_id = data.get("message_id")
        
        # Only booking jobs need OTA
        if job_type == "booking":
            success, msg = push_to_ota(message_id, retry_count)
            
            if success:
                cur.execute(
                    "UPDATE workflow_jobs SET status = 'done', retry_count = %s WHERE job_id = %s",
                    (retry_count, job_id)
                )
            elif retry_count < MAX_RETRIES:
                # Retry later
                cur.execute(
                    "UPDATE workflow_jobs SET status = 'pending', retry_count = %s WHERE job_id = %s",
                    (retry_count + 1, job_id)
                )
                print(f"Job {job_id}: queued for retry (attempt {retry_count + 1})")
            else:
                # Max retries exceeded
                cur.execute(
                    "UPDATE workflow_jobs SET status = 'failed', retry_count = %s WHERE job_id = %s",
                    (retry_count, job_id)
                )
                print(f"Job {job_id}: FAILED - {msg}")
        
        else:
            # Non-booking jobs just mark done
            cur.execute(
                "UPDATE workflow_jobs SET status = 'done' WHERE job_id = %s",
                (job_id,)
            )
            print(f"Job {job_id} ({job_type}): done")
        
        conn.commit()
    
    except Exception as e:
        print(f"Job {job_id}: error: {e}")
        cur.execute(
            "UPDATE workflow_jobs SET status = 'failed' WHERE job_id = %s",
            (job_id,)
        )
        conn.commit()
    
    finally:
        cur.close()


def main_loop():
    """Main worker loop: claim → process → mark done/failed/retry."""
    print("Worker started (with OTA integration)")
    conn = get_conn()
    
    try:
        while True:
            claimed = claim_one_job(conn)
            
            if not claimed:
                time.sleep(0.5)
                continue
            
            job_id, job_type, payload, retry_count = claimed
            print(f"Claimed {job_id} ({job_type}, retry_count={retry_count})")
            
            process_job(conn, job_id, job_type, payload, retry_count)
    
    finally:
        conn.close()


if __name__ == "__main__":
    main_loop()
```

**Metrics**:
- ✅ Idempotent push_id (message_id based)
- ✅ Retry/backoff (exponential 2^attempt)
- ✅ workflow_jobs based (no external queue)
- ✅ Handles 429/500 gracefully
- ✅ Max retries enforcement
- ✅ Non-booking jobs pass through unchanged

---

## Question 7: Estimate effort

### Breakdown:

| Task | Time | Complexity |
|------|------|-----------|
| Understand mock_ota behavior | 5 min | Easy |
| Write OTA call + retry logic | 15 min | Medium |
| Test locally (mock OTA running) | 10 min | Medium |
| **Total** | **30 min** | **Low-Medium** |

### Prerequisites (already done):
- ✅ worker.py exists with claim/mark done logic
- ✅ workflow_jobs table with retry_count field
- ✅ mock_ota_server.py ready to run
- ✅ Worker runs in main loop

### Path to completion:

```
OPTION A: Minimal (30 min)
  1. Copy enhanced worker.py above
  2. pip install requests
  3. Run mock_ota_server.py in one terminal
  4. Run worker.py in another
  5. Test: POST /message with booking intent
  6. Verify OTA calls in mock_ota output

OPTION B: Full (1.5 hours)
  1. Above + add structured logging (JSON logs)
  2. Add retry count tracking to DB payload
  3. Add OTA push_id tracking table (optional)
  4. Write test_ota_retry_resilience.py
  5. Verify idempotency (same push_id → duplicate ignored)
  6. Verify failure recovery (429/500 → retried)

OPTION C: Exhaustive (3+ hours)
  1. Above + add push_id tracking table
  2. Add dead-letter queue for permanently failed jobs
  3. Add health check endpoint /worker-status
  4. Add observability dashboard (logs aggregation)
  5. Load test with concurrent messages
  6. Measure booking latency + OTA call overhead
```

### Recommendation:

**Do OPTION A (30 min)** — gets you the bonus feature with minimal risk. Code is clear, testable, and demonstrable.

---

## Checklist: What You Get with Mock OTA Integration

- ✅ Demonstrates **resilience** (retry on 429/500)
- ✅ Shows **idempotency** (push_id dedup)
- ✅ Shows **async job processing** (worker loop)
- ✅ Shows **workflow orchestration** (routing by intent)
- ✅ Bonus points in evaluation
- ✅ Can report in RESULTS.md: "Successfully delivered X booking jobs, Y OTA calls, Z retried due to failures"

### Example RESULTS.md addition:

```
## Bonus: OTA Integration

- Mock OTA server running on :9000
- Booking workflow pushes availability:
  - Total messages processed: 50
  - Booking intents: 12
  - OTA calls: 12
  - Success rate: 100% (after retries)
  - Failed with max retries: 0
  - Retry attempts needed: 2 (due to intentional 429/500)
  - Push ID idempotency: verified (duplicate push_id → ignored)
```

---

## TL;DR

1. **Mock OTA is BONUS** — not mandatory for Part A
2. **Skip it safely** — 0 impact if you don't implement
3. **Implement it quickly** — 30 minutes, ~50 lines of code
4. **Use workflow_jobs as retry queue** — already has everything (retry_count, status, payload)
5. **Worker should**: claim → route by intent → if booking, call OTA with idempotent push_id → retry on 429/500 → mark done/failed
6. **Push ID strategy**: Use `booking_{message_id}` (deterministic, idempotent, unique per message)
7. **Effort estimate**: **30 min** (minimal), 1.5 hours (full), 3+ hours (exhaustive)

