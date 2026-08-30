"""Tests for the recovery executor's compliance stopping rules.

These are the rules that make ReviveBot safe: they must fire *before* any
recovery action. Each test sends a plan that would normally act, plus a record
that should trip one rule, and checks the outcome.
"""
import config
from revivebot.diagnosis import ActionPlan
from revivebot.executor import execute


def _plan(action="send_payment_link", confidence=0.8, channel="upi"):
    return ActionPlan(action=action, reason="test", confidence=confidence,
                      channel=channel, message_template="hi", stop_if="")


def _record(**overrides):
    record = {
        "payment_id": "pay_TEST", "customer_email": "user@example.com",
        "customer_phone": "+919812345678", "amount": 4999,
        "failure_reason": "BAD_REQUEST_ERROR", "attempts": 1,
    }
    record.update(overrides)
    return record


def test_do_not_contact_customer_is_skipped():
    dnc_email = next(iter(config.DO_NOT_CONTACT))
    outcome = execute(_plan(), _record(customer_email=dnc_email))
    assert outcome["outcome"] == "skipped_dnc"
    assert outcome["recovered"] == 0


def test_permanent_failure_is_unrecoverable():
    outcome = execute(_plan(), _record(failure_reason="PERMANENT_FAILURE"))
    assert outcome["outcome"] == "unrecoverable"


def test_max_attempts_stops_retrying():
    outcome = execute(_plan(), _record(attempts=config.MAX_ATTEMPTS))
    assert outcome["outcome"] == "max_retries_reached"


def test_high_value_payment_is_escalated():
    outcome = execute(_plan(), _record(amount=config.HIGH_VALUE_PAISE + 1))
    assert outcome["outcome"] == "escalated_high_value"


def test_low_confidence_is_escalated():
    outcome = execute(_plan(confidence=0.2), _record())
    assert outcome["outcome"] == "escalated_low_confidence"


def test_do_nothing_recovers_nothing():
    outcome = execute(_plan(action="do_nothing", confidence=0.9), _record())
    assert outcome["outcome"] == "skipped"
    assert outcome["recovered"] == 0


def test_recovery_amount_is_deterministic():
    # Same payment id -> same simulated outcome on every run.
    a = execute(_plan(), _record())
    b = execute(_plan(), _record())
    assert a["recovered"] == b["recovered"]
