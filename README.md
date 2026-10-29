# QuantEdge 1.0 — Serendib University Endowment Risk & Portfolio System

A Python and Streamlit tool that helps decide how to invest a conservative **USD 10M university endowment**, using only the seven approved ETFs (SPY, EFA, EEM, AGG, GLD, XLE, XLK).

> Status: data stage and return objective built; portfolio stage in progress. See `tracking/TASKS.md`.
>
> Repository: https://github.com/MalinduLokuge/Quant-Edge-Final-Challenge-Team-Alpha-Guard (branch `version-1`)

## Reproduce everything (one command)

```bash
pip install -r requirements.txt
python run_all.py --app
```

- `python run_all.py` regenerates all results into `outputs/` without opening the app.
- `streamlit run app/Home.py` opens the app on results that already exist.

## Architecture (code stages — not the brief's methodology Layers 1–5)

| Stage | Package | Produces | Handoff |
|---|---|---|---|
| Data & mandate | `src/quantedge/data` | Clean prices, simple/log returns, ADF, train/val/test split | Clean inputs |
| Portfolio | `src/quantedge/portfolio` | Markowitz/CAPM candidates, benchmarks, KPIs | **P1** candidate weights |
| Risk | `src/quantedge/risk` | VaR ×3, ES, EVT-GPD, GARCH, marginal/component VaR (+ optional copula/wavelet) | **P2** risk evidence |
| Validation | `src/quantedge/validation` | Kupiec, Christoffersen, Basel, stress tests | Validated evidence |
| Decision | `src/quantedge/decision` | Suitability gate, recommendation, report tables | **P3** decision |
| App | `app/` | Streamlit UI: reads `outputs/` only | — |

Each layer reads only what the layer before it saved, so you can test and re-run any layer by itself (`--only risk`).

## Folder map

```
config/        settings.yaml: every assumption (dates, confidence levels, limits, seeds)
data/          raw/ (downloaded, never edited) → interim/ → processed/; external/ = FRED etc.
src/quantedge/ calculation code, one package per layer + common/
app/           Streamlit interface (no model calculations)
tests/         unit/ per function, integration/ per layer handoff
notebooks/     exploration only; nothing the results depend on
outputs/       GENERATED figures, tables, reports, logs (reproducible, safe to delete)
docs/          hand-written docs: instructions, model design, agents, decisions, references, deliverables
tracking/      tasks, innovation log, compliance matrix, human validation log
.claude/agents per-layer AI agent definitions (incl. compliance validator)
```

## Data sources
Yahoo Finance (`yfinance`, adjusted close) and FRED: risk-free rate, 10y yield, breakevens and CPI. The hypothetical stress factors (D9 v2) also come from FRED: DFII10, BAA10Y, DCOILBRENTEU, DCOILWTICO, DTWEXBGS, VIXCLS, DGS2. IMF, World Bank, IEA, EIA and Federal Reserve publications are cited as context only (`docs/research/T11_hypothetical_stress_design.md` §10). The source log is in `data/README.md`.

## AI disclosure
See `docs/AI_DISCLOSURE.md` and `tracking/validation/`.
