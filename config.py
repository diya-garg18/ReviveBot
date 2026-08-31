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
DNC_FILE = ROOT / "data" / "dnc_list.csv"
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

# Customers we must never contact. Loaded from data/dnc_list.csv so the list
# can be maintained without touching code. Falls back to a small default set if
# the file is missing.
_DEFAULT_DNC = {"dnc_customer@example.com", "+919999000001"}


def load_dnc(path: Path | str = None) -> set[str]:
    """Read the do-not-contact list. One contact per line; '#' comments and the
    'contact' header are ignored."""
    path = Path(path or DNC_FILE)
    if not path.exists():
        return set(_DEFAULT_DNC)
    contacts: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        entry = line.strip()
        if not entry or entry.startswith("#") or entry.lower() == "contact":
            continue
        contacts.add(entry)
    return contacts or set(_DEFAULT_DNC)


DO_NOT_CONTACT: set[str] = load_dnc()

# --- Run mode ---------------------------------------------------------------
# When True, diagnosis falls back to deterministic rules if no GROQ_API_KEY
# is set, and executor uses mock comms if no Razorpay keys are set. This lets the
# whole batch run end-to-end for a demo without any credentials.
OFFLINE_OK = os.getenv("REVIVEBOT_OFFLINE_OK", "1") == "1"

# Set True at runtime (e.g. `main.py --offline`) to ignore all credentials and
# run purely on rules + mock comms, even when keys are present.
FORCE_OFFLINE = False


def has_groq() -> bool:
    return bool(GROQ_API_KEY) and not FORCE_OFFLINE


def has_razorpay() -> bool:
    return bool(RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET) and not FORCE_OFFLINE
