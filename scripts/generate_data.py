"""Generate a synthetic batch of failed payments for ReviveBot.

    python scripts/generate_data.py [n]

Writes data/synthetic_payments.csv with a realistic mix of Razorpay-style
failure codes, order types, and a few deliberately tricky records (a DNC
customer, a permanent failure, a high-value payment, exhausted retries, an
overdue B2B invoice) so the demo shows the agent's stopping rules in action.

Seeded for reproducibility.
"""
from __future__ import annotations

import csv
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "synthetic_payments.csv"

FIELDS = [
    "payment_id", "merchant_id", "customer_email", "customer_phone", "amount",
    "failure_reason", "failure_detail", "failure_source", "attempts",
    "created_at", "order_type",
]

# (failure_reason, failure_detail, failure_source) weighted by rough realism.
FAILURE_MIX = [
    ("BAD_REQUEST_ERROR", "FUND_INSUFFICIENT", "customer", 30),
    ("GATEWAY_ERROR", "", "network", 18),
    ("SERVER_ERROR", "", "network", 10),
    ("PAYMENT_CANCELLED", "", "customer", 22),
    ("BAD_REQUEST_ERROR", "MANDATE_REVOKED", "customer", 12),
]
ORDER_TYPES = ["one_time", "subscription", "b2b"]


def _weighted_choice(rng: random.Random):
    population = [(r, d, s) for (r, d, s, _) in FAILURE_MIX]
    weights = [w for (*_, w) in FAILURE_MIX]
    return rng.choices(population, weights=weights, k=1)[0]


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def generate(n: int = 72, seed: int = 42) -> list[dict]:
    rng = random.Random(seed)
    now = datetime.now(timezone.utc)
    rows: list[dict] = []

    for i in range(1, n + 1):
        reason, detail, source = _weighted_choice(rng)
        order_type = rng.choices(ORDER_TYPES, weights=[55, 30, 15], k=1)[0]
        amount = rng.choice([4999, 9900, 19900, 29900, 49900, 99900, 149900])
        age_days = rng.randint(0, 10)
        rows.append({
            "payment_id": f"pay_Test_{i:03d}",
            "merchant_id": f"merch_{rng.randint(1, 3):03d}",
            "customer_email": f"user{i:03d}@example.com",
            "customer_phone": f"+9198{rng.randint(10_000_000, 99_999_999)}",
            "amount": amount,
            "failure_reason": reason,
            "failure_detail": detail,
            "failure_source": source,
            "attempts": rng.choices([1, 2, 3], weights=[70, 20, 10], k=1)[0],
            "created_at": _iso(now - timedelta(days=age_days,
                                               hours=rng.randint(0, 23))),
            "order_type": order_type,
        })

    # --- Deliberately tricky records the agent must handle gracefully -------
    # DNC customer — must be skipped, never contacted.
    rows[16] |= {
        "payment_id": "pay_Test_017", "customer_email": "dnc_customer@example.com",
        "failure_reason": "BAD_REQUEST_ERROR", "failure_detail": "FUND_INSUFFICIENT",
        "attempts": 1,
    }
    # Permanent failure — unrecoverable, do nothing.
    rows[42] |= {
        "payment_id": "pay_Test_043", "failure_reason": "PERMANENT_FAILURE",
        "failure_detail": "", "attempts": 1,
    }
    # Retries exhausted — must stop and escalate.
    rows[60] |= {
        "payment_id": "pay_Test_061", "attempts": 3,
        "failure_reason": "GATEWAY_ERROR", "failure_detail": "",
    }
    # High-value payment — always escalate to a human (over the ₹50,000 rule).
    rows[9] |= {
        "payment_id": "pay_Test_010", "amount": 60_00_000,  # ₹60,000.00
        "failure_reason": "BAD_REQUEST_ERROR", "failure_detail": "FUND_INSUFFICIENT",
    }
    # Overdue B2B invoice — age it past the 30-day threshold.
    rows[25] |= {
        "payment_id": "pay_Test_026", "order_type": "b2b",
        "created_at": _iso(now - timedelta(days=45)),
        "failure_reason": "BAD_REQUEST_ERROR", "failure_detail": "",
    }
    return rows


def main() -> None:
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 72
    rows = generate(n)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {OUT}")


if __name__ == "__main__":
    main()
