# Payment Reconciliation System

A production-style fintech payment reconciliation platform that matches payment gateway transactions against bank settlements, detects mismatches, and provides analytics dashboards.

## Problem Statement

Payment platforms record transactions instantly when customers pay. Banks settle those funds 1–2 business days later. At month end, finance teams must verify that every successful transaction has a matching settlement with the correct amount.

This system automates that reconciliation workflow: ingest CSV exports, run a rules-based reconciliation engine, generate audit reports, and visualize health metrics on a dashboard.

## Assumptions

- **No authentication** — internal tool for finance/ops teams
- **CSV ingestion** — data arrives as batch exports from gateway and bank
- **USD currency** — single-currency reconciliation (multi-currency is a future enhancement)
- **Tolerance** — amounts within `$0.01` are considered matched
- **Success-only matching** — only `payment_status=success` transactions require settlements
- **Settlement delay** — delays over 2 days are flagged (not mismatches by default)
- **SQLite locally** — PostgreSQL for Docker/production-like deployments

## Architecture

```
┌─────────────┐     CSV Upload      ┌──────────────────┐
│   React UI  │ ──────────────────► │  FastAPI Backend │
│  (Vite)     │ ◄── Dashboard API   │  + SQLAlchemy    │
└─────────────┘                     │  + Pandas Engine │
                                    └────────┬─────────┘
                                             │
                    ┌────────────────────────┼────────────────────────┐
                    ▼                        ▼                        ▼
              SQLite/PostgreSQL         reports/                 uploads/
```

**Modules:**
- `routers/` — HTTP endpoints (upload, reconcile, dashboard, export)
- `services/reconciliation_engine.py` — Pandas + Decimal matching logic
- `services/upload_service.py` — CSV parsing and DB persistence
- `services/report_service.py` — Report retrieval and analytics

## Project Structure

```
backend/          FastAPI application
frontend/         React + Vite dashboard
tests/            pytest suite
reports/          Generated reconciliation reports
uploads/          Uploaded CSV files
sample_data/      Demo datasets with intentional gaps
scripts/          Sample data generator
```

## Setup Instructions

### Prerequisites

- Python 3.11+
- Node.js 18+
- (Optional) Docker & Docker Compose

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env       # or use existing .env
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

### Quick Demo

1. Open **Upload Center** → click **Load Sample Data**
2. Click **Run Reconciliation**
3. View **Dashboard**, **Mismatch Explorer**, **Reports**

## Docker Setup

```bash
docker compose up --build
```

- Backend: http://localhost:8000
- Frontend: http://localhost:5173
- PostgreSQL: localhost:5432 (user: `recon`, password: `recon`, db: `reconciliation`)

For PostgreSQL, set:
```
DATABASE_URL=postgresql+asyncpg://recon:recon@postgres:5432/reconciliation
```

## API Documentation

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/upload/transactions` | Upload transactions CSV |
| POST | `/upload/settlements` | Upload settlements CSV |
| POST | `/upload/refunds` | Upload refunds CSV |
| POST | `/upload/sample-data` | Load bundled sample datasets |
| POST | `/reconcile/run` | Start async reconciliation (BackgroundTasks) |
| POST | `/reconcile/run-sync` | Run reconciliation immediately |
| GET | `/reconcile/report/{report_id}` | Fetch report JSON |
| GET | `/dashboard/summary` | Dashboard KPIs |
| GET | `/dashboard/mismatch-trends` | Mismatch by category |
| GET | `/dashboard/settlement-delays` | Delayed settlements |
| GET | `/dashboard/duplicates` | Duplicate settlements |
| GET | `/dashboard/orphan-refunds` | Orphan refunds |
| GET | `/dashboard/daily-trend` | Daily reconciliation trend |
| GET | `/dashboard/monthly-analytics` | Monthly aggregates |
| GET | `/export/report/json` | Download JSON report |
| GET | `/export/report/csv` | Download CSV (`report_type`: mismatch, duplicate, orphan) |

## CSV Format

### transactions.csv
| Column | Required | Description |
|--------|----------|-------------|
| txn_id | Yes | Unique transaction ID |
| customer_id | Yes | Customer identifier |
| order_id | Yes | Order identifier |
| amount | Yes | Transaction amount |
| currency | No | Default USD |
| payment_status | Yes | success, failed, pending |
| payment_method | Yes | card, ach, etc. |
| txn_timestamp | Yes | ISO datetime |
| gateway_reference | No | Gateway ref |

### settlements.csv
| Column | Required | Description |
|--------|----------|-------------|
| settlement_id | Yes | Unique settlement ID |
| txn_id | No | Links to transaction (can be empty) |
| settled_amount | Yes | Amount settled |
| settlement_status | Yes | settled, pending |
| settlement_date | Yes | ISO datetime |
| gateway_fee | No | Fee amount |
| tax | No | Tax amount |
| bank_reference | No | Bank reference |

### refunds.csv
| Column | Required | Description |
|--------|----------|-------------|
| refund_id | Yes | Unique refund ID |
| txn_id | Yes | Original transaction ID |
| refund_amount | Yes | Refund amount |
| refund_date | Yes | ISO datetime |

## Test Execution

```bash
cd /path/to/project
pip install -r backend/requirements.txt
pytest tests/ -v
```

Tests cover: duplicate settlements, orphan refunds, rounding mismatches, cross-month settlements, delayed settlements, null transaction IDs, failed transaction settlements, partial/over settlements, missing settlements, and API integration.

## Screenshots

<!-- Add screenshots after running the app -->
| Page | Path |
|------|------|
| Dashboard | `docs/screenshots/dashboard.png` |
| Upload Center | `docs/screenshots/upload.png` |
| Mismatch Explorer | `docs/screenshots/mismatches.png` |

## Known Limitations

- No real-time streaming — batch CSV only
- Single currency (USD)
- No user authentication or RBAC
- Background reconciliation uses in-memory status (not durable job queue)
- Cross-month detection uses calendar month, not fiscal period
- Refunds are flagged as orphans but not netted against settlement amounts

## Production Improvements

See `production_limitations.md` for a detailed roadmap (idempotency, audit trails, webhook ingestion, multi-tenant isolation, etc.).

## License

MIT — assessment / demo project.
