"""Test the report generator's headline maths.

Builds a tiny audit database in a temp file, runs the report, and checks the
recovered / at-risk totals and recovery rate.
"""
from revivebot import audit, report
from revivebot.diagnosis import ActionPlan


def _plan(action, confidence=0.8):
    return ActionPlan(action=action, reason="test", confidence=confidence,
                      channel="upi", message_template="", stop_if="")


def test_report_totals(tmp_path):
    db = tmp_path / "audit.db"
    audit.init_db(db)

    # Two payments worth ₹100 each; one recovers fully, one recovers nothing.
    audit.log_action({"payment_id": "p1", "amount": 10000}, "network_error",
                     _plan("retry_upi"), {"outcome": "recovered", "recovered": 10000}, db)
    audit.log_action({"payment_id": "p2", "amount": 10000}, "user_abandoned",
                     _plan("send_nudge"), {"outcome": "nudge_sent", "recovered": 0}, db)

    stats = report.generate_report(db, tmp_path / "r.md", tmp_path / "r.csv")

    assert stats["batch_size"] == 2
    assert stats["at_risk"] == 20000
    assert stats["recovered"] == 10000
    assert stats["unrecovered"] == 10000
    assert round(stats["recovery_rate"], 1) == 50.0
    assert (tmp_path / "r.md").exists()
    assert (tmp_path / "r.csv").exists()
