# Distilled Prompt — Payment Reconciliation System

Build a **fintech payment reconciliation** app:

**Stack:** Python FastAPI + Pandas + SQLAlchemy + PostgreSQL/SQLite backend; React Vite + Tailwind + Axios + Recharts frontend.

**Flow:** Upload transactions/settlements/refunds CSVs → run reconciliation → detect mismatches → generate JSON/CSV reports → dashboard analytics.

**Detect:** matched, missing settlement, amount mismatch, duplicates, orphan refunds, partial/over settlement, delays, cross-month, rounding, failed-txn-settled, null txn IDs. Tolerance: $0.01. Use Decimal.

**No:** auth, microservices, Celery, Kafka, Redis, K8s, Next.js, Redux.

**Structure:** `backend/`, `frontend/`, `tests/`, `reports/`, `uploads/`, `sample_data/`.

**APIs:** upload endpoints, `POST /reconcile/run` (BackgroundTasks), report GET, dashboard GETs, export JSON/CSV.

**UI pages:** Dashboard, Upload, Reports, Mismatch Explorer, Duplicates, Refund Analysis. Charts: pie, bar, line (Recharts).

**Tests:** pytest + TestClient for all gap types.

**Deliverables:** README, Docker, .env files, assessment docs (`brainstorming_thread.md`, `test_cases.md`, `production_limitations.md`).
