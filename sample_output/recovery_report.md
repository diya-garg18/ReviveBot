# ReviveBot Recovery Report

- **Run date:** 2026-08-30 22:41:17
- **Batch size:** 72 failed payments
- **Total at risk:** ₹96,736.92

![Recovery summary](recovery_chart.png)

## Actions taken

| Action | Count | At-risk value |
| --- | ---: | ---: |
| send_payment_link | 39 | ₹21,815.95 |
| send_nudge | 16 | ₹68,286.98 |
| retry_upi | 15 | ₹6,335.99 |
| escalate_human | 2 | ₹298.00 |

## Outcomes (simulated)

- **Recovered:** ₹12,124.97  (12.5% of at-risk)
- **Unrecovered:** ₹84,611.95

## Graceful failures (agent knew when to stop)

- `pay_Test_006` — max_retries_reached: attempts=3 >= 3; escalated.
- `pay_Test_010` — escalated_high_value: amount 6000000p over high-value threshold; escalated.
- `pay_Test_017` — skipped_dnc: Customer on do-not-contact list.
- `pay_Test_019` — max_retries_reached: attempts=3 >= 3; escalated.
- `pay_Test_030` — max_retries_reached: attempts=3 >= 3; escalated.
- `pay_Test_034` — max_retries_reached: attempts=3 >= 3; escalated.
- `pay_Test_037` — max_retries_reached: attempts=3 >= 3; escalated.
- `pay_Test_042` — max_retries_reached: attempts=3 >= 3; escalated.
- `pay_Test_043` — unrecoverable: Permanent failure — no action taken.
- `pay_Test_044` — max_retries_reached: attempts=3 >= 3; escalated.
- `pay_Test_051` — max_retries_reached: attempts=3 >= 3; escalated.
- `pay_Test_055` — max_retries_reached: attempts=3 >= 3; escalated.
- `pay_Test_061` — max_retries_reached: attempts=3 >= 3; escalated.

---
_Built for Razorpay Buildathon 2025 · Track 03: AI Revenue Recovery_
