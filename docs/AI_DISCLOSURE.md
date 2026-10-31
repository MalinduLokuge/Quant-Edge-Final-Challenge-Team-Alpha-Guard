# AI Use Disclosure & Human Validation

**Team Alpha-Guard | Quant Edge 1.0 | 31 October 2026**

> **Status:** Draft. Verify tool usage and validation statements before submission.

## Team responsibility
The investment research, methodology, portfolio constraints, testing standards and final recommendation are the team's responsibility. Claude / Claude Code was used mainly as a code-generation and development assistant: implementing, refactoring and debugging Python modules to specifications the team developed and evaluated. Generated code and its results were reviewed, tested and corrected rather than accepted automatically. The team records its investment decisions in `docs/DECISIONS.md` and its verification in `tracking/validation/HUMAN_VALIDATION_LOG.md`.

## Disclosure summary

| AI tool | Purpose and material AI-assisted components | Human review and validation |
|---|---|---|
| Claude / Claude Code (Anthropic) | Main use: code generation, refactoring, debugging and automated-test development. It helped implement data processing, portfolio optimisation and the candidate comparisons (O1–O6), the VaR/ES/EVT and GARCH-EVT risk models, attribution, backtesting, stress and recovery simulations, the decision scripts and the Streamlit app. Material code includes `src/quantedge/`, `scripts/research_t425_*.py`, `app/` and the related tests. It also helped with supporting research summaries and initial drafts of documents and the report. | The team defined and assessed the methodology and risk rules. It reviewed formulas, constraints, code and outputs; ran unit and regression tests, backtests, sensitivity checks and numerical audits; corrected the errors it found; and approved the investment recommendation (D31 v2, D34). |
| Perplexity | Background searches and summaries of public market and financial information. | Relevant facts were checked against original permitted sources and documented with citations or assumptions. |
| ChatGPT (OpenAI) | Editorial and layout help for the executive tear sheet, document review and this disclosure revision. | Final wording, charts and figures must be checked against the approved pipeline outputs. |

## Verification and accountability
- The team kept a decision register, automated tests, numerical audits and human-review records. The validated pipeline and its outputs are documented separately; any later branch change needs revalidation.
- An audit the team requested found and corrected errors in the drawdown simulation settings, the spending implementation and reported figures. The T4.25 research record documents these corrections.
- AI-assisted scripts compared candidate portfolios and identified O6 as a leading option. The team independently evaluated and approved the portfolio choice and the mandate recommendation, and takes responsibility for both.
- Team members are responsible for understanding and defending the submitted methodology, code, assumptions, results and limitations.

**Supporting records:** `docs/DECISIONS.md`; `tracking/validation/HUMAN_VALIDATION_LOG.md`; `docs/research/T4_25_*`; `docs/deliverables/`; technical report.
