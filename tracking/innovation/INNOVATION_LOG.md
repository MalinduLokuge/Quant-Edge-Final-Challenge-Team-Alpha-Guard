# Innovation Log
Innovation is worth 15% of the score (brief p.10). Its examples are regime-conditioned risk, risk overlays and alternative EVT threshold rules. Log each extension when you start it. Keep it only if it is validated and changes a decision.

## Done or in use
| ID | Date | Innovation | Why it matters for the decision | Evidence | Status |
|---|---|---|---|---|---|
| I6 | 2026-10-28 | **Needs-based, risk-constrained return objective** (multiplicative CFA formula) with **highest sustainable spending rate** | Turns a return shortfall into a concrete spending number the committee can act on | `portfolio/return_objective.py`, `outputs/reports/return_objective_summary.md` | In use |
| I7 | 2026-10-28 | **Probabilistic drawdown limit**: historical ≤ 25% *and* P(DD > 25% in 5y) ≤ 5% by block bootstrap with CAPM-reset means | A historical 20% limit still has a 12.6% chance of being breached; limits stated as probabilities | Research doc §4b, `--g1` | In use (D7) |
| I8 | 2026-10-28 | **Two-risk calibration of weight constraints** (drawdown vs purchasing-power shortfall) | Equity range 20–45% comes from the client's risks, not round numbers; showed that a tighter drawdown limit raises the risk of losing purchasing power | Research doc §5c, `--d6b` | In use (D6) |
| I9 | 2026-10-28 | **Feasibility map of risk limits vs return objective** (50,000 portfolios) | Proves D7 and D12 conflict and quantifies the trade-off (20% DD → 2.1% spending, 25% → 2.8–3.1%) | Research doc §4 | In use |
| I10 | 2026-10-28 | **Policy benchmark built from asset classes** (sector ETFs excluded, market-cap equity split, frozen in advance) | Fair IR and alpha for a conservative mandate; SAMURAI-compliant | Research doc §1 | In use (D3) |
| I11 | 2026-10-28 | **Income cross-check**: total-return minus price-return growth vs distribution yield, within 0.1 pp | Shows that adjusted prices and the income data agree | `outputs/tables/income_crosscheck.csv` | In use |
| I15 | 2026-10-28 | **Risk tolerance approximated as min(willingness, capacity)** with spending-aware capacity simulation and spending-rule comparison | Turns 'no number in the brief' into a defensible 25% limit with conditions; links drawdown to scholarships | Research doc §9 | In use (D7, D23, D24 approved) |
| I16 | 2026-10-29 | **Research-calibrated macro stress scenarios** (six factors, back-cast on 6 crises, central + severe, 12-month rebalanced path with D24 spending, Monte Carlo over shock and beta uncertainty) | Hypothetical shocks tied to current conditions (Hormuz, Fed hikes, 10y at 2002 high) and data-estimated ETF sensitivities instead of invented percentages; shows the bond hedge fails in inflationary shocks (AGG = 35% of the severe loss) | `stress_hyp_*.csv`, `docs/research/T11_hypothetical_stress_design.md` | Done (D9 v2, D29) |

## Planned
| ID | Extension | Hypothesis | Baseline compared | Leakage-safe? | Status |
|---|---|---|---|---|---|
| I1 | GARCH-filtered VaR / GARCH-EVT | Time-varying σ reduces exception clustering (Christoffersen) | Historical VaR | Rolling, data ≤ t−1 | **Built and backtested**: selected by D28 on validation; out-of-sample 2020–26 passes Kupiec, Christoffersen and Basel (no red window) where historical fails; stress-window exceptions halved |
| I2 | Student-t copula Monte Carlo | Captures joint crash losses better than Gaussian | Gaussian MC | Fit on window only | Planned (D19) |
| I3 | Wavelet multi-scale correlation | Diversification differs by horizon | Single-scale correlation | — | Recommend drop or appendix only (rec. #13, PROPOSED) |
| I4 | Net-of-cost / ETF exit-liquidity gate | Costs and liquidity don't change the ranking | Gross returns | — | Planned (T4.13, T11.09) |
| I5 | Robust inputs (Ledoit–Wolf on correlations, variances kept) | More stable weights out of sample | Sample covariance | Train only | **Tested: small effect** (δ 1.6% on training; min-var turnover −2.5%); kept as insurance for short windows. Estimation risk sits in expected returns, handled by CAPM + D25 |
| I12 | Alternative EVT threshold rules (named in brief p.10) | Threshold choice changes the 99% tail estimate materially | Fixed 95th percentile | Rolling | **Built**: stability rule with eligibility constraints, 7-threshold sensitivity table + figure |
| I13 | Regime-conditioned VaR (named in brief p.10) | Stress regime needs a different risk scale | Unconditional VaR | Rolling | Candidate (T13) |
| I14 | Conditional drawdown-at-risk (CDaR) optimisation | Optimising on drawdown directly enforces D7 better than variance | Min-Var / Min-CVaR | Train only | Candidate (T13.07) |
