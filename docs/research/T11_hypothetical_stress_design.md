# T11 Hypothetical stress testing: research and design report

**Status:** research and design for approval. No pipeline code changes yet.
- The approved D9 stays in force until the proposed **D9 v2** below is approved.
- Research scripts used: `hs_research.py`, `hs_calib.py`, `hs_path.py`. They will be turned into the pipeline module described in §8.

**Data date:** new FRED snapshots downloaded 2026-10-29 (last observation 2026-10-27), ETF prices to 2026-10-19 (D5).

**Evidence tags:**

| Tag | Meaning |
|---|---|
| [V] | Verified data (FRED or yfinance, in the repo) |
| [H] | Historical observation |
| [F] | Published forecast or official scenario (context only, not a model input) |
| [N] | News or secondary report |
| [A] | Our scenario assumption |

**Data-source rule (brief p.9):**
- **Model inputs:** yfinance and FRED only.
- **Context only:** IMF, World Bank, IEA, EIA and Federal Reserve publications are cited for context. All are disclosed (§10).

---

## 1. Current economic risk assessment

### 1.1 Verified starting point [V]
FRED series are as of 2026-10-27; ETF prices as of 2026-10-19.

| Variable | Now | Percentile vs history | Change in 2026 |
|---|---|---|---|
| Brent oil | **$123** | **99th** (since 1987) | $61 → $127 (Mar) → $70 (Jun) → $123 |
| WTI oil | $103 | 96th | Brent–WTI spread $20: seaborne (Gulf) disruption |
| 10y Treasury | 5.00% (5.29% end-Sep) | 47th (since 1962), highest since 2002 | +0.8 pp since Dec 2025 |
| 10y real yield (TIPS) | **2.64%** | **99th** (since 2003) | +0.7 pp |
| 10y breakeven inflation | 2.35% | 73rd | stable: inflation expectations still anchored |
| 2y Treasury | 4.70% | 51st | +1.2 pp (policy tightening priced) |
| Fed funds | 3.75% (Sep) | — | first hike since 2023 |
| CPI inflation, yoy | **4.0%** (Sep) | — | from 2.7% in Feb |
| Unemployment | 4.2% | — | stable |
| Baa–10y credit spread | **1.45 pp** | **3rd** (since 1986) | near record tight |
| ICE BofA HY spread | 3.18 pp | (FRED holds only 3 years) | — |
| USD broad index | 121.3 | 90th (since 2006) | — |
| VIX | 17.5 | 50th | peaked 25 in Mar 2026 |
| SPY / XLK | −1.6% / −7.9% from their 52-week highs | — | 1-year +17% / **+31%** |
| XLE | at its high | — | 1-year **+64%** |
| GLD | −23% from Feb 2026 peak | — | fell 11% in the Mar 2026 oil spike |
| SPY–AGG 1-year correlation | **+0.44** | positive on 98% of days since 2022 | was −0.21 on average in 2015–19 |

### 1.2 What is driving it [N, F]
- **Energy supply shock:**
  - The US–Israel strikes on Iran on 28 Feb 2026 led to attacks on Gulf infrastructure and a halt of tanker traffic through Hormuz. About 20% of world supply was affected, which CNN described as "the biggest oil disruption in history". Brent rose 51% in March ([IEA OMR Mar 2026](https://www.iea.org/reports/oil-market-report-march-2026), [CNN](https://www.cnn.com/2026/03/09/economy/oil-price-shock), [CNBC](https://www.cnbc.com/2026/04/21/oil-price-iran-war-middle-east.html)).
  - An April truce and a June interim ceasefire brought prices down.
  - The ceasefire collapsed in September after attacks on vessels in Hormuz ([oilprice.com](https://oilprice.com/Latest-Energy-News/World-News/Oil-Prices-Jump-over-7-as-Iran-Ceasefire-Declared-Over.amp.html)).
  - **IEA, Oct 2026:** Gulf exports have recovered to more than 75% of pre-war levels, but new attacks "threaten to derail further gains". Product inventories are unlikely to be rebuilt before the second half of 2027 ([IEA OMR Oct 2026](https://www.iea.org/reports/oil-market-report-october-2026)).
- **Monetary policy:**
  - On 16 Sep 2026 the Fed raised rates to 3.75–4.00%, by a 12–0 vote.
  - The 2026 core PCE projection is 3.4%; 15 of 18 participants see upside inflation risk; most expect another hike this year ([Fed statement](https://www.federalreserve.gov/monetarypolicy/files/monetary20260916a1.pdf), [CNBC](https://www.cnbc.com/2026/09/16/fed-rate-decision-september-2026.html)).
- **Bond market:**
  - The 10y yield hit 5.34% on 1 Oct, the highest since 2002.
  - The selloff is linked to debt and fiscal worries, heavy Treasury and AI-related corporate issuance, and a rising term premium ([Korea Herald / FT summary](https://biz.heraldcorp.com/article/10892348)).
- **Global outlook (IMF WEO, Oct 2026):**
  - Growth is 3.1% in 2026 and global inflation 4.7%.
  - The baseline assumes oil averages $96 and Hormuz flows resume by March 2027.
  - Risks are tilted to the downside: energy, low European gas stocks, a reversal of the AI boom, and fiscal stress ([IMF WEO Oct 2026](https://www.imf.org/en/publications/weo/issues/2026/10/13/world-economic-outlook-october-2026)).
  - The World Bank's April 2026 outlook saw $115 Brent if the war lasted longer ([The Star / World Bank CMO Apr 2026](https://www.thestar.com.my/business/business-news/2026/05/29/world-bank-sees-brent-oil-averaging-us86-in-2026-easing-to-us70-in-2027)).
- **Valuations:**
  - The S&P 500 trades at about 19–21× forward earnings ([First Trust](https://www.ftportfolios.com/Commentary/Insights/2026/10/5/market-minute---october-2026), [YCharts](https://ycharts.com/indicators/sp_500_pe_ratio_forward_estimate)).
  - The Fed's 2026 Financial Stability Report flags elevated valuations and AI concentration; 50% of surveyed participants name AI as a salient risk ([ICBA summary](https://icba.org/w/fed-s-financial-stability-report-highlights-key-risks-2), [PYMNTS](https://www.pymnts.com/cpi-posts/fed-survey-finds-increased-worries-about-ais-impact-on-financial-stability/)).

### 1.3 Vulnerabilities that matter for *this* portfolio
D26 holds AGG 58.1%, SPY 19.6%, XLK 10.0%, EFA 9.0%, XLE 3.1% and GLD 0.1%.

1. **Rate risk on 58% of the fund.** AGG loses about 5.1% per +1 pp rise in the 10y yield (§4, R² 0.91). The 10y is already at a 24-year high, and the Fed is hiking into an energy shock.
2. **The stock–bond hedge is weak today [V].** The correlation is +0.44, compared with −0.33 in 2008. In an inflationary shock, both halves of the portfolio fall together, as in 2022.
3. **Equity risk is concentrated in US growth:**
   - SPY and XLK carry about 60% of the 99% ES (P2 §6a).
   - The equity risk premium is thin. The earnings yield is about 5% against a 2.6% real yield, a premium of about 2.4 pp compared with a historical premium of about 4 pp [our calculation].
4. **Credit is priced for perfection.** Spreads are at the 3rd percentile, so they have room to widen. AGG holds about 25% corporates.
5. **Few real hedges:**
   - Gold is 0.1% of the fund, and it *fell* in the March oil shock as real yields and the dollar rose [V].
   - XLE is 3.1%, and it rose 10% in March 2026 and 67% in 2022 [V].
6. **Less relevant here:** an EM or dollar crisis. D26 holds no EEM; EFA carries currency risk (dollar beta −1.2).

---

## 2. Scenario comparison

| | **A. Energy stagflation with a bond selloff** | B. AI-led equity correction, recession and credit stress | C. Bond and term-premium shock | D. EM / dollar crisis |
|---|---|---|---|---|
| **Trigger** | Hormuz closes again, attacks on Gulf infrastructure, product shortages | AI capex disappointment or a profit shock, with rich valuations and concentration | Fiscal or deficit scare, heavy issuance, the Fed behind inflation | Strong dollar plus capital outflows |
| **Plausible now because** | It happened in Mar 2026 [V]; the ceasefire collapsed in Sep [N]; IEA warns [F]; the Fed is already hiking [V] | Fed FSR and IMF name AI reversal as a key risk [F]; XLK +31% in a year; credit spreads at the 3rd percentile [V] | The 10y hit 5.34%, a 2002 high [N]; real yield at the 99th percentile [V] | The dollar is at the 90th percentile; EM sensitive to oil and the dollar |
| **Sequence** | Oil ↑ → inflation ↑ → Fed hikes → real yields ↑ → equities re-rate ↓, credit ↑, dollar ↑ | Earnings or AI guidance cut → equities ↓ (tech most) → spreads ↑ → recession → Fed cuts → yields ↓ | Term premium ↑ → long yields ↑ → equity and bond prices ↓ together | Dollar ↑ → EM currencies ↓ → EM equities ↓ |
| **Hits** | **Both** bonds and equities; only XLE hedges | Equities, XLK most; **AGG hedges** | Bonds and equities | EEM and EFA |
| **Relevance to D26** | **Highest:** attacks the 58% bond sleeve *and* equities at once | High: SPY + XLK = 30%, but bonds offset | High, but a sub-case of A (no oil) | Low: no EEM |
| **Evidence for size** | Mar 2026, 2022, the 1990 Gulf war; 3-month factor tails | 2000–02, 2008, 2020, DFAST 2026 | 2022, 1994, Oct 2023 | 2008, 2013, 2015 |
| **Weakness** | Oil–equity link depends on the shock's source (§4.3) | Similar to the historical GFC replay | No macro trigger; overlaps A | Not material for D26 |

**Recommendation:**
- **Primary hypothetical: A**, at two severities (central and severe). It is the scenario the current data most directly supports. It is also the one where the endowment's main defence (bonds) fails, which is exactly what the historical replays under-represent: only 2022 is similar.
- **Secondary: B**, as the deflationary mirror image. It shows the bond hedge working, and it tests the XLK and SPY concentration the D27 cap was designed for.
- **C** becomes a sensitivity of A (no oil, larger real-rate shock).
- **D** is not used: D26 has no EEM.

---

## 3. Recommended primary scenario narrative (A, "Hormuz II")

> **Q1 (shock month):** The ceasefire fails for good. Hormuz traffic stops again and Gulf infrastructure is hit. Brent jumps from $123 toward $150–185.
>
> **Q1–Q2:** Headline inflation rises toward 5–7%. With core PCE already at 3.4%, the Fed (on record that inflation must return "clearly and at sufficient speed") hikes further.
>
> **Q2:** Real yields and the term premium rise. Equities de-rate from 21× forward earnings. Credit spreads widen from record tights. The dollar strengthens.
>
> **Q3–Q4:** Partial normalisation. Oil eases on demand destruction and SPR releases. Rates stay high, so bonds do not recover.

The endowment holds through the shock and rebalances quarterly (D11). Spending follows the smoothed D24 rule.

---

## 4. Proposed shock parameters (D9 v2)

### 4.1 Factors
The model uses six factors, each from FRED or yfinance [V]:

| Factor | Series | Why this one |
|---|---|---|
| Equity market | SPY return | market factor |
| Real rate | ΔDFII10, 10y TIPS yield (pp) | drives gold and the equity discount rate |
| Inflation expectations | ΔT10YIE, 10y breakeven (pp) | real + breakeven = nominal 10y, so no separate nominal factor (avoids double counting) |
| Credit | ΔBAA10Y, Moody's Baa – 10y (pp) | 40 years of history; ICE HY on FRED now has only 3 years |
| Oil | Δlog Brent (DCOILBRENTEU) | global seaborne benchmark |
| Dollar | Δlog DTWEXBGS, broad USD | currency effect on EFA, EEM and GLD |

### 4.2 Shock calibration (12-month totals; month 1 carries most of the oil and equity move)

| Factor | Start | **Central** | **Severe** | Range tested | Evidence |
|---|---|---|---|---|---|
| Brent | $123 | **+25% → ~$155** | **+50% → ~$185** | +12% to +60% | Mar 2026: +78% in 1 month from $71 [V]; 1990 Gulf war: +78% in 3 months [V]. 3-month log change: 95th pct +0.30, 99th pct +0.58 [V]. Smaller % than Mar 2026 because the start is already at the 99th percentile and demand destruction caps prices [A] |
| 10y breakeven | 2.35% | **+20 bp** | **+50 bp** | +10 to +60 bp | Anchored in 2022 (−23 bp in H1) and Mar 2026 (+5 bp) [V]; 3-month 95th pct +42 bp, 99th +63 bp [V]. Severe = expectations start to de-anchor [A] |
| 10y real yield | 2.64% | **+40 bp** | **+100 bp** | +20 to +125 bp | 2022 H1 +169 bp [V]; 3-month 95th pct +65 bp, 99th +117 bp [V]; Fed signalling further hikes [F] |
| → nominal 10y | 5.00% | → 5.60% | → 6.50% | | 2022: +258 bp over 10 months [V] |
| Baa spread | 1.45 pp | **+50 bp** | **+150 bp** | +25 to +225 bp | Gulf war +36 bp, 2022 +43 bp, GFC Q4 +182 bp [V]; starting at the 3rd pct; DFAST 2026 severe: corporate spreads to 5.7 pp [F] |
| USD broad | 121.3 | **+4%** | **+8%** | +2% to +10% | 2022 +10.7%, Mar 2026 +2.7% [V]; 3-month 99th pct +7% [V] |
| SPY | — | **−15%** | **−30%** | −7% to −45% | Mar 2026 −5% [V]; 2022 H1 −20% [V]; 1990 S&P −20% peak to trough [H]. Cross-check: price ≈ E/(r−g), so ΔP/P ≈ −Δ(real yield + equity risk premium)/earnings yield; +40 bp real + 50 bp ERP ≈ −18%, and +100 + 100 bp ≈ −40% (upper bound) [A] |

The shocks hang together: oil up, breakevens up, real yields up, credit wider, dollar up and equities down all match the sign pattern of 2022 and March 2026 [V]. Each factor enters the ETF equations once (§4.3), so nothing is double counted.

### 4.3 How factor shocks become ETF moves (method comparison)

| Method | Pros | Cons | Use |
|---|---|---|---|
| Full-sample multifactor OLS (monthly, Feb 2006–Oct 2026, 249 months) | Joint partial effects, so no double counting; R² 0.58–0.91; reproducible | Assumes stable betas; oil–equity link is demand-driven on average | **Primary for AGG, EFA, EEM, XLK** |
| Stress-subsample betas (83 months with SPY in its bottom quartile or credit widening in its top quartile) | Captures correlation change | Fewer data points | **Sensitivity** |
| Duration-based for AGG (D × Δy + spread duration × Δs) | Structural | Needs external fact-sheet data, not an allowed source | Cross-check only: our implied rate sensitivity is 5.1, near AGG's published ~6 years |
| Factor-on-factor conditional expectation (derive SPY from oil) | Fully data-driven | **Wrong sign for supply shocks:** quarterly oil–SPY correlation is +0.42 (demand-driven, Kilian 2009) | **Rejected:** SPY is set from supply-shock episodes instead |
| Episode analogues | Real outcomes | Few episodes, each unique | **Calibrates XLE and GLD ranges** and validates the model |

**Back-test of the factor model on real episodes** (actual factor moves fed through the full-sample betas):

| Mean absolute error | AGG | EFA | EEM | XLK | GLD | XLE |
|---|---|---|---|---|---|---|
| Six episodes (GFC Q4 2008, COVID Q1 2020, 2022 H1, 2022 Jan–Oct, Mar 2026, Mar–Oct 2026) | **1.0 pp** | 2.1 pp | 1.8 pp | 6.0 pp | 8.3 pp | **21.9 pp** |

- **Reliable:** AGG, EFA, EEM and XLK. For example, 2022 Jan–Oct AGG was −15.5% actual vs −15.3% model; March 2026 EFA was −7.8% vs −6.6%.
- **XLE is not reliable.** The model misses 2022 (+67% actual vs −5% model) because energy equities re-rated on profits. In supply shocks the model **understates** XLE's hedge. So:
  - **Central and severe cases:** model XLE (no extra hedge credit). This is conservative.
  - **Hedge variant:** XLE oil beta from the March 2026 and 2022 episodes (+0.5 instead of +0.23).
- **GLD is not reliable.** Errors run both ways: the model says −30% in 2022 vs −11% actual, and −17% vs −22% in Mar–Oct 2026. Report a ±10 pp band. Only 0.1% of D26, but 12% of risk parity.

---

## 5. ETF impact (full-sample betas, primary scenario)

| ETF | Main drivers (betas) | **A central** | **A severe** | B central | B severe |
|---|---|---|---|---|---|
| AGG | −5.1% per +1 pp real yield, −5.1% per +1 pp breakeven, −1.5% per +1 pp Baa spread | **−4.7%** | **−11.7%** | +1.6% | +2.7% |
| SPY | scenario input | −15.0% | −30.0% | −25.0% | −40.0% |
| EFA | 0.68 SPY, −1.21 USD | −15.9% | −32.5% | −21.7% | −37.4% |
| EEM | 0.51 SPY, −1.83 USD | −16.8% | −34.7% | −21.5% | −39.5% |
| XLK | 1.22 SPY, +0.40 USD | −17.7% | −35.6% | −28.5% | −45.0% |
| XLE | 0.72 SPY, +0.23 oil (hedge variant: +0.5 oil) | −4.1% (hedge variant +2%) | −7.3% (+4%) | −26.8% | −46.2% |
| GLD | −0.38 SPY, −8.1% per +1 pp real yield, −1.46 USD | −3.4% (±10) | −8.3% (±10) | +8.8% | +13.7% |

Scenario B is SPY −25% / −40%, real yield −50 / −100 bp, breakeven −30 / −60 bp, Baa +100 / +250 bp, Brent −25% / −45% and USD +3% / +6%. DFAST 2026 severely adverse (equities −58%, VIX 72) is the outer reference [F].

---

## 6. Portfolio impact (saved P1-final weights)

### 6.1 Instant scenario loss (% of $10M)

| Scenario | **D26 selected** | Min-variance | Min-CVaR | Risk parity | Max-Sharpe | Policy 40/50/10 |
|---|---|---|---|---|---|---|
| **A central** | **9.0% ($0.90M)** | 6.8% | 6.7% | 7.6% | 9.4% | 8.9% |
| **A severe** | **19.4% ($1.94M)** | 15.4% | 15.2% | 16.7% | 20.1% | 19.2% |
| B central | 9.6% | 3.7% | 3.3% | 6.0% | 10.4% | 7.8% |
| B severe | 15.6% | 5.8% | 5.2% | 10.1% | 16.5% | 13.0% |
| C term-premium (sensitivity) | 11.4% | 10.2% | 10.1% | 10.2% | 11.9% | 10.9% |
| *Approved D9 v1 (for reference)* | *16.7%* | *13.9%* | — | *13.7%* | *17.5%* | *15.9%* |

**D26 contributions in A severe:**

| Holding | Contribution to the 19.4% loss |
|---|---|
| AGG | −6.8 pp (largest single source) |
| SPY | −5.9 pp |
| XLK | −3.6 pp |
| EFA | −2.9 pp |
| XLE | −0.2 pp |

In B severe, AGG *adds* +1.6 pp and equities drive the loss.

**Diversification:**
- **Scenario A:** 58% of the fund is in bonds, yet bonds deliver 35% of the loss.
- **Scenario B:** bonds offset about 9% of the equity loss.

This is the 2022 regime. The current +0.44 stock–bond correlation [V] says it is the regime we are in now.

### 6.2 Path through 12 months (monthly factor path, quarterly rebalancing D11, 10 bp trading cost [A], D24 spending)

| Scenario | Portfolio | Worst point | After 12 months | Turnover | Next-year spending (D24) | AGG holding in years of spending |
|---|---|---|---|---|---|---|
| A central | D26 | −9.0% | −7.8% | 3.8% | $405k (real −3.7%, 4.39% of NAV) | 13.2 |
| A severe | D26 | **−19.3%** | −16.8% | 8.0% | $399k (real −6.7%, 4.80% of NAV) | 12.1 |
| A severe | Policy 40/50/10 | −18.7% | −16.8% | 7.8% | $399k | 10.4 |
| A severe | Risk parity | −16.3% | −14.8% | 6.8% | $402k | 11.6 |

- **Costs:** trading costs are negligible, under 0.02% of NAV.
- **Spending:** the D24 smoothing limits the real spending cut to 6.7% in the severe case. A pure % of NAV rule would cut it by about 20%.
- **Liquidity:** spending never requires selling equities at the bottom, because AGG covers more than 10 years of spending. AGG's own 1-day dislocations (−6.8% on 2008-10-10, T11 §3) argue for keeping about 1 year of spending in the most liquid sleeve. This is noted for the memo, not modelled.

### 6.3 Against the limits

| Limit | What it measures | A central | A severe |
|---|---|---|---|
| Stress loss ≤ 25% (D7) | Cumulative scenario loss | 9.0%: pass | **19.4%: pass, 5.6 pp headroom** |
| Max drawdown 25% (D7) | Peak to trough on the path | 9.0%: pass | 19.3%: pass. D23 ladder: **"act" at −20% is nearly reached** |
| 1-day ES99 ≤ 2.5% (D7) | **Average loss on the worst 1% of single days**, unconditional | Not comparable to a multi-month scenario loss | Scenario-conditional VaR [A: VIX 30 central / 45 severe]: GARCH-EVT VaR99 0.98% × 30/17.5 ≈ 1.7% (central), × 45/17.5 ≈ **2.5% > the 1.7% VaR limit** (severe) → D23 "watch" and "act" triggers via rolling ES99 |

**Why the ES limit is a different test:**
- The ES limit is a daily statistical limit calibrated on full-cycle history. A stress loss is the sum of many days, including days far less extreme than the 1% tail.
- Example: a 19% loss over a quarter is about 63 days averaging −0.3% a day. No single day needs to breach ES.
- The two limits therefore answer different questions: "how bad is a bad day?" versus "how bad is a bad episode?"

---

## 7. Severity and robustness

| Test (D26, scenario A) | Loss |
|---|---|
| Central / severe | 9.0% / 19.4% |
| Stress-subsample betas (correlation breakdown) | 8.5% / 18.0%. Similar, because AGG's betas are stable in stress |
| **Each severe factor × 1.5, one at a time** | SPY → **25.7% (breach)**; real yield → 20.9%; breakeven, Baa → 20.2%; USD → 20.0%; oil → 19.4% |
| Monte Carlo: 20,000 draws, shocks drawn between half-central and severe, betas drawn with their standard errors, residual noise | Median 10.8%, 95th pct 14.7%, 99th pct 16.0%, P(> 25%) ≈ 0 |
| XLE hedge variant (oil beta 0.5) | About −0.3 pp |
| GLD ±10 pp | ±0.01 pp for D26; ±1.2 pp for risk parity |

**Reading:**
1. **The equity shock decides the result.** Rates and credit add 1–1.5 pp each, while oil works almost entirely through the other factors.
2. **The bond sleeve fails in this scenario,** so a further equity fall of about 45% would breach the limit in combination with severe rate shocks. The recommendation, D26 passes, holds unless equities fall far more than in 2022 *while* real yields rise by 1 pp or more.
3. **Ranking is robust:**
   - Lowest losses in both A and B: min-variance and min-CVaR.
   - Close to the policy benchmark: D26.
   - Highest: max-Sharpe.

---

## 8. Integration and implementation plan (after approval)

**Data (data stage):**
- Add FRED series to `config.data.fred_series`: DFII10, BAA10Y, DCOILBRENTEU, DCOILWTICO, DTWEXBGS, VIXCLS and DGS2. Snapshots are already in `data/external/`.
- Write a monthly factor panel to `data/processed/stress_factors_monthly.csv`.
- Disclose all new series in README and report.

**Config `stress.hypothetical` (D9 v2):**
- Scenarios A and B with central, severe and range values.
- Month profiles.
- XLE and GLD variant settings.
- Trading cost 10 bp.
- Monte Carlo draws 20,000 with seed 42.

**Module `validation/hypothetical.py`:**
- `factor_panel` and `fit_betas`: full and stress samples, with standard errors.
- `backcast`: episode validation.
- `scenario_shocks`: betas × factor vector, plus stated variants.
- `instant_impact`: % and USD, contributions.
- `path`: monthly path with quarterly rebalancing, costs and D24 spending.
- `uncertainty_mc` and `one_at_a_time`.
- `scenario_var`: GARCH-EVT VaR scaled by stressed volatility.

**Outputs:**
- `stress_hyp_betas.csv`, `stress_hyp_backcast.csv`, `stress_hyp_shocks.csv`, `stress_hyp_results.csv`, `stress_hyp_paths.csv`, `stress_hyp_sensitivity.csv`.
- The existing `stress_results.csv` gains the new rows; historical replays are unchanged.

**App (stress page):**
- Scenario and severity selector.
- Factor sliders that recompute live from the saved betas.
- Waterfall of contributions, 12-month path chart, limits table.

**Decision link (T20):**
- Severe A loss and headroom go into the memo's "what can go wrong / how bad / how confident" section.
- If the approved limit is breached at the 1.5× equity shock, propose either keeping the limit (with the D23 ladder) or a gold or XLE hedge test (T4.25).

**Tests:**
- Betas recover synthetic loadings.
- Back-cast arithmetic.
- A zero shock leaves NAV unchanged.
- Rebalancing cost equals 2 × turnover × cost.
- The D24 formula.
- Monte Carlo is reproducible with a fixed seed.
- The scenario factor vector matches the config.
- Portfolio loss equals the sum of contributions.

**Unchanged:**
- D6, D7, D12, D11 and D24 are used as approved.
- Historical replays (T11.01–T11.10) stay as they are.
- D9 v1 numbers stay in the record for comparison.

---

## 9. Limitations
- **Linear model:** factor betas come from monthly data and are linear. Large, fast moves (a one-month oil jump of +50%) are extrapolations. Convexity, gaps and liquidity spirals are not modelled.
- **Unstable relationships:** sector re-rating (XLE in 2022) and gold's link to central-bank buying are not captured. They are handled by variants and bands, not fixed.
- **Hand-set paths:** the shock paths (month profiles) are assumptions; the order of events changes drawdowns more than end losses.
- **Credit proxy:** Moody's Baa – 10y is investment-grade. A high-yield credit event would be larger. AGG holds no high yield, so the effect on our ETFs is limited.
- **No probabilities:** scenarios are not forecasts and carry no probabilities. "Central" means a plausible adverse case, not the expected case.
- **Short history:** the six-factor history starts in 2006, so oil shocks before 2006 (1990, 1973–74, 1979) inform magnitudes only.
- **News sources:** news and secondary summaries [N] are context; key facts were cross-checked against FRED data where possible.

## 10. Sources

**Data (model inputs):**
- **FRED:** DCOILBRENTEU, DCOILWTICO, DGS10, DGS2, DFII10, T10YIE, BAA10Y, BAMLH0A0HYM2 (3-year history only, context), DTWEXBGS, VIXCLS, FEDFUNDS, UNRATE, CPIAUCSL, NFCI. Downloaded 2026-10-29.
- **yfinance:** ETF adjusted prices.

**Context:**
- **IEA:** [OMR Mar 2026](https://www.iea.org/reports/oil-market-report-march-2026), [12 Mar update](https://iea.blob.core.windows.net/assets/a25ddf53-cd6c-4910-ac90-16bfd28399e7/-12MAR2026_OilMarketReport.pdf), [OMR Oct 2026](https://www.iea.org/reports/oil-market-report-october-2026).
- **EIA:** [Q1 2026 prices](https://www.eia.gov/todayinenergy/detail.php?id=67424).
- **IMF:** [WEO Oct 2026](https://www.imf.org/en/publications/weo/issues/2026/10/13/world-economic-outlook-october-2026).
- **World Bank:** CMO Apr 2026, via [The Star](https://www.thestar.com.my/business/business-news/2026/05/29/world-bank-sees-brent-oil-averaging-us86-in-2026-easing-to-us70-in-2027).
- **Federal Reserve:** [FOMC 16 Sep 2026](https://www.federalreserve.gov/monetarypolicy/files/monetary20260916a1.pdf), [press conference](https://www.federalreserve.gov/mediacenter/files/FOMCpresconf20260916.pdf), [2026 stress test scenarios](https://www.federalreserve.gov/publications/files/2026-final-supervisory-stress-test-scenarios-20260204.pdf); Financial Stability Report via [ICBA](https://icba.org/w/fed-s-financial-stability-report-highlights-key-risks-2) and [PYMNTS](https://www.pymnts.com/cpi-posts/fed-survey-finds-increased-worries-about-ais-impact-on-financial-stability/).
- **News:** [CNN](https://www.cnn.com/2026/03/09/economy/oil-price-shock), [CNBC Apr](https://www.cnbc.com/2026/04/21/oil-price-iran-war-middle-east.html), [CNBC Sep](https://www.cnbc.com/2026/09/16/fed-rate-decision-september-2026.html), [oilprice.com](https://oilprice.com/Latest-Energy-News/World-News/Oil-Prices-Jump-over-7-as-Iran-Ceasefire-Declared-Over.amp.html), [Korea Herald](https://biz.heraldcorp.com/article/10892348), [First Trust](https://www.ftportfolios.com/Commentary/Insights/2026/10/5/market-minute---october-2026), [YCharts](https://ycharts.com/indicators/sp_500_pe_ratio_forward_estimate).
- **Method:** Kilian (2009, AER) on supply vs demand oil shocks; McNeil, Frey & Embrechts for the risk-model context.

## 11. Decisions requested
1. **D9 v2:** replace the D9 v1 calibration with scenario A at central and severe levels, using the six-factor model and the XLE/GLD treatment above.
2. **D29:** add scenario B, AI unwind with recession and credit stress, as the secondary hypothetical. Keep C as a sensitivity and drop D.
3. **Method:** primary model is full-sample betas, with stress-subsample betas, the XLE hedge variant, the GLD band and Monte Carlo as robustness. Approve the 10 bp trading-cost assumption.
