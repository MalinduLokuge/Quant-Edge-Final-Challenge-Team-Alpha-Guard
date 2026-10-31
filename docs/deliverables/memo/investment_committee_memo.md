# Investment Committee Memorandum

> **DRAFT for team review (2026-10-30).** Prepared from pipeline outputs with AI assistance (see the AI disclosure); the team must confirm and own it before submission (brief §8.7). Every number traces to `outputs/p3_decision/` or `outputs/tables/`.

**To:** Investment Committee, Serendib University Endowment Fund · **From:** QuantEdge 1.0 Team Alpha Guard · **Date:** [submission date]
**Subject:** Proposed mandate for the USD 10 million endowment portfolio

### Recommendation: **ACCEPT the mandate as proposed**, with the risk limits unchanged and spending at about 2.65% a year
*Verdict confirmed by the team on 2026-10-30 (D34), in the brief's wording (D14).*

**What we propose.** Six exchange-traded funds, rebalanced quarterly to these weights, no tactical trading:

| Bonds (AGG) | US stocks (SPY) | Technology (XLK) | International stocks (EFA) | Energy (XLE) | Gold (GLD) |
|---|---|---|---|---|---|
| 61% · $6.1M | 18% · $1.8M | 10% · $1.0M | 7% · $0.7M | 3% · $0.3M | 0.4% |

**Why this portfolio.** It has the highest expected return we found within the limits the committee's principles imply: no fall beyond 25% from peak even in a 2008-style crash, about a 5% chance of such a fall within 5 years (4.9%, at the limit within simulation and model uncertainty), and no fund above 40% of the worst-day risk. These limits are on investment returns; after spending and costs the fund's value fell 25.3% in 2008, with a 9.5% chance of a 25% fall within 5 years. Its expected 5.8% a year (about 3.4% real) comes from market-based expectations, not past returns. Rebuilt every three years since 2008 with only data then available, it matched the policy benchmark's 7.3% a year with a smaller worst fall (−16% vs −19%); its higher Sharpe ratio is not statistically significant (p = 0.15), so we claim only the smaller fall.

**What it means for spending.** The brief sets no spending rate. A 4% payout would need about 7.2% a year (with our 0.5% real growth and 0.2% cost assumptions), which no portfolio within the fund's weight limits reaches; even without them it would mean falls of about 47%. We recommend **about 2.65% of the fund (about $265,000 next year)**, the rate the portfolio can sustain while keeping its purchasing power, paid through a smoothed rule: 70% of last year's spending (inflation-adjusted) plus 30% of 2.65% of current value.

**What can go wrong** (loss of the $10M):

| Scenario | Loss |
|---|---|
| A repeat of 2008 | about 23% ($2.3M) |
| Energy inflation shock (oil +50%, stocks −30%) | about 19% ($1.9M); bonds fall too, and even 20% gold would cut this by under 1 point |
| Tech-led crash (tech −65%, US stocks −40%) | about 17% ($1.7M) |
| Same crash while inflation keeps rates up (bonds fall too) | about 23% ($2.3M), our worst scenario; within the 25% limit, beyond it if 1.5× larger |
| A bad day (1 day in 100) | 1.4% ($139,000) or more; 2.2% ($220,000) on average on those days |
| Over 10 years | 1-in-5 chance real value ends below 90%; 1-in-4 of a real spending cut over 10% |
| Recovery after a 25%+ fall, still paying spending | price: 254 trading days after the 2008 trough, simulated median 3.0 years; purchasing power typically 15–20 years (about 42–46% chance within 15; 58% at 2.0% spending) |

SPY and XLK carry about 60% of the worst-day risk; counting SPY's holdings, technology is about 18% of the fund.

**How confident we are.** The daily risk model, chosen on 2015–2019 and tested once on 2020–2026, passed the breach-frequency and clustering tests (20 breaches vs 17 expected); its worst Basel window was yellow, never red. Weights built on data to 2014 kept every limit in 2015–2026, but the 3-year rebuild containing COVID reached a 1-day ES99 of 2.9% (limit 2.5%), as every portfolio did. We saw 2015–2026 while choosing the rule, and history has one 2008-type crash, so monitoring is the real test.

**What we ask the committee to approve.**
1. **The portfolio above,** rebalanced quarterly.
2. **Spending of about 2.65%** of fund value through the smoothed rule.
3. **Monitoring.** These are review points, not forced sales:

   | Fall from peak | 10%: watch | 15%: review | 20%: act | 25%: limit |
   |---|---|---|---|---|
   | Action | report | check model, stress tests, spending | decide on risk and spending | accept, adjust the limit, or reject |

   Technology above 20% of the fund (counting SPY's holdings) also triggers a review.
4. **An annual review** of assumptions, weights and spending.
