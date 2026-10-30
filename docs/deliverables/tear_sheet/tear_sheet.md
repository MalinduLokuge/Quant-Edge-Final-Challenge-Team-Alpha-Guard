# Serendib University Endowment: Recommended Portfolio (O6)

> **DRAFT for team review (2026-10-30).** Data to 2026-10-19 · USD 10,000,000 · quarterly rebalancing · sources: `outputs/p3_decision/`, `outputs/tables/`

**Recommendation: ACCEPT the mandate as proposed** (D34): invest as below with the risk limits unchanged, rebalance quarterly, and set spending at about 2.65% of fund value through the smoothed rule.

**Objective.** Preserve and grow capital in real terms while paying the university about **2.65% a year**, with a **25% maximum drawdown** tolerance. The horizon is 5 years with annual review.

| Holding | Weight | USD | Role |
|---|---|---|---|
| AGG US aggregate bonds | 61.1% | $6,105,206 | income (4.2% yield), ballast, cash for spending |
| SPY US large caps | 18.4% | $1,842,204 | core growth |
| XLK technology | 10.0% | $1,000,000 | growth tilt (capped at 10%) |
| EFA developed international | 7.2% | $717,200 | international diversification |
| XLE energy | 3.0% | $296,838 | inflation / oil hedge |
| GLD gold | 0.4% | $38,551 | crisis hedge |

**Expected return and spending**

| | Value |
|---|---|
| Expected return (compound, nominal) | 5.80% a year |
| Expected real return | about 3.4% a year |
| Spending it supports (D12) | 2.65% ≈ $264,883 a year |
| Volatility | 8.2% a year |

**Risk and limits (2004–2026, full cycle)**

| Measure | Value | Limit |
|---|---|---|
| Worst drawdown (incl. 2008) | 23.5% | 25% |
| P(drawdown > 25% within 5 years) | 4.9% | 5% |
| 1-day VaR / ES 99% | 1.39% / 2.20% ($139k / $220k) | VaR 1.7% / ES 2.5% |
| 1-day VaR / ES 95% | 0.71% / 1.20% | VaR 0.9% / ES 1.45% |
| Largest single-fund share of tail risk | SPY 40% | 40% |
| Diversification benefit, 99% VaR / ES (vs the sum of the holdings' own risks) | 28.8% / 24.5% lower | — |

**Stress tests: loss of the $10M**

| Scenario | Recommended | Policy 40/50/10 |
|---|---|---|
| 2008 financial crisis | 23.5% | 25.3% |
| COVID crash 2020 | 16.2% | 16.0% |
| 2022 rates and inflation | 17.8% | 18.6% |
| Energy stagflation, severe (oil +50%, stocks −30%) | 18.8% | 19.2% |
| AI unwind with recession, severe (stocks −40%) | 14.2% | 13.0% |
| Tech-led crash, severe (tech −65%, stocks −40%) | 16.7% | 14.7% |

**Out-of-sample evidence** (weights built only with earlier data)

| | Recommended rule | Policy 40/50/10 |
|---|---|---|
| 2015–2019 return / Sharpe / worst drawdown | 5.7% / 1.08 / −4.6% | 5.9% / 0.89 / −7.9% |
| 2020–2026 return / Sharpe / worst drawdown | 5.0% / 0.30 / −19.6% | 7.2% / 0.49 / −19.2% |
| Walk-forward 2009–2026 (rebuilt every 3 years) | 7.3% / 0.89 / −16.4% | 7.3% / 0.75 / −19.2% |

**Model trust.** The daily risk model (GARCH-EVT) was selected on 2015–19 and tested once on 2020–26: 20 breaches against 17.1 expected. It passed Kupiec (p 0.49) and Christoffersen (p 0.62), and the Basel zone was never red.

**Key risks**
- **Inflation shocks:** bonds and stocks fall together, as in 2022.
- **Equity concentration:** SPY and XLK carry about 60% of the tail risk; counting SPY's holdings, technology is 17.7% of the fund.
- **Rates:** returns are lower if interest rates fall.
- **Limited history:** only one 2008-type crisis is in the data.

**Monitoring (no forced selling)**

| Fall from peak, or other trigger | Action |
|---|---|
| −10%, or rolling ES99 above 2.5% | watch |
| −15%, or Basel yellow | review |
| −20% | act |
| −25%, or Basel red | mandatory committee decision |
| Technology above 20% of the fund (counting SPY's holdings) | review |
| Every year | annual review |
