# V2 Regime-dependent Historical / EVT VaR-ES blend (INNOVATION_LOG I13) [E]

**Reproduce:** `python scripts/research_v2_regime_blend.py` → `outputs/tables/research_v2_regime_blend_*.csv`, `outputs/figures/research_v2_regime_*.png` (about 15 min; `--reuse` re-scores the saved daily table without refitting).

**Research question:** does classifying each day as calm or elevated volatility, and shifting the Historical / EVT mix accordingly (Team Guide §8), improve out-of-sample 1-day VaR / ES forecasts beyond the selected GARCH-EVT model (D28)?

This is a risk-measurement experiment. O6 weights, D24 spending at 2.65%, D6 / D7 / D23 / D27 limits and the approved outputs are not changed. A better VaR forecast improves the information the committee receives. It does not by itself change O6's returns, Sharpe ratio or drawdown, because no trade changes.

---

## Part A — Pre-registration (written and committed before any blend result was computed)

### A1. Audit of what exists (version-3 = version-2 at 1f6ae25)

| Item | Finding | Source |
|---|---|---|
| Methods | 7 rolling methods: historical, normal, student_t, evt, garch_t, garch_evt, monte_carlo | `validation/backtest.py:21` |
| Historical | Empirical α-quantile of the last 1,000 losses; ES = mean of losses ≥ VaR; re-estimated daily | `risk/var_es.py:19`, D13 |
| EVT | POT on the same 1,000 losses, threshold u = 90th percentile (D8), GPD MLE (location 0), refitted daily; McNeil–Frey tail formula | `backtest.py:94–106`, `evt_garch.py:21–34` |
| GARCH-EVT | GARCH(1,1)-t on the 1,000-day window, refitted every 21 days, σ updated daily by the recursion with returns ≤ t−1; GPD on standardised residuals at q = 0.90 | `backtest.py:31–54` |
| Conventions | Portfolio return = Σ wᵢ·simple rᵢ with fixed weights, loss = −return, 1-day horizon, α = 95% and 99% | D17, `settings.yaml` |
| Periods | Validation 2015-01-02 → 2019-12-31 (model selection, D28); test 2020-01-02 → 2026-10-19 (run once after the D28 freeze) | D5, D28 |
| Regime switching | **None in the code.** "Regime" appears only as GARCH current vs long-run σ (`evt_garch.py:113`), crisis vs calm correlations in the stress tests, and VIX scaling of hypothetical VaR. None of these switches estimation methods | grep of `src/`, `scripts/`, `app/` |
| Tracker conflict | SUBTASKS T13.03 and QA audit say "regime VaR built"; INNOVATION_LOG I13 says "Candidate"; DECISIONS item 12 PROPOSED. The code agrees with I13 | `SUBTASKS.md:255`, `QA_AUDIT_2026-10-30.md:142` |
| Stale numbers | T10 doc tables (D26-train GARCH-EVT 13 validation / 22 test exceptions) differ from the committed CSVs (14 / 20). Diagnosed in B1 | `T10_backtesting.md` §2, §4 |
| Test-period exposure | The 2020–26 results of historical, EVT and GARCH-EVT have already been seen by the team (T10 §4) and in the conversation that proposed this experiment. The test period is **not** a blind holdout for this question | — |
| Team Guide | Section 8 (pp.5–6): optional two-regime blend, 20-day volatility vs longer-term volatility, Historical 70 / EVT 30 calm and 30 / 70 crisis, as illustrative weights to be tested with Kupiec, Christoffersen and Basel against the single methods. (PDF text could not be extracted in this environment; content as verified by the team) | `QuantEdge_Team_Guide.pdf` |
| Masterclass | Slide 70: "When four risk models disagree, do not simply average"; slides 73–78: start from a baseline, value after costs, avoid leakage and selection on test data, walk-forward validation | `docs/references/presentations/` |

### A2. Portfolios (weights loaded from files, never retyped)

| Name | Weights | Role | Caveat |
|---|---|---|---|
| **O6** | `p1_final_weights.csv` → `d26_selected` (AGG 61.0 / SPY 18.4 / XLK 10.0 / EFA 7.2 / XLE 3.0 / GLD 0.4) | Primary: the approved portfolio | Weights were estimated on data to 2026, so absolute coverage in earlier years is partly in-sample. Every model forecasts the same O6 series, so the model comparison stays paired and fair |
| **D26-train** | `p1_train_weights.csv` → `d26_selected` | The approved T10 backtest portfolio (weights from data ≤ 2014); baseline reproduction check | — |
| **Policy 40/50/10** | `settings.yaml` benchmark | Fixed weights set in advance (D3): no look-ahead at all | — |

### A3. Models compared (identical target, date, horizon, window, confidence, loss sign)

All component forecasts come from one call of `validation.backtest.rolling_forecasts` with the pipeline's settings (window 1,000, refit 21, EVT q 0.90, seed 42). The blend reuses the historical and EVT numbers from that call. Nothing is refitted separately for it.

| Model | Definition |
|---|---|
| historical, evt, garch_t, garch_evt | Existing methods, unchanged |
| **regime (primary, pre-registered)** | ratio_t = sd(r_{t−20..t−1}) / sd(r_{t−252..t−1}) on the portfolio's own returns; elevated if ratio > 1.00, else calm; w_hist = 0.70 calm, 0.30 elevated; VaR = w·VaR_hist + (1−w)·VaR_evt, ES likewise |
| static 50/50 (control) | w_hist = 0.50 every day: separates the effect of mixing from the effect of switching |
| oracle envelope (bound, not a forecast) | max(VaR_hist, VaR_evt): no blend with weights in [0, 1] can be higher, so its exceptions are a floor for every possible weighting |

**Why the 252-day denominator:** it is the user's specification and a standard "one-year" reference. **Pre-declared alternative:** a 1,000-day denominator, which equals the D13 window that Historical and EVT are estimated on. That ratio measures directly whether today's volatility is above the volatility embedded in the Historical/EVT window, which is when those two methods are mis-scaled.

**Prior expectation, stated before the run:** Historical and EVT are both unconditional estimates from the same 1,000 losses, so their VaRs are close (validation: 14 and 13 exceptions) and react slowly. A blend lies between them. It can move VaR only by the Historical–EVT gap, while GARCH σ can double within weeks. We therefore expect the blend to sit between Historical and EVT and to stay behind GARCH-EVT. The experiment tests this. It does not assume it.

### A4. Sensitivity grid (fixed now; small on purpose)

- Denominator L ∈ {252 (primary), 1,000}
- Threshold c ∈ {0.85, 1.00 (primary), 1.15}
- Weights (w_hist calm / elevated) ∈ {0.70 / 0.30 (primary), 1.00 / 0.00 (hard switch)}

That gives 12 variants. **Selection** among them uses the D28 rule on the **validation period only, O6**: gate = Kupiec p ≥ 0.05 at 95% and 99% plus no red Basel window; rank = lowest FZ0 at 99%. If no variant passes the gate, the primary is kept. The selected variant is reported on the test period as "validation-selected"; the other test-period sensitivity results are labelled post-hoc. GARCH-EVT went through the same D28 rule on the same period, so both models get the same tuning opportunity.

### A5. Evaluation (same framework as T10)

- **Periods:** early 2008-11 → 2014-12 (first day with 1,000 days of history; daily forecasts out-of-sample, but D8 and the D26-train weights used these years), validation 2015–19, test 2020-01-02 → 2026-10-19, plus calendar-year walk-forward.
- **Tests:** exceptions vs expected, Kupiec, Christoffersen independence and conditional coverage, Basel traffic light (99% only, rolling 250-day windows, existing `coverage.basel`), ES severity ratio, Acerbi–Szekely Z2, quantile (tick) loss, FZ0 joint VaR/ES score (Patton–Ziegel–Chen). All from `validation/coverage.py`.
- **Paired uncertainty:** daily score differences (model − GARCH-EVT) on identical dates; moving-block bootstrap, 63-day blocks, 5,000 resamples, seed 42; 95% interval of the mean difference.
- **Stress windows (fixed now):** GFC tail first forecast → 2009-03-09; COVID 2020-02-19 → 2020-04-30 (as T10); rates 2022-01-03 → 2022-10-12 (settings window); tariff shock 2025-04-01 → 2025-05-30.
- **Regime diagnostics:** share of days per state, transitions, mean run length, detection delay after fixed shock dates (2011-08-04, 2015-08-20, 2018-02-02, 2018-10-10, 2020-02-24, 2022-01-03, 2025-04-03), day-to-day VaR jumps, exceptions by state.
- **Decision relevance:** days with VaR99 above the D7 1.7% limit, worst Basel window (the D23 'review' / 'limit' signal).

### A6. Adoption rule (fixed now)

Primary comparison: regime (primary) vs GARCH-EVT, O6, 99%, test period. The validation-selected variant must pass the same rule.

**Recommend to the committee for review** (not automatic integration) only if all hold:
1. **Coverage:** Kupiec p ≥ 0.05 at 95% and 99%, and no red Basel window, in both validation and test.
2. **Independence:** Christoffersen independence p ≥ 0.05 at 99% in the test period, or not lower than GARCH-EVT's.
3. **Score:** mean FZ0 at 99% below GARCH-EVT's with the 95% paired-bootstrap interval of the difference entirely below 0 in the test period, and the same sign in validation and the early period.
4. **Not one episode:** the sign holds with the COVID window removed, and in at least half of the calendar years.
5. **Stable:** the sign holds for all three thresholds with the primary weights.
6. **Decision value:** it changes a monitoring read (D7 limit days or Basel zone) in a direction the backtest supports.
7. **Reproducible:** baseline reproduction exact; tests pass.

**Otherwise:** worse score (interval entirely above 0) or a failed coverage gate → **reject, keep GARCH-EVT**. Interval spanning 0 → **no evidence of improvement; keep the simpler, validated GARCH-EVT**. Mixed results → **inconclusive / limited value**. No minimum improvement size is set: an arbitrary size threshold was criticised in the D31 audit, so the rule uses the paired interval and sign consistency instead.

**Secondary question (reported only, no decision):** is the blend a better full-cycle limit check than Historical (the D7 role of Historical and EVT, T10 §4 conclusion 5)?

O6, D24 and the D7 limits are not reopened by any outcome of this experiment.
