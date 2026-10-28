# Project Knowledge Base (consolidated 2026-10-28)

Single reference for all agents and team members. Source priority: **(1) official brief** `references/competition/Quant edge 1.0 Final Challenge 1.pdf` > (2) team decisions in `DECISIONS.md` > (3) FigJam / Block Reference / tracker > (4) masterclass decks and explainers, which are teaching material based on a *draft* brief.

## 1. Two different "layer" vocabularies: do not mix them

| Brief §8 methodology layer ("BL") | What it requires | Implemented in code stage |
|---|---|---|
| BL1 Foundations | Markowitz, CAPM, KPIs (Sharpe, Sortino, Treynor, Jensen α, IR, MaxDD, Calmar) | `portfolio` |
| BL2 VaR | Historical, Parametric, MC on the same portfolio at 95% and 99%; explain why they disagree; critique the assumptions | `risk` |
| BL3 ES | Report ES, with a rationale | `risk` |
| BL4 EVT | Extreme downside, performance under stress, justified threshold | `risk` (+ `validation` for stress windows) |
| BL5 Backtesting | Out-of-sample Kupiec, Christoffersen, Basel traffic light for the chosen VaR model | `validation` |
| §8.6 Practical investor | Marginal VaR/ES risk budgeting, stress (2008/Mar-2020/2022 + 1 hypothetical), 1-page memo | `risk`, `validation`, `decision` |

Code stages (software architecture): `data → portfolio → risk → validation → decision → app`.
Handoffs (FigJam): **P1** = frozen candidate weights, **P2** = risk evidence per candidate, **P3** = final decision.

## 2. Verified official facts (brief page numbers)
- Client: USD 10M, conservative endowment. Objectives: capital preservation, **income generation, sustainable real growth**, resilience in stress (p.3).
- Team decides the horizon, allocation, return objective and risk constraints, and must justify them. A single fund or any combination of the eligible funds is allowed (p.4).
- Must also show: return-vs-risk trade-offs, assumptions, diversification benefits, tail awareness, crisis resilience (p.4). Must answer "what can go wrong, how bad, **how confident** are you" (p.5).
- Universe: SPY, EFA, EEM, AGG, GLD, XLE, XLK (p.5). No cash, futures or other instruments are listed.
- App minimum: sidebar (confidence **90/95/99**, VaR method, backtest date range); portfolio panel (weights, cumulative return, drawdown); risk dashboard (VaR, ES, EVT side by side at the same confidence); backtest panel (Kupiec/Christoffersen + traffic light); stress panel; **Assumptions & Limitations page (explicitly graded)** (pp.5–6).
- Free toolkit only. Suggested: pandas/NumPy/SciPy, statsmodels/arch, pyextremes or hand-rolled GPD MLE, matplotlib/Plotly, Streamlit Community Cloud (p.6).
- Deliverables: GitHub + README; app deployed **or** runnable locally with **one command**; 7–15 pp technical report covering methodology, data sources and cleaning, results, assumptions and limitations; 1-page tear sheet readable in under 5 minutes; finalists only: 10–12 min pitch (p.6). Plus a 1-page committee memo: **accept the mandate as proposed / adjust the risk limit / reject** (p.8).
- AI disclosure columns: tool, purpose, human validation, material AI-generated components. Teams can lose marks or be disqualified if they can't explain their own work (pp.8–9).
- Data sources: yfinance (adjusted close), FRED (risk-free rate e.g. 3M T-bill; macro data for CAPM and stress), World Bank/IMF (memo context only). Any undisclosed source is a rubric violation. Cleaning rules: adjusted close, documented calendar alignment, log returns for statistics with simple-return use justified, flag rather than delete, ADF test, fully reproducible (p.9).
- Rubric: **Decision 30%**, Technical 25%, Software 15%, Innovation 15%, Communication 15%. Innovation examples: regime-conditioned risk, risk overlays, alternative EVT threshold rules. The decision score credits "assessment of all relevant variables (**including optional items**)" (p.10).

## 3. Calculation conventions (proposed; confirm in DECISIONS.md)
| Item | Convention |
|---|---|
| Portfolio return | Σ wᵢ·(simple return)ᵢ. Log returns do not add across assets. |
| Statistical modelling | Log returns for per-asset statistics, ADF, GARCH, EVT on portfolio log-loss |
| Loss | L = −(portfolio return), reported as positive % and USD on the NAV |
| Primary risk horizon | 1 trading day (the backtestable one). Longer horizons by simulation, not √t, or flagged if √t is used |
| Confidence | 90/95/99 in the app; 95/99 in the report |
| Annualisation | 252 days; risk-free from FRED, converted to daily and aligned to trading days |
| Fees | ETF expense ratios are already inside adjusted prices. Don't subtract them again. |

## 4. Known data facts
- The latest inception is GLD (Nov 2004), so the common 7-ETF sample starts in late 2004. That still covers 2008.
- Since yfinance 0.2.51, `auto_adjust=True` by default (no separate "Adj Close" column). Document which one we use.
- Yahoo revises adjusted history over time, so commit a dated raw snapshot to keep results reproducible.
