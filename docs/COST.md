# Cost report (ConfigProof)

## Model and prices used
- Provider/model: **fake provider** (no API key, no network), so real cost is $0.
- Prices in `.env`: `PRICE_INPUT_PER_MILLION=0` and `PRICE_OUTPUT_PER_MILLION=0`.
- Pricing page: not applicable for the fake provider. For the cost estimate below I used the example prices from the Session 5 notes (hypothetical): $0.50 per million input tokens and $1.50 per million output tokens.

## Measured from GET /usage
- Questions asked through POST /chat: 11 calls (10 ConfigProof questions about Kconfig and Apache NuttX, plus one repeated question)
- Total input tokens: 139
- Total output tokens: 268
- Average input tokens per question: 139 / 11 = 12.6
- Average output tokens per question: 268 / 11 = 24.4
- Note: the fake provider does not report usage, so these tokens are **estimated** (about 4 characters per token, `usage_estimated: true`). They are for logging only, not for billing.

## Cost
Formula: input tokens x input price + output tokens x output price, per million.

| | Value |
|---|---|
| Cost per question (example prices) | about $0.000043 |
| Cost per 1,000 questions (example prices) | about $0.043 |
| Real cost with the fake provider | $0 |

Working: (12.6 x 0.50 + 24.4 x 1.50) / 1,000,000 = about $0.0000429 per question.

## One way I would cut the cost for ConfigProof
Real questions will include retrieved Kconfig context (option name, type, default, dependencies, help text). Input tokens will dominate the bill, so I would retrieve only the few most relevant Kconfig options instead of whole files, and cache repeated questions.
