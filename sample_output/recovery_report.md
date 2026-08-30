# ReviveBot Recovery Report

- **Run date:** 2026-08-30 21:43:20
- **Batch size:** 72 failed payments
- **Total at risk:** ₹96,736.92

## Actions taken

| Action | Count | At-risk value |
| --- | ---: | ---: |
| send_payment_link | 38 | ₹78,817.95 |
| retry_upi | 20 | ₹9,381.98 |
| send_nudge | 12 | ₹8,238.99 |
| escalate_human | 1 | ₹199.00 |
| do_nothing | 1 | ₹99.00 |

## Outcomes (simulated)

- **Recovered:** ₹10,978.96  (11.3% of at-risk)
- **Unrecovered:** ₹85,757.96

## Graceful failures (agent knew when to stop)

- `pay_Test_006` — max_retries_reached: attempts=3 >= 3; escalated.
- `pay_Test_010` — escalated_high_value: amount 6000000p over high-value threshold; escalated.
- `pay_Test_017` — skipped_dnc: Customer on do-not-contact list.
- `pay_Test_019` — max_retries_reached: attempts=3 >= 3; escalated.
- `pay_Test_026` — escalated: Flagged for human follow-up; no further retries.
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
