"""Central configuration for ReviveBot.

Reads secrets from environment (.env) and defines the tunable thresholds and
stopping rules that gate every recovery action. Nothing here should ever be
committed with real values — see .env.example.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# --- Paths ------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent
DATA_CSV = ROOT / "data" / "synthetic_payments.csv"
AUDIT_DB = ROOT / "audit.db"
REPORT_MD = ROOT / "recovery_report.md"
RESULTS_CSV = ROOT / "results.csv"

# --- Groq (diagnosis engine) -----------------------------------------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
# A fast, capable Groq model. Override with GROQ_MODEL in .env if you like.
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

# --- Razorpay (recovery executor) ------------------------------------------
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")

# --- Stopping rules & compliance -------------------------------------------
# These are the visible, explainable guardrails that make this Track 03 and
# not just a retry script. See section 6 of the spec.
MAX_ATTEMPTS = 3                    # never retry a payment more than this
MIN_CONFIDENCE = 0.5               # below this, escalate instead of auto-acting
HIGH_VALUE_PAISE = 50_000 * 100    # amount above which we always escalate (₹50,000)
INVOICE_OVERDUE_DAYS = 30          # B2B invoice age that counts as overdue

# Customers we must never contact (loaded from a DNC list in a real system).
DO_NOT_CONTACT: set[str] = {
    "dnc_customer@example.com",
    "+919999000001",
}

# --- Run mode ---------------------------------------------------------------
# When True, diagnosis falls back to deterministic rules if no GROQ_API_KEY
# is set, and executor uses mock comms if no Razorpay keys are set. This lets the
# whole batch run end-to-end for a demo without any credentials.
OFFLINE_OK = os.getenv("REVIVEBOT_OFFLINE_OK", "1") == "1"


def has_groq() -> bool:
    return bool(GROQ_API_KEY)


def has_razorpay() -> bool:
    return bool(RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET)
