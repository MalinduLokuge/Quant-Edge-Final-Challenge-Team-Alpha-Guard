# Assumptions & Limitations
The Streamlit page and the report section are both built from this file, so they always say the same thing.

## Data
- Risk-free rate = FRED DTB3 (3-month T-bill). Its discount-basis quote is treated as an annual yield without converting to bond-equivalent yield (≈0.1 pp difference at 4–5%).
- FRED values are carried forward to ETF trading days when FRED has no same-day value (holidays): at most 5 business days, past values only.
- Extreme returns are real market moves (verified against known events) and are kept. Flags record them; no data is removed or winsorised.
- CPI for a month is published about two weeks after it ends. Any use in decisions applies a one-month lag.
- Yahoo revises adjusted history over time, so results are reproduced from dated snapshots (prices 2026-10-20, income and FRED 2026-10-28), not live downloads.

## Client & return objective (D12, D10)
- The university's spending is assumed to be in **USD**, so US inflation (10-year breakeven) is the relevant measure and there is no currency cost. Spending in Sri Lankan rupees would add currency risk this model does not capture.
- Spending 4%, real growth 0.5% and extra costs 0.2% are team assumptions. The US endowment average is 4.8% (NACUBO FY2024), cited as context only.
- **Tax-exempt base case.** As a sensitivity, withholding is applied per ETF on its own distribution yield. With 30% on equity ETFs and AGG's interest distributions exempt, the cost is −0.09 to −0.37 pp a year; at 30% on everything (upper bound), −0.55 to −0.87 pp. Treaty rates (e.g. US–Sri Lanka) are not modelled and need checking.
- No cash sleeve or derivatives: 100% in the seven ETFs. Spending is paid by selling AGG.

## Expected returns (D12)
- Expected returns come from CAPM (today's T-bill 4.10% + β × 5% equity risk premium). They are estimates with wide uncertainty: our own-data ERP is 9.7% with a 95% CI of 3.5–15.8%.
- CAPM gives gold about 4.6% because its beta is near zero. That ignores gold's value as an inflation and crisis hedge.
- The base case uses today's T-bill (4.10%) for the whole 5-year horizon. Scenarios at 3.0% and 2.5% lower every CAPM expected return one-for-one (60/40: 6.59% → 4.99%). AGG's true sensitivity is smaller, because its current yield is locked in for about 6 years of duration.
- Variance drag uses daily-return covariance, consistent with the VaR/ES framework. Monthly returns give lower volatility (60/40: 9.4% vs 11.5%) and are reported for information only.
- Gold's expected return stays at its CAPM value (~4.6%). Its hedge value (+24.9% in the GFC, −8.8% vs −15% for AGG in 2022) is shown through stress tests, not by raising its expected return.

## Benchmarks & risk limits (D3, D6, D7)
- 1-day risk limits (% NAV): VaR99 ≤ 1.7%, ES99 ≤ 2.5% (binding); VaR95 ≤ 0.9%, ES95 ≤ 1.45% (reported). Limits sit at 99% because 95% losses occur about 13 days a year (normal noise), while 99% captures the rare crisis days, and Basel's traffic light is defined at 99%.
- **Client risk tolerance is approximated**, because the brief gives no number: tolerance = lower of willingness (mandate wording, NACUBO peer losses → ~25% peak-to-trough) and ability (capacity: with fixed 4% spending, ~20–27%). The 25% limit is conditional on a smoothed spending rule and is not a guarantee: a crisis 25% worse than 2008 would breach it.
- The policy benchmark weights (40/50/10) are a judgement fixed in advance, not an optimisation result.
- Drawdown and ES limits are calibrated on 2004–2026 data. That history contains only one 2008-type crisis, so future losses can exceed every historical figure. **Limits are targets, not guarantees.**
- Forward drawdown probabilities come from resampling past returns (block bootstrap). They cannot create crises unlike anything in the sample (e.g. 1970s stagflation or a sovereign default).
- Calibration used the full sample. Training-only data gives the same drawdowns because 2008 binds in both, but the risk limits were not chosen blind to the test period.
- The 7 ETFs are among the most liquid in the world, but in a panic they can trade below the value of their holdings (AGG −7.1% on 2008-10-10).

## Models
## Tail / EVT uncertainty
## Backtesting scope
## Not captured
