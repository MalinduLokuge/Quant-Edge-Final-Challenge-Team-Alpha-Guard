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
| Portfolio expected compound return | wᵀE[R] − ½·wᵀΣw − Σwᵢ·yieldᵢ·WHT | fraction p.a. | `cma.portfolio_expected` | test_return_objective | ✅ |
| Return gap | required − expected compound (> 0 = shortfall) | fraction p.a. | `return_objective.feasibility` | test_return_objective | ✅ |
| Sustainable spending | S* = (1+E)/((1+I)(1+G)(1+C)) − 1 | fraction p.a. | `return_objective.sustainable_spending` | test_return_objective | ✅ |

## Portfolio stage (brief Layer 1)
| Quantity | Formula | Units | Status |
|---|---|---|---|
| Sharpe | (R̄_p − r̄_f)·252 / (σ_p·√252) | ratio | ⏳ |
| Sortino | annual excess return / annual downside deviation (MAR = r_f) | ratio | ⏳ |
| Treynor | annual excess return / β | fraction p.a. | ⏳ |
| Jensen's α | annual (R_p−r_f) − β·(R_m−r_f), regression intercept × 252 | fraction p.a. | ⏳ |
| Information ratio | annual mean(R_p−R_b) / tracking error, benchmark = D3 | ratio | ⏳ |
| Max drawdown | min DDₜ | fraction ≤ 0 | ⏳ |
| Calmar | annual return / abs(max drawdown) | ratio | ⏳ |

## Risk stage (brief Layers 2–4, §8.6)
All at α ∈ {90, 95, 99}%, 1-day horizon, on portfolio loss L, reported as % of NAV and USD, each with an uncertainty band (D18).
| Quantity | Formula / method | Status |
|---|---|---|
| Historical VaR | empirical α-quantile of L | ⏳ |
| Parametric VaR | μ_L + σ·q_α (normal, plus Student-t variant) | ⏳ |
| Monte Carlo VaR | α-quantile of simulated L, multivariate t / t-copula, fixed seed (D19) | ⏳ |
| Expected Shortfall | E[L ∣ L ≥ VaR_α] | ⏳ |
| EVT VaR / ES | POT-GPD: VaR = u + β/ξ·[((n/Nᵤ)(1−α))^(−ξ) − 1]; ES = (VaR + β − ξu)/(1−ξ) | ⏳ |
| Component VaR/ES | Euler: wᵢ·∂VaR/∂wᵢ ≈ E[−wᵢRᵢ ∣ L ≈ VaR]; ES: E[−wᵢRᵢ ∣ L ≥ VaR]; sums to the total | ⏳ |

## Validation stage (brief Layer 5)
| Quantity | Formula | Status |
|---|---|---|
| Exception | Iₜ = 1{Lₜ > VaRₜ}, VaRₜ uses data up to t−1 only | ⏳ |
| Kupiec POF | LR = −2 ln[(1−p)^(n−x) pˣ / (1−x/n)^(n−x) (x/n)ˣ] ~ χ²(1) | ⏳ |
| Christoffersen independence | LR_ind from the 2×2 exception transition matrix ~ χ²(1); handle n₁₁ = 0 | ⏳ |
| Basel traffic light | 99% VaR, 250 days: green 0–4, yellow 5–9, red ≥ 10 exceptions | ⏳ |
