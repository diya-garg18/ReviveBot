"""Signal detector — classify each payment record into a failure bucket.

The detector is deliberately dumb and deterministic: it maps Razorpay-style
error codes and order metadata to one of a small, fixed set of failure types.
All the *judgement* about what to do lives in the diagnosis engine.
"""
from __future__ import annotations

from datetime import datetime, timezone

# Failure buckets and the raw signals that map into them. A signal is matched as
# a prefix of "<failure_reason>" or "<failure_reason>:<failure_detail>".
FAILURE_TYPES: dict[str, list[str]] = {
    "insufficient_funds": ["BAD_REQUEST_ERROR:FUND"],
    "network_error": ["GATEWAY_ERROR", "SERVER_ERROR"],
    "user_abandoned": ["PAYMENT_CANCELLED"],
    "mandate_broken": ["BAD_REQUEST_ERROR:MANDATE"],
    "invoice_overdue": [],  # handled specially via order_type + age
}

# Reasons that can never be recovered — the detector flags them so the executor
# stops immediately instead of burning retries.
PERMANENT_FAILURES = {"PERMANENT_FAILURE"}


def days_since(iso_ts: str) -> int:
    """Whole days between an ISO-8601 timestamp and now (UTC)."""
    ts = datetime.fromisoformat(iso_ts.replace("Z", "+00:00"))
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - ts).days


def _signal(row: dict) -> str:
    """Build the match key: 'REASON' or 'REASON:DETAIL' (both upper-cased)."""
    reason = str(row.get("failure_reason", "")).strip().upper()
    detail = str(row.get("failure_detail", "")).strip().upper()
    return f"{reason}:{detail}" if detail else reason


def classify(row: dict) -> str:
    """Return the failure bucket for a payment record.

    Order matters: overdue B2B invoices and permanent failures take precedence
    over the generic error-code mapping.
    """
    reason = str(row.get("failure_reason", "")).strip().upper()
    if reason in PERMANENT_FAILURES:
        return "permanent_failure"

    if row.get("order_type") == "b2b":
        created = row.get("created_at")
        from config import INVOICE_OVERDUE_DAYS

        if created and days_since(created) > INVOICE_OVERDUE_DAYS:
            return "invoice_overdue"

    signal = _signal(row)
    for bucket, codes in FAILURE_TYPES.items():
        if any(signal.startswith(code) for code in codes):
            return bucket

    return "unknown"
