# Production Limitations & Improvement Roadmap

## Current Limitations

### Data & Ingestion
- **Batch-only CSV** — no SFTP, API webhooks, or streaming from payment gateways
- **Replace-on-upload** — uploads wipe prior data; no incremental append or versioning
- **No idempotency keys** — duplicate uploads can corrupt state

### Reconciliation Logic
- **Single currency** — no FX conversion or multi-currency netting
- **Simple tolerance** — flat $0.01; no percentage-based or currency-specific rules
- **Refund netting** — refunds flagged but not subtracted from expected settlement amounts
- **Calendar month** — cross-month uses calendar boundaries, not configurable fiscal periods
- **In-memory job status** — `POST /reconcile/run` status lost on restart

### Security & Compliance
- **No authentication** — unsuitable for production without SSO/OAuth2
- **No audit log** — who ran reconciliation, when, and what changed
- **No PII encryption** — customer IDs stored in plain text
- **No SOC2 controls** — retention policies, access reviews absent

### Scalability
- **Single-process Pandas** — large files (millions of rows) will OOM
- **No partitioning** — cannot reconcile by merchant/date shard in parallel
- **SQLite local** — not HA; Postgres in Docker still single instance

### Observability
- **Basic logging** — no structured traces, metrics, or alerting (PagerDuty)
- **No SLA dashboards** — reconciliation completion time not tracked

## Recommended Production Improvements

### Phase 1 — Hardening (4–6 weeks)
1. Add OAuth2 / API keys and role-based access (finance vs ops)
2. Persistent job table for async reconciliation with retry
3. Immutable audit trail for uploads and report generation
4. Idempotent uploads with file hash deduplication

### Phase 2 — Scale (6–8 weeks)
1. Chunked Pandas or Spark/DuckDB for large files
2. Partition reconciliation by `settlement_date` month
3. Read replicas for dashboard queries
4. S3/GCS for report storage with signed URLs

### Phase 3 — Integration (8+ weeks)
1. Gateway webhooks (Stripe, Adyen) for real-time transaction feed
2. Bank file parsers (BAI2, MT940) beyond CSV
3. Net refund adjustments in expected settlement calculation
4. Multi-currency with daily FX rates table

### Phase 4 — Finance Ops
1. Exception workflow (assign, resolve, comment)
2. Month-end close checklist integration
3. Automated email/Slack alerts on health score drop
4. Reconciliation certification sign-off

## Risk Matrix

| Risk | Severity | Mitigation |
|------|----------|------------|
| Wrong match due to float | High | ✅ Decimal used |
| Duplicate settlement undetected | High | ✅ Duplicate detection |
| Data loss on restart | Medium | Job persistence (Phase 1) |
| Unauthorized access | Critical | Auth (Phase 1) |
| Slow month-end run | Medium | Partitioning (Phase 2) |
