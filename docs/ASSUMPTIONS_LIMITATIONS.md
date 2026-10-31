# Assumptions & Limitations
The Streamlit page and the report section are both built from this file, so they always say the same thing.

## Data
- Risk-free rate = FRED DTB3 (3-month T-bill). Its discount-basis quote is treated as an annual yield without converting to bond-equivalent yield (≈0.1 pp difference at 4–5%).
- FRED values are carried forward to ETF trading days when FRED has no same-day value (holidays): at most 5 business days, past values only.
- Extreme returns are real market moves (verified against known events) and are kept. Flags record them; no data is removed or winsorised.
- CPI for a month is published about two weeks after it ends. Any use in decisions applies a one-month lag.
- Yahoo revises adjusted history over time, so results are reproduced from dated snapshots (prices 2026-10-20; income and core FRED series 2026-10-28; stress factors 2026-10-29), not live downloads.

## Client & return objective (D12, D10)
- The university's spending is assumed to be in **USD**, so US inflation (10-year breakeven) is the relevant measure and there is no currency cost. Spending in Sri Lankan rupees would add currency risk this model does not capture.
- **Spending about 2.65%** (D30, revised 2026-10-30), real growth 0.5% and extra costs 0.2% are team decisions. The brief sets no spending rate and does not say the fund is the university's only income. 4% was the starting assumption; it needs about 7.2% a year, which the risk limits do not allow. The US endowment average of 4.8% (NACUBO FY2024) is context only.
- **Tax-exempt base case.** As a sensitivity, withholding is applied per ETF on its own distribution yield. With 30% on equity ETFs and AGG's interest distributions exempt, the cost is −0.09 to −0.37 pp a year; at 30% on everything (upper bound), −0.55 to −0.87 pp. Treaty rates (e.g. US–Sri Lanka) are not modelled and need checking.
- No cash sleeve or derivatives: 100% in the seven ETFs. Spending is paid by selling AGG.

## Expected returns (D12)
- Expected returns come from CAPM (today's T-bill 4.10% + β × 5% equity risk premium). They are estimates with wide uncertainty: our own-data ERP is 9.7% with a 95% CI of 3.5–15.8%.
- AGG's expected return is its distribution yield on the as-of date (D25), not CAPM: with a near-zero T-bill (2014), CAPM would give bonds about 0.2%. The yield ignores future price gains or losses from rate changes and defaults.
- The optimiser uses a Ledoit–Wolf shrunk covariance (correlations shrunk toward zero by δ, variances kept). With 7 ETFs and years of daily data δ is small (0.8–1.6%), so results barely differ from the sample covariance.
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
- The 7 ETFs are among the most liquid in the world, but in a panic they can trade below the value of their holdings (AGG −6.8% on 2008-10-10 in our data).

## Hypothetical stress scenarios (D9 v2, D29)
- Scenarios are plausible adverse cases, **not forecasts**, and carry no probabilities. Shock sizes come from past episodes (1990, 2008, 2020, 2022, Mar 2026), factor-change tails and current levels.
- ETF moves use linear monthly factor betas (2006–2026). They are reliable for AGG, EFA, EEM and XLK (episode errors 1–6 pp), not for XLE (re-rates with energy profits) or GLD (central-bank demand). Those two get a hedge variant and a ±10 pp band.
- The equity fall is a scenario input. It is not derived from oil, because the average oil–equity link is demand-driven and has the wrong sign for a supply shock.
- Monthly paths are stylised: order and timing are assumptions. Gaps, convexity and liquidity spirals are not modelled. The credit factor is investment grade (Moody's Baa).
- A multi-month scenario loss is not comparable to the 1-day ES limit. Scenario VaR is a volatility rescaling of GARCH-EVT, not a re-estimated model.

## Five-year drawdown test and recovery (audit 2026-10-29)
- P(drawdown > 25% within 5 years) is a block-bootstrap estimate. It now uses 32,000 paths (Monte Carlo error about ±0.12 pp at 5%). With 4,000 paths and one seed, the selection rule had tuned itself to simulation noise.
- **The estimate depends on the block length.** Longer blocks keep bear markets intact and raise P. The test now uses **126-day blocks (D32)**, because the data's own volatility clustering lasts about 120–160 days (Politis–White). The final portfolio scores 4.94% (limit 5%); an independent re-run with other random seeds gave 4.58%. It sits close to the limit by design (D26 picks the highest-return portfolio that passes).
- In falling-rate scenarios, AGG keeps its current yield (bonds held over the horizon lock it in). New money would earn less, so low-rate results flatter bond-heavy portfolios slightly.
- **Spending at about 2.65% (D30) leaves only about 0.5% a year of expected real growth.** After any large fall the fund regains its *nominal* value within a few years, but its *real* value can take much longer (`sustainability_*.csv`). Recovery paths are stylised scenarios, not forecasts.
- **The real-recovery figures assume daily rebalancing.** With the approved quarterly rebalancing (D11), the chance of regaining real value within 15 years after a 25%+ fall is about 42–45%, not 46% (D39 note, D40). A crisis buffer that pays spending from AGG and pauses rebalancing does not improve this (D40).

## Models
- **Daily losses are far from normal.** Excess kurtosis is about 25, and Jarque–Bera and Ljung–Box tests reject normality and independence (`p2_diagnostics.csv`).
  - The normal model therefore understates the 1-day 99% loss: VaR 1.18% vs 1.39% historical, and ES 1.35% vs 2.20%.
  - A Student-t fitted to the whole sample has about 2.2 degrees of freedom and overstates ES (3.18%).
  - We rely on historical simulation, EVT and the t-copula Monte Carlo, which agree closely.
- **The Monte Carlo reuses each ETF's own history** (empirical marginals). It cannot create a single-ETF day worse than any seen since 2004; only the way ETFs fall together is simulated.
- **Two conventions for the 1-day measures.** Risk-stage VaR/ES hold weights constant every day. The D7 limit checks use the quarterly-rebalanced path (ES99 2.20% vs 2.10%). Both are within limits.
- **Expected returns come from a one-factor CAPM** with an assumed 5% equity premium. The data alone cannot pin the premium down (95% range 3.5–15.8%). Expected returns are the least certain input, which is why the selection rule tops out at the risk limits instead of chasing return.
- **Correlations and volatilities are estimated over 2004–2026 as if stable.** They are not: the stock–bond correlation has been positive since 2022, so bonds protect less against inflation-driven falls than the long-run numbers suggest.
- **Risk is measured over 1 day and over 5-year simulated paths.** Losses over other horizons are not obtained by √t scaling.

## Tail / EVT uncertainty
- **EVT fits a generalised Pareto distribution to losses above a threshold.** The threshold was chosen by a stability rule on 2004–2019 data only (D8): q = 0.92, tail shape ξ ≈ 0.28. The 99% EVT VaR is 1.43% with a 95% interval of 1.33–1.52%. At 99.5% the estimate (1.85%) rests on few observations, and beyond that EVT is extrapolation.
- **EVT assumes extreme days are independent, but real crisis days cluster.** After filtering with GARCH, the tail shape is close to zero. Most of the fat tail comes from volatility bunching up in crises, which is why GARCH-EVT is the monitoring model.
- **The data contain one 2008-type crisis, one pandemic crash and one inflation shock.** Every tail estimate, limit and stress loss is calibrated on that short list, so **the limits are targets, not guarantees.**

## Backtesting scope
- **The backtest checks whether VaR breaches happen as often as forecast, and whether they bunch together.**
  - It checks the size of losses beyond VaR only roughly (ES severity ratio 1.06).
  - It runs at 95% and 99%; the app's 90% setting shows the 99% backtest.
- **The tests have low power.** About 17 breaches are expected in 2020–26 at 99%, so models whose true breach rates differ by a fraction of a percent cannot be told apart. Passing means "not rejected", not "proven right".
- **What is truly out of sample:**
  - The VaR model was chosen using 2015–19 only and frozen before 2020–26 was run.
  - The portfolio weights in the backtest were built with data up to 2014.
  - However, 2015–26 was looked at while choosing among final portfolios, so for the portfolio choice it is not untouched. The walk-forward and future monitoring are the honest tests.
- **No model catches the first day of a sudden shock** (24 Feb 2020, 3–4 Apr 2025). Risk forecasts rise only after volatility does.

## Not captured
In plain language, the model does **not** capture:
- **Crises unlike any in 2004–2026:**
  - years of 1970s-style stagflation;
  - a US government default or a dollar crisis;
  - a war or market closure beyond the designed scenarios.
- **Trading frictions in a panic.** Results assume the ETFs trade at their closing price. In a panic, prices can gap, spreads widen, and an ETF can trade below its holdings.
- **Changes in how assets behave together.** Examples are stocks and bonds falling together for years, or gold failing as a hedge (it fell 11% in the March 2026 oil shock). Stress-model betas are linear and estimated from history.
- **Costs and taxes beyond those stated:** 0.2% a year, 10 bp on trades, and the withholding cases.
- **University-side realities.** The model does not include:
  - other income (fees, donations, grants) and the timing of large payments;
  - university cost inflation running above CPI;
  - currency risk if spending is in Sri Lankan rupees.
- **Operational risk:** late rebalancing, governance delays, errors in vendor data.
- **What is inside each ETF:** single-company concentration (e.g. a few large firms in XLK and SPY), credit quality within AGG, and climate or regulatory risk.
