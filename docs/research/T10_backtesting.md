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

## 3. Proposed selection rule (D28, awaiting approval)
On validation data only, for the D26 portfolio:
1. **Gate:** Kupiec p ≥ 0.05 at 99% and at 95%, and no red Basel window.
2. **Rank:** lowest FZ0 score at 99% (a strictly consistent score for VaR and ES together).
3. **Report, do not gate:** Christoffersen. No frequency-correct model passes it here (point 3), so gating on it would leave only a model that fails the frequency test.

**Result:** eligible = GARCH-EVT, GARCH-t, EVT, historical, Monte Carlo → **GARCH-EVT selected**. It is then frozen and run once on the 2020–2026 test period.
