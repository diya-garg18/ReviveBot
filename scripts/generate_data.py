"""Generate a synthetic batch of failed payments for ReviveBot.

    python scripts/generate_data.py [n]

Writes data/synthetic_payments.csv with a realistic mix of Razorpay-style
failure codes, order types, and customer details. A few rows are made
deliberately tricky so the demo shows every stopping rule in action:
  - a couple of customers pulled from data/dnc_list.csv (must be skipped)
  - a permanent failure (unrecoverable)
  - a high-value payment (always escalate)
  - a retry-exhausted payment (stop)
  - an overdue B2B invoice (escalate to sales)

Seeded, so runs are reproducible.
"""
from __future__ import annotations

import csv
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "synthetic_payments.csv"
DNC_FILE = ROOT / "data" / "dnc_list.csv"

FIELDS = [
    "payment_id", "merchant_id", "customer_name", "customer_email",
    "customer_phone", "amount", "currency", "failure_reason", "failure_detail",
    "failure_source", "attempts", "created_at", "order_type",
]

# (failure_reason, failure_detail, failure_source, weight) — weights are rough
# real-world proportions so the batch looks like a real merchant's stream.
FAILURE_MIX = [
    ("BAD_REQUEST_ERROR", "FUND_INSUFFICIENT", "customer", 26),
    ("GATEWAY_ERROR", "", "network", 14),
    ("SERVER_ERROR", "", "network", 8),
    ("PAYMENT_CANCELLED", "", "customer", 16),
    ("PAYMENT_TIMEOUT", "", "customer", 8),
    ("BAD_REQUEST_ERROR", "MANDATE_REVOKED", "customer", 8),
    ("BAD_REQUEST_ERROR", "MANDATE_EXPIRED", "bank", 6),
    ("BAD_REQUEST_ERROR", "CARD_EXPIRED", "bank", 8),
    ("BAD_REQUEST_ERROR", "CARD_DECLINED", "bank", 6),
]

ORDER_TYPES = ["one_time", "subscription", "b2b"]
FIRST_NAMES = ["Aarav", "Diya", "Kabir", "Isha", "Rohan", "Meera", "Vikram",
               "Ananya", "Arjun", "Priya", "Karan", "Sara"]
LAST_NAMES = ["Sharma", "Patel", "Reddy", "Nair", "Gupta", "Singh", "Iyer",
              "Bose", "Khan", "Rao"]
AMOUNTS = [4999, 9900, 19900, 29900, 49900, 79900, 99900, 149900, 249900]


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_dnc_contacts() -> list[str]:
    """Read the do-not-contact list so some rows can reuse those contacts."""
    if not DNC_FILE.exists():
        return []
    contacts = []
    for line in DNC_FILE.read_text(encoding="utf-8").splitlines():
        entry = line.strip()
        if entry and not entry.startswith("#") and entry.lower() != "contact":
            contacts.append(entry)
    return contacts


def _weighted_failure(rng: random.Random):
    population = [(r, d, s) for (r, d, s, _) in FAILURE_MIX]
    weights = [w for (*_, w) in FAILURE_MIX]
    return rng.choices(population, weights=weights, k=1)[0]


def generate(n: int = 80, seed: int = 42) -> list[dict]:
    rng = random.Random(seed)
    now = datetime.now(timezone.utc)
    rows: list[dict] = []

    for i in range(1, n + 1):
        reason, detail, source = _weighted_failure(rng)
        name = f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"
        rows.append({
            "payment_id": f"pay_Test_{i:03d}",
            "merchant_id": f"merch_{rng.randint(1, 4):03d}",
            "customer_name": name,
            "customer_email": f"user{i:03d}@example.com",
            "customer_phone": f"+9198{rng.randint(10_000_000, 99_999_999)}",
            "amount": rng.choice(AMOUNTS),
            "currency": "INR",
            "failure_reason": reason,
            "failure_detail": detail,
            "failure_source": source,
            "attempts": rng.choices([1, 2, 3], weights=[70, 20, 10], k=1)[0],
            "created_at": _iso(now - timedelta(days=rng.randint(0, 10),
                                               hours=rng.randint(0, 23))),
            "order_type": rng.choices(ORDER_TYPES, weights=[55, 30, 15], k=1)[0],
        })

    _inject_tricky_rows(rows, now)
    return rows


def _inject_tricky_rows(rows: list[dict], now: datetime) -> None:
    """Overwrite a few rows so every stopping rule is exercised."""
    dnc = load_dnc_contacts()
    dnc_emails = [c for c in dnc if "@" in c]

    # Two DNC customers — must be skipped, never contacted.
    if len(dnc_emails) >= 2:
        rows[16] |= {"payment_id": "pay_Test_017", "customer_email": dnc_emails[0],
                     "failure_reason": "BAD_REQUEST_ERROR",
                     "failure_detail": "FUND_INSUFFICIENT", "attempts": 1}
        rows[33] |= {"payment_id": "pay_Test_034", "customer_email": dnc_emails[1],
                     "failure_reason": "PAYMENT_CANCELLED", "failure_detail": "",
                     "attempts": 1}

    # Permanent failure — unrecoverable, do nothing.
    rows[42] |= {"payment_id": "pay_Test_043", "failure_reason": "PERMANENT_FAILURE",
                 "failure_detail": "", "attempts": 1}

    # Retries exhausted — must stop and escalate.
    rows[60] |= {"payment_id": "pay_Test_061", "attempts": 3,
                 "failure_reason": "GATEWAY_ERROR", "failure_detail": ""}

    # High-value payment — always escalate to a human (over the ₹50,000 rule).
    rows[9] |= {"payment_id": "pay_Test_010", "amount": 60_00_000,  # ₹60,000
                "failure_reason": "BAD_REQUEST_ERROR",
                "failure_detail": "FUND_INSUFFICIENT"}

    # Overdue B2B invoice — age it past the 30-day threshold.
    rows[25] |= {"payment_id": "pay_Test_026", "order_type": "b2b",
                 "created_at": _iso(now - timedelta(days=45)),
                 "failure_reason": "BAD_REQUEST_ERROR", "failure_detail": ""}


def main() -> None:
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 80
    rows = generate(n)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {OUT}")


if __name__ == "__main__":
    main()
