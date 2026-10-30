# AI Disclosure

Format follows the brief (p.8): AI tool · purpose · human validation · material AI-generated components.

**Status: DRAFT, updated 2026-10-30.**
- The team must review this list, correct it, and add any other tools used (for example ChatGPT for the explainer documents, or GitHub Copilot).
- Every row is backed by entries in `tracking/validation/HUMAN_VALIDATION_LOG.md`, which each team member must sign (T18.08).

| AI tool | Purpose | Human validation | Material AI-generated components |
|---|---|---|---|
| Claude Code (Anthropic) | Project structure; reading and summarising the brief, decks and trackers; gap analysis | Team reviewed the findings against the brief and approved each decision (DECISIONS.md) | Folder structure, docs/PROJECT_KNOWLEDGE.md, INSTRUCTIONS.md, review drafts |
| Claude Code | Port of the team's data notebook into tested code; FRED, income and quality checks | Regression test reproduces the team's original outputs (diff ≤ 3e-14); flags reviewed against market events | `src/quantedge/data/*`, data tests |
| Claude Code | Return objective, capital market assumptions, benchmark and risk-limit research | Formulas checked against CALCULATION_DICTIONARY; table spot checks; external facts verified by web search; team approved D3, D6, D7, D12, D24, D25 | `src/quantedge/portfolio/*`, `scripts/research_d3_d7.py`, `scripts/research_d7_capacity.py`, research docs |
| Claude Code | Portfolio optimiser (CVaR / CDaR constraints, D22), candidates, KPIs, efficient frontier, D26 selection rule, component-ES cap (D27) | Unit tests (closed forms: min-variance, risk parity, max-Sharpe; limits bind; ES cap holds); team approved D22, D26, D27 after reviewing the evidence | `portfolio/optimise.py`, `frontier.py`, `candidates.py`, `kpis.py`, `scripts/research_d27_cap.py` |
| Claude Code | Risk stage: VaR/ES (historical, normal, t, t-copula Monte Carlo), EVT (POT-GPD, threshold rule), GARCH and GARCH-EVT, Euler attribution | Tests against known distributions (GPD recovery, exponential tail, GARCH persistence, components sum to total); a Monte Carlo bug (multivariate t understated VaR about 3×) found in review and replaced by a t-copula; team approved D8 | `src/quantedge/risk/*` |
| Claude Code | Out-of-sample backtesting (Kupiec, Christoffersen, Basel, ES checks), model-selection rule, limit stability | Tests (hand-computed Kupiec, n₁₁ = 0, Basel zones, no look-ahead); selection rule approved (D28) and frozen in a commit **before** the test period was run | `src/quantedge/validation/backtest.py`, `coverage.py`, `limits.py` |
| Claude Code | Stress tests: historical replays; research on current macro conditions (web search) and the design of hypothetical scenarios; six-factor model | Factor model back-tested on six crises (errors reported by ETF); sources dated and tagged as verified data / historical / forecast / news / assumption; team approved D9 v2 and D29 after reading the design report | `validation/stress.py`, `hypothetical.py`, `docs/research/T11_*` |
| Claude Code | Final-selection evaluation (O1–O6), self-audit, walk-forward validation, sustainability and recovery test | **Team-requested audit found AI errors:** a seed-tuned drawdown test, a spending decision not applied in code, arbitrary thresholds, one misreported number. All were fixed and documented (T4.25 §0). The team chose D30, D31 v2, D32 and D33 | `scripts/research_t425_*.py`, `scripts/research_walkforward.py`, `validation/sustainability.py`, `docs/research/T4_25_*` |
| Claude Code | Decision stage and Streamlit app | Every app page runs in an automated test; numbers come only from saved outputs | `src/quantedge/decision/`, `app/*` |
| Claude Code | First drafts of the committee memo, tear sheet and technical report; number audit | `scripts/check_deliverables.py` checks 30 key figures against outputs; the team edits and owns the text and confirmed the memo verdict (D34) | `docs/deliverables/*` (drafts) |
| Claude Code | Task tracking, Excel exports, compliance matrix, innovation log | Team reviewed the task lists | `tracking/*` |

**Decisions that remain the team's own judgement:**
- **Inputs and limits:** horizon (D4), spending, growth, cost and ERP values (D12, D30), benchmarks (D3), risk limits and test design (D7, D32), weight and concentration limits (D6, D27, D33), data split (D5).
- **Model and scenarios:** model selection (D28), stress scenarios (D9 v2, D29).
- **The recommendation:** the final portfolio (D31 v2) and the memo verdict (D34).

**Ownership:** each member must be able to explain each module (T18.06). The AI was used as a tool; the conclusions were checked, challenged (including the audit) and approved by the team.
