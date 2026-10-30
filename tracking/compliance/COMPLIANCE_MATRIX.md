# Compliance Matrix

Maintained by `compliance-validator`. Every R-item must be ✅ before submission. Going beyond the brief is fine; missing an item is not.
Status: ✅ done with evidence · 🟡 partly done or decided but not built · ⬜ not started. Last full audit: 2026-10-28 (`docs/research/PROJECT_REVIEW_2026-10-28.md`).

| Req | Requirement (docs/INSTRUCTIONS.md, brief page) | Stage | Code / evidence | Status | Last checked |
|---|---|---|---|---|---|
| R1 | Mandate: horizon, return objective, limits, suitability (pp.3–4) | data/decision | D4, D6, D7/D32, D12/D30, D23, D24, D26, D31 v2, D33, D34 APPROVED; suitability gate (Decision page); IPS-style A&L incomplete (QA-01) | 🟡 | 2026-10-30 |
| R2 | 7 prescribed ETFs only (p.5) | data | `conventions.validate_weights` rejects other instruments (test_conventions); config `universe` | ✅ | 2026-10-28 |
| R3 | Markowitz + CAPM (p.7) | portfolio | Markowitz target-return, min-variance, max-Sharpe (`optimise.py`), CAPM betas/expected returns (`cma.py`), frontier; tests | ✅ | 2026-10-29 |
| R4 | 7 KPIs (p.7) | portfolio | `kpis.py` (Sharpe, Sortino, Treynor, Jensen α, IR, max DD, Calmar), kpis.csv per period; 4 tests. Interpretation: research doc P1_candidates_and_kpis.md (report text pending) | ✅ | 2026-10-29 |
| R5 | VaR ×3 at 95/99 on the same portfolio, explain disagreement (p.7) | risk | Historical, parametric (normal + t), Monte Carlo (t-copula) on identical losses; p2_var_es.csv; research doc P2_var_es_methods.md §2; 6 tests | ✅ | 2026-10-29 |
| R6 | Expected Shortfall + rationale (p.7) | risk | ES for all 4 methods with intervals; rationale in research doc §4 (ES/VaR 1.5× at 99%) | ✅ | 2026-10-29 |
| R7 | EVT, justified threshold (p.7) | risk | POT-GPD on raw and GARCH-filtered losses; threshold by documented stability rule on 2004–2019 (figure + p2_evt_thresholds.csv); intervals; 6 tests | ✅ | 2026-10-29 |
| R8 | Marginal/component VaR/ES → position sizing (p.8) | risk/portfolio | Euler component + marginal VaR/ES (p2_attribution.csv, figure, tests); position-sizing rule D27 (no ETF > 40% of 99% ES) applied in D26 selection: SPY 36→20%, EFA 0→9%; 5-cap evaluation (research_d27_cap.csv) | ✅ | 2026-10-29 |
| R9 | Kupiec, Christoffersen, Basel, out-of-sample (p.7) | validation | Rolling 1,000-day forecasts (data ≤ t−1), 7 methods × 6 portfolios; Kupiec, Christoffersen (n₁₁ = 0 handled), Basel (99%, 250-day windows), ES severity/Z2; model chosen on 2015–19 (D28) and frozen; 2020–26 test run once: GARCH-EVT passes all | ✅ | 2026-10-29 |
| R10 | Stress 2008 / Mar-2020 / 2022 + hypothetical (p.8) | validation | 4 historical replays + research-calibrated hypotheticals (D9 v2 energy stagflation, D29 AI unwind/recession; central + severe, six-factor model back-cast on 6 episodes, 12-month rebalanced path, D24 spending, Monte Carlo); D26 worst 19.4% < 25% limit | ✅ | 2026-10-29 |
| R11 | Data governance + ADF (p.9) | data | `src/quantedge/data/`, data/README.md, 21+ tests, flag review | ✅ (team sign-off pending) | 2026-10-28 |
| R12 | Streamlit panels & sidebar (pp.5–6) | app | 9 pages; sidebar confidence 90/95/99 + VaR method + backtest dates; portfolio weights/cumulative/drawdown; VaR-ES-EVT side by side; Kupiec/Christoffersen + traffic light; stress panel; test_app.py runs every page. Backtest at 90% falls back to 99% (QA-09) | ✅ | 2026-10-30 |
| R13 | Assumptions & Limitations page, explicitly graded (p.6) | app/docs | docs/ASSUMPTIONS_LIMITATIONS.md complete (data, client, expected returns, limits, stress, 5-year test, models, tail/EVT, backtesting scope, not captured), rendered by app/pages/7_Assumptions.py | ✅ | 2026-10-30 |
| R14 | Repo + README, one-command run, 7–15 pp report, tear sheet, 1-page memo (pp.6, 8) | decision/docs | Repo + `python run_all.py --app` (≈ 2 h full run); drafts of report (2,766 words), tear sheet, memo (verdict D34); number audit 0 mismatches. README stale (QA-03); page counts and PDFs not verified (QA-06, QA-08) | 🟡 | 2026-10-30 |
| R15 | AI disclosure (4 columns) + human validation (pp.8–9) | docs | docs/AI_DISCLOSURE.md 11 rows, all stages; 29 validation-log entries unsigned (T18.08) | 🟡 | 2026-10-30 |
| R16 | Quantify return vs risk trade-offs; diversification benefits (p.4) | portfolio/risk | Trade-off: frontier, p3_tradeoff.csv, Sustainability page; diversification: p2_diversification.csv (O6 VaR99 −28.8%, ES99 −24.5%, DR 1.38), report §5, tear sheet, Risk page | ✅ | 2026-10-30 |
| R17 | Confidence in risk estimates (p.5) | risk | Bootstrap intervals (VaR/ES/EVT), MC SE, ξ intervals; GARCH current vs long-run regime | ✅ | 2026-10-29 |
| R18 | Risk models under stressed conditions (p.7) | risk/validation | GARCH regime contrast; stress-window backtest: COVID 2020 GARCH-EVT 4 vs historical 8 exceptions (0.5 expected), 2022 3 vs 8 (2.1 expected) | ✅ | 2026-10-29 |
| R19 | Critically assess model assumptions (p.7) | risk | Jarque–Bera, kurtosis, Ljung–Box on squared losses, t ν per portfolio (p2_diagnostics.csv); interpretation research doc §2–3 | ✅ | 2026-10-29 |
| R20 | App confidence 90/95/99% (p.5) | risk/app | Sidebar 90/95/99 drives Risk page (all methods at 3 levels); backtests at 95/99 only (QA-09) | ✅ | 2026-10-30 |
