# P2: VaR and ES by Four Methods, and Why They Disagree (2026-10-29)

**Reproduce:** `python run_all.py --only risk` → `outputs/tables/p2_var_es.csv`, `p2_diagnostics.csv`.
**Setup:** 1-day loss on constant target weights (P1-final), full sample 2004-11 → 2026-10 (full cycle, D7). VaR and ES at 90/95/99% with 95% intervals (bootstrap; Monte Carlo batch standard error). NAV $10M.

## 1. D26 selected portfolio (AGG 55 / SPY 36 / XLK 7 / GLD 2) [E]
| Method | 95% VaR | 95% ES | **99% VaR** (95% interval) | **99% ES** (95% interval) | 99% in USD |
|---|---|---|---|---|---|
| Historical | 0.78% | 1.29% | **1.56%** (1.33–1.72) | **2.34%** (2.02–2.65) | $156k / $234k |
| Normal | 0.88% | 1.11% | 1.26% (1.18–1.35) | 1.44% (1.35–1.55) | $126k / $144k |
| Student-t (unconditional, ν = 2.2) | 0.75% | 1.53% | 1.77% (1.46–1.83) | 3.35% (2.32–3.52) | $177k / $335k |
| Monte Carlo (t-copula, empirical marginals, ν = 5) | 0.78% | 1.27% | 1.54% (±0.03) | 2.16% (±0.05) | $154k / $216k |

**D7 check:** historical VaR99 1.56% ≤ 1.7% and ES99 2.34% ≤ 2.5% ✅. But the 95% interval of VaR99 (1.33–1.72%) **reaches the limit**, so we cannot be fully confident the limit holds. This answers the brief's "how confident are you" (p.5).

All portfolios (99% VaR, ES in brackets, % NAV):

| Portfolio | Historical | Normal | Student-t | Monte Carlo |
|---|---|---|---|---|
| Min-Variance | 0.92 (1.48) | 0.80 (0.92) | 1.14 (2.22) | 0.90 (1.34) |
| Min-CVaR | 0.93 (1.46) | 0.81 (0.94) | 1.18 (2.30) | 0.92 (1.37) |
| Risk Parity | 1.36 (2.09) | 1.16 (1.34) | 1.31 (1.96) | 1.35 (1.89) |
| D26 selected | 1.56 (2.34) | 1.26 (1.44) | 1.77 (3.35) | 1.54 (2.16) |
| Max-Sharpe | 1.61 (2.41) | 1.30 (1.49) | 1.82 (3.45) | 1.58 (2.21) |
| Policy 40/50/10 | 1.51 (2.30) | 1.26 (1.45) | 1.82 (3.45) | 1.51 (2.16) |

## 2. Why the methods disagree (brief p.7, "where the three disagree and why")
1. **The normal model understates the crash tail and overstates ordinary bad days.** Returns are far from normal: excess kurtosis is 21–47 and Jarque–Bera rejects normality for every portfolio. Real losses have thin "shoulders" and fat tails. So normal VaR is too high at 95% (0.88% vs 0.78% observed) and too low at 99% (1.26% vs 1.56%). Its 99% ES (1.44%) misses about **$90k** of tail loss.
2. **The unconditional Student-t overshoots the tail.** Fitting one t-distribution to 22 years mixes calm and crisis periods. Volatility clustering (Ljung–Box on squared losses rejects independence everywhere) makes the combined data look extremely fat-tailed (ν ≈ 2.2), so the t's 99% ES (3.35%) is about 40% above what actually happened. This is why **GARCH** (time-varying volatility) and **EVT** (fitting the tail only) come next (T8).
3. **Historical and Monte Carlo agree** (1.56% vs 1.54%), because the copula Monte Carlo reuses each ETF's real return distribution. Its ES is a little lower (2.16% vs 2.34%) because the simulated joint tail is milder than 2008's actual combination. It cannot exceed each asset's worst historical day.
4. **A plain multivariate-t Monte Carlo was rejected** (finding during build). With ν ≈ 2, matching the sample covariance shrinks ordinary days and gave a 99% VaR of 0.54%, about 3× too low. The t-copula with empirical marginals (approved D19 option) fixes this.

## 3. Assumption diagnostics (D21, brief p.7) [E]
| Portfolio | Skew | Excess kurtosis | Normal rejected | Volatility clustering | t ν | Copula ν |
|---|---|---|---|---|---|---|
| D26 selected | −0.22 | 22.3 | yes | yes | 2.2 | 5 |
| Min-Variance | +0.65 | 46.5 | yes | yes | 2.1 | 5 |
| Risk Parity | −0.04 | 20.8 | yes | yes | 3.3 | 5 |

Bond-heavy portfolios (Min-Variance) have positive skew and the most extreme kurtosis: calm days are very calm, so the rare big moves stand out more.

## 4. Implications
- **For the committee:** report historical (or Monte Carlo) VaR/ES as primary, with intervals. Show normal as the "textbook" number that understates crash risk.
- **ES vs VaR (brief Layer 3):** at 99% the average loss beyond VaR is 1.5× the VaR itself ($234k vs $156k for D26). VaR alone would hide a third of the loss on the worst days.
- **Next (T8):** GARCH-filtered and EVT tail estimates, then component VaR/ES (T9) to set the risk-contribution cap. Backtests (T10) will test which method's forecasts hold up out of sample.
- **Convention note:** these use constant target weights, the standard for risk forecasts. The D7 checks in P1 use quarterly-rebalanced NAV, so the figures differ slightly (D26 ES99 2.34% vs 2.25%).

## 5. GARCH and EVT (T8, D8) [E]
**Reproduce:** risk stage → `p2_evt.csv`, `p2_garch_evt.csv`, `p2_evt_thresholds.csv`, `p2_garch.csv`, `outputs/figures/evt_threshold_d26.png`.

**GARCH(1,1)-t (full sample):** persistence 0.990–0.992 for every portfolio. A volatility shock fades with a half-life of 68–85 days. For D26, today's (2026-10-19) forecast volatility is **6.4% a year** against a long-run average of **10.3%**, so the market is in a calm regime now.

**EVT threshold (chosen on 2004–2019 only, D5/D8):**
- **Rule:** among thresholds with at least 150 exceedances and below the 95th percentile (so EVT applies at the 95/99% reporting levels), take the lowest one whose tail shape ξ is stable at all higher thresholds.
- **Result:** q = 90% for every portfolio (381 exceedances).
- **Evidence (figure):** ξ ≈ 0.18–0.24 from the 90th to the 96th percentile; above 96% it is noise (115 exceedances or fewer, very wide intervals).
- **Raw-loss tail:** ξ = 0.18–0.32, a genuinely fat (power-law) tail. After GARCH filtering, ξ ≈ 0.00–0.11, an almost exponential tail. Most of the fat tail comes from volatility clustering (the McNeil–Frey result).

**D26 portfolio, 1 day (% NAV):**

| Method | 95% VaR / ES | 99% VaR / ES | 99.5% VaR / ES |
|---|---|---|---|
| Historical | 0.78 / 1.29 | 1.56 / 2.34 | — |
| **EVT (POT-GPD), interval** | 0.78 / 1.30 | **1.55 (1.44–1.68) / 2.34 (2.06–2.72)** | 1.99 / 2.94 |
| GARCH-EVT, **today's calm regime** | 0.65 / 0.94 | **1.11 / 1.40** | 1.31 / 1.61 |
| GARCH-EVT, long-run average regime | 1.08 / 1.54 | 1.81 / 2.29 | 2.14 / 2.62 |
| Normal (for contrast) | 0.88 / 1.11 | 1.26 / 1.44 | — |

90%: EVT is not applicable (at the threshold quantile; D8 rule). The app will show "n/a".

**What it means:**
1. **EVT confirms the historical tail at 99%** (1.55% vs 1.56%) and extends it beyond the data: at 99.5% the expected loss on the worst days is 2.9% (**$294k**). That is the "how bad could it get" number history alone cannot give reliably.
2. **Risk depends on the regime.** Today's calm market gives a 99% VaR of only 1.11%. A committee shown only today's number would be lulled; in a long-run average regime it is 1.81%, above the 1.7% D7 VaR limit. **D7 limits are therefore checked on full-cycle (unconditional) estimates, as approved, and the GARCH figure is a monitoring signal.**
3. GARCH-EVT is the strongest candidate for out-of-sample backtesting (T10), because it reacts to volatility clustering. Christoffersen's test is designed to catch exactly that clustering.
4. **Not done here (moved to T10):** evaluating each model on stress windows (T8.11) needs rolling out-of-sample forecasts, which the backtesting stage builds.
