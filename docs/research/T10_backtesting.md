# T10 Out-of-sample VaR / ES backtesting [E]

**Reproduce:** `python run_all.py --only validation` → `backtest_forecasts_validation.csv`, `backtest_results_validation.csv`, `backtest_window_sensitivity.csv`.

## 1. Design
- **No look-ahead:** the forecast for day t uses days t−1000 … t−1 (D13), re-estimated daily. GARCH parameters and the Monte Carlo copula are refitted every 21 days; GARCH σ is updated daily by its recursion with returns up to t−1. Unit test: changing future returns leaves earlier forecasts identical.
- **Weights:** P1-train weights (chosen with data ≤ 2014), so nothing is fitted on the evaluation years. Fixed target weights, as in the risk stage.
- **Methods (7):** historical, normal, Student-t, EVT (POT, q = 0.90), GARCH-t, GARCH-EVT (McNeil–Frey), Monte Carlo t-copula (20k scenarios per refit).
- **Portfolios (6):** D26 selected, min-variance, min-CVaR, risk parity, max-Sharpe, Policy 40/50/10.
- **Tests:** Kupiec (frequency), Christoffersen independence and conditional coverage (n₁₁ = 0 handled), Basel traffic light (99%, every 250-day window), ES severity ratio and Acerbi–Szekely Z2, scores: quantile loss and FZ0 (joint VaR/ES).
- **Integrity gate:** only the validation period (2015–2019, 1,258 days) has been run. The test period (2020 →) is locked in code until the selection rule (D28) is approved and the chosen model is frozen in config.

## 2. Validation results, D26 selected portfolio, 99% 1-day

| Method | Exceptions (exp. 12.6) | Kupiec p | Christoffersen ind. p | Cond. cov. p | Worst Basel window | ES severity | FZ0 (lower better) |
|---|---|---|---|---|---|---|---|
| **GARCH-EVT** | **13** | **0.91** | 0.006 | 0.022 | 7 (yellow) | **1.08** | **−4.692** |
| GARCH-t | 20 | 0.053 | 0.038 | 0.018 | 7 (yellow) | 1.03 | −4.690 |
| EVT | 14 | 0.69 | 0.008 | 0.027 | 7 (yellow) | 1.02 | −4.597 |
| Historical | 14 | 0.69 | 0.008 | 0.027 | 7 (yellow) | 1.01 | −4.580 |
| Monte Carlo | 15 | 0.51 | 0.011 | 0.031 | 7 (yellow) | 1.06 | −4.570 |
| Normal | 26 | 0.001 | 0.11 | 0.001 | **10 (red)** | 1.14 | −4.479 |
| Student-t | 5 | 0.015 | 0.84 | 0.049 | 2 (green) | 0.60 | −4.369 |

At 95%, the same five models pass Kupiec (p 0.44–0.91).

**Reading:**
1. **Normal fails:** twice the expected exceptions, a red Basel window, and losses on exception days 14% beyond its ES. Fat tails matter.
2. **Student-t (unfiltered) is too conservative:** 5 exceptions against 12.6 expected (Kupiec fails), average VaR 1.08% vs about 0.71–0.76% for the others. It would overstate risk and constrain the portfolio for no reason.
3. **Every frequency-correct model fails Christoffersen independence at 99%.** The exceptions cluster in single episodes: 20–24 Aug 2015 (China devaluation), early Feb 2018 (volatility spike), Oct 2018. With about 13 exceptions in 5 years, one 3-day cluster is enough to reject. GARCH reacts only after the first shock day, so it reduces but cannot remove this.
4. **GARCH-EVT is the best overall:** the most accurate exception count (13 vs 12.6), ES within 8%, and the best joint VaR/ES score.
5. **Window (T10.09):** 1,000 days beats 500 for every method on FZ0; for GARCH-EVT, 500 days gives 15 exceptions and p_cc 0.002. D13 (1,000) confirmed.

## 3. Selection rule (D28, APPROVED 2026-10-29)
On validation data only, for the D26 portfolio:
1. **Gate:** Kupiec p ≥ 0.05 at 99% and at 95%, and no red Basel window.
2. **Rank:** lowest FZ0 score at 99% (a strictly consistent score for VaR and ES together).
3. **Report, do not gate:** Christoffersen. No frequency-correct model passes it here (point 3), so gating on it would leave only a model that fails the frequency test.

**Result:** eligible = GARCH-EVT, GARCH-t, EVT, historical, Monte Carlo → **GARCH-EVT selected**. It is then frozen and run once on the 2020–2026 test period.

## 4. Test period 2020-01-02 → 2026-10-19 (run once, after the freeze; commit 60e67e3)
**Reproduce:** `python run_all.py --only validation` (validation.test_unlocked: true) → `backtest_forecasts_test.csv`, `backtest_results_test.csv`.

**D26 selected portfolio, 99% 1-day (1,708 days, 17.1 exceptions expected):**

| Method | Exceptions | Kupiec p | Christoffersen ind. p | Cond. cov. p | Worst Basel window | Red windows | ES severity | FZ0 |
|---|---|---|---|---|---|---|---|---|
| **GARCH-EVT (selected)** | **22** | **0.25** | **0.29** | **0.29** | **8 (yellow)** | **0%** | **1.06** | **−4.08** |
| GARCH-t | 32 | 0.001 | 0.63 | 0.005 | 9 | 0% | 1.08 | −4.01 |
| Student-t | 16 | 0.79 | 0.14 | 0.32 | 8 | 0% | 1.04 | −3.66 |
| EVT | 19 | 0.65 | 0.21 | 0.40 | 9 | 0% | 1.20 | −3.52 |
| Historical | 26 | 0.044 | 0.06 | 0.023 | **11 (red)** | 3% | 0.95 | −3.53 |
| Monte Carlo | 23 | 0.17 | 0.037 | 0.045 | **10 (red)** | 2% | 1.32 | −3.30 |
| Normal | 30 | 0.005 | 0.002 | 0.0001 | **13 (red)** | 3% | 1.53 | −3.07 |

At 95%: GARCH-EVT 95 exceptions vs 85.4 expected (Kupiec p 0.29, cond. cov. p 0.48); historical, EVT, Monte Carlo and Student-t all fail at 95% (p_cc ≤ 0.0001).

**Stress windows (T8.11, R18), D26, 99%:**

| Window | Days | Expected | GARCH-EVT | Historical |
|---|---|---|---|---|
| COVID crash (19 Feb – 30 Apr 2020) | 51 | 0.5 | 4 | 8 |
| 2022 rate shock (Jan – Oct 2022) | 209 | 2.1 | 3 | 8 |

**GARCH-EVT across all portfolios (test, 99%):** passes Kupiec and conditional coverage for D26, max-Sharpe, min-variance, risk parity (cc p 0.054) and the Policy 40/50/10 benchmark; min-CVaR is borderline (26 exceptions, p_uc 0.044). No portfolio has a red Basel window under GARCH-EVT except min-CVaR (13 at worst).

**Conclusions:**
1. **The validation choice held out of sample.** GARCH-EVT passes every test at 99% and 95% in 2020–2026, including Christoffersen, and has the best joint VaR/ES score. The selection was not tuned to the test data.
2. **Static models break in regime changes.** Historical simulation lagged in COVID (8 exceptions in 51 days) and 2022 (8 in 209) and reached the Basel red zone. GARCH-EVT halved the stress-window exceptions because its σ rises within days.
3. **Losses on exception days were 6% beyond the GARCH-EVT ES forecast** (severity 1.06), close to the 1.0 target. The normal model's ES was 53% too low.
4. **Still not perfect:** 22 exceptions against 17.1 expected (not statistically significant), and the first day of a shock is still missed (e.g. 24 Feb 2020, 3–4 Apr 2025). This is why D7 limits are set on full-cycle history and the D23 action ladder reacts to drawdowns, not to VaR alone.
5. **Monitoring model:** GARCH-EVT is the VaR model for the memo, the app's backtest page and the D23 watch triggers; historical and EVT stay as full-cycle limit checks (D7).
