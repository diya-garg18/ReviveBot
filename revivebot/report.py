"""Report generator — turn the audit log into the money shot.

Produces two artefacts from audit.db:
  * recovery_report.md — human-readable headline numbers for the judges
  * results.csv        — the full per-payment table for a spreadsheet

The headline is measured money: recovered vs. at-risk, and the recovery rate.
"""
from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

import config
from revivebot.audit import connect


def _rupees(paise: int) -> str:
    """Format paise as ₹ with two decimals."""
    rupees = paise / 100
    s = f"{rupees:,.2f}"
    return f"₹{s}"


def _fetch_rows(db_path: Path | str = None) -> list[dict]:
    with connect(db_path) as conn:
        cur = conn.execute("SELECT * FROM audit_log ORDER BY id")
        return [dict(r) for r in cur.fetchall()]


def _write_csv(rows: list[dict], out_csv: Path) -> None:
    if not rows:
        out_csv.write_text("", encoding="utf-8")
        return
    fields = list(rows[0].keys())
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def generate_report(
    db_path: Path | str = None,
    out_md: Path | str = None,
    out_csv: Path | str = None,
) -> dict:
    """Build the report files and return the headline stats as a dict."""
    out_md = Path(out_md or config.REPORT_MD)
    out_csv = Path(out_csv or config.RESULTS_CSV)

    rows = _fetch_rows(db_path)
    _write_csv(rows, out_csv)

    total = len(rows)
    at_risk = sum(r["amount"] for r in rows)
    recovered = sum(r["recovered"] for r in rows)
    unrecovered = at_risk - recovered
    rate = (recovered / at_risk * 100) if at_risk else 0.0

    # Actions taken: count + at-risk value per action.
    by_action: dict[str, dict[str, int]] = {}
    for r in rows:
        a = by_action.setdefault(r["action"] or "unknown", {"count": 0, "at_risk": 0})
        a["count"] += 1
        a["at_risk"] += r["amount"]

    # Recovery by failure type: count, at-risk, recovered, and rate per bucket.
    by_failure: dict[str, dict[str, int]] = {}
    for r in rows:
        f = by_failure.setdefault(r["failure_type"] or "unknown",
                                  {"count": 0, "at_risk": 0, "recovered": 0})
        f["count"] += 1
        f["at_risk"] += r["amount"]
        f["recovered"] += r["recovered"]

    # Graceful failures — the cases where the agent correctly stopped.
    graceful_outcomes = {
        "escalated", "escalated_high_value", "escalated_low_confidence",
        "max_retries_reached", "skipped_dnc", "unrecoverable",
    }
    graceful = [r for r in rows if r["outcome"] in graceful_outcomes]

    # Draw the summary chart next to the report. Optional: if matplotlib isn't
    # installed the report is still produced, just without the image.
    chart_name = None
    if rows:
        chart_stats = {"recovered": recovered, "unrecovered": unrecovered,
                       "recovery_rate": rate}
        try:
            from revivebot.chart import render_chart
            out_png = out_md.with_name("recovery_chart.png")
            render_chart(rows, chart_stats, out_png)
            chart_name = out_png.name
        except Exception:
            chart_name = None

    lines: list[str] = []
    lines.append("# ReviveBot Recovery Report")
    lines.append("")
    lines.append(f"- **Run date:** {datetime.now():%Y-%m-%d %H:%M:%S}")
    lines.append(f"- **Batch size:** {total} failed payments")
    lines.append(f"- **Total at risk:** {_rupees(at_risk)}")
    lines.append("")
    if chart_name:
        lines.append(f"![Recovery summary]({chart_name})")
        lines.append("")
    lines.append("## Actions taken")
    lines.append("")
    lines.append("| Action | Count | At-risk value |")
    lines.append("| --- | ---: | ---: |")
    for action, stats in sorted(by_action.items(), key=lambda kv: -kv[1]["count"]):
        lines.append(f"| {action} | {stats['count']} | {_rupees(stats['at_risk'])} |")
    lines.append("")
    lines.append("## Outcomes (simulated)")
    lines.append("")
    lines.append(f"- **Recovered:** {_rupees(recovered)}  ({rate:.1f}% of at-risk)")
    lines.append(f"- **Unrecovered:** {_rupees(unrecovered)}")
    lines.append("")
    lines.append("## Recovery by failure type")
    lines.append("")
    lines.append("| Failure type | Count | At risk | Recovered | Rate |")
    lines.append("| --- | ---: | ---: | ---: | ---: |")
    for ftype, s in sorted(by_failure.items(), key=lambda kv: -kv[1]["at_risk"]):
        ftype_rate = (s["recovered"] / s["at_risk"] * 100) if s["at_risk"] else 0.0
        lines.append(
            f"| {ftype} | {s['count']} | {_rupees(s['at_risk'])} | "
            f"{_rupees(s['recovered'])} | {ftype_rate:.1f}% |"
        )
    lines.append("")
    lines.append("## Graceful failures (agent knew when to stop)")
    lines.append("")
    if graceful:
        for r in graceful[:15]:
            lines.append(f"- `{r['payment_id']}` — {r['outcome']}: {r['note']}")
    else:
        lines.append("- (none in this batch)")
    lines.append("")
    lines.append("---")
    lines.append("_Built for Razorpay Buildathon 2025 · Track 03: AI Revenue Recovery_")

    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    return {
        "batch_size": total,
        "at_risk": at_risk,
        "recovered": recovered,
        "unrecovered": unrecovered,
        "recovery_rate": rate,
        "report_md": str(out_md),
        "results_csv": str(out_csv),
    }
