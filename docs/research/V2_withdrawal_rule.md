# V2 research: crisis spending buffer and withdrawal rule (D40)

**Status: research on branch `version-2`. Result: not adopted.** O6, D10 (no cash sleeve) and D11 (quarterly rebalancing) are unchanged. D39 gains a note on its rebalancing assumption.

## Question
The university must keep receiving its spending in a crash. Would a dedicated crisis buffer, paying spending from bonds instead of selling equities after a fall, help the fund regain its purchasing power faster?

## Mandate check
A cash or T-bill reserve is not allowed. The brief asks for a portfolio "from the prescribed investable universe" built from "eligible funds" (p.3–4), and the universe is the seven ETFs (p.5). FRED's 3-month T-bill is a data source (risk-free rate), not an investable asset. D10 already records this. So only rules inside O6's seven ETFs were tested, using AGG (about 61% of O6) as the buffer.

## Method (`scripts/research_v2_withdrawal_rule.py`)
Same machinery as D39 (T20.09 view 4): 8,000 bootstrap paths of 25 years, CMA-reset means, 63-day blocks, D24 spending at 2.65%, 0.2% costs, breakeven inflation, same seeds. The new part is simulating each ETF holding, so the source of each withdrawal and the rebalancing policy matter. Rebalancing trades pay 10 bp of turnover. Crises are the same events in every arm (O6's own price drawdown of 20% / 25% within years 0–10). Recovery means the arm's real value after spending and costs is back at its pre-crisis level. All arms were re-run on independent seeds with 16,000 paths.

| Arm | Rule |
|---|---|
| **A** | D11: pro-rata withdrawals, quarterly rebalance to O6 (approved policy) |
| **B** | Crisis buffer: from a 15% fall (D23 "review"), spending comes from AGG only and rebalancing pauses until the price is back at the pre-crisis peak |
| **C** | Withdraw from the most overweight holdings; rebalance only when a weight drifts more than 5 pp |

"Pay from AGG but keep rebalancing quarterly" is identical to A: after the rebalance, the source of the withdrawal makes no difference.

## Results (`outputs/tables/research_v2_withdrawal_rule.csv`)
| | A | B | C |
|---|---|---|---|
| P(real back within 15y \| fall ≥ 25%), 8k / new seeds 16k | 42.0% / 44.6% | 41.2% / 43.3% | 43.2% / 45.4% |
| Same within 20 years | 47.1% / 50.3% | 46.7% / 49.2% | 48.7% / 50.8% |
| P(real back within 15y \| fall ≥ 20%) | 60.4% / 60.9% | 59.5% / 60.2% | 60.5% / 61.1% |
| Avg real spending, years 1–20 | 2.8% | 2.8% | 2.8% |
| P(real spending cut > 10% ever) | 37.0% / 37.9% | 37.3% / 38.2% | 37.2% / 38.1% |
| Turnover a year | 6.2% | 5.7% | 1.5% |

## Findings
1. **The crisis buffer does not help.** Quarterly rebalancing already acts as the recovery buffer: after a fall it sells AGG and buys equities while they are cheap. Pausing rebalancing to protect equities stops that buying, and real recovery gets slightly worse (about −1 pp).
2. **Band rebalancing helps only slightly** (about +1 pp, with less trading). The gain is small and its drifted weights were not re-tested on D7, so it is not adopted.
3. **Spending is the same in every arm.** A buffer changes which asset is sold, not how much the university receives.
4. **D39 assumes daily rebalancing.** On the same paths, the D39 portfolio-level model gives 46.1% (matching `sustainability_recovery.csv`). The per-ETF model with quarterly rebalancing gives 42.0%, with or without the trading cost, so the gap comes from rebalancing frequency. Under D11 the realistic figure is about 42–45%.

## Decision (D40)
Keep O6, quarterly rebalancing (D11) and no cash sleeve (D10); no separate crisis buffer. The fund's protections are AGG liquidity, quarterly rebalancing that buys equities after falls, and the D23 monitoring ladder. Recovery after a 25%+ fall is quoted as "about 42–46% within 15 years".
