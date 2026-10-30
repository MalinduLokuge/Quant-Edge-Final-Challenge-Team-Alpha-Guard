# Task Tracker

Main-task view. **Every subtask, with its output, priority, owner, dependency and status, is in [`SUBTASKS.md`](SUBTASKS.md).**
Sources merged: Project Management Tracker (`.xlsm`, Drive "alpha guard"), FigJam Pipeline Block Reference (`.xlsm`), official brief, `docs/DECISIONS.md`.
**This repo tracker is the master copy.** An Excel version with the same 174 subtasks (original layout, formulas and dropdowns kept) is at `exports/QuantEdge_1_0_Project_Management_Tracker.xlsm` (2026-10-28). Upload it to Drive as a new version of the original tracker.

| ID | Task | Stage | Owner | Priority | Target | Subtasks | Done | In progress | Blocked | Progress |
|---|---|---|---|---|---|---|---|---|---|---|
| T1 | Project setup & shared decisions | — | Malindu | Supporting | Week 1 | 11 | 7 | 3 | 0 | 64% |
| T2 | Data pipeline & cleaning | data | Raveena | Core | Week 1 | 17 | 14 | 0 | 0 | 82% |
| T3 | Client mandate (investment policy) | mandate | Sujan | Core | Week 1 | 29 | 27 | 1 | 0 | 93% |
| T4 | Portfolio construction & selection | portfolio | Dewmini | Core | Weeks 1–2 | 26 | 25 | 0 | 0 | 96% |
| T5 | KPIs & benchmarks | portfolio | Raveena | Supporting | Week 2 | 9 | 9 | 0 | 0 | 100% |
| T6 | VaR with 3 methods | risk | Sujan | Core | Week 2 | 13 | 11 | 0 | 0 | 85% |
| T7 | Expected Shortfall | risk | Sujan | Core | Week 2 | 5 | 5 | 0 | 0 | 100% |
| T8 | EVT & GARCH | risk | Sujan | Core | Week 2 | 12 | 11 | 0 | 0 | 92% |
| T9 | Risk budgeting | risk | Sujan | Supporting | Week 2 | 6 | 6 | 0 | 0 | 100% |
| T10 | Backtesting | validation | Malindu | Core | Weeks 2–3 | 12 | 12 | 0 | 0 | 100% |
| T11 | Stress testing | validation | Dewmini | Core | Weeks 2–3 | 23 | 22 | 0 | 0 | 96% |
| T12 | Macro & industry risk (optional) | validation | Malindu | Optional | Week 3 | 5 | 3 | 2 | 0 | 60% |
| T13 | Innovation extension | risk/validation | Sujan | Optional | Week 3 | 7 | 4 | 0 | 0 | 57% |
| T14 | Streamlit app | app | Malindu | Core | Weeks 2–3 | 13 | 12 | 1 | 0 | 92% |
| T15 | Assumptions & Limitations | docs/app | Raveena + Dewmini | Core | Week 3 | 6 | 5 | 1 | 0 | 83% |
| T16 | Written deliverables | decision/docs | Raveena | Core | Week 3 | 7 | 2 | 5 | 0 | 29% |
| T17 | Repository & reproducibility | — | Malindu | Core | Week 3 | 9 | 3 | 2 | 0 | 33% |
| T18 | AI disclosure & validation log | — | Malindu | Core | Ongoing | 8 | 4 | 1 | 0 | 50% |
| T19 | Pitch & Q&A prep | — | All members | Conditional | If finalist | 4 | 0 | 0 | 0 | 0% |
| T20 | Decision gate & final recommendation (P3) | decision | All members | Core | Week 3 | 10 | 10 | 0 | 0 | 100% |
| T21 | Quality gates & compliance QA | — | Malindu (coordinates) | Core | Ongoing | 17 | 8 | 4 | 0 | 47% |
| | **Total** | | | | | **249** | **200** | **20** | **0** | **80%** |

Progress = share of subtasks marked Done. Recount with `python tracking/update_counts.py` after editing `SUBTASKS.md`.

## Verification criteria (definition of done per task)
A task is Done only when **every** criterion holds and the evidence is linked in SUBTASKS.md (Output column) and the validation log.
| Task | Done when |
|---|---|
| T1 | All decisions APPROVED in DECISIONS.md; conventions tested; repo builds from README |
| T2 | `run_all.py --only data` rebuilds every processed file from snapshots; regression + unit tests pass; split labels with leakage test |
| T3 | docs/IPS.md states horizon, return objective, constraints, limits and suitability criteria, consistent with config |
| T4 | Each candidate meets D6 v2 + D7 (tests); P1-train and P1-final saved; frontier and trade-off table produced |
| T5 | Every KPI unit-tested on a hand-computed example; same rebalancing for portfolio and benchmarks |
| T6–T8 | Each method tested against a known answer (e.g. normal VaR = μ + zσ); 90/95/99 with uncertainty bands; assumption diagnostics reported |
| T9 | Component VaR/ES sum to the total (test); risk-budget recommendation stated |
| T10 | Forecasts use data ≤ t−1 (leakage test); Kupiec/Christoffersen match textbook examples; model chosen on validation, test run once |
| T11 | Every scenario defined with dates/sources; losses in USD and % NAV; checked against D7 |
| T12–T13 | Optional: kept only if validated against a baseline and logged in INNOVATION_LOG |
| T14 | Every brief p.5–6 panel present; app reads outputs only; runs with one command |
| T15 | App page and report section generated from ASSUMPTIONS_LIMITATIONS.md |
| T16 | Every number traces to outputs/; report 7–15 pp; tear sheet and memo one page each |
| T17 | Fresh clone + `pip install -r requirements.txt` + `python run_all.py --app` works on a clean machine |
| T18 | Disclosure in the brief's 4 columns; every validation-log row signed by a team member |
| T19 | Only if finalist: 10–12 min deck rehearsed; Q&A bank covers assumptions, VaR, crisis results |
| T20 | Gate decision recorded per candidate; P3 in brief wording (accept / adjust risk limit / reject) |
| T21 | compliance-validator passes all R1–R20 |
## Critical path (implementation order)
```
T1.07 decisions D3/D5/D6/D7/D12 ──► T2.13 split ──► T4 portfolio + T5 KPIs ──► T4.16 P1 freeze
   ──► T6/T7/T8/T9 risk (P2) ──► T10 backtests + T11 stress ──► T20 decision gate (P3)
   ──► T14 app · T15 limitations · T16 report/memo/tear sheet ──► T17 reproducibility ──► T21 final QA
T18 AI log and T21 compliance checks run alongside every stage.
```
Can start now, without the decisions: T6.02–T6.04, T7.01–T7.02, T8.01, T8.08 and T10.04–T10.06 as generic functions tested on synthetic data; T11.01; T2.14–T2.15; T3.06.

## Open blockers
- **Decisions:** all blocking decisions approved 2026-10-28 (D3, D5, D6, D7, D12). Still open, deferred: D9 (before stress stage), D16 (before submission), component-ES cap (risk stage).
- T2.12: confirm the GLD move on 2026-01-30. T2.16: team sign-off on the validation log.
- T1.09: Batch04 explainer missing; duplicate Batch02.
- T21.05: FigJam memo wording (D14) and Min-CVaR block (D20).
