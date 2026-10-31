# Serendib University Endowment: Recommended Portfolio (O6)

> **DRAFT for team review (2026-10-30).** Data to 2026-10-19 · USD 10,000,000 · quarterly rebalancing · sources: `outputs/p3_decision/`, `outputs/tables/`

**Recommendation: ACCEPT the mandate as proposed** (D34), with the risk limits unchanged. The aim is to preserve and grow capital in real terms while paying the university about **2.65% a year** through the smoothed rule, within a **25% maximum drawdown**. The horizon is 5 years, with an annual review.

| Holding | Weight | USD | Role |
|---|---|---|---|
| AGG US aggregate bonds | 61.1% | $6,105,206 | income (4.2% yield), ballast, cash for spending |
| SPY US large caps | 18.4% | $1,842,204 | core growth |
| XLK technology | 10.0% | $1,000,000 | growth tilt (capped at 10%) |
| EFA developed international | 7.2% | $717,200 | international diversification |
| XLE energy | 3.0% | $296,838 | inflation / oil hedge |
| GLD gold | 0.4% | $38,551 | residual weight from the optimiser; too small to hedge, no hedge credit taken |

**Return, spending and risk** (risk measured over 2004–2026, a full cycle)

| Measure | Value | Limit |
|---|---|---|
| Expected return, compound nominal / real (volatility 8.2%) | 5.80% / about 3.4% a year | — |
| Spending it supports (D12) | 2.65% ≈ $264,883 a year | — |
| Worst drawdown (incl. 2008) / P(drawdown > 25% within 5 years), **investment returns: official D7** | 23.5% / 4.9% | 25% / 5% |
| Same, fund value after D24 spending and costs (disclosure, not the limit) | 25.3% / 9.5% | — |
| 1-day VaR / ES 99% ($139k / $220k); 95% | 1.39% / 2.20%; 0.71% / 1.20% | 1.7% / 2.5%; 0.9% / 1.45% |
| Largest single-fund share of tail risk | SPY 40% (90% interval 36.8%–43.7%) | 40% |
| Diversification benefit, 99% VaR / ES (vs sum of holdings' own risks) | 28.8% / 24.5% lower | — |

**Stress tests: loss of the $10M**

| Scenario | Recommended | Policy 40/50/10 |
|---|---|---|
| 2008 financial crisis / COVID crash 2020 | 23.5% / 16.2% | 25.3% / 16.0% |
| 2022 rates and inflation | 17.8% | 18.6% |
| Energy stagflation, severe (oil +50%, stocks −30%) | 18.8% | 19.2% |
| AI unwind with recession, severe (stocks −40%) | 14.2% | 13.0% |
| Tech-led crash, severe (tech −65%, stocks −40%) | 16.7% | 14.7% |

**Out-of-sample evidence** (weights built only with earlier data): return / Sharpe / worst drawdown

| | Recommended rule | Policy 40/50/10 |
|---|---|---|
| 2015–2019 | 5.7% / 1.08 / −4.6% | 5.9% / 0.89 / −7.9% |
| 2020–2026 | 5.0% / 0.30 / −19.6% | 7.2% / 0.49 / −19.2% |
| Walk-forward 2009–2026 (rebuilt every 3 years) | 7.3% / 0.89 / −16.4% | 7.3% / 0.75 / −19.2% |

No Sharpe difference is statistically significant (Ledoit–Wolf test, p 0.10–0.21); the consistent edge is the smaller worst fall.

**Model trust.** GARCH-EVT, selected on 2015–19 and tested once on 2020–26: 20 breaches vs 17.1 expected; passed Kupiec (p 0.49) and Christoffersen (p 0.62); Basel zone never red.

**Key risks.** **Inflation shocks:** bonds and stocks fall together, as in 2022. **Concentration:** SPY and XLK carry about 60% of the tail risk; counting SPY's holdings, technology is 17.7% of the fund. **Rates:** returns are lower if rates fall. **Slow real recovery:** in 2008 the price recovered 254 trading days (about 1 year) after the trough, and simulated 25% falls take a median 3.0 years to recover in price; purchasing power (spending still paid) typically takes 15–20 years (about 42–46% chance within 15). **Limited history:** only one 2008-type crisis is in the data.

**Monitoring (no forced selling).**

| Trigger | −10% or rolling ES99 > 2.5% | −15% or Basel yellow | −20% | −25% or Basel red | Tech > 20% of fund (look-through) | Every year |
|---|---|---|---|---|---|---|
| Action | watch | review | act | mandatory committee decision | review | annual review |
