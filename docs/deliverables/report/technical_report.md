# QuantEdge 1.0: Technical Report
## A conservative, tail-aware portfolio for the Serendib University Endowment Fund (USD 10 million)

> **DRAFT for team review (2026-10-30).** Prepared from the pipeline outputs with AI assistance (see §11). The team must review, edit and take ownership of every judgement before submission (brief §8.7). Target length is 7–15 pages; tables and figures come from `outputs/`, and each section names its source files. Decisions are cited as D1–D33 (`docs/DECISIONS.md`).

---

## 1. Executive summary
- **Recommendation:** invest the $10M in **AGG 61.1%, SPY 18.4%, XLK 10.0%, EFA 7.2%, XLE 3.0%, GLD 0.4%**, rebalance quarterly, and spend about **2.65% a year** (≈ $265k) through a smoothed rule. The portfolio is called O6 (D31 v2).
- **Return:** expected 5.80% a year nominal, about 3.4% real.
- **Downside:** worst historical drawdown 23.5% (limit 25%); P(drawdown > 25% within 5 years) 4.9% (limit 5%); worst stress loss 23.5% (2008 replay).
- **Model trust:** the daily VaR model (GARCH-EVT) was selected on 2015–19 data and, on 2020–26, passed Kupiec and Christoffersen at 99% and 95%; its worst Basel window was yellow (7 breaches), never red. Out of sample, weights built on data to 2014 kept every D7 limit in 2015–26, but the walk-forward segment containing COVID reached a 1-day ES99 of 2.9% against the 2.5% full-cycle limit, as every portfolio did (§4.5). The 2015–26 data were seen during selection (§10).
- **Why it is suitable:** it is the highest-expected-return mix we found that passes every risk limit derived from the committee's principle that "avoiding large losses is more important than maximizing gains". It was checked out of sample and by a walk-forward that rebuilds it every three years with only past data.
- **Evidence standard: observed is not proven.**
  - The rule matched the policy benchmark's return with a smaller worst fall.
  - Its higher Sharpe ratio is not statistically significant (Ledoit–Wolf p = 0.15), so we do not claim better risk-adjusted returns (§4.5).
  - The same standard led us to reject a regime-switching VaR model that looked plausible but failed the tests (D41, §6).
  - **Gold** (D43, §4.5): O6's 0.4% follows from CAPM's 4.6% for gold, and it is given no hedge credit. Raising gold's assumed return moves its weight up to the 20% cap. Even then, the 2022 and stagflation losses improve by under 1 pp, and the portfolio fails the D7 5-year test on our base assumptions. The gap is disclosed: O6 has no effective inflation hedge (§10).
- **The main trade-off is spending.** A 4% payout needs about 7.2% a year (given the team's 0.5% real-growth and 0.2% cost inputs, D12 / D30). No portfolio within the D6 weight limits reaches it at any risk level; without D6 it would need a 47% drawdown tolerance (the 6.66% minimum tier needs 35%; §4.4). We therefore recommend about 2.65% and state it openly. The brief sets no spending rate.

## 2. Client, horizon and return objective
- **Client:** a conservative endowment that values capital preservation, income and sustainable real growth, with resilience in stress (brief p.3). It is a long-term pool supporting scholarships, research, faculty and capital projects. The brief does not say it is the university's only income.
- **Horizon:** 5-year strategic horizon with annual review. Risk is measured on 1-day losses (backtestable) and on 5-year drawdown paths (D4, D17).
- **Return objective (D12, D30):** (1 + R) = (1 + inflation)(1 + spending)(1 + real growth)(1 + costs).
  - **Inputs:** inflation = 10-year breakeven 2.35% (FRED); real growth 0.5%; costs 0.2%.
  - **At 4% spending:** R = 7.19%. Our research shows this is infeasible within the risk limits (§4.4).
  - **Spending is flexible (D30).** At the sustainable rate of **2.65%**, R = **5.80%**, which equals O6's expected return.
- **Spending rule (D24):** next year's spending = 70% × last year's × (1 + inflation) + 30% × 2.65% × fund value. This smooths cuts after a crash.

## 3. Data sources and cleaning
**Sources** (`data/README.md`):
- **Prices:** Yahoo Finance adjusted closes for the 7 ETFs; distributions for the income check.
- **FRED:**
  - 3-month T-bill (risk-free rate); 10-year Treasury; 10-year and 5-year breakevens; CPI.
  - For the hypothetical stress: 10-year TIPS yield, Moody's Baa spread, Brent and WTI oil, broad USD index, VIX, 2-year yield.
- **Context only** (not model inputs): IMF, World Bank, IEA, EIA and Federal Reserve publications.

**Source compliance (brief §9.1: Yahoo Finance, FRED, World Bank / IMF).** Every series the models compute from is from Yahoo Finance or FRED. Three items fall outside the list. All are public and disclosed, and none is proprietary:

| Item | Used for | Source | Status |
|---|---|---|---|
| SPY technology share (38.4%) | D35 / D37 / D44 look-through: tech-crash stress and the 20% trigger | SSGA fund page, 29 Oct 2026 (EFA, EEM approximate) | Model input outside §9.1. Cross-check from Yahoo Finance (`yahoo_fund_sectors_*.csv`): SPY 40.4%, EFA 12.0%, EEM 44.2% (Morningstar sectors, broader than GICS IT), giving look-through 18.3% instead of 17.7%, still below the 20% trigger |
| IEA, EIA, Federal Reserve publications | Narrative and plausibility of the hypothetical scenarios (T11) | Public reports, dated and cited | Context only; shock sizes are team judgements calibrated on FRED / Yahoo history (T11 design doc) |
| NACUBO peer-endowment losses | Context for the 25% drawdown tolerance (D7) | NACUBO study | Context for a team judgement, not a model input |

Academic papers are cited as method references, not data.

**Sample:**
- **Common sample:** 2004-11-18 (GLD inception) to 2026-10-19 (D1): 5,513 trading days of prices, giving 5,512 daily returns (the split below counts returns).
- **Chronological split (D5):**
  - **Train:** to 2014-12-31 (2,546 days).
  - **Validation:** 2015–2019 (1,258 days).
  - **Test:** 2020-01-02 to 2026-10-19 (1,708 days), used once.

**Cleaning:**
- Adjusted closes, dates aligned to days when all 7 ETFs trade, and FRED values carried forward from past observations only (at most 5 business days).
- Log returns for statistics; simple returns for portfolio P&L (D17).
- Nothing is deleted. Data are flagged: 128 |z| > 5 observations and 53 quality flags (jumps, large negative days, e.g. AGG −6.8% on 2008-10-10).
- ADF tests reject a unit root in every ETF's returns (p < 10⁻²⁶).
- Returns are strongly non-normal: excess kurtosis 25 for O6; Jarque–Bera and Ljung–Box on squared returns reject normality and independence (volatility clustering). This motivates fat-tailed and conditional risk models (§5).

## 4. Portfolio construction
### 4.1 Capital market assumptions (D12, D25)
- **Equities and gold:** CAPM expected returns: risk-free 4.10% + β × 5% equity risk premium. The approved ERP is cross-checked against the data's own 9.7% (95% CI 3.5–15.8%).
- **Bonds:** AGG's expected return is its current yield (4.2%, D25).
- **Covariance:** daily, with Ledoit–Wolf shrinkage of correlations.
- **Variance drag:** expected compound return = arithmetic − ½ variance.

### 4.2 Constraints and limits
- **D6 weight limits:**
  - Equities 20–45%; gold up to 20%.
  - Each ETF at most 2× its benchmark weight.
  - XLE and XLK each at most 10%, together at most 15%.
  - AGG at least 8% (liquidity).
- **D7 risk limits:**
  - Max drawdown 25% including a 2008 replay.
  - P(drawdown > 25% within 5 years) ≤ 5%, by block bootstrap with CAPM-reset means, **126-day blocks (D32)**, 32,000 paths.
  - 1-day ES99 ≤ 2.5%, VaR99 ≤ 1.7%, ES95 ≤ 1.45%, VaR95 ≤ 0.9%.
  - Every stress scenario ≤ 25%.
  - **Basis (D42):** both drawdown tests are measured on **investment returns** (quarterly-rebalanced, before spending and costs). That is the official D7 test. The fund's value after D24 spending and costs is reported next to it as a disclosure, not as the limit:

    | O6 (`d7_fund_value.csv`) | Investment returns (official D7) | Fund value after D24 spending and costs |
    |---|---|---|
    | Max drawdown incl. 2008 (limit 25%) | 23.5% (pass) | 25.3% |
    | P(drawdown > 25% within 5 years) (limit 5%) | 4.9% (pass) | 9.5% |

    - Spending deepens the fall: D24 keeps paying near last year's level while the value drops. On the fund-value basis O6 would exceed both limits. The policy benchmark exceeds them on both bases (25.3% / 9.0% on investment returns).
- **D27:** no ETF above 40% of the 99% ES (Euler component ES).
- **D33 precedence:** D7 > D6 > D27 > return target.
- **Optimiser:** cvxpy with a CVaR linear programme for ES and conditional drawdown-at-risk (CDaR) for drawdown, then post-checks on the compounded, quarterly-rebalanced path (D22).

### 4.3 Candidates and benchmarks
- **Candidates:** minimum variance, minimum CVaR, risk parity, maximum Sharpe, and Markowitz target-return.
- **Benchmarks (D3, frozen):**
  - Policy 40/50/10 (equity / AGG / GLD);
  - 60/40 SPY/AGG;
  - equal weight;
  - SPY.
- **KPIs:** Sharpe, Sortino, beta, Jensen's α, Treynor, information ratio vs the policy benchmark, Calmar (`kpis.csv`).

### 4.4 Selection rule (D26 with D32)
**Feasibility:**
- The return objective is not attainable within D6 + D7.
- Without the D6 weight limits, reaching 6.66% needs a 35% drawdown tolerance (ES99 3.3%), and 7.19% needs 47% (ES99 4.5%). With D6, neither is reachable at any risk level.

**Rule:** choose the **highest-expected-return Markowitz portfolio that passes every D7 test, plus the D27 cap**.

**The block-length choice (D32):**
- The 5-year test resamples history in blocks.
- The Politis–White optimal block length is 5–14 days for returns but **120–160 days for absolute and squared returns** (volatility clustering).
- Drawdowns depend on runs of turbulent days, so the test uses 126-day blocks instead of the original 63.
- **This is a heuristic and a conservative choice, not a proof.** The Politis–White rule (with the Patton–Politis–White 2009 correction) is derived for stationary and circular bootstraps and for a specific statistic. Applying it to |r| and r² and using the result as a moving-block length is a judgement. The 21-, 63- and 252-day results are reported as sensitivity analysis.

### 4.5 Final selection and its audit (T4.25; `research_t425_*`)
**Options.** Six options were evaluated under identical assumptions:
- **O1:** D26 with the 63-day test.
- **O2:** P ≤ 4% margin.
- **O3:** 50/50 with risk parity.
- **O4:** 5% gold floor.
- **O5:** risk parity.
- **O6:** D26 with the 126-day test.

**The audit.** It found and fixed:
- **(a) A seed-tuned 5-year test.** 4,000 paths with one seed: the original pick sat at exactly 5.00% on that seed but was truly 5.1%.
- **(b) Spending not propagated** to the hurdle and the stress tests.
- **(c) Two arbitrary thresholds.**

**Result:**
- **O6 passes the 5-year test at both block lengths** on 2026 and 2014 inputs, and it survives a 1.5× larger equity shock in the severe scenarios.
  - Passing at 126 days is partly by construction: the rule picks the highest return whose 126-day probability is still ≤ 5% (O6 sits just under 5%), and 63-day blocks always give a lower probability. The 2014-input result (4.9%) is the less circular check.
- **The gold floor (O4) was rejected.** Its +0.01 pp expected-return edge reverses if rates fall. Its 2020–26 outperformance came mostly from one gold cycle (+64% in 2025) that was seen before the option was proposed.
- **Gold's 0.4% follows from its expected return, and more gold would not buy a hedge** (`research_v2_gold_return.csv`; the D26 rule re-run with only gold's expected return changed):
  - At a zero real return (Erb & Harvey 2013) gold drops to 0%; at CAPM's 4.6% it is 0.4% (O6).
  - Each extra percentage point assumed for gold adds about 9 pp of gold, taken from AGG: 4.7% at +0.5 pp, 9.2% at +1 pp, 18.0% at +2 pp, and the 20% cap from +4 pp.
  - Even at 18–20% gold, the 2022 and stagflation losses improve by less than 1 pp (2022: −16.9% vs −17.8%), because gold replaces bonds, not equities.
  - Under our base assumptions those portfolios fail the D7 5-year drawdown test (5.3–6.3% vs 5%), and supportable spending falls to 2.58%.
  - The literature is mixed. Baur & Lucey (2010) find gold a safe haven only for about two weeks after a crash. Erb & Harvey (2013) find it an unreliable inflation hedge over practical horizons.
  - We therefore keep CAPM for gold, take no hedge credit for the 0.4%, and disclose the gap (§10).

| | O1 | O2 | O3 | O4 | O5 | **O6** |
|---|---|---|---|---|---|---|
| Expected return | 5.89% | 5.81% | 5.73% | 5.90% | 5.54% | **5.80%** |
| Spending supported | 2.74% | 2.67% | 2.58% | 2.75% | 2.40% | **2.65%** |
| P(DD > 25%), 126-day, 2026 / 2014 inputs | 6.5 / 6.2% | 5.2 / 5.0% | 4.8 / 6.2% | 6.7 / 6.3% | 4.5 / 7.3% | **5.0 / 4.9%**¹ |
| Stagflation severe × 1.5 equity | 25.6% | 24.9% | 23.0% | 25.1% | 20.3% | **24.8%** |

*(Option table computed at 2.8% spending; O6 at the final 2.65% is in §1. Source: `docs/research/T4_25_final_selection_evaluation.md`.)*
¹ Research run (4.97%). The pipeline's own run gives 4.94% (§1, tear sheet). Both are within the Monte Carlo error (±0.12 pp) of the 5% limit and move by 1–2 pp with block length, so "passes" means "at the limit", not "safely below it". Likewise O6's expected return is within 0.1 pp of O1, O2 and O4, inside the estimation error of the inputs.

**Walk-forward (T20.07):**
- The rule was re-run at year ends 2008–2023 with only the data available then, and each portfolio was held for 3 years.
- **The drawdown limit held in all six segments.**
- Chained 2009–2026 result: 7.3% a year, Sharpe 0.89, worst drawdown −16.4%, against 7.3%, 0.75 and −19.2% for the policy benchmark.
- **Sharpe differences are not significant** (Ledoit–Wolf 2008 test, robust to fat tails and volatility clustering; `research_v2_sharpe_test.csv`):
  - walk-forward +0.14 (p = 0.15);
  - 2015–19 +0.19 (p = 0.21);
  - 2020–26 −0.19 (p = 0.10);
  - O6 full sample +0.02 (p = 0.67, in-sample).
  - The two portfolios hold the same ETFs (return correlation 0.91–0.96), so six to eighteen years cannot separate their Sharpe ratios. Our claim is the smaller drawdown within the D7 limit, not a better Sharpe ratio. The policy benchmark breaches that limit (−25.3% in 2008).
- At the 2008 and 2011 origins, D27 could not be met together with D7, so the rule fell back to capped minimum variance (now written down as D33).

## 5. Risk measurement (P2; `p2_*.csv`)
**Methods:** historical, normal, Student-t (MLE) and Monte Carlo with a t-copula and empirical marginals (100,000 simulations), at 90/95/99%, with bootstrap intervals.

**O6, 1-day loss as % of NAV:**

| Method | VaR 95% | ES 95% | VaR 99% | ES 99% |
|---|---|---|---|---|
| Historical | 0.71% | 1.20% | 1.39% (1.22–1.60) | 2.20% |
| Normal | 0.82% | 1.04% | 1.18% | 1.35% |
| Student-t | 0.71% | 1.45% | 1.67% | 3.18% |
| Monte Carlo (t-copula) | 0.71% | 1.14% | 1.38% | 1.93% |
| EVT (POT-GPD, threshold q = 0.92, ξ = 0.28) | 0.71% | 1.20% | 1.43% (1.33–1.52) | 2.20% |
| GARCH-EVT, today's / long-run volatility | — | — | 0.94% / 1.48% | — |

**Reading the table:**
- **The normal model understates the 99% tail by about 40%.**
- **EVT confirms the historical tail** and extends it to 99.5%: VaR 1.85%, ES 2.79%.
- **GARCH:** persistence 0.989 and a volatility half-life of 65 days. Today's calm regime gives a 99% VaR of 0.94%, against 1.48% in an average regime. This is why D7 is checked on full-cycle history.
- **Attribution:** SPY carries 40% of the 99% ES, XLK 22%, EFA 16% and AGG 14%. Bonds are 61% of the capital but a small part of the tail risk.
  - **SPY sits on the D27 cap by construction, and the share is an estimate.** It comes from 56 tail days. A 21-day block bootstrap gives SPY 40.0% with a 90% interval of 36.8%–43.7%, and 51% of resamples put it above 40% (`p2_attribution_ci.csv`; 63-day blocks give the same picture). Component-ES estimates are noisy (Tasche 2000; Yamai & Yoshiba 2002), so D27 is a target for the point estimate, not a guarantee.

**Diversification benefit** (brief p.4; `p2_diversification.csv`). The undiversified risk is each ETF's own VaR or ES, weighted and added up, as if all holdings had their worst days together.

| 1-day, 99% | Portfolio | Undiversified | Benefit |
|---|---|---|---|
| O6 VaR | 1.39% | 1.95% | 28.8% |
| O6 ES | 2.20% | 2.91% | 24.5% |
| Policy 40/50/10 VaR / ES | 1.51% / 2.30% | 2.18% / 3.29% | 30.9% / 30.0% |
| Risk parity VaR / ES | 1.36% / 2.09% | 2.17% / 3.23% | 37.4% / 35.4% |

- **O6 diversification ratio:** 1.38. The weighted average volatility is 38% above the portfolio's own.
- **Diversification shrinks in crises.** It is smaller in the tail (ES) than at the VaR level, because correlations rise in stress (T11 §3).
- **O6 diversifies less than risk parity.** It gives up some diversification for a higher expected return within the same limits; the D27 cap stops any single fund from dominating the tail.

## 6. Out-of-sample backtesting (T10; `backtest_*.csv`)
**Setup:**
- Rolling 1,000-day window (D13), re-estimated daily on data up to t−1, for 7 methods × 6 portfolios.
- Weights built with data to 2014.

**Tests:** Kupiec, Christoffersen (independence and conditional coverage), Basel traffic light, ES severity and Acerbi–Szekely Z2, and the FZ0 joint score.

**Model choice (D28):**
- The rule was fixed before the test: pass Kupiec at 95% and 99% with no red Basel window, then rank by FZ0, using **2015–2019 only**.
- **GARCH-EVT was selected and frozen** (commit 60e67e3) before 2020–26 was run.

**Backtest portfolio (D26 rule on data to 2014), 99%, 2020–2026:**
- **GARCH-EVT:** 20 exceptions against 17.1 expected; Kupiec p 0.49, Christoffersen p 0.62; worst Basel window 7 (yellow, never red).
  - **ES:** Acerbi–Székely Z2 = 0.26, below the approximate 5% critical value of 0.70 (Acerbi & Székely 2014), so the ES forecast is not rejected. Severity ratio 1.09. FZ0 joint VaR/ES score −4.12, the best of the 7 methods (historical −3.55, normal −3.10).
- **Others:**
  - historical: 26 exceptions, red zone;
  - normal: 30, red;
  - GARCH-t: 33, fails.
- **Stress windows:** GARCH-EVT halves the exceptions of historical simulation in COVID and 2022, because its volatility rises within days.

**A regime-switching alternative was tested and rejected (D41; research doc V2_regime_blend):**
- **Idea (Team Guide §8):** classify each day as calm or elevated volatility (20-day vs 252-day σ, data up to t−1). Weight historical 70% / EVT 30% when calm and 30 / 70 when elevated.
- **Integrity:** the design, 12 variants and the adoption rule were committed before the first run, and the baseline reproduced exactly.
- **O6 (final weights), 99%, 2020–26:**
  - blend: 22 exceptions, Christoffersen p 0.002, worst Basel window 12 (red);
  - GARCH-EVT: 24, p 0.35, 8 (yellow).
  - The 2014-weights portfolio above and the policy benchmark give the same result.
- **Why it fails:** the detector flagged COVID, 2022 and 2025 on day 0, but historical and EVT share one 1,000-day window.
  - A blend moves VaR by less than 15% on 95% of days.
  - In the COVID weeks its 99% VaR averaged 1.25% against 4.37% for GARCH-EVT.
- **Result:**
  - The FZ0 score is worse than GARCH-EVT's in 2008–14, 2015–19 and 2020–26, for every variant.
  - Even max(historical, EVT) stays red.
  - GARCH-EVT is kept. This measures forecast quality only: O6's weights and returns do not change.

**What backtesting cannot show:**
- The first day of a sudden shock is still missed.
- Six years contain few tail events.
- 2015–26 has been examined during portfolio selection, so it is not untouched for the portfolio choice. It is untouched only for the frozen VaR model.

**Limit stability (T10.12):** portfolios built on 2004–2014 data kept every D7 limit in 2015–19 and 2020–26.

## 7. Stress testing (T11; `stress_*.csv`)
**Historical replays**, with quarterly rebalancing along the real path (worst peak-to-trough loss of O6):

| Crisis | O6 | Policy 40/50/10 |
|---|---|---|
| GFC 2007-09 | 23.5% | 25.3% |
| Taper tantrum 2013 | 4.8% | 6.0% |
| COVID 2020 | 16.2% | 16.0% |
| Rates and inflation 2022 | 17.8% | 18.6% |

**Hypothetical scenarios (D9 v2, D29).** These were designed from research into current conditions to 27 October 2026:
- the 2026 Strait of Hormuz oil disruption (Brent $118–123, 99th percentile);
- Fed hikes and the 10-year yield at a 2002 high;
- credit spreads at the 3rd percentile;
- stocks and bonds positively correlated since 2022.

**Calibration.** Shocks come from crisis episodes and factor-change tails. ETF moves come from a six-factor monthly model (2006–2026): equity, real yield, breakeven, Baa spread, Brent and USD. That model was back-tested on six crises: errors are 1–2 pp for AGG, EFA and EEM, but large for XLE and GLD, which get variants and bands.

| Scenario (instant loss of O6) | Central | Severe |
|---|---|---|
| A Energy stagflation "Hormuz II" (oil +25 / +50%, real yield +40 / +100 bp, stocks −15 / −30%) | 8.7% | 18.8% |
| B AI unwind with recession (stocks −25 / −40%, credit +100 / +250 bp) | 8.8% | 14.2% |
| C Term-premium shock (sensitivity) | 11.3% | — |
| T Tech-led crash (D35; tech −40 / −65%, other stocks −10 / −25%) | 9.2% | 16.7% |

**Tech-led crash (D35).** SPY already holds the large technology companies that make up XLK. Counting SPY's holdings, technology is 17.7% of the fund and 46% of its equities (SPY's own share is 38.4%, SSGA, 29 October 2026). Scenario T gives SPY the same loss as B but leads it with technology. Each equity ETF moves by the technology share of its holdings, and bonds and gold get no hedge credit. O6 loses 16.7% in the severe case, 2.6 pp more than in B. History cannot test this: 2004–26 has no tech-led crash, and XLK helped in 2008. Portfolios with less XLK were evaluated under a rule fixed in advance and not adopted. All of them deepen the 2008 drawdown, and none reaches O6's return within D7 (research doc V2). Instead, technology above 20% of the fund triggers a committee review (D37). Counting SPY and XLK as one source, O6 has 2.3 effective risk contributors rather than 3.9 (D36).

**What the scenarios show:**
- **The bond hedge fails in inflationary shocks.** In A severe, AGG contributes over a third of the loss; in a recession it rallies.
- **Robustness:**
  - Monte Carlo over shock and beta uncertainty: 99th percentile 15.5% (A) and 14.6% (B).
  - **The equity shock decides the outcome:** at 1.5× the severe equity fall, losses are 24.8% (A) and 22.1% (B), still within the limit.
- **An AI unwind is survivable over a year.** On the 12-month path of B severe, the worst fall is 15.5% and the 12-month result is −11.9%. Next year's spending dips only from $265,000 to $257,432 under the smoothed rule.
- **The worst AI case is a tech crash while inflation keeps rates up (T + I, D44; `research_v2_ai_inflation.csv`).** Scenario T was run again with the rates leg of A at the same severity (real yield +40 / +100 bp, breakeven +20 / +50 bp, Baa +50 / +150 bp) applied to AGG and gold.
  - O6 loses 11.5% (central) and **22.8% (severe, $2.28M)**, against 20.5% for the policy benchmark. Bonds and gold add 6.1 pp of the severe loss instead of cushioning it.
  - That is the largest hypothetical loss, close to the 2008 replay (23.5%), but within the 25% limit.
  - Monte Carlo over shock sizes: 99th percentile 17.9%, with no draw above 25%.
  - **At 1.5× it breaches the limit:** 31.2% for the equity leg (tech −97.5%, beyond the dot-com fall of about 78%) and 25.9% for the rates leg. T alone at 1.5× is 25.1%. The benchmark also breaches (27.8%).
  - Less XLK was tested and not adopted (D35), and more gold barely helps (D43). The limit is kept, and the D23 ladder and the D37 technology trigger are the response.
- **Why the 61% bond allocation is right, even when bonds fail as a hedge** (`research_v2_ai_inflation_whatif.csv`; O6 changed by hand, everything else fixed):
  - In T + I, AGG falls 9.9% while O6's equities fall 43.4% on average. Bonds lose too, but four times less, which is what keeps the worst case inside the limit.
  - Moving only 5 pp from AGG to SPY breaks the 25% limit in a 2008 repeat (−25.2%) and raises P(DD > 25% in 5 years) to 7.9%. At 10 pp, T + I itself breaches (25.9%). 60/40 loses 28.2% in T + I and 35.0% in 2008.
  - The policy benchmark has the same expected return as O6 (5.79% vs 5.80%) but fails D7: −25.3% in 2008 and a 9.0% five-year probability. O6's mix earns the same return within the committee's limits.
- **The 10% tech tilt is a deliberate cost:**
  - It is why O6 loses 2.3 pp more than the benchmark in T + I.
  - SPY is already at the 40% cap on its share of 99% ES (D27). Moving XLK into SPY would put SPY at 62% of tail risk.
  - Moving XLK into AGG cuts the T + I loss to 17.3%, but costs 0.45 pp of expected return a year (about $45,000 of spending).
  - We keep the tilt within its 10% cap, and the D37 trigger reviews it if look-through technology passes 20% of the fund.
- **Scenario losses vs the 1-day ES limit:** a multi-month scenario loss is not comparable to the 1-day ES limit. Scaling GARCH-EVT VaR by stressed volatility gives 2.3–2.8% in the severe cases, above the 1.7% VaR limit, so the D23 review would trigger.

## 8. Spending sustainability and recovery (T20.09; `sustainability_*.csv`)
**Setup:**
- 15/20/25% falls, recoveries of 1, 3, 5 or 7 years and a lost decade.
- D24 spending at 2.65%, 0.2% costs, inflation at the breakeven (stagflation variant at 5%), and tax cases.
- A market-crash view and a 20,000-path bootstrap.

**Findings (O6):**
- **Recovery speed matters more than depth.** After a 25% fall with a 3-year recovery, the real value after 10 years is 0.83× today's, against 1.06× with no crisis.
- **The fund regains its nominal $10M in 5, 9 or 13 years** for 1-, 3- or 5-year market recoveries, and not within 15 years if the recovery takes 7 years.
- **Bootstrap, 10 years:**
  - median real value 1.08×;
  - 21% chance of ending below 90% of today's real value;
  - 24% chance of a real spending cut above 10% at some point;
  - median recovery of the portfolio's *price* from a 25% drawdown 3.0 years (p90 5.3), before spending and inflation.
- **The options differ by only 1–3 pp here.** The spending policy matters more than the portfolio choice.

**Real recovery after a crisis (view 4, D39; `sustainability_recovery.csv`).** On 8,000 bootstrap paths of 25 years, a crisis is O6's own drawdown reaching 20% or 25% within the first 10 years. Recovery means real value after spending and costs is back at its pre-crisis level.

| Spending rule | P(back within 15 years) after ≥ 25% / ≥ 20% fall | Median years (≥ 25%) | Avg real spending, years 1–20 | P(real spending cut > 10%) |
|---|---|---|---|---|
| D24 at 2.65% (policy) | 46% / 64% | 17.8 | 2.9% of start value | 33% |
| D24 at 2.45% | 50% / 68% | 15.5 | 2.7% | 30% |
| D24 at 2.25% | 54% / 71% | 13.5 | 2.5% | 27% |
| D24 at 2.00% | 58% / 76% | 11.5 | 2.3% | 23% |
| D24 capped at 2.65% of current value | 49% / 66% | 15.8 | 2.8% | 48% |

- **After a severe fall, the price recovers in about 1–3 years, but purchasing power typically takes 15–20 years and returns within 15 years only about half the time.**
  - Historical: in 2008 O6's price was back at its pre-crisis level 254 trading days (about 1 year) after the trough (`stress_results.csv`; one crisis, −23.5%).
  - Simulated: median 3.0 years (p90 5.3) for a 25% fall on the bootstrap paths, before spending and inflation. We give a range, not one year: the median moves by about 2 years between simulation seeds. Without a crisis, real value grows only about 0.6% a year after spending, so a 25% loss is slow to rebuild: the fund would need about 1.9% a year to do it in 15 years.
- **Lowering spending helps only slowly.** At 2.0%, the chance rises by 12 pp, at a cost of about 0.6% of start value in average real spending a year. A crisis cap gains 3 pp but makes real spending cuts above 10% much more likely.
- **The portfolio cannot close the gap.** O6 is already the highest-return portfolio within D7. The policy benchmark recovers a little faster after a severe fall (52%) but suffers one more often (845 vs 629 crisis paths).
- **A stricter target was tested and rejected (research doc V2_recovery_target).** We tested a 60% chance of real recovery within 15 years after a 25%+ fall, under a rule fixed before the run and with every D6/D7/D27 and stress test applied:
  - **It can be met only by cutting spending.** It needs either 1.8% permanent spending (61%, confirmed on new seeds) or a crisis-time cut to 1.0% of value (62%). The second means about 30% of the normal budget for about 8 years.
  - **No portfolio solves it.** No allocation within the limits reaches 60% at 2.65%: the best is Risk Parity at 48%. Lower-risk portfolios crash less often but recover more slowly.
  - **O6 stays best on the long-run measure.** It keeps the highest chance that real value is at least today's after 15 years (67%).
  - **A stronger recovery target is not a better policy** if meeting it undermines the university's funding purpose.
- **Rebalancing assumption.** The table assumes daily rebalancing (constant weights). Under the approved quarterly rebalancing (D11), the chance after a 25%+ fall is about 42–45%, so we quote "about 42–46%".
- **A crisis spending buffer was tested and rejected (D40, research doc V2_withdrawal_rule).** A cash or T-bill reserve is outside the seven-ETF universe, so we tested rules within O6, with AGG as the buffer, on the same paths and crises (P back within 15 years after a 25%+ fall, 8k / new-seed 16k paths):
  - **Quarterly rebalancing (D11):** 42.0% / 44.6%.
  - **Spend from AGG only and pause rebalancing from a 15% fall:** 41.2% / 43.3%. Rebalancing already buys equities with AGG after a fall; pausing it slows recovery.
  - **Withdraw from overweight holdings, rebalance beyond ±5 pp:** 43.2% / 45.4%. The gain is small and the drifted weights were not re-tested on D7.
  - Real spending is the same in all three. We keep D11 and add no buffer.
- **Decision (D39, D40):** keep O6, 2.65% and quarterly rebalancing, set no recovery deadline, and review spending at the D23 "act" step (−20%).

## 9. Recommendation and monitoring (`outputs/p3_decision/`)
**Recommendation:** O6 as above; spending about 2.65% via D24; quarterly rebalancing.

**Monitoring (D23, no forced selling):**

| Step | Trigger | Action |
|---|---|---|
| Watch | −10%, or rolling 250-day ES99 > 2.5% | report to the committee |
| Review | −15%, or Basel yellow | committee check of model, stress and spending |
| Act | −20% | formal decision on risk and spending |
| Limit | −25%, or Basel red | mandatory decision: accept / adjust risk limit / reject |
| Annual | every year | refresh assumptions, rerun the rule, re-check D7 / D27 / D33 and spending |

On 2004–2026 history the watch trigger was active 7–10% of the time; the −20% level was reached only in 2008.

## 10. Assumptions and limitations
These are summarised from `docs/ASSUMPTIONS_LIMITATIONS.md`, which is identical to the app page:
- **CAPM expected returns** with a 5% ERP. AGG's yield is assumed locked in when rates fall. Returns are lower if the T-bill falls (at a 2.5% T-bill and a 4% ERP, the supported spending is about 1.7%).
- **History** contains one 2008-type crisis, so limits are targets, not guarantees. The bootstrap cannot create crises unlike the sample's.
- **AI / tech crash:**
  - The data start in 2004, so there is no dot-com-style crash: technology fell about 78% over 2.5 years then. The AI scenarios (B, T, T + I) are one-step shocks with linear betas.
  - The worst case, a tech crash with inflation (T + I, 22.8%), is within the limit but breaches it at 1.5× (§7).
- **The 5-year drawdown test is sensitive to block length** (model uncertainty, reported). The 126-day block is a heuristic, conservative choice; 21/63/252 days are sensitivity analysis.
- **Drawdown limits are measured on investment returns** (D42). After D24 spending and costs, O6's fund value fell 25.3% in 2008 and P(fall > 25% in 5 years) is 9.5%, above both limits. The committee should read the D7 limits as limits on investment performance.
- **Component ES is estimated from 56 tail days.** SPY's 40.0% share has a 90% interval of 36.8%–43.7%.
- **The factor stress model is linear**; XLE and GLD sensitivities are unstable.
- **ETFs can trade below the value of their holdings in a panic** (AGG −6.8% in a day in 2008). The AGG floor and D24 avoid forced sales.
- **Selection bias:** 2015–26 was examined during selection. The walk-forward and live monitoring are the defensible tests.
  - More than 20 portfolio variants were compared (6 P1 candidates, options O1–O6, two walk-forward rules, the V2 recovery-target and tech-concentration variants), so the best observed Sharpe ratio is biased upward.
  - A deflated Sharpe ratio (Bailey and López de Prado, 2014) would correct for the number of trials. It can only lower significance, and we already claim no Sharpe advantage (Ledoit–Wolf, §4.5), so no conclusion changes. O6 was chosen by the D26 rule (highest return within the D7 limits), not by Sharpe.
- **No real inflation hedge.** O6 holds XLE 3.0% and GLD 0.4%. In a 2022-type shock or stagflation, bonds and stocks fall together (O6: −17.8% in 2022, −18.8% in the severe stagflation case). A larger gold weight would help by under 1 pp and fails D7 under our assumptions (§4.5), so the committee accepts this risk through D7 and the D23 ladder.
- **Spending:** the brief sets no spending rate; 2.65% is the team's recommendation.

## 11. AI use and human validation
- **AI tool:** Claude Code (Anthropic) was used for code scaffolding, research, documentation and drafting.
- **Validation:**
  - every module has unit tests (164 tests);
  - every AI-assisted component is recorded in `tracking/validation/HUMAN_VALIDATION_LOG.md` for team sign-off;
  - the brief's four disclosure columns, and a sign-off table each member signs, are in `docs/AI_DISCLOSURE.md`.
- **Decisions:** all decisions (D1–D44 in `docs/DECISIONS.md`) were taken by the team.
- **The audit of 2026-10-29** and an **independent human QA review on 2026-10-31** caught AI-introduced errors and overclaims; the corrections are in D42 and the commit history.

## Appendix: reproducibility
- **One command:** `python run_all.py` reruns all stages from the committed data snapshots. `python run_all.py --app` also opens the Streamlit app.
- **Research evidence:** scripts in `scripts/`.
- **Decision log:** `docs/DECISIONS.md`.
