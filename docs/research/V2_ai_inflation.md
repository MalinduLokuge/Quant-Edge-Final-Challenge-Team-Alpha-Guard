# V2 AI / tech-led crash with inflation (scenario T + I, D44) [E]

**Reproduce:** `python scripts/research_v2_ai_inflation.py` → `outputs/tables/research_v2_ai_inflation.csv` (about 1 min).

**Question:** how does O6 stand up to an AI-bubble crash? The existing scenarios were B (AI unwind with recession, in which rates fall and bonds help) and T (tech-led crash, with no bond or gold credit). Neither combines a tech crash with sticky inflation, where bonds fall too, as in 2022. T also had no robustness checks.

## Method
- **T** is the D35 look-through shock. Each equity ETF moves by its technology share × the tech move plus the rest × the other-equity move: −40 / −10% central, −65 / −25% severe. It reproduces `stress_results.csv` (O6 9.2% / 16.7%).
- **T + I** is T plus the inflation-rates leg of scenario A at the same severity: real yield +40 / +100 bp, breakeven +20 / +50 bp, Baa spread +50 / +150 bp. That leg is applied to AGG and GLD through their full-sample factor betas. Equities keep only the T move, so nothing is counted twice.
- **Robustness:**
  - equity leg × 1.5 and rates leg × 1.5;
  - a Monte Carlo of 20,000 draws, each shock drawn from triangular(0.5 × central, central, severe), as in the A / B Monte Carlo, with the same draws for both portfolios.

## Results

| Loss | O6 central | O6 severe | Severe, equity × 1.5 | Severe, rates × 1.5 | MC p95 / p99 | Policy 40/50/10 severe |
|---|---|---|---|---|---|---|
| T tech-led crash | 9.2% | 16.7% | **25.1%** | — | 13.3% / 14.5% | 14.7% (× 1.5: 22.0%) |
| **T + I tech crash with inflation** | 11.5% | **22.8%** | **31.2%** | **25.9%** | 16.7% / 17.9% | 20.5% (× 1.5: 27.8%) |

- Bonds and gold add **6.1 pp** to O6's severe T + I loss (2.3 pp central) instead of cushioning it.
- None of the Monte Carlo draws exceeds 25%. The draws stay within the central–severe range, so the 1.5× cases lie outside them.

## Reading
1. **T + I is the worst hypothetical scenario.** At 22.8% it is close to the 2008 replay (23.5%) and within the 25% stress limit.
2. **A larger shock breaches the limit.** 1.5× the equity leg means tech −97.5%, beyond the dot-com fall of about 78% over 2000–02. 1.5× the rates leg means real yields +150 bp. The policy benchmark breaches as well.
3. **The weakness is shared, not O6-specific.** O6 loses about 2 pp more than the benchmark because of its technology exposure (17.7% look-through). The bigger effect is bonds failing as a hedge, which hits any 60%-bond portfolio.
4. **Remedies already tested:** less XLK (D35) deepens the 2008 drawdown and lowers return within D7. More gold improves inflationary losses by under 1 pp (D43). Following the T11 design rule (a breach at 1.5× → keep the limit with D23, or test a hedge), we keep the limit. The D23 ladder (review at −15%, act at −20%) and the D37 technology trigger (review above 20%) are the response.

## What the worst case says about the allocation (`research_v2_ai_inflation_whatif.csv`)
O6 changed by hand, with everything else fixed. Each portfolio gets the same T + I severe shock, the 2008 replay and the D7 / D27 tests.

| Portfolio | T + I severe | 2008 replay | Expected return (geo) | Largest ES share | P(DD > 25%, 5y) |
|---|---|---|---|---|---|
| **O6** | **22.8%** | **−23.5%** | **5.80%** | SPY 40.0% | **4.9%** |
| 5 pp AGG → SPY | 24.3% | −25.2% (breach) | 5.98% | 46.8% | 7.9% |
| 10 pp AGG → SPY | 25.9% (breach) | −28.1% | 6.15% | 52.6% | 14.1% |
| 20 pp AGG → SPY | 28.9% | −34.0% | 6.46% | 62.1% | 23.6% |
| XLK → SPY | 20.4% | −23.5% | 5.75% | 62.1% (D27 breach) | 4.6% |
| XLK → AGG | 17.3% | −20.8% | 5.35% | 44.4% | 1.8% |
| 60/40 SPY/AGG | 28.2% | −35.0% | 6.47% | 95.7% | 24.0% |
| Policy 40/50/10 | 20.5% | −25.3% (breach) | 5.79% | 50.9% | 9.0% |

- **Bonds:** in T + I, AGG falls 9.9% against 43.4% for O6's equities. Bonds stop hedging, but they still lose four times less than equities. Any shift from bonds to stocks breaks D7: at 5 pp in the 2008 replay and the 5-year test, and at 10 pp in T + I itself. The 61% AGG weight is what keeps both the inflationary and the deflationary worst cases inside 25%.
- **Benchmark:** the policy mix has the same expected return as O6 (5.79% vs 5.80%) but fails D7. O6 earns that return within the committee's limits.
- **Tech tilt:**
  - XLK is why O6 loses 2.3 pp more than the benchmark in T + I.
  - It cannot move into SPY: SPY is already at the D27 cap of 40% of 99% ES, and the swap would take it to 62%.
  - Moving XLK into AGG lowers the T + I loss to 17.3% but costs 0.45 pp of expected return a year (about $45,000 of spending).
  - The tilt is a deliberate, capped cost, monitored by the D37 trigger. This scenario shows its price; it does not show that the tilt protects.

## Also fixed in the documents
- **Report §7:** the Monte Carlo 99th percentile was given as 15.5% for both scenarios. It is 15.5% for A and 14.6% for B.
- **Report §7:** the B 12-month path is now reported: worst fall 15.5%, 12-month result −11.9%, next year's spending $265,000 → $257,432.
- **Report §10 and A&L:** no dot-com-style crash in the 2004–26 data; the scenarios are one-step shocks with linear betas.

## Limitations
- The scenarios are one-step shocks and carry no probabilities. Factor betas are linear, and the GLD and XLE betas are unstable (T11).
- Pairing T's equity move with A's rates leg is a design choice: the correlation between a tech crash and inflation is assumed, not estimated.
- The look-through technology shares are as of 29 October 2026, and EFA and EEM are approximate (D35).
