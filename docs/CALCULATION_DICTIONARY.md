# Calculation Dictionary

Every metric the system reports: its formula, inputs, units, sign, where it lives in the code and which test covers it.
Add a row **before** implementing a new metric. The report and app must use the same definitions.
Conventions: decision D17. Status ✅ = implemented and tested, ⏳ = planned.

## Returns & conventions (`common/conventions.py`, `data/clean.py`)
| Quantity | Formula | Units / sign | Code | Test | Status |
|---|---|---|---|---|---|
| Simple return | Rₜ = Pₜ/Pₜ₋₁ − 1 | fraction | `clean.simple_returns` | test_data_clean | ✅ |
| Log return | rₜ = ln(Pₜ/Pₜ₋₁) | fraction | `clean.log_returns` | test_data_clean | ✅ |
| Portfolio return | R_p,t = Σᵢ wᵢ·Rᵢ,ₜ (simple returns only) | fraction | `conventions.portfolio_returns` | test_conventions | ✅ |
| Weights | wᵢ ≥ 0, Σwᵢ = 1, 7 approved ETFs only (D10) | fraction | `conventions.validate_weights` | test_conventions | ✅ |
| Rebalanced portfolio return | weights drift with prices, reset to target on the last trading day of each completed period (D11 quarterly); turnover = ½Σ\|drift − target\| per rebalance, annualised | fraction / fraction p.a. | `conventions.rebalanced_returns` | test_conventions | ✅ |
| Loss | L = −R | positive = loss | `conventions.to_loss` | test_conventions | ✅ |
| USD amount | x · NAV, NAV = $10,000,000 | USD | `conventions.to_usd` | test_conventions | ✅ |
| NAV path | Vₜ = V₀·Π(1+Rₛ) | USD or index | `conventions.wealth_index` | test_conventions | ✅ |
| Drawdown | DDₜ = Vₜ / maxₛ≤ₜ Vₛ − 1 | ≤ 0 | `conventions.drawdown` | test_conventions | ✅ |
| Annual return | (Π(1+Rₜ))^(252/n) − 1 | fraction p.a. | `conventions.annualised_return` | test_conventions | ✅ |
| Annual volatility | σ_d·√252 (volatility only; never used to scale VaR/ES) | fraction p.a. | `conventions.annualised_volatility` | test_conventions | ✅ |
| Daily risk-free | (1 + DTB3/100)^(1/252) − 1 | fraction/day | `fred.annual_pct_to_daily` | test_data_fred | ✅ |
| Excess return | Rₜ − r_f,ₜ (same date) | fraction | `conventions.excess_returns` | test_conventions | ✅ |
| Inflation YoY | CPIₘ / CPIₘ₋₁₂ − 1, used with a 1-month release lag | fraction | `fred.cpi_inflation` | test_data_fred | ✅ |
| TTM distribution yield | Σ distributions (ex-date in last 365 days) / unadjusted close | fraction p.a. | `income.ttm_distribution_yield` | test_data_income | ✅ |
| Data split (D5) | train ≤ 2014-12-31 < validation ≤ 2019-12-31 < test; `segment()` never returns later rows | label | `split.split_labels`, `split.segment` | test_data_split | ✅ |
| Expected inflation | FRED 10y breakeven (T10YIE) on the as-of date | fraction p.a. | `portfolio.run` | — | ✅ |

## Return objective & capital market assumptions (D12)
| Quantity | Formula | Units | Code | Test | Status |
|---|---|---|---|---|---|
| Required return | (1+I)(1+S)(1+G)(1+C) − 1 | fraction p.a. | `return_objective.required_return` | test_return_objective | ✅ |
| CAPM beta | Cov(monthly excess asset, excess SPY) / Var(excess SPY) (monthly: avoids non-synchronous bias) | — | `cma.capm_betas` | test_return_objective | ✅ |
| Equity risk premium (own data) | 12 × mean monthly (SPY − T-bill), 95% CI = ± 1.96·12·s/√n | fraction p.a. | `cma.equity_risk_premium` | test_return_objective | ✅ |
| CAPM expected return | r_f(as-of) + β·ERP | fraction p.a. | `cma.capm_expected` | test_return_objective | ✅ |
| Annual covariance Σ | daily simple-return covariance × 252 (monthly version reported only) | fraction² p.a. | `cma.annual_covariance` | test_return_objective | ✅ |
| Portfolio expected compound return | wᵀE[R] − ½·wᵀΣw − Σwᵢ·yieldᵢ·WHTᵢ (WHT per ETF, sensitivity) | fraction p.a. | `cma.portfolio_expected` | test_return_objective | ✅ |
| Shrunk covariance (T4.08) | Ledoit–Wolf on standardised returns: corrᵢⱼ ← (1−δ)·corrᵢⱼ, variances unchanged, × 252 | fraction² p.a. | `cma.shrunk_covariance` | test_cma_as_of | ✅ |
| Expected return used (D25) | CAPM for equity ETFs and GLD; AGG = its TTM distribution yield on the as-of date | fraction p.a. | `cma.expected_returns` | test_cma_as_of | ✅ |
| CMA as of a date | betas, covariance, rf and yields from data ≤ as-of only; train set = D5 train end, full set = last date; ERP = approved assumption | — | `cma.estimate_as_of` | test_cma_as_of | ✅ |
| Required return as of a date | same formula; inflation = breakeven on the as-of date, S/G/C = D12 policy; minimum uses G = 0 | fraction p.a. | `return_objective.required_return_as_of` | test_return_objective | ✅ |
| Return gap | required − expected compound (> 0 = shortfall) | fraction p.a. | `return_objective.feasibility` | test_return_objective | ✅ |
| Sustainable spending | S* = (1+E)/((1+I)(1+G)(1+C)) − 1 | fraction p.a. | `return_objective.sustainable_spending` | test_return_objective | ✅ |

## Candidate portfolios (T4, D20, D22) — `portfolio/optimise.py`, tests: test_optimise, integration
| Candidate | Problem | Status |
|---|---|---|
| Minimum variance | min wᵀΣw (Σ shrunk) | ✅ |
| Risk parity | Spinu: min ½yᵀΣy − Σ log y, w = y/Σy; then closest weights meeting D6 + D7 | ✅ |
| Max-Sharpe | homogenised: min yᵀΣy s.t. (μ−r_f)ᵀy = 1, constraints × κ; w = y/κ | ✅ |
| Min-CVaR | min CVaR99 (Rockafellar–Uryasev LP) s.t. expected ≥ hurdle; fallback min CVaR99 | ✅ |
| Target-return Markowitz | min wᵀΣw s.t. μᵀw − ½wᵀΣw ≥ hurdle; fallback (D12) lowest risk | ✅ |
| Frontier (T4.11) | 9 targets from min-variance to max expected return; each = min wᵀΣw s.t. expected ≥ target, D6 + D7 | ✅ |
| D7 5-year test | P(drawdown > 25% within 5 yrs) by moving-block bootstrap (63-day blocks, 4,000 paths, means = expected returns) ≤ 5%; post-check on every candidate and frontier point | ✅ |
| All candidates | D6 v2 weights; CVaR99 ≤ 2.5%; summed-return drawdown ≤ bound (CDaR β→1), bound bisected until compounded quarterly-rebalanced drawdown ≤ 25%; VaR/ES95 post-checked | ✅ |

## Portfolio stage (brief Layer 1)
| Quantity | Formula | Units | Status |
|---|---|---|---|
| Sharpe | (R̄_p − r̄_f)·252 / (σ_p·√252) | ratio | ✅ (`kpis.kpis`, test_kpis) |
| Sortino | annual excess return / annual downside deviation (MAR = r_f) | ratio | ✅ (`kpis.kpis`, test_kpis) |
| Treynor | annual excess return / β | fraction p.a. | ✅ (`kpis.kpis`, test_kpis) |
| Jensen's α | annual (R_p−r_f) − β·(R_m−r_f), regression intercept × 252 | fraction p.a. | ✅ (`kpis.kpis`, test_kpis) |
| Information ratio | annual mean(R_p−R_b) / tracking error, benchmark = D3 | ratio | ✅ (`kpis.kpis`, test_kpis) |
| Max drawdown | min DDₜ | fraction ≤ 0 | ✅ (`kpis.kpis`, test_kpis) |
| Calmar | annual return / abs(max drawdown) | ratio | ✅ (`kpis.kpis`, test_kpis) |

## Risk stage (brief Layers 2–4, §8.6)
All at α ∈ {90, 95, 99}%, 1-day horizon, on portfolio loss L, reported as % of NAV and USD, each with an uncertainty band (D18).
| Quantity | Formula / method | Status |
|---|---|---|
| Historical VaR | empirical α-quantile of L (`var_es.historical`) | ✅ |
| Parametric VaR | μ_L + σ·z_α (normal); m + s·t_α(ν) (Student-t, MLE) (`var_es.normal`, `student_t`) | ✅ |
| Monte Carlo VaR | α-quantile of 100k simulated L; t-copula (Kendall-τ correlation, ν by profile ML) + empirical marginals, seed 42 (`var_es.monte_carlo`) | ✅ |
| Expected Shortfall | E[L ∣ L ≥ VaR_α]; normal μ+σφ(z)/(1−α); t: m+s·(ν+t²)/(ν−1)·f(t)/(1−α) | ✅ |
| EVT VaR / ES | POT-GPD: VaR = u + β/ξ·[((n/Nᵤ)(1−α))^(−ξ) − 1]; ES = (VaR + β − ξu)/(1−ξ); n/a if α ≤ q (`evt_garch.evt_table`) | ✅ |
| GARCH(1,1)-t | σ²ₜ = ω + αε²ₜ₋₁ + βσ²ₜ₋₁; half-life ln0.5/ln(α+β); long-run σ = √(ω/(1−α−β)) (`evt_garch.fit_garch`, `garch_summary`) | ✅ |
| P(DD > 25% in 5 years) | Moving-block bootstrap (63-day blocks), each ETF's mean reset to its CMA expected return; 32,000 paths in batches of 4,000 (seed 7 + k, common random numbers); s.e. = √(p(1−p)/n) (`frontier.forward_drawdown_prob`, `mc_se`) | probability | `portfolio/frontier.py` | test_optimise | ✅ |
| Recovery path (D24) | NAVₜ = NAVₜ₋₁(1+gₜ)(1−costs−tax) − Sₜ; S₁ = rate·NAV₀, Sₜ = 0.7Sₜ₋₁(1+πₜ₋₁) + 0.3·rate·NAVₜ₋₁; real = nominal / Π(1+π); recovery gₜ = (1/(1−d))^(1/R) − 1 (`sustainability.d24_path`, `recovery_returns`) | NAV index | `validation/sustainability.py` | test_sustainability | ✅ |
| Market-view recovery | year return = w·B·f + carry, carry = μ_p − β_p,SPY·μ_SPY; f scaled to SPY = −d, reverting over R years (`sustainability.market_returns`) | fraction | `validation/sustainability.py` | test_sustainability | ✅ |
| Stress factor betas (D9 v2) | OLS monthly rᵢ on SPY, Δreal10, Δbreakeven10, ΔBaa spread (pp), Δln Brent, Δln USD; 2006-02 → data end; full + stress-month samples, SEs (`hypothetical.fit_betas`) | fraction per unit factor | `validation/hypothetical.py` | test_hypothetical | ✅ |
| Hypothetical scenario move | ΔRᵢ = Σ_f βᵢ,f·shock_f (no intercept; oil/USD % → log); portfolio = Σ wᵢ ΔRᵢ = Σ contributions (`hypothetical.instant`) | fraction (negative = loss) | `validation/hypothetical.py` | test_hypothetical | ✅ |
| Scenario path | monthly factor path = peak shock × profile; quarterly rebalance (D11), cost = 2 × one-way turnover × 10 bp × NAV (`hypothetical.path`) | NAV index | `validation/hypothetical.py` | test_hypothetical | ✅ |
| Next-year spending (D24) | 0.7 × last spending × (1 + π) + 0.3 × 4% × NAV (`hypothetical.next_year_spending`) | USD | `validation/hypothetical.py` | test_hypothetical | ✅ |
| Scenario 1-day VaR / ES | GARCH-EVT current VaR/ES × VIX_scenario / VIX_now (`hypothetical.scenario_var`) | fraction | `validation/hypothetical.py` | test_hypothetical | ✅ |
| GARCH-EVT | GPD on standardised losses −(r−μ)/σₜ; loss VaR = −μ + σ·VaR_ℓ (current and long-run σ) (`evt_garch.garch_evt`) | ✅ |
| Component VaR/ES | Euler: wᵢ·∂VaR/∂wᵢ ≈ E[−wᵢRᵢ ∣ L ≈ VaR] (band ±0.25 pp, rescaled); ES: E[−wᵢRᵢ ∣ L ≥ VaR] (exact sum); normal cross-check wᵢ(Σw)ᵢ/σ·z (`attribution.py`, test_attribution) | ✅ |

## Validation stage (brief Layer 5)
| Quantity | Formula | Status |
|---|---|---|
| Exception | Iₜ = 1{Lₜ > VaRₜ}, VaRₜ uses data up to t−1 only | ⏳ |
| Kupiec POF | LR = −2 ln[(1−p)^(n−x) pˣ / (1−x/n)^(n−x) (x/n)ˣ] ~ χ²(1) | ⏳ |
| Christoffersen independence | LR_ind from the 2×2 exception transition matrix ~ χ²(1); handle n₁₁ = 0 | ⏳ |
| Basel traffic light | 99% VaR, 250 days: green 0–4, yellow 5–9, red ≥ 10 exceptions | ⏳ |
