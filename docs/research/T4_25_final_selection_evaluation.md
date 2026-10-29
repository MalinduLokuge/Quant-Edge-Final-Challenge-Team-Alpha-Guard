# T4.25 / T20 Final portfolio selection: evaluation of O1–O6 (corrected 2026-10-29) [E]

**Status: O6 APPROVED as the final portfolio** (team, 2026-10-30, D31 v2), together with D32 (126-day test), D30 revised to about 2.65% spending, and D33 (precedence when rules conflict). Walk-forward validation is in §6. D6 is unchanged. The tables below were computed at 2.8% spending; the pipeline now uses 2.65%.

**Reproduce:**

```
python run_all.py --only portfolio
python scripts/research_t425_options.py
python scripts/research_t425_evaluation.py
```

Outputs: `research_t425_options.csv`, `research_t425_option_weights*.csv`, `research_t425_eval_*.csv` (including `_o6.csv`, `_train_blocks.csv`, `_sustainability_*.csv`), and `limit_stability.csv`.

## 0. Corrections to the first version (audit at the team's request)

| # | Error in v1 | Effect | Fix |
|---|---|---|---|
| 1 | The 5-year drawdown test used 4,000 paths with one seed. The D26 bisection stopped at exactly P = 5.00% *on that seed* | O1 and O4 "passed" while the true value was 5.06–5.29%; O3 "failed" on 2014 inputs at 5.15% while the true value was 4.98% | 32,000 paths in batches (s.e. ±0.12 pp), common random numbers, unit test; D26 re-selected |
| 2 | D30 (spending about 2.8%) was not in the code | Hurdle still 7.19%; stress-test spending at 4% | `mandate.spending_rate.base = 0.028` → hurdle **5.95%**; stress and recovery tests use 2.8% |
| 3 | Arbitrary thresholds: "margin = 3 MC s.e." and "spending within 0.1 pp" | Conditions not evidence-based | Replaced by a data-driven test of model uncertainty (block length, §2) |
| 4 | O2 under the ×1.5 equity shock reported as "at the limit" | It was 25.03% (breach) | Values recomputed; see table |
| 5 | Block length of the 5-year test never examined | Hidden model uncertainty | Sensitivity at 21 / 63 / 126 / 252 days and the Politis–White optimal block (§2) |

**D31 (O2) is withdrawn.** All numbers below are from the corrected pipeline.

## 1. Candidates (same rules, assumptions and data for all)
**Inputs and assumptions:**
- CMA full: rf 4.10%, ERP 5%, AGG = its yield (D25; AGG's yield stays locked in when rates fall, as in the approved D12 code).
- Quarterly rebalancing; 10 bp trading costs.
- D24 spending at 2.8% (D30); costs 0.2%; inflation 2.35% (10y breakeven).

**Options:**
- **O1:** D26 + D27, re-selected with the corrected test.
- **O2:** D26 with P ≤ 4%.
- **O3:** 50/50 D26 + Risk Parity.
- **O4:** D26 + gold floor 5%.
- **O5:** Risk Parity.
- **O6 (new):** D26 with the 5-year test run at the data-driven block length (126 days, §2).

| | O1 | O2 | O3 | O4 | O5 | **O6** |
|---|---|---|---|---|---|---|
| Weights | AGG 58.5, SPY 19.4, XLK 10.0, EFA 8.8, XLE 3.1, GLD 0.2 | AGG 60.6, SPY 18.6, XLK 10.0, EFA 7.4, XLE 3.0 | AGG 56.7, SPY 13.5, XLK 8.5, EFA 7.7, GLD 6.6, XLE 4.4, EEM 2.6 | AGG 53.7, SPY 19.3, XLK 10.0, EFA 8.9, GLD 5.0, XLE 3.0 | AGG 54.8, GLD 13.1, SPY 7.6, XLK 6.9, EFA 6.7, XLE 5.7, EEM 5.3 | **AGG 61.0, SPY 18.4, XLK 10.0, EFA 7.2, XLE 3.0** |
| **A. Return and spending** | | | | | | |
| Expected return (base) | 5.89% | 5.81% | 5.73% | 5.90% | 5.54% | 5.80% |
| Spending supported (required 5.95% at 2.8%) | 2.74% | 2.67% | 2.58% | 2.75% | 2.40% | 2.65% |
| Expected return, rf 2.5% | 5.23% | 5.18% | 5.03% | 5.16% | 4.81% | ≈ O2 |
| **B. Risk** (limit) | | | | | | |
| Volatility | 8.4% | 8.1% | 8.0% | 8.5% | 7.9% | 8.0% |
| ES99 / VaR99, 1-day (2.5% / 1.7%) | 2.22 / 1.48% | 2.12 / 1.40% | 2.05 / 1.36% | 2.21 / 1.51% | 1.97 / 1.33% | 2.10 / 1.38% |
| Max drawdown incl. GFC (25%) | 24.4% | 23.6% | 23.5% | 24.3% | 23.2% | 23.5% |
| **P(DD > 25%, 5y), 63-day blocks (approved, 5%)** | 4.86% ✓ | 3.88% ✓ | 3.55% ✓ | 4.88% ✓ | 3.23% ✓ | 3.74% ✓ |
| P, 126-day blocks (data-driven, §2) | **6.49% ✗** | 5.18% ✗ | 4.84% ✓ | **6.73% ✗** | 4.47% ✓ | **4.97% ✓** |
| P, 252-day blocks | 6.33% | 5.05% | 4.57% | 6.94% | 4.14% | 4.83% |
| Same test on 2014 inputs, 63 / 126 days | 4.86 / 6.21% | 3.93 / 5.04% | 4.98 / 6.24% | 4.94 / 6.28% | 5.59 / 7.26% | **3.80 / 4.86%** |
| GFC recovery (trading days after trough) | 277 | 257 | 230 | 225 | 191 | 254 |
| SPY + XLK share of ES99 / effective risk contributors | 60% / 3.8 | 61% / 3.9 | 48% / 5.3 | 60% / 3.9 | 31% / 6.8 | 62% / 3.9 |
| **D. Stress losses** (limit 25%) | | | | | | |
| COVID / 2022 | 16.9 / 18.0% | 16.3 / 17.8% | 16.1 / 16.5% | 16.9 / 17.8% | 15.4 / 15.3% | 16.2 / 17.8% |
| A stagflation severe / × 1.5 equity | 19.4 / **25.6%** | 18.9 / 24.9% | 18.0 / 23.0% | 19.2 / **25.1%** | 16.7 / 20.3% | 18.9 / 24.8% |
| B recession severe / × 1.5 equity | 15.4 / 23.7% | 14.4 / 22.3% | 12.7 / 19.3% | 14.8 / 22.7% | 10.0 / 14.9% | 14.2 / 22.1% |
| **E. Out of sample (2014-built weights)** | | | | | | |
| 2015–19 return / Sharpe | 5.7% / 1.04 | 5.7% / 1.08 | 5.5% / 0.99 | 6.0% / 1.08 | 5.2% / 0.91 | 5.7% / 1.08 |
| 2020–26 return / Sharpe | 5.3% / 0.32 | 5.1% / 0.31 | 6.2% / 0.43 | 6.3% / 0.43 | 7.1% / 0.53 | 5.0% / 0.30 |
| 2015–26 vs O1 a year (block-bootstrap 95% CI) | — | −0.14% (ns) | +0.40% (ns) | +0.70% (sig.) | +0.81% (ns) | −0.16% |
| D7 limits held in 2015–19 and 2020–26 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Turnover / cost a year | 7.1% / 0.01% | 7.0% / 0.01% | 7.5% / 0.02% | 7.4% / 0.01% | 7.8% / 0.02% | 7.0% / 0.01% |
| **G. Sustainability and recovery (T20.09)** | | | | | | |
| Bootstrap 10 years: median real value | 1.076 | 1.067 | 1.056 | 1.077 | 1.035 | 1.066 |
| P(real value < 90% after 10 years) | 23.0% | 23.4% | 24.2% | 22.9% | 26.9% | 23.4% |
| P(real spending ever cut > 10%) | 25.4% | 25.2% | 26.0% | 25.5% | 28.2% | 25.2% |
| P(DD ≥ 25% within 10 years) / median years to recover | 10.7% / 3.0 | 8.6% / 3.0 | 7.9% / 3.0 | 10.6% / 2.9 | 7.4% / 3.0 | 8.3% / 3.0 |
| Real value after 10 years: no crisis / 25% fall, 3-year recovery | 1.056 / 0.817 | 1.047 / 0.814 | 1.038 / 0.809 | 1.057 / 0.818 | 1.018 / 0.800 | 1.046 / 0.813 |
| SPY −25%, 3-year recovery: year-1 loss (stagflation) / real value year 10 (stagflation, recession) | −13.3% / 0.930, 0.943 | −12.9% / 0.927, 0.941 | −11.7% / 0.938, 0.951 | −13.0% / 0.936, 0.949 | −10.1% / 0.943, 0.955 | — / 0.927, 0.940 |

Policy 40/50/10 for reference: real value after 10 years 1.045 with no crisis; bootstrap median 1.065.

## 2. Key evidence

**How long do bad periods persist?** This sets the bootstrap block length.
- The Politis–White optimal block length (arch `optimal_block_length`) on each option's daily returns is only 5–14 days for returns themselves, but **120–160 days for their absolute and squared values**: volatility clustering.
- Drawdowns are driven by runs of turbulent days, so the dependence that matters for a 5-year drawdown test lasts about half a year. The approved 63-day blocks cut these runs in half and understate drawdown risk.
- At 126 days, P rises by 1.1–1.9 pp for every option.
- **This is evidence, not a chosen margin.** It is a reason to run the D7 test at about 126 days (a D7 *method* change, which the team must approve).

**Does O4's gold floor help?** No.
- **Return:** +0.01 pp of expected return. Below O1 at rf 2.5% (5.16% vs 5.23%).
- **Risk:** the worst P under long blocks (6.9% at 252 days); still breaches under the ×1.5 equity shock; equity concentration unchanged (SPY + XLK 60% of ES).
- **Track record:** its significant 2015–26 edge (+0.70% a year) comes from GLD (+8.3 pp) and extra SPY (+4.4 pp) in 2020–26, when gold returned +25% (2020), +27% (2024) and +64% (2025). That cycle was seen before the gold floor was proposed, so the edge is not independent evidence.
- **Recovery and sustainability results:** the same as O1 (median real value 1.077 vs 1.076).

**Recovery and sustainability (T20.09).**
1. **Spending policy matters more than the option.** At 2.8% spending, expected real growth is only about 0.5% a year. A 15–25% fall followed by a 3-year recovery leaves real value about 0.81–0.82 after 10 years for *every* option, against 1.04–1.06 with no crisis.
   - Recovery speed matters more than the depth of the fall: in view 1 the depth barely changes the outcome once the level is regained.
   - The D24 smoothing limits the real spending cut, about 19% at the 10-year low in that case.
2. **Options differ by 1–3 pp of real value**, inside the uncertainty. O5 is weakest (lowest return); O1 and O4 lead with no crisis or a portfolio-level crisis; O3 and O5 lead when the *stock market* crashes (smaller year-1 losses).
3. **About 1 in 4 bootstrap paths cut real spending by more than 10%** at some point over 10 years, and about 1 in 4 end below 90% of real value. This is the same for all options and is mainly a consequence of 2.8% spending with about 0.5% real growth.
4. **Recovery from a 25% drawdown:** median about 3 years, p90 about 5.1–5.3 years. That matches the D4 5-year horizon.

**Why O3 and O5 fail on 2014 inputs.**
- **The approved 63-day test** passes O3 narrowly (4.98% ± 0.12%; v1 said fail). O5 fails (5.59%).
- **At 126 days** O3 (6.24%) and O5 (7.26%) both fail.
- **Cause:** Risk Parity's construction does not include the probabilistic test. With near-zero 2014 rates, CAPM gave gold about 0.6% expected return, so a large gold weight lowers drift and raises simulated drawdown risk.
- **Not weight instability:** O5 has the most stable weights, with only a 6% shift between 2014 and 2026.

## 3. Approval conditions (anchored to approved items; nothing invented)

| # | Condition | Basis | O1 | O2 | O3 | O4 | O5 | O6 |
|---|---|---|---|---|---|---|---|---|
| M1 | D6 + D7 + D27 on 2026 inputs, approved test (63 days, 32k paths) | D6, D7, D27 | ✅ | ✅ | ✅ | ✅ (needs D6 change) | ✅ | ✅ |
| M2 | Same on 2014 inputs | D5 rule consistency | ✅ | ✅ | ✅ (4.98%) | ✅ | ❌ | ✅ |
| M3 | 5-year test at the data-driven block length, 2026 and 2014 inputs | D7 + Politis–White (§2) | ❌ | ❌ (5.18 / 5.04%) | ❌ (2014) | ❌ | ❌ (2014) | ✅ |
| M4 | D7 limits held out of sample | T10.12 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| M5 | Spending under D30 (about 2.8%, required 5.95%) | D30 | 2.74% (closest) | 2.67% | 2.58% | 2.75% | 2.40% | 2.65% |
| M6 | A D6 change only with a robust benefit | D6 | n/a | n/a | n/a | ❌ | n/a | n/a |
| M7 | Walk-forward validation of the selection rule | Selection-bias precaution | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ |
| D1 | Severe stress with ×1.5 equity ≤ 25% | D9 v2 robustness (approved method) | ❌ | ✅ | ✅ | ❌ | ✅ | ✅ |
| D2 | Recovery within the D4 5-year horizon (p90, 25% drawdown) | D4 | ✅ (5.2y ≈) | ✅ | ✅ | ✅ | ✅ | ✅ |
| D3 | Diversification: SPY + XLK < 50% of ES | D27 intent | ❌ | ❌ | ✅ | ❌ | ✅ | ❌ |

- **M3 depends on the team accepting the 126-day test.** It is a proposed D7 method change, not yet approved.
- **M5:** no D7-compliant option reaches 2.8%. The D30 text needs the figure the chosen option supports.

## 4. Recommendation: **B, conditional approval of O6**
**Why O6:**
- It is the only option that passes the drawdown test on both input sets, at the approved *and* the data-driven block length.
- It survives the ×1.5 equity shock in both scenarios (24.8% and 22.1%).
- It keeps D6 unchanged and is produced by the same D26 rule, not a hand-picked blend.
- That fits the committee's principle that avoiding large losses matters more than maximising gains.

**Main weaknesses:**
- Spending 2.65% vs 2.74% for O1, about $9k a year less, and 0.15 pp below D30's 2.8%.
- About 0.16% a year lower out-of-sample return than O1 in 2015–26.
- Still equity-concentrated (SPY + XLK 62% of ES, within D27).

**Why the others are less suitable:**
- **O1:** highest compliant spending under the *approved* test, but fails it at the data-driven block length (6.5% on 2026 inputs, 6.2% on 2014) and breaches under ×1.5 equity. It remains the fallback if the team keeps the 63-day test.
- **O2:** almost identical to O6 but narrowly fails at 126 days. O6 is O2 with an evidence-based instead of arbitrary margin.
- **O3:** best diversification and lower stress losses, but fails on 2014 inputs at 126 days. Its 50% blend weight is ad hoc, and spending is 2.58%.
- **O4:** no meaningful advantage (§2); would require a D6 change. **Not recommended.**
- **O5:** fails on 2014 inputs at both block lengths; spending only 2.40%.

**Confidence: moderate.**
- High confidence that O4 adds nothing and O5 is unsuitable.
- The choice between O6 and O1 depends on one decision the team must make: run the D7 5-year test at the data-driven block length (126 days) or keep 63 days.

**Before final approval:**
1. **Team decision on the D7 test block length.** Proposed: 126 days, with the evidence in §2.
2. **Walk-forward validation (T20.07)** of the chosen rule at several past origins.
3. **D30 wording:** spending about 2.65% (O6) or 2.75% (O1).
4. **D23 rolling-ES trigger recalibration** (T20.08, desirable).

**Consequences of a 5% GLD minimum in D6 (O4):** it binds the optimiser to hold gold at about 4% expected return (≈ rf). Expected return is flat now and lower if rates fall. Drawdown probability under long blocks gets worse, and the decision would rest on one gold cycle already observed. Not justified.

## 5. Validation precaution (selection bias)
- **2015–2026 has been examined while comparing options.** It is reported as "examined during selection", never as an untouched test.
- **O6 is defined by a statistical criterion** (the Politis–White block length), not by its 2015–26 performance. Its out-of-sample numbers were computed after the rule was fixed, but O2 (very similar) had already been seen.
- **Defensible next step:** walk-forward evaluation of the *rule*. At origins such as 2009, 2012, 2015, 2018 and 2021, use CMA as of each origin, select, and hold to the next origin. Report D7 compliance and returns across all segments.
- **Live monitoring** (D23 triggers, the GARCH-EVT backtest) is the only truly untouched test.

## 6. Walk-forward validation of the selection rule (T20.07, condition M7)
**Reproduce:** `python scripts/research_walkforward.py` → `research_walkforward_{weights,segments,summary}.csv`.

**Method:**
- At each year-end origin (2008, 2011, 2014, 2017, 2020, 2023), the D26 rule is re-run with **only data up to that date**: CMA as of the origin, that day's breakeven for the hurdle, D6 + D7 + D27, 32k-path 5-year test.
- The weights are then held (quarterly rebalancing) until the next origin.
- Rules compared: **R126** (D32 → O6) and **R63** (old test → O1), plus the policy benchmark.

| Origin → next 3 years | R126 (O6 rule): return / max DD / ES99 | R63 (O1 rule) | Policy 40/50/10 |
|---|---|---|---|
| 2008 → 2011 | 8.8% / −7.4% / 1.1% | same (min-variance fallback) | 10.6% / −12.4% / 1.9% |
| 2011 → 2014 | 5.7% / −4.2% / 0.7% | same (min-variance fallback) | 6.7% / −6.0% / 1.2% |
| 2014 → 2017 | 5.0% / −4.6% / 0.9% | 5.2% / −5.0% / 0.9% | 5.6% / −7.6% / 1.2% |
| 2017 → 2020 | 9.4% / −14.8% / **2.9%** | 9.5% / −15.3% / **3.0%** | 8.8% / −16.0% / **3.1%** |
| 2020 → 2023 | 2.9% / −16.4% / 1.7% | 2.8% / −16.4% / 1.7% | 1.3% / −19.2% / 1.7% |
| 2023 → Oct 2026 | 12.9% / −6.4% / 1.8% | 13.7% / −6.8% / 1.9% | 11.5% / −6.4% / 1.7% |
| **Chained 2009 → 2026** | **7.3% a year, Sharpe 0.89, max DD −16.4%, ES99 1.7%** | 7.5%, 0.88, −16.4%, 1.8% | 7.3%, 0.75, −19.2%, 1.9% |

**Findings:**
1. **The drawdown limit held in every out-of-sample segment** for both rules (worst −16.4%, 2022).
   - The 1-day ES99 limit was exceeded only in the 2017→2020 segment, which contains COVID. It was exceeded by every portfolio, the benchmark included.
   - ES99 is a full-cycle limit (D7). A 3-year window around COVID is not a full cycle; D23 treats such a breach as a review trigger.
2. **The rule matched the policy benchmark's return** (7.3% a year) with lower volatility (6.7% vs 8.0%), a higher Sharpe ratio (0.89 vs 0.75) and a shallower worst drawdown (−16.4% vs −19.2%). That fits the conservative mandate.
3. **The D32 test (R126) costs about 0.2% a year** against R63 over 2009–2026, with the same worst drawdown. The difference is small and within noise; the robustness gain is in the tail-risk test, not in realised history.
4. **Interaction found:** at the 2008 and 2011 origins the D27 cap (≤ 40% of ES per ETF) could not be met together with D7. With the 2008 crash in the sample, AGG carried about 62% of the low-risk portfolio's ES, and adding equity to dilute it would breach the 25% drawdown. The rule fell back to capped minimum variance, which was a safe outcome.
   - **Recommendation:** add an explicit precedence rule, "if D27 and D7 conflict, D7 wins and D27 is reported", to D27's text. This would be a documentation change, not a new parameter.
5. **Limits of the evidence:** six segments, and the rule was chosen in 2026 after the 2015–2026 data had been examined. The rule's pass record from 2009–2014 (pre-split data) is the least biased part.

**Condition M7: met**, with notes 1 and 4.
