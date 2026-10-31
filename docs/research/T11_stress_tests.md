# T11 Stress tests [E]

**Reproduce:** `python run_all.py --only validation` → `stress_results.csv`, `stress_contributions.csv`, `stress_factor_betas.csv`, `stress_correlations.csv`.
**Weights:** P1-final (recommended D26 with the D27 cap) and the comparison portfolios; quarterly rebalancing (D11) along the real path. Limit: loss ≤ 25% in every scenario (D7).

## 1. Scenarios
| Scenario | Window | Why |
|---|---|---|
| GFC 2007–09 | 2007-10-09 → 2009-03-09 | S&P 500 peak to trough; equity and credit crash |
| Taper tantrum 2013 | 2013-05-02 → 2013-06-24 | 10y yield +1 pp in 7 weeks; bond stress (D26 is 58% AGG) |
| COVID 2020 | 2020-02-19 → 2020-03-23 | fastest crash on record; even AGG fell 4% in a day |
| Rates and inflation 2022 | 2022-01-03 → 2022-10-12 | stocks and bonds fell together (10y +2.4 pp) |
| **Hypothetical (D9 v2, approved): energy stagflation "Hormuz II"** + **D29 AI unwind with recession** | central and severe, 12-month path | see `T11_hypothetical_stress_design.md` (six-factor model) |

**Hypothetical method:** each ETF's move comes from its betas to SPY, the 10y yield and the 10y breakeven, estimated by OLS on monthly data (2004–2026). No ETF gets a hand-picked return in the primary case, so gold and energy get no hedge credit beyond their measured betas. A variant adds a 2022-style energy rally (XLE +30%) and gold +10%.

| ETF | β SPY | β 10y (per pp) | β breakeven | R² | Shock | Variant |
|---|---|---|---|---|---|---|
| AGG | 0.08 | **−0.049** | 0.01 | 0.87 | **−11.2%** | −11.2% |
| SPY | 1.00 | — | — | 1.00 | −25.0% | −25.0% |
| EFA | 0.93 | −0.015 | 0.02 | 0.74 | −24.0% | −24.0% |
| EEM | 0.94 | −0.022 | 0.07 | 0.57 | −21.1% | −21.1% |
| XLK | 1.15 | −0.002 | −0.01 | 0.78 | −29.8% | −29.8% |
| XLE | 0.85 | 0.032 | 0.11 | 0.44 | −3.8% | +30% |
| GLD | −0.09 | −0.104 | 0.13 | 0.22 | −5.5% | +10% |

**AGG rate sensitivity (T11.08):** −4.9% per +1 pp in the 10y yield (controlling for equities), an effective duration of about 5 years, estimated from the data rather than an external fact sheet.

## 2. Results: loss in each scenario (worst peak-to-trough inside the window)

| Scenario | **D26 selected** | Min-variance | Risk parity | Max-Sharpe | Policy 40/50/10 |
|---|---|---|---|---|---|
| GFC 2007–09 | **24.5%** ($2.45M) | 17.4% | 23.2% | 25.0% | 25.3% |
| Taper tantrum 2013 | **4.9%** | 4.0% | 6.2% | 4.5% | 6.0% |
| COVID 2020 | **17.0%** ($1.70M) | 11.4% | 15.4% | 16.9% | 16.0% |
| Rates and inflation 2022 | **18.0%** ($1.80M) | 16.7% | 15.3% | 19.2% | 18.6% |
| Stagflation shock (D9) | **16.7%** ($1.67M) | 13.9% | 13.7% | 17.5% | 15.9% |
| Stagflation + oil/gold spike | **15.6%** | 13.9% | 9.8% | 17.0% | 14.3% |

**D26 detail:** worst day −5.2% (2008-10-10) and −6.2% (2020-03-12). Recovery to the pre-crisis level: GFC 277 trading days after the trough, COVID 53, 2022 303, taper tantrum 16 (D26 weights at the time of T11). Final O6 (`stress_results.csv`): GFC 254, COVID 52, 2022 325, taper tantrum 18.

## 3. Findings
1. **No breach (T11.10):** D26 passes every scenario. The GFC is the binding one (24.5% vs the 25% limit). That is by design, because D7 includes the 2008 replay, but it leaves only 0.5 pp of headroom. A deeper crisis than 2008 would breach.
2. **What drives the loss (T11.06):** equities. In the GFC, SPY contributed −10.7 pp of the window loss, XLK −5.1 and EFA −5.4; AGG *gained* +4.2 pp. In 2022 the roles flipped: AGG lost −8.7 pp, the largest single loss, because bonds and stocks fell together. In the stagflation shock, AGG (−6.5 pp) and SPY (−4.9 pp) both lose.
3. **Diversification weakens when it is needed (T11.07):** SPY–EFA correlation 0.85 in calm markets → 0.93 in stress; SPY–XLE 0.66 → 0.78. SPY–AGG moves from −0.05 to +0.06, so the bond hedge disappears on stress days. Only gold stays near zero (0.01).
4. **Inflation is the main weakness:** in 2022 and in the stagflation shock, the 58% AGG allocation is a source of loss, not protection. Gold (0.1% in D26) and energy (3.1%) are the only measured hedges. Risk parity, with 12% gold and 5% XLE, loses least in the variant (9.8%).
5. **Liquidity (T11.09):** AGG fell 6.8% on 2008-10-10 and 4.0% on 2020-03-12, far more than its rate risk explains, because the ETF traded at a discount to its bonds in the panic. Spending cash should not depend on selling AGG on such days: the D6 8% AGG floor is a liquidity buffer, and D24 smoothed spending avoids forced sales.

## 4. Possible adjustments (for the decision stage, T20)
- **Keep:** passes every limit; the drawdown limit is already binding on the GFC.
- **Inflation hedge:** raise gold toward the benchmark's 10% (D6 allows 20%). This would cut losses in 2022 and stagflation, but adds risk elsewhere and lowers CAPM expected return. To test in T4.25.
- **No extra equity:** any further equity raises the GFC loss above 25%.

## 5. Update: D9 v1 superseded by D9 v2 and D29 (2026-10-29)
The one-quarter stagflation shock of §1–2 (D9 v1; D26 loss 16.7%) is replaced in the pipeline by the research-calibrated scenarios in `T11_hypothetical_stress_design.md`.
- **New model:** six factors (equity, real yield, breakeven, Baa spread, Brent, USD), central and severe levels, 12-month rebalanced path, robustness tests.
- **D26 losses:** A energy stagflation 9.0% / **19.4%**; B AI unwind with recession 9.6% / 15.5%.
- **Unchanged:** the historical replays above, and the conclusions on inflation as the main weakness.
- **D9 v1** numbers above are kept for comparison only.
