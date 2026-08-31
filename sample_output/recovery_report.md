# ReviveBot Recovery Report

- **Run date:** 2026-08-31 09:52:05
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

## Recovery by failure type

| Failure type | Count | At risk | Recovered | Rate |
| --- | ---: | ---: | ---: | ---: |
| insufficient_funds | 24 | ₹78,477.00 | ₹4,992.00 | 6.4% |
| mandate_broken | 26 | ₹23,626.97 | ₹13,837.99 | 58.6% |
| user_abandoned | 17 | ₹18,583.00 | ₹9,191.00 | 49.5% |
| network_error | 11 | ₹9,689.00 | ₹0.00 | 0.0% |
| invoice_overdue | 1 | ₹499.00 | ₹499.00 | 100.0% |
| permanent_failure | 1 | ₹49.99 | ₹0.00 | 0.0% |

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
