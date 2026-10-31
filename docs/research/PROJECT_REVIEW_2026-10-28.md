# Project Review & Gap Analysis (2026-10-28)

**Sources reviewed:** official brief (10 pp.); FigJam board 0BsezYr2IQNrweujKm3yF3; PM Tracker and Block Reference `.xlsm`; masterclass and risk decks + explainers; DECISIONS.md (D1–D22); research report D3/D7; repo code, tests and outputs.
**Rule used:** a task is Done only with evidence (code + test, output file or approved decision).

## 1. Compliance assessment (full detail: `tracking/compliance/COMPLIANCE_MATRIX.md`)
| Status | Requirements |
|---|---|
| ✅ Met with evidence | R2 universe enforcement, R11 data governance (team sign-off pending) |
| 🟡 Decided or partly built | R1 mandate, R3 CAPM (Markowitz pending), R10 stress (hypothetical pending), R13 limitations doc (app pending), R14 one-command run (no commit/remote, no report), R15 AI disclosure (draft, unsigned), R16 trade-offs, R17 confidence |
| ⬜ Not started | R4 KPIs, R5 VaR ×3, R6 ES, R7 EVT, R8 component risk, R9 backtests, R12 app, R18 stress-model performance, R19 assumption critique, R20 90% level |

Design coverage is complete: every brief requirement maps to an approved or proposed method and a tracked subtask. **No mandatory requirement is missing from the plan.** Implementation is about 15% done (all of it in the data stage and the return objective).

## 2. Gaps found
| # | Finding | Evidence | Severity | Action |
|---|---|---|---|---|
| G-1 | **Expected returns use the full sample (to 2026).** Using them in the out-of-sample backtest would leak test-period information | `portfolio/__init__.py` docstring | Critical | T4.18 training-window CMA; T4.19 P1-train vs P1-final |
| G-2 | **Drawdown limit can't be put directly into a standard optimiser** (non-convex) | D7, D6 v2 | Critical | **D22 proposed:** CVaR constraint + CDaR, with post-check fallback; needs approval |
| G-3 | **Decisions in use but not approved:** D4 5-year horizon (D7 uses it), D11 quarterly (D3 uses it), D13 window, D1, D2, D8 | DECISIONS.md | High | T1.10. **Approval needed** |
| G-4 | Rebalancing logic only exists in the research script; the KPI module would otherwise compare a daily-rebalanced portfolio with a quarterly benchmark | `scripts/research_d3_d7.py` | High | T2.17, T5.09 |
| G-5 | **Research evidence is not reproduced by the one-command run** (scripts/ is outside run_all) | brief p.6, p.9 reproducibility | High | T17.09 |
| G-6 | **Nothing committed; no GitHub remote** | `git status` | Critical | T17.08 (needs your OK to commit) |
| G-7 | AI disclosure was empty; 9 validation-log rows unsigned | brief pp.8–9 | Critical | Drafted (T18.07); sign-off T18.08 |
| G-8 | Compliance matrix lacked R16–R20 | INSTRUCTIONS vs matrix | Medium | Fixed (T21.06) |
| G-9 | Innovation log didn't record the innovations already built | INNOVATION_LOG | Medium | Fixed (T21.07): I6–I11 |
| G-10 | Assumptions doc covered data only | ASSUMPTIONS_LIMITATIONS | High | Fixed (T15.06): client, return, benchmark, risk-limit sections |
| G-11 | `requirements.txt` unpinned; yfinance 1.7.0 and pandas 2.1.4 installed | requirements.txt | High | T17.02 |
| G-12 | CAPM values gold at about 4.6% (β ≈ 0), so the optimiser will under-weight gold whatever its hedge value | cma_assets.csv | Medium | Documented in limitations; ERP/CMA sensitivity (T8.12). Consider a gold-specific assumption: **team decision**. Resolved 2026-10-31 (V2_gold_return.md): tested with gold-specific returns; CAPM kept, 0.4% given no hedge credit |
| G-13 | Validation period (2015–19) is calm | D5 | Medium | Accepted limitation; stress-window evaluation (T8.11) compensates |
| G-14 | Hypothetical scenario D9 still open; R10 can't close | D9 | High | T11.03 |
| G-15 | Team of five required (brief p.2); tracker lists four members | PM tracker | Low | Confirm fifth member and owner assignments |
| G-16 | Excel trackers and FigJam out of date vs repo | exports, board | Medium | Excel regenerated (§5); FigJam edits proposed (§4) |

Nothing found to be unnecessarily complex, except wavelets (rec. #13, still PROPOSED to drop or move to an appendix).

## 3. Recommended improvements requiring approval
| ID | Proposal | Why | Priority |
|---|---|---|---|
| D4 | 5-year horizon, annual review | Already the basis of D7 | Critical |
| D11 | Quarterly rebalancing | Already the basis of D3 | Critical |
| D13 | 1,000-day VaR window (500 sensitivity) | Enough tail points at 99%; fits D5 | High |
| D22 | CVaR + CDaR optimisation | Enforces D7 exactly; matches brief's "innovation" | Critical |
| D1 / D2 / D8 | Full sample to 2026-10-19 / DTB3 / EVT threshold method | Implemented or ready | High |
| rec #11–14 | Macro section, innovation set, drop wavelets, cloud deployment | Still PROPOSED since first review | Medium |

## 4. FigJam board: proposed edits (not applied; need approval)
| Block | Current text | Proposed change | Decision |
|---|---|---|---|
| Master 02 "Client rules" | "Cash needs • spending" / cash buffer | "Spending 4% paid by selling AGG; no cash sleeve" | D10 |
| Mandate 01 return objective | "Return hurdle" | "(1+I)(1+S)(1+G)(1+C): 7.19% target / 6.66% minimum; sustainable spending fallback" | D12 |
| Mandate 02 risk & liquidity | "VaR/ES • drawdown limits" | "DD 25% (P ≤ 5% in 5y), ES99 ≤ 2.5%, stress ≤ 25%, AGG ≥ 8%" | D7 |
| Mandate 06 split | "Train → validation → test" | "2004–14 / 2015–19 / 2020+" | D5 |
| Portfolio candidates | Min-Var, Risk Parity, Max-Sharpe, Target-return | **Add Min-CVaR block** | D20 |
| Portfolio feasibility (06) | "Client limits" | "D6 v2 layers: equity 20–45%, GLD ≤ 20%, ≤ 2× benchmark, sector tilts ≤ 10/15%" | D6 |
| CAPM / benchmark (N01) | "Market beta • FRED T-bill" | "SPY proxy; Policy 40/50/10 primary; 60/40, EW7 secondary" | D3 |
| Risk N01 confidence | "95% / 99% + app 90%" | "+ uncertainty bands" | D18 |
| Monte Carlo | "Simulate ETF portfolio losses" | "Multivariate t / t-copula, fixed seed" | D19 |
| Validation 08/10 decision | "Accept • resize/reduce • reject" | "**Accept as proposed • adjust the risk limit • reject**" | D14 |
| Validation 09 revise & retest | "hedge/cash buffer" | Remove "hedge/cash buffer" (no derivatives or cash) | D10 |

## 5. Tracking updates made
| File | Change |
|---|---|
| `tracking/SUBTASKS.md` | +19 subtasks (T1.10–1.11, T2.17, T4.18–4.21, T5.09, T13.07, T14.13, T15.06, T16.07, T17.08–17.09, T18.07–18.08, T21.06–21.08); 6 status corrections; 6 revised descriptions → **208 subtasks** |
| `tracking/TASKS.md` | Counts; verification criteria (definition of done) per task |
| `tracking/compliance/COMPLIANCE_MATRIX.md` | R16–R20 added; every status re-checked with evidence |
| `tracking/innovation/INNOVATION_LOG.md` | I6–I11 recorded; planned list tied to brief's innovation examples |
| `docs/ASSUMPTIONS_LIMITATIONS.md` | Client, expected-return, benchmark and risk-limit assumptions |
| `docs/AI_DISCLOSURE.md` | Draft in the brief's 4-column format |
| `docs/DECISIONS.md` | D4, D11, D13 proposals; D22 added |
| `docs/MODEL_DESIGN.md` | P1-train / P1-final; portfolio-stage contract |
| `tracking/exports/*.xlsm` | Both Excel files regenerated from the repo tracker (`python tracking/export_excel.py`) |

## 6. Next priorities (dependency order)
1. **Approvals:** D4, D11, D13, D22 (+ D1, D2, D8); OK to commit to git (T17.08).
2. T2.13 split labels + leakage test → T2.17 rebalanced NAV in common.
3. T4.18 training-window CMA → T4.08 robust covariance → T4.02–T4.10 candidates under D6/D7 (needs D22) → T4.16/T4.19 P1-train and P1-final.
4. T5 KPIs vs benchmarks (T5.09).
5. T6–T9 risk stage (can start in parallel on synthetic data: VaR/ES/EVT functions).
6. T10 backtests → T11 stress (needs D9) → T20 decision gate → T14 app → T16 report.
