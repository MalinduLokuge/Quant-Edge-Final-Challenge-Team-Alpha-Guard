# QuantEdge 1.0: Serendib University Endowment Risk & Portfolio System

A Python and Streamlit tool that recommends how to invest a conservative **USD 10M university endowment** in the seven approved ETFs (SPY, EFA, EEM, AGG, GLD, XLE, XLK). It measures and backtests the portfolio's risk, stress-tests it, and supports a committee decision.

**Team Alpha Guard** · Repository: https://github.com/MalinduLokuge/Quant-Edge-Final-Challenge-Team-Alpha-Guard (branch `version-1`)

## Recommendation (outputs/p3_decision)

| | |
|---|---|
| **Portfolio (O6)** | AGG 61.1% · SPY 18.4% · XLK 10.0% · EFA 7.2% · XLE 3.0% · GLD 0.4%, rebalanced quarterly |
| **Expected return / spending** | 5.80% a year, supporting **about 2.65% spending** (≈ $265k a year) via a smoothed rule |
| **Downside** | worst historical drawdown 23.5% (limit 25%); worst stress loss 23.5% (2008 replay) |
| **Daily 99% VaR / ES** | 1.39% / 2.20%; GARCH-EVT model passed out-of-sample backtests in 2020–26 |
| **Committee verdict** | **ACCEPT** the mandate as proposed (D34) |

## Run it

**Requirements:** Python 3.12, about 3 GB free disk. Everything is free and open source.

```bash
pip install -r requirements.txt
python run_all.py --app
```

- **`python run_all.py --app`** regenerates every result from the committed data snapshots, then opens the app at http://localhost:8501.
  - The full run takes **about 1.5–2 hours** on a laptop, mostly the daily rolling backtests (2015–2026, 7 methods × 6 portfolios).
- **`python run_all.py`** regenerates the results without opening the app.
- **`python run_all.py --only risk`** re-runs one stage. The stages are data, portfolio, risk, validation and decision; each reads only what the stage before it saved.
- **`streamlit run app/Home.py`** opens the app on results that already exist in `outputs/`.
- **`python -m pytest -q`** runs the tests: unit tests plus integration tests, one of which runs every app page.
- **`python scripts/check_deliverables.py`** checks that the numbers in the memo, tear sheet and report match the outputs.

**Troubleshooting:**
- **numpy must stay below 2.** cvxpy 1.5 and pyarrow 19 are built for numpy 1.26, and `requirements.txt` pins exact versions.
- **Windows:** keep the repo in a short path (e.g. `C:\qe`). Some packages have very long file paths that exceed the default 260-character limit.
- **Prices and FRED series are dated snapshots** in `data/raw` and `data/external`, so no internet is needed. `--refresh-data` downloads fresh data and therefore changes results.

## The app (9 pages)

**Sidebar** (applies to every page): confidence level 90 / 95 / 99%, VaR method, backtest date range.

| Page | What it shows |
|---|---|
| Home | The recommendation at a glance |
| Portfolio | Weights, growth of $10M vs benchmarks, drawdown vs the 25% limit, KPIs (Sharpe, Sortino, Treynor, Jensen α, IR, Calmar) by period |
| Risk | VaR, ES, EVT and GARCH-EVT side by side at the chosen confidence, with intervals; which ETF drives the tail; diversification benefit |
| Backtest | Kupiec, Christoffersen and the Basel traffic light, recomputed for any date range; exception chart |
| Stress | 2008, 2013, COVID and 2022 replays plus designed scenarios (energy stagflation, AI unwind / recession); loss drivers; 12-month paths; sliders for your own scenario |
| Sustainability | Spending vs drawdown trade-off; what-if sliders (spending, growth, costs, inflation, equity premium); recovery after 15–25% falls |
| Decision | Recommendation, pass/fail against every limit, validation summary, monitoring triggers, downloads |
| Assumptions & Limitations | What the model does and does not capture (same text as the report) |
| Disclosure | AI use, data sources, decision log |

## How it works

| Stage | Package | What it does | Brief layer |
|---|---|---|---|
| Data | `src/quantedge/data` | Adjusted closes, calendar alignment, simple and log returns, flags (no deletion), ADF, chronological split, FRED series | Data governance |
| Portfolio | `src/quantedge/portfolio` | CAPM expected returns, Markowitz candidates with drawdown/ES constraints, KPIs, selection rule (D26 + D32) | Layer 1 |
| Risk | `src/quantedge/risk` | VaR and ES (historical, normal, Student-t, t-copula Monte Carlo), EVT (POT-GPD), GARCH-EVT, component VaR/ES, diversification | Layers 2–4 |
| Validation | `src/quantedge/validation` | Rolling out-of-sample backtests (Kupiec, Christoffersen, Basel), historical and hypothetical stress, limit stability, recovery test | Layer 5, stress |
| Decision | `src/quantedge/decision` | Final recommendation, monitoring triggers, trade-off table | §8.6 |
| App | `app/` | Streamlit UI; reads `outputs/` only, never re-estimates | §6 |

**Key documents:**
- `docs/DECISIONS.md`: every modelling decision, D1–D34.
- `docs/ASSUMPTIONS_LIMITATIONS.md`
- `docs/research/`: evidence behind each decision, including the QA audit.
- `docs/deliverables/`: memo, tear sheet, report.

## Data sources
- **Model inputs:**
  - **Yahoo Finance** (`yfinance`, adjusted close, distributions).
  - **FRED:** 3-month T-bill, 10y Treasury, 10y and 5y breakevens, CPI, and the stress factors (10y TIPS yield, Moody's Baa spread, Brent and WTI oil, broad dollar index, VIX, 2y Treasury).
- **Context only** (cited, not model inputs): IMF and World Bank, plus other cited publications in `docs/research/T11_hypothetical_stress_design.md` §10.
- **Source log:** `data/README.md`.

## AI disclosure
AI assistance (Claude Code) is disclosed in the brief's four columns in `docs/AI_DISCLOSURE.md`. Human checks are recorded in `tracking/validation/HUMAN_VALIDATION_LOG.md`.
