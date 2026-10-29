# T4.25 / T20 Final portfolio selection: evaluation of O1–O5 [E]

**Status:** evidence and recommendation for the team's decision. No portfolio is approved, D6 is unchanged and the memo is not final.

**Reproduce:**

```
python scripts/research_t425_options.py
python scripts/research_t425_evaluation.py
```

These write `research_t425_options.csv`, `research_t425_option_weights.csv` and `research_t425_eval_*.csv`. `limit_stability.csv` comes from the validation stage.

**Same assumptions for every option:**
- CMA "full" set: rf 4.10%, ERP 5%, AGG = its yield (D25).
- Quarterly rebalancing (D11); 10 bp trading cost.
- D7 and D27 checks; the D9 v2 / D29 stress scenarios.
- **In-sample KPIs** use 2026 weights; **out-of-sample KPIs** use 2014-built weights.

| Option | Weights (2026 inputs) |
|---|---|
| O1 D26 + D27 (current) | AGG 58.1, SPY 19.6, XLK 10.0, EFA 9.0, XLE 3.1 |
| O2 D26 with 5-year test margin (P ≤ 4%) | AGG 60.2, SPY 18.8, XLK 10.0, EFA 7.7, XLE 3.0 |
| O3 50/50 D26 + Risk Parity | AGG 56.4, SPY 13.6, XLK 8.5, EFA 7.8, GLD 6.6, XLE 4.4, EEM 2.6 |
| O4 D26 + gold floor 5% | AGG 52.9, SPY 19.7, XLK 10.0, EFA 9.4, GLD 5.0, XLE 3.1 |
| O5 Risk Parity | AGG 54.8, GLD 13.1, SPY 7.6, EFA 6.7, XLK 6.9, XLE 5.7, EEM 5.3 |

## 1. Comparison table

| | O1 | O2 | O3 | O4 | O5 |
|---|---|---|---|---|---|
| **A. Return and spending** | | | | | |
| Expected return (base) | 5.91% | 5.83% | 5.74% | 5.93% | 5.54% |
| Expected return, ERP 3% | 5.05% | 5.02% | 4.96% | 5.06% | 4.85% |
| Expected return, rf 2.5% | **5.24%** | 5.19% | 5.04% | 5.18% | 4.81% |
| Spending supported (base) | 2.76% | 2.68% | 2.59% | **2.78%** | 2.40% |
| Spending supported, rf 2.5% + ERP 4% | **1.69%** | 1.67% | 1.54% | 1.62% | 1.36% |
| Real NAV drift a year at 2.8% spending | +0.46% | +0.38% | +0.29% | +0.48% | +0.11% |
| Withholding drag (30% on equity ETFs) | 0.18% | 0.16% | 0.17% | 0.18% | 0.16% |
| **B. Risk and safety margins** (limit) | | | | | |
| Volatility | 8.5% | 8.1% | 8.0% | 8.6% | 7.9% |
| ES99 1-day (2.5%) | 2.24% | 2.14% | 2.06% | 2.25% | 1.97% |
| VaR99 1-day (1.7%) | 1.50% | 1.41% | 1.37% | **1.53%** | 1.33% |
| Max drawdown (25%) | 24.5% | 23.8% | 23.5% | **24.7%** | 23.2% |
| P(DD > 25% in 5 years) (5%) ± MC s.e. | 5.0 ± 0.34% | **4.0 ± 0.31%** | 3.7% | 5.0 ± 0.34% | 3.2% |
| GFC recovery (trading days after trough) | 277 | 272 | 230 | 228 | 191 |
| Largest ES share (D27 ≤ 40%) | SPY 40% | SPY 40% | SPY 30% | SPY 40% | XLE 17% |
| SPY + XLK share of ES | 60% | 61% | 48% | 60% | 31% |
| Effective risk contributors | 3.8 | 3.9 | 5.3 | 3.9 | 6.8 |
| **D. Stress losses** | | | | | |
| GFC / COVID / 2022 | 24.5 / 17.0 / 18.0 | 23.8 / 16.4 / 17.8 | 23.5 / 16.2 / 16.5 | 24.7 / 17.1 / 17.8 | 23.2 / 15.4 / 15.3 |
| A stagflation severe (stress betas) | 19.4 (18.0) | 19.0 (17.6) | 18.1 (16.8) | 19.4 (18.3) | 16.7 (15.6) |
| B AI unwind / recession, severe | 15.5 | 14.6 | 12.8 | 15.1 | 10.0 |
| A severe with SPY × 1.5 (limit 25%) | **25.7 ✗** | 25.0 | 23.0 | **25.4 ✗** | 20.3 |
| **E. KPIs, out of sample (2014-built weights)** | | | | | |
| 2015–19 return / Sharpe / IR vs policy | 5.7% / 1.04 / −0.13 | 5.7% / 1.07 / −0.15 | 5.5% / 0.99 / −0.32 | 6.0% / 1.09 / +0.04 | 5.2% / 0.91 / −0.43 |
| 2020–26 return / Sharpe / max DD | 5.3% / 0.32 / −19.8% | 5.1% / 0.30 / −19.6% | 6.2% / 0.43 / −17.8% | 6.3% / 0.43 / −19.5% | 7.1% / 0.53 / −16.0% |
| D7 limits held in 2015–19 and 2020–26 | ✅ | ✅ | ✅ | ✅ | ✅ |
| Turnover / cost a year | 7.1% / 0.01% | 7.0% / 0.01% | 7.5% / 0.02% | 7.4% / 0.01% | 7.8% / 0.02% |
| **F. Reliability** | | | | | |
| Passes the same rules on 2014 inputs | ✅ | ✅ | ❌ (P 5.15%) | ✅ | ❌ (P 5.9%) |
| Weight shift, 2014 → 2026 inputs (one-way) | 15% | 14% | 10% | 14% | 6% |

Benchmarks for reference:
- **Policy 40/50/10:** 2015–19 return 5.9%; 2020–26 return 7.2%, Sharpe 0.49; GFC drawdown 25.3% (outside the 25% limit).
- **60/40 SPY/AGG:** full-sample max drawdown 35%. It is not D7-compliant.

## 2. Does O4's gold floor give a meaningful benefit?
**Short answer: not on reliable evidence.**

1. **The expected-return edge is noise and depends on assumptions.**
   - The gain is +0.02 pp ($2k a year of spending).
   - At rf 2.5% the edge *reverses*: O4 5.18% vs O1 5.24%. With rf 2.5% and ERP 4%, O4 supports less spending (1.62% vs 1.69%).
   - The reason: gold has near-zero beta, so its CAPM return is about the T-bill rate. Gold only adds expected return while T-bills pay 4%.
2. **Risk is slightly worse, not better.**
   - Drawdown is 24.7% vs 24.5%, leaving a 0.28 pp margin.
   - VaR99 margin is 0.17 pp vs 0.20 pp.
   - ES99 and the 5-year test are the same.
   - The equity concentration that drives tail risk is unchanged (SPY + XLK = 60% of ES), because the gold comes out of AGG, not equities.
3. **Stress benefit is marginal and inconsistent.**
   - **Better:** 2022 by 0.2 pp, B severe by 0.4 pp, GFC recovery 49 days faster.
   - **Worse:** GFC by 0.2 pp, COVID by 0.1 pp, A severe under stress betas by 0.3 pp.
   - **Weak evidence for hedging:** the factor model is least reliable for GLD (back-cast error 8 pp). Gold *fell* 11% in the March 2026 oil shock.
4. **The out-of-sample advantage is real in the data but not a reliable guide.**
   - O4 beat O1 by 0.68% a year over 2015–26 (block-bootstrap 95% CI 0.31–1.05%) and by 0.97% a year in 2020–26.
   - **Not significant in 2015–19** (+0.28%, CI −0.18 to +0.70).
   - **Where the 2020–26 gap came from:** GLD +8.3 pp and SPY +4.4 pp (the 2014-built O4 held more SPY: 10.7% vs 8%). Gold returned +25% in 2020, +27% in 2024 and **+64% in 2025**.
   - **Selection bias:** the gold floor was proposed *after* seeing stress and 2015–26 results.

   So this edge is one exceptional gold cycle that we already knew about, not independent evidence.

**Conclusion:** O4 offers no meaningful advantage over O1. Changing D6 to require 5% gold is not justified by this evidence.

## 3. Other findings
- **Why O3 and O5 fail on 2014 inputs:**
  - **Not a stability problem.** Risk Parity weights are the most stable (6% shift), and both pass every historical limit.
  - **What fails:** the probabilistic 5-year test (5.9% and 5.15%).
  - **Cause:**
    1. Risk Parity's construction does not include that test; only historical D7 is enforced by projection.
    2. With near-zero 2014 rates, CAPM gave gold a 0.6% expected return. A 12% high-volatility, low-mean holding raises simulated drawdown risk.
  - **Read:** a rule failure, not bad luck. O5's spending (2.40%) is also well below D30.
- **O1 and O4 sit exactly on the 5-year test boundary.** D26 picks the highest compliant target, so P(DD) = 5.00% ± 0.34%: about a 50% chance the true value is above the limit. The original D26 approval note recommended option (b) *with a safety margin*. The current rule has none.
- **Justified margin.** A margin equal to about 3 Monte Carlo standard errors (3 × 0.34% ≈ 1 pp) puts the limit at P ≤ 4%. This is O2.
  - **What it buys:** drawdown margin 0.5 → 1.2 pp, ES margin 0.26 → 0.36 pp, and the ×1.5 equity shock drops from 25.7% (breach) to 25.0% (at the limit).
  - **What it costs:** 0.08 pp of expected return, about $8k a year of spending (2.76% → 2.68%), and 0.19% a year out of sample in 2020–26 (significant).
- **No option is dominated on every measure.**
  - O1 vs O4: O4 is not better on risk and is no better on robust return.
  - O2 vs O1: O2 trades return for margin.
  - O3 and O5: lowest risk and stress losses, but they fail the rule on 2014 inputs and miss D30 spending.
- **D30 target:** no D7-compliant option reaches 2.8–2.9% in the base case (the maximum is about 2.78%). The D30 target should read "about 2.7–2.8%".
- **Costs and taxes** are immaterial and equal across options (rebalancing under 0.02% a year; withholding 0.16–0.18%).

## 4. Approval conditions

| # | Condition | Type | Measure / threshold (basis) | O1 | O2 | O3 | O4 | O5 |
|---|---|---|---|---|---|---|---|---|
| M1 | D6 + D7 + D27 on 2026 inputs | Mandatory | All limits (approved) | ✅ | ✅ | ✅ | ✅ (needs D6 change) | ✅ |
| M2 | Same rules pass on 2014 inputs | Mandatory | Rule consistency (D5) | ✅ | ✅ | ❌ | ✅ | ❌ |
| M3 | Statistical margin on the 5-year test | Mandatory | P ≤ 5% − 3 MC s.e. ≈ 4% | ❌ | ✅ | ✅ | ❌ | ✅ |
| M4 | D7 limits held out of sample | Mandatory | T10.12, 2015–19 and 2020–26 | ✅ | ✅ | ✅ | ✅ | ✅ |
| M5 | Spending under D30 | Mandatory | Within 0.1 pp of the highest compliant (2.78%) | ✅ | ✅ (−0.10) | ❌ | ✅ | ❌ |
| M6 | Credible expected-return edge | Mandatory for any D6 change | Edge holds across rf / ERP grid | n/a | n/a | n/a | ❌ (reverses at rf 2.5%) | n/a |
| M7 | Walk-forward validation of the selection rule | Mandatory | Rule re-run at several past dates; D7 kept next period | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ |
| D1 | Severe stress with ×1.5 equity shock ≤ 25% | Desirable | Robustness | ❌ 25.7 | ≈ 25.0 | ✅ | ❌ 25.4 | ✅ |
| D2 | Lower equity concentration (SPY + XLK < 50% of ES) | Desirable | D27 intent | ❌ | ❌ | ✅ | ❌ | ✅ |
| D3 | Rolling-ES "watch" trigger recalibrated (fires 26% of days today) | Desirable | D23 practicality | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ |
| D4 | Costs immaterial | Desirable | < 0.05% a year | ✅ | ✅ | ✅ | ✅ | ✅ |

On M5: the D30 target of 2.8–2.9% is not reachable by any compliant option, so the threshold is relative to the best compliant portfolio.

## 5. Recommendation: **B, conditional approval of O2**
- **Strongest candidate: O2.**
  - It is the only option that passes every mandatory condition with evidence today (M7 pending for all).
  - It is the D26 rule with a *statistically justified* margin on the 5-year test, consistent with the committee's belief "avoiding large losses is more important than maximizing gains" and with the original D26 approval note.
  - **Main weakness:** spending 2.68% vs 2.76% for O1 (about $8k a year less), and a slightly lower out-of-sample return.
- **O1** is the fallback if the committee prefers the extra $8k a year over the margin. It operates *on* the 5-year limit (50% chance the true value is above it).
- **O4 is not recommended.** Do not change D6. Its edge is noise in expectations and one gold cycle in hindsight, with thinner margins.
- **O3 and O5 are not recommended** as the final portfolio: they fail the rule on 2014 inputs and miss D30. Their lower stress losses are worth noting in the memo as the "more defensive" end of the trade-off.

**Confidence: moderate.**
- The O4 rejection is well supported.
- The O2 vs O1 choice is a value judgement: about $8k a year against limit headroom. The team must make it.

**Conditions before final approval:**
1. **M7 walk-forward validation:** re-run the D26 rule (O1 and O2 variants) at several origins with only past data, using `cma.estimate_as_of`. Check each portfolio over the following period. This replaces the single 2015–26 look, which is no longer untouched.
2. **D30 wording:** confirm spending "about 2.7%" (O2) or "about 2.75%" (O1).
3. **Recalibrate the D23 rolling-ES watch trigger** (desirable).

## 6. Validation precaution (selection bias)
2015–2026 has now been used to compare options, so it is **not** a clean final test for the chosen one. Defensible procedure:
- **(a)** Freeze the selection rule *before* new evidence: D26 with the P ≤ 4% margin (if O2), with no hand-picked constraints.
- **(b)** Walk-forward rolling-origin evaluation of the *rule*, not the chosen weights. At origins such as 2009, 2012, 2015, 2018 and 2021, use CMA as of each origin, select, and hold to the next origin. Report D7 compliance and returns across all segments. This tests the procedure rather than one outcome.
- **(c)** Report 2015–26 results as "examined during selection", never as "untouched test".
- **(d)** The only truly untouched test is live monitoring after adoption: D23 triggers plus the GARCH-EVT backtest (D28) going forward.
