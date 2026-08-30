"""Tests for the failure detector.

Each test builds one payment record and checks it lands in the expected
failure bucket. The detector is pure and deterministic, so these are simple
input-to-label checks.
"""
from datetime import datetime, timedelta, timezone

from revivebot.detector import classify


def _iso_days_ago(days: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


def test_insufficient_funds_is_detected():
    row = {"failure_reason": "BAD_REQUEST_ERROR", "failure_detail": "FUND_INSUFFICIENT",
           "order_type": "one_time", "created_at": _iso_days_ago(1)}
    assert classify(row) == "insufficient_funds"


def test_network_error_is_detected():
    row = {"failure_reason": "GATEWAY_ERROR", "failure_detail": "",
           "order_type": "one_time", "created_at": _iso_days_ago(1)}
    assert classify(row) == "network_error"


def test_cancelled_payment_is_user_abandoned():
    row = {"failure_reason": "PAYMENT_CANCELLED", "failure_detail": "",
           "order_type": "subscription", "created_at": _iso_days_ago(1)}
    assert classify(row) == "user_abandoned"


def test_broken_mandate_is_detected():
    row = {"failure_reason": "BAD_REQUEST_ERROR", "failure_detail": "MANDATE_REVOKED",
           "order_type": "subscription", "created_at": _iso_days_ago(1)}
    assert classify(row) == "mandate_broken"


def test_old_b2b_invoice_is_overdue():
    row = {"failure_reason": "BAD_REQUEST_ERROR", "failure_detail": "",
           "order_type": "b2b", "created_at": _iso_days_ago(45)}
    assert classify(row) == "invoice_overdue"


def test_recent_b2b_invoice_is_not_overdue():
    row = {"failure_reason": "GATEWAY_ERROR", "failure_detail": "",
           "order_type": "b2b", "created_at": _iso_days_ago(5)}
    assert classify(row) == "network_error"


def test_permanent_failure_is_detected():
    row = {"failure_reason": "PERMANENT_FAILURE", "failure_detail": "",
           "order_type": "one_time", "created_at": _iso_days_ago(1)}
    assert classify(row) == "permanent_failure"


def test_unrecognised_reason_is_unknown():
    row = {"failure_reason": "SOMETHING_NEW", "failure_detail": "",
           "order_type": "one_time", "created_at": _iso_days_ago(1)}
    assert classify(row) == "unknown"
