"""Diagnosis engine — decide the right recovery action for a failed payment.

Primary path: call Claude with a tight schema (via ``messages.parse``) so the
response is a *validated* action plan — no hand-rolled JSON parsing, no
malformed-JSON retries.

Fallback path: if no ANTHROPIC_API_KEY is configured (and OFFLINE_OK is set),
a deterministic rule table produces the same shape of plan so the batch still
runs end-to-end for a demo.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

import config

Action = Literal[
    "retry_upi",
    "send_payment_link",
    "send_nudge",
    "escalate_human",
    "do_nothing",
]
Channel = Literal["upi", "card", "email", "whatsapp", "none"]


class ActionPlan(BaseModel):
    """The structured decision the agent commits to for one payment."""

    action: Action
    reason: str = Field(description="One sentence explaining the choice.")
    confidence: float = Field(ge=0.0, le=1.0)
    channel: Channel
    message_template: str = Field(
        default="", description="Short customer message, if a message is sent."
    )
    stop_if: str = Field(
        default="", description="Condition that should halt further retries."
    )


SYSTEM_PROMPT = """You are a payment recovery specialist for an Indian merchant.
Given a single failed payment record and its classified failure_type, choose the
single best recovery action. Be conservative and compliant:

- Prefer the cheapest effective channel. For subscription customers prefer
  WhatsApp over email; for one-time payments a payment link is usually best.
- If the failure looks permanent, or the customer is high-value/risky, choose
  escalate_human rather than auto-acting.
- If nothing productive can be done, choose do_nothing.

Return an action plan. confidence is your own calibrated 0-1 estimate that the
action will recover the payment. Keep message_template under 160 characters."""


def _diagnose_claude(record: dict, failure_type: str) -> ActionPlan:
    import json

    import anthropic  # imported lazily so offline runs need no SDK

    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    user_payload = {
        "failure_type": failure_type,
        "payment": {
            "payment_id": record.get("payment_id"),
            "amount_paise": record.get("amount"),
            "order_type": record.get("order_type"),
            "attempts": record.get("attempts"),
            "failure_reason": record.get("failure_reason"),
            "failure_detail": record.get("failure_detail"),
            "failure_source": record.get("failure_source"),
            "created_at": record.get("created_at"),
        },
    }
    response = client.messages.parse(
        model=config.CLAUDE_MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": json.dumps(user_payload)}],
        output_format=ActionPlan,
    )
    return response.parsed_output


# --- Deterministic fallback -------------------------------------------------
_RULES: dict[str, ActionPlan] = {
    "insufficient_funds": ActionPlan(
        action="send_payment_link", reason="Funds may be available on retry via a fresh link.",
        confidence=0.6, channel="upi",
        message_template="Your payment didn't go through. Complete it here: {link}",
        stop_if="attempts >= 3",
    ),
    "network_error": ActionPlan(
        action="retry_upi", reason="Transient gateway/network error is worth one retry.",
        confidence=0.7, channel="upi",
        message_template="We hit a glitch. Retry your payment here: {link}",
        stop_if="attempts >= 3",
    ),
    "user_abandoned": ActionPlan(
        action="send_nudge", reason="Customer dropped off; a contextual nudge can recover it.",
        confidence=0.55, channel="whatsapp",
        message_template="Still want it? Finish checkout here: {link}",
        stop_if="customer replies STOP",
    ),
    "mandate_broken": ActionPlan(
        action="send_payment_link", reason="Broken mandate needs re-initiation via a new link.",
        confidence=0.5, channel="email",
        message_template="Please re-authorise your subscription: {link}",
        stop_if="attempts >= 3",
    ),
    "invoice_overdue": ActionPlan(
        action="escalate_human", reason="Overdue B2B invoice needs human/sales follow-up.",
        confidence=0.8, channel="email",
        message_template="", stop_if="handed to sales",
    ),
    "permanent_failure": ActionPlan(
        action="do_nothing", reason="Permanent failure is unrecoverable; do not retry.",
        confidence=0.95, channel="none", message_template="", stop_if="always",
    ),
    "unknown": ActionPlan(
        action="escalate_human", reason="Unclassified failure — escalate for a human look.",
        confidence=0.4, channel="none", message_template="", stop_if="",
    ),
}


def _diagnose_rules(record: dict, failure_type: str) -> ActionPlan:
    return _RULES.get(failure_type, _RULES["unknown"]).model_copy()


def diagnose(record: dict, failure_type: str) -> ActionPlan:
    """Return an ActionPlan for one record, via Claude or the rule fallback."""
    if config.has_claude():
        try:
            return _diagnose_claude(record, failure_type)
        except Exception as exc:  # never let one bad call kill the batch
            if not config.OFFLINE_OK:
                raise
            plan = _diagnose_rules(record, failure_type)
            plan.reason = f"[fallback: {type(exc).__name__}] {plan.reason}"
            return plan
    if not config.OFFLINE_OK:
        raise RuntimeError("No ANTHROPIC_API_KEY set and OFFLINE_OK is disabled.")
    return _diagnose_rules(record, failure_type)
