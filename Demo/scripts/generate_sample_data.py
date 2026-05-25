#!/usr/bin/env python3
"""Generate realistic sample CSV datasets with intentional reconciliation gaps."""

from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

OUTPUT = Path(__file__).resolve().parent.parent / "sample_data"
OUTPUT.mkdir(parents=True, exist_ok=True)

BASE = datetime(2025, 4, 28, 10, 0, 0)


def main():
    transactions = []
    settlements = []
    refunds = []

    # Normal matched transactions
    for i in range(1, 21):
        tid = f"TXN-{i:04d}"
        amt = round(50.0 + i * 12.5, 2)
        ts = BASE + timedelta(hours=i)
        transactions.append({
            "txn_id": tid,
            "customer_id": f"CUST-{1000 + i}",
            "order_id": f"ORD-{2000 + i}",
            "amount": amt,
            "currency": "USD",
            "payment_status": "success",
            "payment_method": "card" if i % 2 else "ach",
            "txn_timestamp": ts.isoformat(),
            "gateway_reference": f"GW-{tid}",
        })
        settlements.append({
            "settlement_id": f"STL-{i:04d}",
            "txn_id": tid,
            "settled_amount": amt,
            "settlement_status": "settled",
            "settlement_date": (ts + timedelta(days=1)).isoformat(),
            "gateway_fee": round(amt * 0.029, 2),
            "tax": round(amt * 0.01, 2),
            "bank_reference": f"BANK-{i:04d}",
        })

    # 1. Cross-month settlement (txn April, settlement May)
    transactions.append({
        "txn_id": "TXN-CROSS-01",
        "customer_id": "CUST-9001",
        "order_id": "ORD-9001",
        "amount": 250.00,
        "currency": "USD",
        "payment_status": "success",
        "payment_method": "card",
        "txn_timestamp": "2025-04-30T23:55:00",
        "gateway_reference": "GW-CROSS-01",
    })
    settlements.append({
        "settlement_id": "STL-CROSS-01",
        "txn_id": "TXN-CROSS-01",
        "settled_amount": 250.00,
        "settlement_status": "settled",
        "settlement_date": "2025-05-02T10:00:00",
        "gateway_fee": 7.25,
        "tax": 2.50,
        "bank_reference": "BANK-CROSS-01",
    })

    # 2. Rounding mismatch (off by 0.02 - outside 0.01 tolerance)
    transactions.append({
        "txn_id": "TXN-ROUND-01",
        "customer_id": "CUST-9002",
        "order_id": "ORD-9002",
        "amount": 99.99,
        "currency": "USD",
        "payment_status": "success",
        "payment_method": "card",
        "txn_timestamp": (BASE + timedelta(days=2)).isoformat(),
        "gateway_reference": "GW-ROUND-01",
    })
    settlements.append({
        "settlement_id": "STL-ROUND-01",
        "txn_id": "TXN-ROUND-01",
        "settled_amount": 99.97,
        "settlement_status": "settled",
        "settlement_date": (BASE + timedelta(days=3)).isoformat(),
        "gateway_fee": 2.90,
        "tax": 1.00,
        "bank_reference": "BANK-ROUND-01",
    })

    # 3. Duplicate settlement
    transactions.append({
        "txn_id": "TXN-DUP-01",
        "customer_id": "CUST-9003",
        "order_id": "ORD-9003",
        "amount": 500.00,
        "currency": "USD",
        "payment_status": "success",
        "payment_method": "ach",
        "txn_timestamp": (BASE + timedelta(days=3)).isoformat(),
        "gateway_reference": "GW-DUP-01",
    })
    for j in range(2):
        settlements.append({
            "settlement_id": f"STL-DUP-01-{j}",
            "txn_id": "TXN-DUP-01",
            "settled_amount": 500.00,
            "settlement_status": "settled",
            "settlement_date": (BASE + timedelta(days=4 + j)).isoformat(),
            "gateway_fee": 14.50,
            "tax": 5.00,
            "bank_reference": f"BANK-DUP-01-{j}",
        })

    # 4. Orphan refund
    refunds.append({
        "refund_id": "REF-ORPHAN-01",
        "txn_id": "TXN-NONEXIST-999",
        "refund_amount": 75.00,
        "refund_date": (BASE + timedelta(days=5)).isoformat(),
    })

    # Valid refund
    refunds.append({
        "refund_id": "REF-0001",
        "txn_id": "TXN-0005",
        "refund_amount": 25.00,
        "refund_date": (BASE + timedelta(days=6)).isoformat(),
    })

    # 5. Partial settlement
    transactions.append({
        "txn_id": "TXN-PARTIAL-01",
        "customer_id": "CUST-9004",
        "order_id": "ORD-9004",
        "amount": 300.00,
        "currency": "USD",
        "payment_status": "success",
        "payment_method": "card",
        "txn_timestamp": (BASE + timedelta(days=4)).isoformat(),
        "gateway_reference": "GW-PARTIAL-01",
    })
    settlements.append({
        "settlement_id": "STL-PARTIAL-01",
        "txn_id": "TXN-PARTIAL-01",
        "settled_amount": 250.00,
        "settlement_status": "settled",
        "settlement_date": (BASE + timedelta(days=5)).isoformat(),
        "gateway_fee": 7.25,
        "tax": 2.50,
        "bank_reference": "BANK-PARTIAL-01",
    })

    # 6. Over settlement
    transactions.append({
        "txn_id": "TXN-OVER-01",
        "customer_id": "CUST-9005",
        "order_id": "ORD-9005",
        "amount": 150.00,
        "currency": "USD",
        "payment_status": "success",
        "payment_method": "card",
        "txn_timestamp": (BASE + timedelta(days=5)).isoformat(),
        "gateway_reference": "GW-OVER-01",
    })
    settlements.append({
        "settlement_id": "STL-OVER-01",
        "txn_id": "TXN-OVER-01",
        "settled_amount": 175.00,
        "settlement_status": "settled",
        "settlement_date": (BASE + timedelta(days=6)).isoformat(),
        "gateway_fee": 5.08,
        "tax": 1.75,
        "bank_reference": "BANK-OVER-01",
    })

    # 7. Failed transaction settled
    transactions.append({
        "txn_id": "TXN-FAILED-01",
        "customer_id": "CUST-9006",
        "order_id": "ORD-9006",
        "amount": 200.00,
        "currency": "USD",
        "payment_status": "failed",
        "payment_method": "card",
        "txn_timestamp": (BASE + timedelta(days=6)).isoformat(),
        "gateway_reference": "GW-FAILED-01",
    })
    settlements.append({
        "settlement_id": "STL-FAILED-01",
        "txn_id": "TXN-FAILED-01",
        "settled_amount": 200.00,
        "settlement_status": "settled",
        "settlement_date": (BASE + timedelta(days=7)).isoformat(),
        "gateway_fee": 5.80,
        "tax": 2.00,
        "bank_reference": "BANK-FAILED-01",
    })

    # 8. Null transaction IDs
    settlements.append({
        "settlement_id": "STL-NULL-01",
        "txn_id": "",
        "settled_amount": 88.00,
        "settlement_status": "settled",
        "settlement_date": (BASE + timedelta(days=7)).isoformat(),
        "gateway_fee": 2.55,
        "tax": 0.88,
        "bank_reference": "BANK-NULL-01",
    })

    # Missing settlement
    transactions.append({
        "txn_id": "TXN-MISSING-01",
        "customer_id": "CUST-9007",
        "order_id": "ORD-9007",
        "amount": 420.00,
        "currency": "USD",
        "payment_status": "success",
        "payment_method": "ach",
        "txn_timestamp": (BASE + timedelta(days=8)).isoformat(),
        "gateway_reference": "GW-MISSING-01",
    })

    # Delayed settlement (>2 days)
    transactions.append({
        "txn_id": "TXN-DELAY-01",
        "customer_id": "CUST-9008",
        "order_id": "ORD-9008",
        "amount": 180.00,
        "currency": "USD",
        "payment_status": "success",
        "payment_method": "card",
        "txn_timestamp": (BASE + timedelta(days=1)).isoformat(),
        "gateway_reference": "GW-DELAY-01",
    })
    settlements.append({
        "settlement_id": "STL-DELAY-01",
        "txn_id": "TXN-DELAY-01",
        "settled_amount": 180.00,
        "settlement_status": "settled",
        "settlement_date": (BASE + timedelta(days=5)).isoformat(),
        "gateway_fee": 5.22,
        "tax": 1.80,
        "bank_reference": "BANK-DELAY-01",
    })

    pd.DataFrame(transactions).to_csv(OUTPUT / "transactions.csv", index=False)
    pd.DataFrame(settlements).to_csv(OUTPUT / "settlements.csv", index=False)
    pd.DataFrame(refunds).to_csv(OUTPUT / "refunds.csv", index=False)
    print(f"Generated sample data in {OUTPUT}")
    print(f"  transactions: {len(transactions)} rows")
    print(f"  settlements: {len(settlements)} rows")
    print(f"  refunds: {len(refunds)} rows")


if __name__ == "__main__":
    main()
