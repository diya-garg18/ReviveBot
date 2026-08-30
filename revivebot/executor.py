"""Recovery executor — apply stopping rules, then run the chosen action.

The stopping rules run *before* any action and are the compliance backbone of
the agent: max retries, do-not-contact, high-value escalation, low-confidence
escalation, permanent-failure handling. Only if every rule passes does the
executor actually act.

Actions go to Razorpay test mode when keys are present, otherwise to a mock
comms channel. Either way the *outcome* (whether the money came back) is
simulated deterministically so the batch produces a measurable report without
moving real money.
"""
from __future__ import annotations

import hashlib

import config
from revivebot.diagnosis import ActionPlan


class MockComms:
    """Stand-in for email/WhatsApp/SMS providers. Records what would be sent."""

    def send(self, channel: str, to: str, message: str) -> dict:
        return {"provider": "mock", "channel": channel, "to": to, "sent": True}


mock_comms = MockComms()


def _recovery_probability(plan: ActionPlan, record: dict) -> float:
    """Blend the model's confidence with a per-action base rate."""
    base = {
        "retry_upi": 0.55,
        "send_payment_link": 0.45,
        "send_nudge": 0.30,
        "escalate_human": 0.20,
        "do_nothing": 0.0,
    }.get(plan.action, 0.0)
    return max(0.0, min(1.0, 0.5 * base + 0.5 * plan.confidence))


def _simulate_recovered(plan: ActionPlan, record: dict) -> int:
    """Deterministic simulated outcome, in paise. Seeded by payment_id so runs
    are reproducible and judges see stable numbers."""
    prob = _recovery_probability(plan, record)
    seed = hashlib.sha256(str(record.get("payment_id", "")).encode()).hexdigest()
    roll = int(seed[:8], 16) / 0xFFFFFFFF  # uniform 0..1
    return int(record.get("amount", 0)) if roll < prob else 0


def _stopping_rule(plan: ActionPlan, record: dict) -> dict | None:
    """Return a terminal outcome if a compliance rule fires, else None."""
    email = str(record.get("customer_email", ""))
    phone = str(record.get("customer_phone", ""))
    amount = int(record.get("amount", 0))
    attempts = int(record.get("attempts", 0))

    if email in config.DO_NOT_CONTACT or phone in config.DO_NOT_CONTACT:
        return {"outcome": "skipped_dnc", "recovered": 0,
                "note": "Customer on do-not-contact list."}
    if str(record.get("failure_reason", "")).upper() == "PERMANENT_FAILURE":
        return {"outcome": "unrecoverable", "recovered": 0,
                "note": "Permanent failure — no action taken."}
    if attempts >= config.MAX_ATTEMPTS:
        return {"outcome": "max_retries_reached", "recovered": 0,
                "note": f"attempts={attempts} >= {config.MAX_ATTEMPTS}; escalated."}
    if amount > config.HIGH_VALUE_PAISE and plan.action != "escalate_human":
        return {"outcome": "escalated_high_value", "recovered": 0,
                "note": f"amount {amount}p over high-value threshold; escalated."}
    if plan.confidence < config.MIN_CONFIDENCE and plan.action not in (
        "escalate_human", "do_nothing"
    ):
        return {"outcome": "escalated_low_confidence", "recovered": 0,
                "note": f"confidence {plan.confidence:.2f} < {config.MIN_CONFIDENCE}."}
    return None


def _razorpay_client():
    import razorpay  # lazy import — only needed when keys are present

    return razorpay.Client(auth=(config.RAZORPAY_KEY_ID, config.RAZORPAY_KEY_SECRET))


def _create_payment_link(record: dict) -> dict:
    """Create a Razorpay test-mode payment link, or a mock one when offline."""
    if config.has_razorpay():
        client = _razorpay_client()
        link = client.payment_link.create({
            "amount": int(record["amount"]),
            "currency": "INR",
            "description": f"Recovery: {record['payment_id']}",
            "customer": {
                "email": record.get("customer_email", ""),
                "contact": record.get("customer_phone", ""),
            },
            "notify": {"email": True, "sms": True},
            "notes": {"original_payment": record["payment_id"]},
        })
        return {"provider": "razorpay_test", "link_id": link.get("id"),
                "link": link.get("short_url")}
    return {"provider": "mock", "link_id": f"plink_mock_{record['payment_id']}",
            "link": f"https://rzp.io/i/mock/{record['payment_id']}"}


def execute(plan: ActionPlan, record: dict) -> dict:
    """Run the plan for one record and return an outcome dict.

    Outcome keys: outcome (str), recovered (int paise), plus action-specific
    detail. Every path returns a dict — nothing is silently dropped.
    """
    stop = _stopping_rule(plan, record)
    if stop is not None:
        return stop

    if plan.action == "do_nothing":
        return {"outcome": "skipped", "recovered": 0, "note": plan.reason}

    if plan.action == "escalate_human":
        return {"outcome": "escalated", "recovered": 0,
                "note": "Flagged for human follow-up; no further retries."}

    if plan.action in ("retry_upi", "send_payment_link"):
        link = _create_payment_link(record)
        recovered = _simulate_recovered(plan, record)
        return {"outcome": "recovered" if recovered else "link_sent",
                "recovered": recovered, **link}

    if plan.action == "send_nudge":
        msg = plan.message_template or "Complete your payment."
        to = (record.get("customer_phone") if plan.channel == "whatsapp"
              else record.get("customer_email", ""))
        sent = mock_comms.send(plan.channel, to, msg)
        recovered = _simulate_recovered(plan, record)
        return {"outcome": "recovered" if recovered else "nudge_sent",
                "recovered": recovered, **sent}

    return {"outcome": "no_action", "recovered": 0,
            "note": f"Unhandled action: {plan.action}"}
