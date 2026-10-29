# P1 Candidates, Frontier, D26 Selection and KPIs (2026-10-29)

**Reproduce:** `python run_all.py --only portfolio` writes `outputs/tables/p1_*`, `frontier_full.csv`, `kpis.csv` and `outputs/figures/frontier_full.png`.
**Labels:** [E] evidence · [A] assumption · [O] open.

## 1. Candidates within D6 v2 + D7 (P1-final, 2026 inputs) [E]
| Candidate | AGG | SPY | XLK | GLD | Other | Expected | Max DD | ES99 | P(DD > 25%, 5y) | D7 | Spending |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Min-Variance (= target-return fallback) | 80 | 20 | – | – | – | 5.00% | −17.8% | 1.46% | 0.1% | ✅ | 1.9% |
| Min-CVaR | 74 | 20 | – | 6 | – | 5.02% | −17.5% | 1.44% | 0.1% | ✅ | 1.9% |
| Risk Parity | 55 | 8 | 7 | 13 | EFA 7, EEM 5, XLE 6 | 5.54% | −23.2% | 1.97% | 3.2% | ✅ | 2.4% |
| Max-Sharpe | 54 | 34 | 9 | 2 | XLE 1 | 6.02% | −25.0% | 2.32% | 5.7% | ❌ (5-yr test) | 2.9% |
| **D26 selected** | **55** | **36** | **7** | **2** | – | **5.96%** | **−24.3%** | **2.25%** | **5.0%** | ✅ (at boundary) | **2.80%** |

- The D12 hurdle (7.19%) is infeasible within D6 + D7. The highest-return portfolio within the limits expects 6.02%.
- **D26 (approved):** pick the Markowitz target-return portfolio with the highest target that passes every D7 test. It sits exactly at the 5% boundary of the 5-year test. Bootstrap noise is about ±0.35 pp, so a margin should be considered at final selection [O].
- **Frontier:** about +$12k a year of spending per 0.13 pp of expected return, from $187k (min-variance) to $287k (max return).

## 2. KPIs: P1-train weights scored on later, unseen data [E]
Weights fixed with 2014 information (D5), quarterly rebalancing; benchmarks per D3.

| Portfolio | Validation 2015–19 Sharpe / Calmar / max DD | **Test 2020–26** CAGR / Sharpe / Calmar / max DD | Test Jensen α / IR vs policy |
|---|---|---|---|
| Min-Variance | **1.26** / 1.65 / −3.4% | 4.73% / 0.28 / 0.25 / −18.6% | −1.55% / −0.64 |
| Min-CVaR | 1.24 / 1.42 / −4.1% | 5.93% / 0.42 / 0.33 / −18.1% | −0.47% / −0.40 |
| Risk Parity | 0.91 / 0.74 / −7.1% | **7.12% / 0.53 / 0.45 / −16.0%** | **+0.09% / −0.07** |
| Max-Sharpe | 1.25 / 1.61 / −3.5% | 4.48% / 0.25 / 0.24 / −18.7% | −1.77% / −0.67 |
| D26 selected | 1.04 / 1.12 / −5.1% | 5.25% / 0.32 / 0.26 / −19.8% | −1.89% / −0.73 |
| Policy 40/50/10 (benchmark) | 0.89 / 0.75 / −7.9% | 7.19% / 0.49 / 0.37 / −19.2% | −0.85% / — |
| 60/40 SPY/AGG | 0.92 / 0.75 / −11.0% | 9.53% / 0.57 / 0.45 / −21.0% | −1.13% / +0.49 |

**Findings:**
1. **No candidate wins in every regime.** Bond-heavy optimised portfolios (Min-Variance, Max-Sharpe on 2014 inputs) led in calm 2015–19 but lagged in 2020–26, when bonds fell with stocks (2022). Risk Parity, which does not use expected returns, held up best in the test period, with the best Calmar and the smallest drawdown among candidates.
2. **Return-based optimisation is fragile out of sample.** The 2014 CAPM inputs (near-zero T-bill) pushed optimisers into bonds just before the 2022 bond crash. This matches the literature (DeMiguel, Garlappi & Uppal 2009: estimated-return optimisers often fail to beat simple diversification).
3. **Every candidate stayed well inside the 25% drawdown limit out of sample** (worst −19.8%). D7 held.
4. **Raw returns favoured equity-heavy benchmarks** (SPY 15.3% a year in 2020–26). That was the cost of a conservative mandate in a strong equity period, not a model failure.

**Implications for the decision stage [O]:**
- The D26 pick is the right *rule* for meeting spending. But out-of-sample evidence favours more diversification (Risk Parity's structure).
- Before the final choice (T20), weigh in the risk-stage results (component ES cap), backtests and stress tests.
- Consider a **D26 portfolio with a component-ES cap** or a **blend with Risk Parity** as robustness options.
- Per D5, model selection should rest on the validation period; the test period is reported once.
