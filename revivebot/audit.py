"""Audit logger — every decision and outcome is written to SQLite.

This is the agent's accountability record: one row per payment processed, with
the failure type, the action chosen, the model's reason and confidence, and the
outcome including rupees recovered. Judges can open audit.db and inspect it.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import config
from revivebot.diagnosis import ActionPlan

SCHEMA = """
CREATE TABLE IF NOT EXISTS audit_log (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    payment_id   TEXT NOT NULL,
    failure_type TEXT,
    action       TEXT,
    reason       TEXT,
    confidence   REAL,
    channel      TEXT,
    outcome      TEXT,
    recovered    INTEGER DEFAULT 0,   -- paise
    amount       INTEGER DEFAULT 0,   -- paise, at-risk
    note         TEXT,
    ts           TEXT DEFAULT (datetime('now'))
);
"""


def connect(db_path: Path | str = None) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path or config.AUDIT_DB))
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path | str = None) -> None:
    """Create the table if needed and clear any prior run for a clean report."""
    with connect(db_path) as conn:
        conn.executescript(SCHEMA)
        conn.execute("DELETE FROM audit_log")
        conn.commit()


def log_action(
    record: dict,
    failure_type: str,
    plan: ActionPlan,
    outcome: dict,
    db_path: Path | str = None,
) -> None:
    with connect(db_path) as conn:
        conn.execute(
            """INSERT INTO audit_log
               (payment_id, failure_type, action, reason, confidence, channel,
                outcome, recovered, amount, note)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                record.get("payment_id"),
                failure_type,
                plan.action,
                plan.reason,
                plan.confidence,
                plan.channel,
                outcome.get("outcome"),
                int(outcome.get("recovered", 0)),
                int(record.get("amount", 0)),
                outcome.get("note", ""),
            ),
        )
        conn.commit()
