# AI Disclosure

Format follows the brief (p.8): tool · purpose · human validation · material AI-generated components.
**Status: DRAFT, prepared 2026-10-28. The team must review, correct and add any other tools used (e.g. ChatGPT for the explainer documents).**

| AI tool | Purpose | Human validation | Material AI-generated components |
|---|---|---|---|
| Claude Code (Anthropic) | Project structure, reading and summarising the brief, decks and trackers; gap analysis | Team reviewed the findings against the brief and approved each decision (DECISIONS.md) | Folder structure, docs/PROJECT_KNOWLEDGE.md, INSTRUCTIONS.md, research reports (drafts) |
| Claude Code (Anthropic) | Port of the team's data notebook into tested code; FRED, income and quality checks | Regression test reproduces the team's original outputs (diff ≤ 3e-14); flag review against market events; HUMAN_VALIDATION_LOG entries | `src/quantedge/data/*`, `tests/*` for data |
| Claude Code (Anthropic) | Return objective, capital market assumptions, benchmark and risk-limit research analysis | Formulas checked against CALCULATION_DICTIONARY; spot checks of tables; external facts verified by web search | `src/quantedge/portfolio/*`, `scripts/research_d3_d7.py`, outputs/tables/research_* |
| Claude Code (Anthropic) | Task tracker breakdown and Excel exports | Team reviewed the task list | tracking/SUBTASKS.md, tracking/exports/* |

Decisions that remain the team's own judgement: horizon, spending, growth, cost and ERP values (D12), benchmark choice (D3), risk limits (D7), weight constraints (D6), data split (D5), and the final recommendation.
