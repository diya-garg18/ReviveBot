"""ReviveBot entry point — run the recovery agent over a batch of failures.

    python main.py

Reads data/synthetic_payments.csv, and for each failed payment:
  detect failure type -> diagnose action -> execute (with stopping rules)
  -> log to audit.db. Finally, generate recovery_report.md + results.csv.

Runs with no credentials at all: diagnosis falls back to rules and comms are
mocked (see config.OFFLINE_OK). Set ANTHROPIC_API_KEY / RAZORPAY_* to use the
real Claude diagnosis and Razorpay test-mode links.
"""
from __future__ import annotations

import csv
import sys

# Windows consoles default to cp1252, which can't encode ₹ or em dashes.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

import config
from revivebot.audit import init_db, log_action
from revivebot.detector import classify
from revivebot.diagnosis import diagnose
from revivebot.executor import execute
from revivebot.report import generate_report


def load_records(csv_path=None) -> list[dict]:
    path = csv_path or config.DATA_CSV
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def run(limit: int | None = None) -> dict:
    mode = "Groq" if config.has_groq() else "rule-based (offline)"
    comms = "Razorpay test" if config.has_razorpay() else "mock comms (offline)"
    print(f"ReviveBot — diagnosis: {mode} | execution: {comms}")
    print("-" * 60)

    records = load_records()
    if limit is not None:
        records = records[:limit]  # process only the first N (handy for demos)
    init_db()

    for record in records:
        ftype = classify(record)
        plan = diagnose(record, ftype)
        outcome = execute(plan, record)
        log_action(record, ftype, plan, outcome)
        print(
            f"{record['payment_id']:>16}  {ftype:<18} "
            f"-> {plan.action:<18} -> {outcome['outcome']}"
        )

    print("-" * 60)
    stats = generate_report()
    print(
        f"Batch: {stats['batch_size']} | "
        f"At risk: ₹{stats['at_risk']/100:,.2f} | "
        f"Recovered: ₹{stats['recovered']/100:,.2f} "
        f"({stats['recovery_rate']:.1f}%)"
    )
    print(f"Report:  {stats['report_md']}")
    print(f"Results: {stats['results_csv']}")
    print(f"Audit:   {config.AUDIT_DB}")
    return stats


def _parse_args():
    import argparse

    parser = argparse.ArgumentParser(description="Run the ReviveBot recovery agent.")
    parser.add_argument(
        "--limit", type=int, default=None, metavar="N",
        help="only process the first N payments (useful for a quick demo)",
    )
    parser.add_argument(
        "--offline", action="store_true",
        help="ignore all API keys and run on rules + mock comms only",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    if args.offline:
        config.FORCE_OFFLINE = True
    run(limit=args.limit)
