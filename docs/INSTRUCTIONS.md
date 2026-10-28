# Competition Instructions & Objectives

> **Authority:** the official PDF in `docs/references/competition/`. Page refs below verified against it on 2026-10-28. Full detail in `PROJECT_KNOWLEDGE.md`.

## Mandate
- Client: Serendib University Endowment, USD 10M, conservative.
- Philosophy: avoiding large losses matters more than maximising return.
- Universe: SPY, EFA, EEM, AGG, GLD, XLE, XLK only.

## Mandatory requirements (verified)
| # | Requirement | Brief page |
|---|---|---|
| R1 | Justify the horizon, return objective, risk limits and why the portfolio suits the client | pp.3–4 |
| R2 | Use only the 7 prescribed ETFs | p.5 |
| R3 | Markowitz mean-variance + CAPM | p.7 |
| R4 | Sharpe, Sortino, Treynor, Jensen α, IR, Max DD, Calmar | p.7 |
| R5 | Historical, Parametric, Monte Carlo VaR on the same portfolio at 95% & 99% | p.7 |
| R6 | Expected Shortfall, and why it adds information beyond VaR | p.7 |
| R7 | EVT with a justified threshold and tail uncertainty | p.7 |
| R8 | Marginal/component VaR/ES → risk budget and position sizing | p.8 |
| R9 | Out-of-sample Kupiec, Christoffersen, Basel traffic light | p.7 |
| R10 | Stress tests: 2008, March 2020, 2022 + one hypothetical | p.8 |
| R11 | Approved data sources, adjusted closes, calendar alignment, ADF, reproducible | p.9 |
| R12 | Streamlit: sidebar (90/95/99, VaR method, backtest dates), portfolio, risk, backtest, stress panels | pp.5–6 |
| R13 | Assumptions & Limitations page (in the app and the report) | p.6 |
| R14 | GitHub+README, runnable app, 7–15 page report, one-page tear sheet, one-page decision memo | pp.6,8 |
| R15 | AI disclosure + independent human validation | pp.8–9 |

| R16 | Quantify return vs. risk-reduction trade-offs; show diversification benefits | p.4 |
| R17 | State confidence in the risk estimates (uncertainty) | p.5 |
| R18 | Show how risk models perform under stressed conditions (EVT layer) | p.7 |
| R19 | Critically assess the assumptions behind each risk model | p.7 |
| R20 | App lets users pick 90% confidence too (VaR/ES/EVT all at 90/95/99) | p.5 |

## Optional (scored)
- Macro, industry or market-specific risks (p.4 #9). This counts toward the Decision 30% (p.10).
- Innovation examples in the brief: regime-conditioned risk, risk overlays, alternative EVT threshold rules (p.10).
- GARCH, copulas and wavelets are **not named in the brief**. They are team extensions; keep them only if they are validated and affect the decision.

## Judging weights
Decision 30% · Technical 25% · Software 15% · Innovation 15% · Communication 15% (p.10).
