# V2 Sharpe-ratio significance vs the policy benchmark (Ledoit–Wolf 2008) [E]

**Reproduce:** `python scripts/research_v2_sharpe_test.py` → `outputs/tables/research_v2_sharpe_test.csv` (about 2 min).

**Question (raised in an external QA review):** our documents quote a higher Sharpe ratio than the Policy 40/50/10 benchmark (walk-forward 0.89 vs 0.75). Is the difference statistically significant?

## Method
- **Test:** Ledoit & Wolf (2008), "Robust performance hypothesis testing with the Sharpe ratio". H0 is that the two portfolios have equal Sharpe ratios. The data are daily excess returns over DTB3, and both portfolios are rebalanced quarterly (D11).
  - **Primary:** HAC standard error from the delta method on the first and second moments, with a Parzen kernel and the Andrews (1991) automatic bandwidth.
  - **Check:** their studentized circular block bootstrap with blocks of 21 days (5 and 63 as sensitivity), 5,000 resamples, seed 42.
- **Why not Jobson–Korkie / Memmel:** those assume i.i.d. normal returns. Our returns have fat tails and volatility clustering (P2, T8), which is exactly the case Ledoit–Wolf was designed for.
- **Reproduction first:** every Sharpe ratio is recomputed and matches the published value within 0.001. The walk-forward is rebuilt from `research_walkforward_weights.csv`; the period figures come from `kpis.csv`.
- **Code:** `validation/sharpe_test.py`, with 5 unit tests:
  - zero difference for identical series;
  - the HAC se matches the exact i.i.d.-normal formula within 8%;
  - the null is rejected 2–9% of the time at 5%;
  - at most 11% under GARCH clustering with t(5) shocks;
  - the bootstrap is reproducible.

## Results

| Comparison | Days | Correlation | Sharpe: ours / policy | Difference (se) | p (HAC) | p (bootstrap, b = 5 / 21 / 63) |
|---|---|---|---|---|---|---|
| Walk-forward 2009–26 (R126 rule → O6) | 4,476 | 0.91 | 0.89 / 0.75 | +0.14 (0.09) | **0.15** | 0.15 / 0.15 / 0.16 |
| 2015–19 (D26 weights from data ≤ 2014) | 1,258 | 0.95 | 1.08 / 0.89 | +0.19 (0.15) | **0.21** | 0.22 / 0.21 / 0.23 |
| 2020–26 (same weights) | 1,708 | 0.96 | 0.30 / 0.49 | −0.19 (0.11) | **0.10** | 0.10 / 0.11 / 0.13 |
| Full sample 2004–26 (O6, in-sample) | 5,512 | 0.96 | 0.62 / 0.59 | +0.02 (0.06) | **0.67** | 0.67 / 0.67 / 0.68 |

**No difference is significant at 5%**, in either direction, with any method or block length. The two portfolios hold the same ETFs and their daily returns correlate at 0.91–0.96. At that correlation, a Sharpe gap of about 0.2 needs far more than 6–18 years of data to be distinguished from noise.

## What this changes
- **Claims:** we no longer imply better risk-adjusted performance. The memo, tear sheet and report now say that the Sharpe difference is not significant and that our consistent edge is the smaller worst fall. Walk-forward: −16.4% vs −19.2%. Full history: −23.5%, within the 25% D7 limit, vs −25.3% for the benchmark, which breaches it.
- **Underperformance in 2020–26** (Sharpe 0.30 vs 0.49) is not significant either (p 0.10). It is still shown openly in the tear sheet.
- **Not changed:** O6, D24 at 2.65%, the D7 limits and the D34 verdict. The mandate asks for the highest return within the loss limits, not for beating the benchmark (§2 of the report), and the benchmark breaches the 25% limit.

## Limitations
- Sharpe ratio only. The drawdown advantage was not tested for significance, because maximum drawdown is a single path statistic with no standard test. It is supported by the walk-forward, the 2008 replay and the D7 5-year probability.
- The walk-forward rule was chosen in 2026 after the earlier years had been seen, as already disclosed in T20.07.
- Multiple testing (raised in a second QA review): more than 20 portfolio variants were compared, so the best observed Sharpe is biased upward. A deflated Sharpe ratio (Bailey and López de Prado, 2014) corrects for the number of trials, but it can only lower significance. No difference is significant even before that correction, so no claim changes and the DSR was not computed. O6 was selected by the D26 rule, not by Sharpe.
