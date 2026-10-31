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

---

## Part B — Results (run 2026-10-31 on commit 0460495 plus a column-name fix in the script; seeds and versions in `research_v2_regime_blend_runinfo.csv`)

### B1. Baseline reproduction (checked before any blend number was read)
- **16 / 16 exact.** Historical, EVT, GARCH-t and GARCH-EVT for D26-train, 95% and 99%, validation and test, recomputed by the research script, equal the approved `backtest_forecasts_<period>.csv` (max |ΔVaR|, |ΔES| < 1e-10, same dates, same exception counts). See `research_v2_regime_blend_reproduction.csv`.
- **Reference checkpoints:** the D26-train test figures quoted when this experiment was proposed (historical 26 / EVT 20 / GARCH-EVT 20 exceptions; Kupiec 0.04 / 0.49 / 0.49; independence 0.06 / 0.02 / 0.49) reproduce exactly. They are D26-train, not O6. On O6, GARCH-EVT has 24 test exceptions (O6 holds more equity: SPY 18.4% vs 7.9%).
- **Stale T10 doc:** T10 §2 and §4 report D26-train GARCH-EVT 13 (validation) and 22 (test) exceptions; the committed CSVs give 14 and 20. Cause: D32 (commit b9bc407) changed the D26 rule's 5-year drawdown test from 63- to 126-day blocks. That re-selected the p1_train D26 weights, and the backtest CSVs were regenerated but the T10 tables were not. On the regenerated validation results D28 still selects GARCH-EVT (FZ0 −4.747 vs GARCH-t −4.735; Kupiec p 0.69). A dated note was added to T10 §4; its numbers were not rewritten.

### B2. Main comparison: O6, 99%, 1-day
All models are scored on identical dates. ES is finite and ≥ VaR on every day for every model.

| Model | Period | Exceptions (expected) | Kupiec p | Independence p | Worst Basel window | ES severity | FZ0 (lower better) | Verdict |
|---|---|---|---|---|---|---|---|---|
| **GARCH-EVT** | test | 24 (17.1) | 0.11 | 0.35 | 8 yellow | 0.97 | **−3.963** | pass |
| GARCH-t | test | 29 (17.1) | 0.008 | 0.52 | 8 yellow | 1.07 | −3.893 | fails Kupiec |
| Historical | test | 25 (17.1) | 0.07 | 0.0003 | 13 **red** | 0.99 | −3.390 | fails independence, red |
| EVT | test | 19 (17.1) | 0.65 | 0.0008 | 11 **red** | 1.24 | −3.391 | fails independence, red |
| Static 50/50 (control) | test | 22 (17.1) | 0.25 | 0.002 | 12 **red** | 1.10 | −3.394 | fails independence, red |
| **Regime (primary)** | test | 22 (17.1) | 0.25 | **0.002** | 12 **red** | 1.10 | **−3.398** | fails independence, red |
| Regime (validation-selected) | test | 22 (17.1) | 0.25 | 0.002 | 13 **red** | 1.10 | −3.397 | fails independence, red |
| Oracle envelope (bound) | test | 19 (17.1) | 0.65 | 0.0008 | 11 red | 1.22 | −3.395 | not a forecast |
| GARCH-EVT | validation | 17 (12.6) | 0.23 | 0.019 | 6 yellow | 1.00 | **−4.511** | fails independence |
| Regime (primary) | validation | 14 (12.6) | 0.69 | 0.008 | 7 yellow | 1.06 | −4.342 | fails independence |
| GARCH-EVT | early | 10 (15.5) | 0.14 | 0.72 | 3 green | 1.02 | **−4.415** | pass |
| Regime (primary) | early | 8 (15.5) | 0.04 | 0.03 | 6 yellow | 0.73 | −3.930 | fails Kupiec, independence |

At 95%, test period:
- GARCH-EVT: 92 exceptions vs 85.4 expected; Kupiec 0.47, independence 0.63, FZ0 −4.441.
- Regime: 94 exceptions; Kupiec 0.35, independence **0.002**, FZ0 −4.156.
- Historical: 93 exceptions; Kupiec 0.41, independence 0.005.

In every period and at both levels the regime blend scores within ±0.01 FZ0 of Historical, EVT and the static 50/50 mix. It is 0.16–0.49 worse than GARCH-EVT.

**Other portfolios (test, 99%):**
- D26-train: regime 24 exceptions, independence p 0.045, worst Basel window 11 (red), FZ0 −3.548. GARCH-EVT: 20, 0.49, 7, −4.117.
- Policy 40/50/10: regime 22, 0.002, 11 (red), −3.405. GARCH-EVT: 24, 0.35, 8, −3.884.

The conclusion is the same on all three portfolios.

### B3. Paired score differences
Regime (primary) minus GARCH-EVT, O6. Intervals come from a 63-day moving-block bootstrap with 5,000 resamples.

| Period | 99% FZ0 difference [95% interval] | 95% FZ0 difference [95% interval] |
|---|---|---|
| Early 2008-11 → 2014 | +0.485 [+0.311, +0.611] | +0.301 [+0.159, +0.373] |
| Validation 2015–19 | +0.169 [+0.007, +0.349] | +0.162 [+0.087, +0.246] |
| Test 2020–26 | +0.565 [−0.003, +1.504] | +0.286 [+0.019, +0.706] |
| Test without COVID (19 Feb – 30 Apr 2020) | +0.093 | +0.071 |

- Positive means worse than GARCH-EVT. Five of the six intervals lie entirely above 0.
- The test 99% interval is wide and touches 0 because most of the gap comes from the COVID weeks. Resamples that miss those weeks show a small gap. Without COVID the blend is still worse.
- Against Historical, the regime blend's 99% FZ0 differences are +0.003 (early), +0.004 (validation) and −0.008 (test). Every interval spans 0, so the switch adds nothing measurable to Historical either.

### B4. Why the blend cannot work here (mechanism, confirmed by the data)
1. **The lever is too small.** Historical and EVT are fitted on the same 1,000 losses, so a blend can only move between them.
   - On 95% of days the gap |EVT − Historical| / Historical is below 15%.
   - GARCH-EVT's VaR ranges from 0.58× to 2.38× its median.
   - In the COVID weeks the blend's mean 99% VaR was 1.25% of NAV, against 4.37% for GARCH-EVT. The blend had 10 exceptions against 0.5 expected; GARCH-EVT had 4.
2. **The oracle bound settles the question.** On every day, max(Historical, EVT) is the most conservative forecast any weighting can produce. In the test period it still has a red worst Basel window (11), independence p 0.0008 and FZ0 −3.395. No choice of weights or threshold in [0, 1] can reach GARCH-EVT.
3. **The switch can point the wrong way.** When the 1,000-day window still contains an old crisis, the EVT tail can sit below the empirical quantile. On elevated days EVT was below Historical 57% of the time in 2008–14, 56% in 2015–19 and 2% in 2020–26. On those days shifting weight to EVT *lowered* VaR just as volatility rose (visible in 2010 and 2011 in `research_v2_regime_timeline.png`).
4. **Detection is not the problem.** The 20/252 classifier flagged these episodes on day 0: COVID (24 Feb 2020), the 2022 rate shock, the 2025 tariff shock, the 2011 downgrade and the Feb 2018 spike. It flagged the 2015 and Q4 2018 sell-offs within 1–2 days. The 1,000-day reference was slower (2022: 28 days). The state was right; the response was too small.

### B5. Stress windows (O6, 99%, fixed in A5)

| Window | Days | Expected | Share elevated | Historical | EVT | **GARCH-EVT** | Regime | Mean VaR: regime / GARCH-EVT |
|---|---|---|---|---|---|---|---|---|
| GFC tail 2008-11-10 → 2009-03-09 | 81 | 0.8 | 38% | 5 | 6 | **1** | 6 | 2.05% / 3.35% |
| COVID 2020-02-19 → 04-30 | 51 | 0.5 | 96% | 10 | 10 | **4** | 10 | 1.25% / 4.37% |
| Rates 2022-01-03 → 10-12 | 196 | 2.0 | 93% | 6 | 3 | **3** | 4 | 1.68% / 2.11% |
| Tariffs 2025-04-01 → 05-30 | 42 | 0.4 | 69% | 3 | 3 | **2** | 3 | 1.42% / 2.35% |

The samples are small (0.4–2 expected exceptions per window), so read the direction, not the decimals. In 2022 the blend beat Historical (4 vs 6) and matched EVT, but not GARCH-EVT.

### B6. Regime diagnostics (O6, primary rule)
- **States:** the elevated share is 27% (early), 36% (validation) and 36% (test). There are 40–44 switches per period. Mean runs last 37–56 days when calm and 20–28 days when elevated.
- **Stability:** daily VaR changes stay small. The 99th percentile is 3.8% of VaR, against 3.5% for Historical and 53% for GARCH-EVT, so switching does not create unstable jumps. The hard-switch variant reaches 9.5%.
- **Exceptions by state, test 99%:**
  - Calm days (11.0 expected): GARCH-EVT 14, regime 4, Historical 5.
  - Elevated days (6.1 expected): GARCH-EVT 10, regime 18, Historical 20.
  - The blend is too conservative when calm and far too low when volatile; this is the clustering Christoffersen detects. GARCH-EVT's errors are spread across both states.
- **A finding about GARCH-EVT itself:** it has more exceptions than expected on calm days in every period (validation 14 vs 8.1, test 14 vs 11.0). σ shrinks in long calm stretches, and the first day of a shock is missed (T10 §4 point 4). This is disclosed, not acted on; it does not change the D28 choice.

### B7. Sensitivity and selection
- All 12 pre-declared variants passed the validation gate.
- The D28 rule selected L = 1,000, c = 0.85, hard switch (validation FZ0 −4.3462 vs −4.3419 for the primary).
- At 99%, every variant is worse than GARCH-EVT: by 0.561–0.571 FZ0 in the test period, 0.165–0.174 in validation and 0.484–0.503 in the early period.
- The spread across variants (≈ 0.01) is about 2% of the gap to GARCH-EVT, so no threshold, denominator or weighting matters. See `research_v2_regime_sensitivity.png`.

### B8. Walk-forward by calendar year (O6, 99%)
The blend scores better than GARCH-EVT in 3 of 19 years (2016, 2024, 2026), all calm years with few exceptions. It is worse in every stress year (2008, 2011, 2018, 2020, 2022, 2025).

### B9. Adoption rule (A6), evaluated mechanically
Source: `research_v2_regime_blend_decision.csv`.

| Criterion | Primary | Validation-selected |
|---|---|---|
| 1 Coverage (Kupiec 95/99, no red Basel; validation and test) | **fail** (red window 12 in test) | **fail** (13) |
| 2 Independence (test 99%) | **fail** (p 0.002 vs 0.35) | **fail** |
| 3 Score better than GARCH-EVT | **fail** (+0.565; worse in all periods) | **fail** |
| 4 Not one episode | **fail** (worse without COVID; better in 3 of 19 years) | **fail** |
| 5 Stable across thresholds | **fail** (worse at all three) | **fail** |
| 6 Decision value | worse: its red Basel window would fire the D23 'limit' step from a model failure, where GARCH-EVT shows yellow | — |
| 7 Reproducible | pass (16 / 16 exact; tests pass) | pass |
| **Outcome** | **Reject: keep GARCH-EVT** | **Reject** |

Secondary question: the blend is not a better full-cycle limit check than Historical. The paired differences span 0 in every period. Days in the test period with VaR99 above the D7 1.7% limit: Historical 359, blend 421, EVT 462.

### B10. Selection-bias and leakage audit
- **Time-safety:** every input to day t's forecast ends at t−1. Unit tests show `vol_ratio` is unchanged when day t and later change, and the backtest's no-look-ahead test is unchanged. No full-sample statistic is used.
- **Equal treatment:** one `rolling_forecasts` call produces every component, with identical dates, losses, window, refits, EVT threshold and seed. No dates were dropped (0 invalid forecasts, 0 cases of ES < VaR).
- **Tuning parity:** the 12 variants were chosen in advance, and one was selected on validation with the same D28 rule that selected GARCH-EVT. The selected variant's test result is reported as validation-selected; the other variants' test results are post-hoc. A unit test confirms that changing test-period data does not change the selection.
- **Test period not blind:** the 2020–26 results of Historical, EVT and GARCH-EVT were known before this design. The rejection does not rely on the test period: the blend is also significantly worse in validation and in the early period.
- **O6 weights** use data to 2026. They are identical for every model, so the paired comparison is fair. D26-train (weights from data ≤ 2014) and the fixed Policy benchmark give the same conclusion.
- **Bias that could favour the blend:** none found. The static 50/50 control and the oracle bound show that any advantage would have to come from switching, and switching changed nothing.

### B11. What this means for the investment decision
- **Forecasting vs portfolio performance.** O6's weights, rebalancing and spending are identical under every model. This experiment therefore measures the quality of the risk information given to the committee, not returns, Sharpe ratio or drawdown. A better VaR model would have changed monitoring signals, not performance.
- **For monitoring, the blend would be harmful.** In 2020–26 it shows a red Basel window, which under D23 forces a 'limit' decision. The red comes from the model lagging, not from O6 taking more risk. GARCH-EVT stays the monitoring model (D28). Historical and EVT keep their D7 role as full-cycle limit checks, where a slow reaction is intended.
- **Nothing to reopen:** O6, D24 at 2.65%, the D7 limits and the ACCEPT verdict (D34) are unaffected.

### B12. Plain-English summary for the committee and judges
- **The idea:** our Team Guide proposed watching whether markets are calm or turbulent, and leaning more on the extreme-value model when they are turbulent. We tested it.
- **The detector worked.** It recognised COVID, the 2022 rate shock and the 2025 tariff shock on the first day.
- **The models it switches between are too slow.** Both look back over the same four years of data, so they give similar answers and react slowly. Switching between two slow models is still slow.
- **Example:** in March 2020 the blend expected a worst-day loss of about 1.25%, while real losses reached 6%. GARCH-EVT, which adjusts to current volatility every day, expected about 4.4%.
- **Result:** across 2008–2026, with every reasonable setting we tried, the blend was less accurate than our current model. It would also have sent a false red-alert signal to the committee.
- **Decision: we keep GARCH-EVT.** This is a deliberate, tested choice. The idea was tried fairly and failed for a clear, measurable reason.

### B13. Limitations and future research
- One-day horizon, one data snapshot, three portfolios. Exceptions at 99% are few (0.4–17 expected per window), so window-level results are indicative only.
- ES backtesting is limited. The severity ratio and Z2 are diagnostics; FZ0 scores VaR and ES jointly but has no pass/fail threshold.
- The bootstrap treats the daily score differences as stationary within 63-day blocks; no alternative block length was run.
- Not tested, because they are outside the pre-registered scope: a regime switch *into* GARCH-EVT, a regime-dependent EVT threshold, or a calm-period floor for GARCH-EVT (B6). Each would need its own pre-registration on validation data.
- The 20/252 classifier is a fast, transparent volatility flag. Using it as a committee indicator next to the D23 ladder would be a separate proposal; it is not made here.

### B14. Amendments
- **Applied 2026-10-31 (approved in chat by Malindu):** technical report §6 has a paragraph saying that regime switching was tested and rejected in favour of GARCH-EVT (the same pattern as D39 and D40). Its figures are registered in `scripts/check_deliverables.py` (51 figures, 0 mismatches).
- **Open, flagged, not changed:** report §6 is headed "O6, 99%, 2020–2026", but it quotes the D26-train backtest (GARCH-EVT 20 exceptions, Kupiec 0.49). On O6 the figures are 24 exceptions, Kupiec 0.11, independence 0.35, worst Basel window 8. Either the label or the numbers need correcting.
- DECISIONS D41 (PROPOSED): record the rejection.
- The memo, tear sheet, app, approved outputs and the D28 choice are unchanged.

### B15. Files
- **Code:** `src/quantedge/risk/extensions/regime.py`, `scripts/research_v2_regime_blend.py`, `tests/unit/test_regime.py` (10 tests; full suite 158 passed).
- **Outputs** (new, research only):
  - Tables: `outputs/tables/research_v2_regime_blend_{daily, summary, paired, sensitivity, stress, yearly, regimes, decision, reproduction, runinfo}.csv`.
  - Figures: `outputs/figures/research_v2_regime_{timeline, crises, exceptions, sensitivity, scores}.png`.
- **AI assistance:** built with Claude Code. The brief (pp.8–9) requires the team to be able to explain and independently validate this work. Human sign-off is pending in `tracking/validation/HUMAN_VALIDATION_LOG.md`.
