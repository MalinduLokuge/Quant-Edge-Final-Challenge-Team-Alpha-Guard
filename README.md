# QuantEdge 1.0: Serendib University Endowment Risk & Portfolio System

**Team Alpha Guard** · QuantEdge 1.0 Final Challenge · https://github.com/MalinduLokuge/Quant-Edge-Final-Challenge-Team-Alpha-Guard

This is a Python and Streamlit system that recommends how to invest a conservative **USD 10M university endowment** in the seven approved ETFs (SPY, EFA, EEM, AGG, GLD, XLE, XLK). It measures the portfolio's risk with VaR, ES, EVT and GARCH-EVT, backtests that risk model out of sample, stress-tests the portfolio, and supports an investment-committee decision. Every number in the deliverables traces back to a file in `outputs/`.

## Recommendation (`outputs/p3_decision/`)

| | |
|---|---|
| **Portfolio (O6)** | AGG 61.1% · SPY 18.4% · XLK 10.0% · EFA 7.2% · XLE 3.0% · GLD 0.4%, rebalanced quarterly |
| **Expected return / spending** | 5.80% a year nominal (about 3.4% real), supporting **about 2.65% spending** (≈ $265k a year) through a smoothed rule |
| **Downside (D7 limits)** | worst historical drawdown 23.5% (limit 25%); P(drawdown > 25% within 5 years) 4.9% (limit 5%); worst historical stress loss 23.5% (2008 replay); worst hypothetical 22.8% (tech crash with inflation) |
| **Daily 99% VaR / ES** | 1.39% / 2.20% (historical); the GARCH-EVT monitoring model passed the 2020–26 out-of-sample backtest |
| **Committee verdict** | **ACCEPT** the mandate as proposed (D34) |

## Deliverables

| Deliverable | File |
|---|---|
| Technical report (7–15 pp) | `docs/deliverables/report/technical_report.md` |
| Investment-committee memo (1 page) | `docs/deliverables/memo/investment_committee_memo.md` |
| Tear sheet (1 page) | `docs/deliverables/tear_sheet/tear_sheet.md` |
| Streamlit application | `app/` (see below) |
| AI-use disclosure | `docs/AI_DISCLOSURE.md` |
| Pitch deck | `docs/deliverables/pitch/` (finalists only) |

## Run it

**Requirements:** Python 3.12 and about 3 GB of free disk. Every package is free and open source, and `requirements.txt` pins exact versions.

```bash
pip install -r requirements.txt
```

| Goal | Command | Time |
|---|---|---|
| Open the app on the committed results | `streamlit run app/Home.py` (http://localhost:8501) | ~1 min |
| Regenerate every result from the data snapshots | `python run_all.py` | 1.5–2 h |
| Regenerate, then open the app | `python run_all.py --app` | 1.5–2 h |
| Re-run one stage | `python run_all.py --only data\|portfolio\|risk\|validation\|decision` | minutes |
| Run the automated tests (unit + integration, including every app page) | `python -m pytest -q` | ~2–5 min |
| Check every figure in the memo, tear sheet and report against `outputs/` | `python scripts/check_deliverables.py` | seconds |
| Independent QA recomputation from raw prices | `python scripts/qa/qa_recompute.py` | seconds |

- **Stage outputs:** each stage reads only what the stage before it saved: data → portfolio (optimisation, P1) → risk (VaR / ES / EVT / GARCH-EVT, P2) → validation (backtests, stress tests, sustainability) → decision (P3).
- **Committed results:** `outputs/` is committed as a results snapshot (D16), so the app works right after cloning. Re-running the pipeline reproduces it, using fixed seeds and the dated data snapshots.
- **numpy must stay below 2:** cvxpy 1.5 is built for numpy 1.26.
- **Windows:** keep the repository in a short path, such as `C:\qe`. Some packages exceed the default 260-character path limit.
- **No internet needed:** prices and FRED series are dated snapshots in `data/raw` and `data/external`. `--refresh-data` downloads fresh data and will therefore change the results.

## The app (9 pages)
The sidebar sets the confidence level (90 / 95 / 99%), the VaR method and the backtest date range for every page. The app reads `outputs/` only and never re-estimates a model.

| Page | What it shows |
|---|---|
| Home | Recommendation at a glance; monitoring status (D23 step as of the data end) |
| Portfolio | Weights, growth of $10M vs benchmarks, drawdowns vs the D23 ladder and the 25% limit, KPIs by period |
| Risk | VaR, ES, EVT and GARCH-EVT side by side with intervals; tail-risk drivers; diversification benefit |
| Backtest | Kupiec, Christoffersen and the Basel traffic light for any date range; exception chart |
| Stress | 2008, 2013, COVID and 2022 replays; designed scenarios (stagflation, AI unwind, tech-led crash); 12-month paths; your own scenario |
| Sustainability | Spending vs drawdown trade-off; what-if sliders; recovery after 15–25% falls |
| Decision | Recommendation, pass/fail against every limit, validation summary, monitoring triggers, downloads |
| Assumptions & Limitations | Same text as `docs/ASSUMPTIONS_LIMITATIONS.md` |

## Methodology

| Stage | Package | What it does |
|---|---|---|
| Data | `src/quantedge/data` | Adjusted closes, calendar alignment, simple and log returns, quality flags (no deletion), ADF, chronological split (train ≤ 2014, validation 2015–19, test 2020–26), FRED series |
| Portfolio | `src/quantedge/portfolio` | CAPM expected returns (5% ERP; AGG at its yield), Ledoit–Wolf covariance, Markowitz candidates with CVaR and drawdown constraints, KPIs, selection rule (D26 + D32 five-year drawdown test + D27 risk-share cap) |
| Risk | `src/quantedge/risk` | VaR and ES (historical, normal, Student-t, t-copula Monte Carlo), EVT (POT-GPD), GARCH-EVT, component VaR / ES, diversification |
| Validation | `src/quantedge/validation` | Rolling 1,000-day out-of-sample backtests (Kupiec, Christoffersen, Basel, FZ0), historical and hypothetical stress tests, limit stability, sustainability and recovery, Ledoit–Wolf Sharpe test |
| Decision | `src/quantedge/decision` | Final recommendation, D23 monitoring triggers, trade-off table |

All conventions (loss sign, simple vs log returns, annualisation, 1-day horizon) are in `docs/CALCULATION_DICTIONARY.md`. Every modelling choice is in `docs/DECISIONS.md` (D1–D44).

## Data sources
- **Model inputs:** Yahoo Finance (adjusted close, distributions, fund sector weights) and FRED. The FRED series are the 3-month T-bill, 10y Treasury, 10y and 5y breakevens, CPI, 10y TIPS yield, Baa spread, Brent and WTI oil, broad dollar index, VIX and 2y Treasury. All are dated snapshots, logged in `data/README.md`.
- **Context only** (cited, not model inputs): IMF, World Bank and the publications cited in `docs/research/T11_hypothetical_stress_design.md`.

## Repository structure
```
app/                     Streamlit app (Home + 8 pages); reads outputs/ only
config/settings.yaml     every assumption and approved parameter (single source of truth)
data/raw, data/external  dated price and FRED snapshots (inputs)
data/processed           cleaned returns, rates, flags (data-stage outputs)
src/quantedge/           pipeline: data, portfolio, risk, validation, decision (+ risk/extensions/regime.py, research only)
run_all.py               one command for the whole pipeline
outputs/                 committed results snapshot: tables/, figures/, reports/, p3_decision/
tests/                   unit and integration tests (164), incl. no-look-ahead, data-stage reference and app-page tests
scripts/                 research scripts behind each decision, check_deliverables.py, qa/qa_recompute.py
notebooks/               the team's original data notebook (provenance of the data stage)
docs/deliverables/       report, memo, tear sheet
docs/research/           evidence for every decision, incl. tested-and-rejected alternatives
docs/                    DECISIONS, ASSUMPTIONS_LIMITATIONS, CALCULATION_DICTIONARY, MODEL_DESIGN, AI_DISCLOSURE
docs/references/         official competition brief
tracking/                task tracker, compliance matrix, innovation log, human-validation log, reproducibility record
```

## Validation evidence

| Evidence | Where |
|---|---|
| Out-of-sample VaR backtest; model chosen on 2015–19 and tested once on 2020–26 | `docs/research/T10_backtesting.md`, `outputs/tables/backtest_*` |
| Final-portfolio selection, audit corrections, walk-forward 2009–26 | `docs/research/T4_25_final_selection_evaluation.md`, `scripts/research_t425_*.py`, `scripts/research_walkforward.py` |
| Benchmarks, risk limits, risk capacity, gold assessment | `docs/research/D3_D7_benchmarks_and_risk_limits.md`, `scripts/research_d3_d7.py`, `scripts/research_d7_capacity.py`, `scripts/research_d27_cap.py` |
| Stress-test design and results | `docs/research/T11_*.md` |
| Version-2/3 research (each with its script and `outputs/tables/research_v2_*`) | `docs/research/V2_*.md`: tech concentration (D35–D37), recovery target (D39), withdrawal rule (D40), regime-switching VaR (D41, rejected), Sharpe significance, gold return (D43), AI crash with inflation (D44) |
| Independent QA audit and recomputation | `docs/research/QA_AUDIT_2026-10-30.md`, `scripts/qa/qa_recompute.py` |
| Human validation of each AI-assisted component | `tracking/validation/HUMAN_VALIDATION_LOG.md` |
| Reproducibility record | `tracking/validation/REPRODUCIBILITY.md` |
| Compliance with the brief | `tracking/compliance/COMPLIANCE_MATRIX.md` |

## Known limitations (full list: `docs/ASSUMPTIONS_LIMITATIONS.md`)
- **Expected returns:** they are the least certain input. CAPM uses a 5% equity premium, and the data's own 95% range is 3.5–15.8%.
- **One crisis of each kind:** the 2004–26 data hold one 2008-type crisis and no dot-com-style tech crash, so the limits are targets, not guarantees.
- **Five-year drawdown test:** O6's probability is 4.9% against a 5% limit, within simulation error, and it is sensitive to block length. After D24 spending, the fund-value drawdown is 25.3% (D42 disclosure).
- **No effective inflation hedge:** XLE is 3.0% and GLD 0.4%. A tech crash with inflation loses 22.8%, within the limit, and breaches it at 1.5× (D44).
- **Concentration:** look-through technology is 17.7% of the fund, and SPY's 40% share of tail risk sits at the D27 cap.
- **Benchmark comparison:** Sharpe differences against the policy benchmark are not statistically significant (Ledoit–Wolf). The documented edge is the smaller drawdown.
- **Selection bias:** 2015–26 was examined during selection. The walk-forward and live monitoring are the defensible tests.
- **Research evidence without a writer script:** three research tables cited in T4_25 (`research_t425_eval_o6.csv`, `research_t425_eval_train_blocks.csv`, `research_t425_option_weights_o6.csv`) came from an interactive re-run during the O6 re-evaluation. No script in the repository writes them. Their figures are corroborated by the pipeline's own O6 outputs (`p1_final_*`, `p3_summary.csv`).

## AI use
AI assistance (Claude Code) is disclosed in `docs/AI_DISCLOSURE.md` under the brief's four headings: tool, purpose, human validation and material AI-generated components. Each AI-assisted component has a human check recorded in `tracking/validation/HUMAN_VALIDATION_LOG.md`, where team members sign it off. The agent roles used during development are in `docs/AGENTS.md` and `.claude/agents/`.
