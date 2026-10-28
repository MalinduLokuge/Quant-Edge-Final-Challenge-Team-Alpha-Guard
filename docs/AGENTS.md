# AI Agent Roster

One specialist agent per layer, plus a compliance validator that every layer must pass before it is merged. Agent definitions live in `.claude/agents/`.

| Agent | Scope (writes) | Reads | Must not |
|---|---|---|---|
| `data-agent` | `src/quantedge/data`, `data/`, its tests | config | change the split once the portfolio stage starts |
| `portfolio-agent` | `portfolio`, its tests | processed data (train only) | use validation/test data |
| `risk-agent` | `risk` (+extensions), its tests | P1 weights, train data | tune parameters to make results look better |
| `validation-agent` | `validation`, its tests | P1, P2, held-out data | refit models on test data |
| `decision-agent` | `decision`, `docs/deliverables` | all outputs | add numbers that are not in outputs/ |
| `app-agent` | `app/` | outputs/ only | run model calculations in the UI |
| `compliance-validator` | `tracking/compliance` (read-only on code) | everything + official brief | approve when any R-item is missing |

## Rules for every agent
1. Read `docs/INSTRUCTIONS.md`, `docs/MODEL_DESIGN.md`, `docs/DECISIONS.md` and `config/settings.yaml` first.
2. Do not decide anything marked DECIDE. Raise it for the team.
3. Every change ships with tests and a line in `tracking/validation/HUMAN_VALIDATION_LOG.md`.
4. A layer is done only after `compliance-validator` passes it.
