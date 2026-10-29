# Compliance Matrix

Maintained by `compliance-validator`. Every R-item must be ✅ before submission. Going beyond the brief is fine; missing an item is not.
Status: ✅ done with evidence · 🟡 partly done or decided but not built · ⬜ not started. Last full audit: 2026-10-28 (`docs/research/PROJECT_REVIEW_2026-10-28.md`).

| Req | Requirement (docs/INSTRUCTIONS.md, brief page) | Stage | Code / evidence | Status | Last checked |
|---|---|---|---|---|---|
| R1 | Mandate: horizon, return objective, limits, suitability (pp.3–4) | data/decision | D4 (5y), D6, D7 (+ tolerance/capacity §9), D12, D23, D24, D26 APPROVED; IPS doc not written (T3.05) | 🟡 | 2026-10-29 |
| R2 | 7 prescribed ETFs only (p.5) | data | `conventions.validate_weights` rejects other instruments (test_conventions); config `universe` | ✅ | 2026-10-28 |
| R3 | Markowitz + CAPM (p.7) | portfolio | Markowitz target-return, min-variance, max-Sharpe (`optimise.py`), CAPM betas/expected returns (`cma.py`), frontier; tests | ✅ | 2026-10-29 |
| R4 | 7 KPIs (p.7) | portfolio | `kpis.py` (Sharpe, Sortino, Treynor, Jensen α, IR, max DD, Calmar), kpis.csv per period; 4 tests. Interpretation: research doc P1_candidates_and_kpis.md (report text pending) | ✅ | 2026-10-29 |
| R5 | VaR ×3 at 95/99 on the same portfolio (p.7) | risk | Not built (T6) | ⬜ | 2026-10-28 |
| R6 | Expected Shortfall + rationale (p.7) | risk | Historical ES in research script only (T7) | ⬜ | 2026-10-28 |
| R7 | EVT, justified threshold (p.7) | risk | Method PROPOSED (D8); not built (T8) | ⬜ | 2026-10-28 |
| R8 | Marginal/component VaR/ES → position sizing (p.8) | risk | Not built (T9); risk-budget layer reserved in D6 L4 | ⬜ | 2026-10-28 |
| R9 | Kupiec, Christoffersen, Basel, out-of-sample (p.7) | validation | Split APPROVED (D5); tests not built (T10) | ⬜ | 2026-10-28 |
| R10 | Stress 2008 / Mar-2020 / 2022 + hypothetical (p.8) | validation | Crisis windows computed for benchmarks (research script); hypothetical D9 OPEN (T11) | 🟡 | 2026-10-28 |
| R11 | Data governance + ADF (p.9) | data | `src/quantedge/data/`, data/README.md, 21+ tests, flag review | ✅ (team sign-off pending) | 2026-10-28 |
| R12 | Streamlit panels & sidebar (pp.5–6) | app | Stub `app/Home.py` only (T14) | ⬜ | 2026-10-28 |
| R13 | Assumptions & Limitations page, explicitly graded (p.6) | app/docs | docs/ASSUMPTIONS_LIMITATIONS.md has data + D3/D7/D12 sections; app page not built (T15.05, T14.07) | 🟡 | 2026-10-28 |
| R14 | Repo + README, one-command run, 7–15 pp report, tear sheet, 1-page memo (pp.6, 8) | decision/docs | GitHub branch version-1; `run_all.py` runs data → portfolio; report/memo/tear sheet not started | 🟡 | 2026-10-29 |
| R15 | AI disclosure (4 columns) + human validation (pp.8–9) | docs | Validation log has 9 entries, all unsigned (T18.08); disclosure drafted, team review pending (T18.07) | 🟡 | 2026-10-28 |
| R16 | Quantify return vs risk trade-offs; diversification benefits (p.4) | portfolio | Frontier with spending $ (frontier_full.csv/.png), feasibility map; diversification metrics still pending (T4.14) | 🟡 | 2026-10-29 |
| R17 | Confidence in risk estimates (p.5) | risk | ERP CI done; VaR/ES/EVT bands approved (D18), not built (T6.09, T8.09) | 🟡 | 2026-10-28 |
| R18 | Risk models under stressed conditions (p.7) | risk/validation | Not built (T8.11) | ⬜ | 2026-10-28 |
| R19 | Critically assess model assumptions (p.7) | risk | Approved (D21), not built (T6.08) | ⬜ | 2026-10-28 |
| R20 | App confidence 90/95/99% (p.5) | risk/app | In config (`risk.confidence_levels`); not built | ⬜ | 2026-10-28 |
