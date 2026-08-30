# ReviveBot Recovery Report

- **Run date:** 2026-08-30 23:04:39
- **Batch size:** 80 failed payments
- **Total at risk:** ₹130,924.96

![Recovery summary](recovery_chart.png)

## Actions taken

| Action | Count | At-risk value |
| --- | ---: | ---: |
| send_payment_link | 52 | ₹43,649.98 |
| send_nudge | 20 | ₹79,031.99 |
| retry_upi | 7 | ₹8,193.00 |
| escalate_human | 1 | ₹49.99 |

## Outcomes (simulated)

- **Recovered:** ₹28,519.99  (21.8% of at-risk)
- **Unrecovered:** ₹102,404.97

## Graceful failures (agent knew when to stop)

- `pay_Test_010` — escalated_high_value: amount 6000000p over high-value threshold; escalated.
- `pay_Test_017` — skipped_dnc: Customer on do-not-contact list.
- `pay_Test_034` — skipped_dnc: Customer on do-not-contact list.
- `pay_Test_041` — max_retries_reached: attempts=3 >= 3; escalated.
- `pay_Test_043` — unrecoverable: Permanent failure — no action taken.
- `pay_Test_044` — max_retries_reached: attempts=3 >= 3; escalated.
- `pay_Test_061` — max_retries_reached: attempts=3 >= 3; escalated.
- `pay_Test_063` — max_retries_reached: attempts=3 >= 3; escalated.
- `pay_Test_073` — max_retries_reached: attempts=3 >= 3; escalated.

---
_Built for Razorpay Buildathon 2025 · Track 03: AI Revenue Recovery_
