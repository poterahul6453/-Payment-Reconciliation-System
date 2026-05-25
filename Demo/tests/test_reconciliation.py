"""Reconciliation engine tests for all gap types."""

import pytest
from httpx import AsyncClient

from app.services.reconciliation_engine import ReconciliationEngine
from app.services import upload_service


@pytest.mark.asyncio
async def test_load_sample_and_reconcile(client: AsyncClient, sample_dir, db_session):
    tx = (sample_dir / "transactions.csv").read_bytes()
    st = (sample_dir / "settlements.csv").read_bytes()
    rf = (sample_dir / "refunds.csv").read_bytes()
    await upload_service.import_transactions(db_session, tx)
    await upload_service.import_settlements(db_session, st)
    await upload_service.import_refunds(db_session, rf)

    engine = ReconciliationEngine(db_session)
    report = await engine.run()
    summary = report["summary"]
    categories = {m["category"] for m in report["mismatches"]}

    assert summary["matched_count"] >= 10
    assert summary["mismatch_count"] > 0
    assert "duplicate_settlement" in categories or summary["duplicate_count"] > 0
    assert "orphan_refund" in categories or summary["orphan_refund_count"] > 0


@pytest.mark.asyncio
async def test_duplicate_settlements(client: AsyncClient, db_session):
    await upload_service.import_transactions(
        db_session,
        b"txn_id,customer_id,order_id,amount,currency,payment_status,payment_method,txn_timestamp,gateway_reference\n"
        b"TXN-DUP,C1,O1,100,USD,success,card,2025-05-01T10:00:00,GW1\n",
    )
    await upload_service.import_settlements(
        db_session,
        b"settlement_id,txn_id,settled_amount,settlement_status,settlement_date,gateway_fee,tax,bank_reference\n"
        b"STL1,TXN-DUP,100,settled,2025-05-02T10:00:00,1,0,B1\n"
        b"STL2,TXN-DUP,100,settled,2025-05-03T10:00:00,1,0,B2\n",
    )
    engine = ReconciliationEngine(db_session)
    report = await engine.run()
    assert report["summary"]["duplicate_count"] >= 1
    assert any(m["category"] == "duplicate_settlement" for m in report["mismatches"])


@pytest.mark.asyncio
async def test_orphan_refunds(db_session):
    await upload_service.import_transactions(
        db_session,
        b"txn_id,customer_id,order_id,amount,currency,payment_status,payment_method,txn_timestamp,gateway_reference\n"
        b"TXN1,C1,O1,50,USD,success,card,2025-05-01T10:00:00,GW1\n",
    )
    await upload_service.import_refunds(
        db_session,
        b"refund_id,txn_id,refund_amount,refund_date\n"
        b"REF1,TXN-MISSING,25,2025-05-02T10:00:00\n",
    )
    report = await ReconciliationEngine(db_session).run()
    assert report["summary"]["orphan_refund_count"] >= 1
    assert len(report["orphan_refunds"]) >= 1


@pytest.mark.asyncio
async def test_rounding_mismatch(db_session):
    await upload_service.import_transactions(
        db_session,
        b"txn_id,customer_id,order_id,amount,currency,payment_status,payment_method,txn_timestamp,gateway_reference\n"
        b"TXN-R,C1,O1,99.99,USD,success,card,2025-05-01T10:00:00,GW1\n",
    )
    await upload_service.import_settlements(
        db_session,
        b"settlement_id,txn_id,settled_amount,settlement_status,settlement_date,gateway_fee,tax,bank_reference\n"
        b"STL-R,TXN-R,99.97,settled,2025-05-02T10:00:00,1,0,B1\n",
    )
    report = await ReconciliationEngine(db_session).run()
    assert any(m["category"] == "rounding_mismatch" for m in report["mismatches"])


@pytest.mark.asyncio
async def test_cross_month_settlement(db_session):
    await upload_service.import_transactions(
        db_session,
        b"txn_id,customer_id,order_id,amount,currency,payment_status,payment_method,txn_timestamp,gateway_reference\n"
        b"TXN-X,C1,O1,200,USD,success,card,2025-04-30T23:00:00,GW1\n",
    )
    await upload_service.import_settlements(
        db_session,
        b"settlement_id,txn_id,settled_amount,settlement_status,settlement_date,gateway_fee,tax,bank_reference\n"
        b"STL-X,TXN-X,200,settled,2025-05-02T10:00:00,1,0,B1\n",
    )
    report = await ReconciliationEngine(db_session).run()
    assert any(m["category"] == "cross_month_settlement" for m in report["mismatches"])


@pytest.mark.asyncio
async def test_delayed_settlement(db_session):
    await upload_service.import_transactions(
        db_session,
        b"txn_id,customer_id,order_id,amount,currency,payment_status,payment_method,txn_timestamp,gateway_reference\n"
        b"TXN-D,C1,O1,100,USD,success,card,2025-05-01T10:00:00,GW1\n",
    )
    await upload_service.import_settlements(
        db_session,
        b"settlement_id,txn_id,settled_amount,settlement_status,settlement_date,gateway_fee,tax,bank_reference\n"
        b"STL-D,TXN-D,100,settled,2025-05-06T10:00:00,1,0,B1\n",
    )
    report = await ReconciliationEngine(db_session).run()
    assert len(report["settlement_delays"]) >= 1
    assert report["settlement_delays"][0]["delay_days"] > 2


@pytest.mark.asyncio
async def test_null_transaction_ids(db_session):
    await upload_service.import_settlements(
        db_session,
        b"settlement_id,txn_id,settled_amount,settlement_status,settlement_date,gateway_fee,tax,bank_reference\n"
        b"STL-N,,50,settled,2025-05-02T10:00:00,1,0,B1\n",
    )
    report = await ReconciliationEngine(db_session).run()
    assert any(m["category"] == "null_transaction_id" for m in report["mismatches"])


@pytest.mark.asyncio
async def test_failed_transaction_settled(db_session):
    await upload_service.import_transactions(
        db_session,
        b"txn_id,customer_id,order_id,amount,currency,payment_status,payment_method,txn_timestamp,gateway_reference\n"
        b"TXN-F,C1,O1,100,USD,failed,card,2025-05-01T10:00:00,GW1\n",
    )
    await upload_service.import_settlements(
        db_session,
        b"settlement_id,txn_id,settled_amount,settlement_status,settlement_date,gateway_fee,tax,bank_reference\n"
        b"STL-F,TXN-F,100,settled,2025-05-02T10:00:00,1,0,B1\n",
    )
    report = await ReconciliationEngine(db_session).run()
    assert any(m["category"] == "failed_transaction_settled" for m in report["mismatches"])


@pytest.mark.asyncio
async def test_partial_settlement(db_session):
    await upload_service.import_transactions(
        db_session,
        b"txn_id,customer_id,order_id,amount,currency,payment_status,payment_method,txn_timestamp,gateway_reference\n"
        b"TXN-P,C1,O1,300,USD,success,card,2025-05-01T10:00:00,GW1\n",
    )
    await upload_service.import_settlements(
        db_session,
        b"settlement_id,txn_id,settled_amount,settlement_status,settlement_date,gateway_fee,tax,bank_reference\n"
        b"STL-P,TXN-P,250,settled,2025-05-02T10:00:00,1,0,B1\n",
    )
    report = await ReconciliationEngine(db_session).run()
    assert any(m["category"] == "partial_settlement" for m in report["mismatches"])


@pytest.mark.asyncio
async def test_over_settlement(db_session):
    await upload_service.import_transactions(
        db_session,
        b"txn_id,customer_id,order_id,amount,currency,payment_status,payment_method,txn_timestamp,gateway_reference\n"
        b"TXN-O,C1,O1,150,USD,success,card,2025-05-01T10:00:00,GW1\n",
    )
    await upload_service.import_settlements(
        db_session,
        b"settlement_id,txn_id,settled_amount,settlement_status,settlement_date,gateway_fee,tax,bank_reference\n"
        b"STL-O,TXN-O,175,settled,2025-05-02T10:00:00,1,0,B1\n",
    )
    report = await ReconciliationEngine(db_session).run()
    assert any(m["category"] == "over_settlement" for m in report["mismatches"])


@pytest.mark.asyncio
async def test_missing_settlement(db_session):
    await upload_service.import_transactions(
        db_session,
        b"txn_id,customer_id,order_id,amount,currency,payment_status,payment_method,txn_timestamp,gateway_reference\n"
        b"TXN-M,C1,O1,100,USD,success,card,2025-05-01T10:00:00,GW1\n",
    )
    report = await ReconciliationEngine(db_session).run()
    assert any(m["category"] == "missing_settlement" for m in report["mismatches"])


@pytest.mark.asyncio
async def test_api_run_sync(client: AsyncClient, sample_dir):
    await client.post("/upload/sample-data")
    res = await client.post("/reconcile/run-sync")
    assert res.status_code == 200
    data = res.json()
    assert "report_id" in data
    assert data["summary"]["mismatch_count"] > 0


@pytest.mark.asyncio
async def test_dashboard_endpoints(client: AsyncClient, sample_dir):
    await client.post("/upload/sample-data")
    await client.post("/reconcile/run-sync")
    summary = await client.get("/dashboard/summary")
    assert summary.status_code == 200
    assert summary.json()["total_transactions"] > 0
    trends = await client.get("/dashboard/mismatch-trends")
    assert trends.status_code == 200
