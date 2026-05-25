# Test Cases — Payment Reconciliation System

## Reconciliation Engine

| ID | Scenario | Input | Expected |
|----|----------|-------|----------|
| TC-01 | Matched transaction | Txn $100 success + settlement $100 | `matched_transactions` contains txn |
| TC-02 | Missing settlement | Success txn, no settlement | `missing_settlement` mismatch |
| TC-03 | Duplicate settlement | 2 settlements same txn_id | `duplicate_count` ≥ 1, duplicate report |
| TC-04 | Orphan refund | Refund for non-existent txn_id | `orphan_refund_count` ≥ 1 |
| TC-05 | Rounding mismatch | $99.99 vs $99.97 | `rounding_mismatch` category |
| TC-06 | Cross-month | April txn, May settlement | `cross_month_settlement` category |
| TC-07 | Delayed settlement | Settlement >2 days after txn | `settlement_delays` entry |
| TC-08 | Null txn_id | Settlement with empty txn_id | `null_transaction_id` category |
| TC-09 | Failed txn settled | failed status + settlement | `failed_transaction_settled` |
| TC-10 | Partial settlement | $300 txn, $250 settlement | `partial_settlement` |
| TC-11 | Over settlement | $150 txn, $175 settlement | `over_settlement` |
| TC-12 | Full sample load | sample_data/*.csv | Multiple categories, health score computed |

## API

| ID | Endpoint | Expected |
|----|----------|----------|
| TC-API-01 | POST /upload/sample-data | 200, row counts returned |
| TC-API-02 | POST /reconcile/run-sync | 200, report_id + summary |
| TC-API-03 | GET /dashboard/summary | 200, totals after reconcile |
| TC-API-04 | GET /dashboard/mismatch-trends | 200, category array |
| TC-API-05 | GET /export/report/json | 200 file download |

## Frontend (Manual)

| ID | Page | Steps | Expected |
|----|------|-------|----------|
| TC-UI-01 | Upload | Load sample + reconcile | Summary JSON shown |
| TC-UI-02 | Dashboard | After reconcile | Charts populated |
| TC-UI-03 | Mismatch Explorer | Filter by category | Table filters |
| TC-UI-04 | Reports | Export links | Files download |

## Running Automated Tests

```bash
pytest tests/ -v
```
