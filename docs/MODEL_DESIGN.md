# Model Design & Structure

Source: FigJam "Updated One — QuantEdge Master Pipeline" and `QuantEdge_FigJam_Pipeline_Block_Reference.xlsm`, revised by the approved review recommendations (DECISIONS.md D10, D14, D17–D21).
Stage names are the code architecture. The brief's methodology Layers 1–5 are mapped in `PROJECT_KNOWLEDGE.md §1`.

## Flow
```
Mandate & client rules → data stage: clean data, FRED, quality flags, chronological split
  → portfolio stage: return objective (D12) + CAPM expectations → candidates (Min-Var, Risk Parity, capped Max-Sharpe,
       Min-CVaR, Markowitz target-return) under D6 v2 + D7 → benchmarks (D3) + KPIs + frontier
       ── P1-train (fit on 2004–14, frozen, for out-of-sample tests) and P1-final (same method, full sample)
  → risk stage, per candidate: Hist / Param / MC (t) VaR, ES, EVT-GPD, GARCH σ, component VaR/ES,
       uncertainty bands, assumption diagnostics ── P2
  → validation stage: out-of-sample backtests + stress tests ── gate: validated & within client limits?
       no → revise & retest
  → decision stage: P3 (accept the mandate as proposed / adjust the risk limit / reject)
       + monitoring triggers → report, tear sheet, memo, app
```

## Conventions (D17, approved; formulas in CALCULATION_DICTIONARY.md)
| Item | Convention |
|---|---|
| Portfolio returns | Σ wᵢ·simple returnᵢ (`common/conventions.portfolio_returns`) |
| Statistical modelling | Per-asset log returns (ADF, GARCH); EVT on portfolio loss |
| Loss sign | Loss = −return; reported as positive % of NAV and USD |
| Weights | Long-only, fully invested across the 7 ETFs, no cash or derivatives (D10) |
| Confidence | 90 / 95 / 99% in the app, 95 / 99% in the report (D18) |
| Risk horizon | 1 trading day primary; longer horizons by simulation, never silent √t |
| Annualisation | 252 trading days |
| Fees | Already inside adjusted prices; not deducted again |

## Stage contracts
| Stage | Inputs | Outputs | Tests |
|---|---|---|---|
| data ✅ | `data/raw/` snapshot, `data/external/` FRED snapshots, config | `data/processed/`: prices_aligned, log_returns, simple_returns, outlier_flags_zscore, data_quality_flags, rates_daily, cpi_monthly. `outputs/tables/`: adf_results, data_quality_* , structural_breaks_inclan_tiao | test_data_clean, test_data_fred, test_data_quality, test_data_stage_reference |
| portfolio 🟡 | processed data, config (D3 benchmarks, D6 constraints, D7 limits, D12 mandate) | Done: cma_assets, erp_estimate, required_return_grid, required_vs_expected, return_objective_summary. Done: cma_train / cma_full with matching hurdles (train 6.49% target / 5.96% minimum; full 7.19% / 6.66%). To do: P1-train, P1-final, KPI table, frontier | test_return_objective |
| risk ⏳ | P1 weights, returns | P2: VaR/ES/EVT per candidate & confidence, component risk, diagnostics | — |
| validation ⏳ | P1, P2 models, held-out returns | backtest exceptions & tests, stress P&L | — |
| decision ⏳ | all outputs, client limits | P3 decision, memo / tear-sheet tables | — |
