"""Render a small summary chart for the recovery report.

One figure, two simple panels:
  1. Money recovered vs. still unrecovered (₹).
  2. How many payments got each action.

Kept dependency-light and optional: report.py skips the chart if matplotlib
isn't installed, so the batch never fails just because a chart can't be drawn.
"""
from __future__ import annotations

from pathlib import Path


def render_chart(rows: list[dict], stats: dict, out_png: Path) -> Path:
    """Draw the summary chart to out_png and return its path."""
    import matplotlib
    matplotlib.use("Agg")  # no display needed — write straight to a file
    import matplotlib.pyplot as plt

    fig, (ax_money, ax_actions) = plt.subplots(1, 2, figsize=(11, 4.2))
    fig.suptitle("ReviveBot — recovery summary", fontsize=14, fontweight="bold")

    # Panel 1: recovered vs unrecovered money (convert paise -> rupees).
    recovered = stats["recovered"] / 100
    unrecovered = stats["unrecovered"] / 100
    ax_money.bar(["Recovered", "Unrecovered"], [recovered, unrecovered],
                 color=["#2e7d32", "#c62828"])
    ax_money.set_ylabel("₹")
    ax_money.set_title(f"{stats['recovery_rate']:.1f}% of at-risk recovered")
    for i, value in enumerate([recovered, unrecovered]):
        ax_money.text(i, value, f"₹{value:,.0f}", ha="center", va="bottom")

    # Panel 2: count of payments per action, largest at the top.
    counts: dict[str, int] = {}
    for row in rows:
        key = row["action"] or "unknown"
        counts[key] = counts.get(key, 0) + 1
    actions = sorted(counts, key=counts.get)
    ax_actions.barh(actions, [counts[a] for a in actions], color="#1565c0")
    ax_actions.set_xlabel("payments")
    ax_actions.set_title("Actions taken")
    for i, action in enumerate(actions):
        ax_actions.text(counts[action], i, f" {counts[action]}", va="center")

    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(out_png, dpi=120)
    plt.close(fig)
    return out_png
