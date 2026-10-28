# Subtask Tracker

Detailed breakdown of every main task in `TASKS.md`. Sources: **PM** = Project Management Tracker (original 98 subtasks, IDs kept), **FJ** = FigJam Pipeline Block Reference (block id), **BR** = official brief (page), **DEC** = `docs/DECISIONS.md`, **REV** = 2026-10-28 review / data findings.

**How to update:** change only the Status cell (`Not started` → `In progress` → `Done`, or `Blocked (…)`), then run `python tracking/update_counts.py`. New subtasks take the next free number in their task. Never renumber.
Priority: **Critical** = brief-mandated or blocks other work · **High** = needed for correctness · **Medium** = strengthens the submission · **Low** = nice to have.

## T1 — Project setup & shared decisions
Stage: — · Owner: Malindu · Priority: Supporting · Target: Week 1

| ID | Subtask | Expected output | Priority | Owner | Depends on | Status | Source |
|---|---|---|---|---|---|---|---|
| T1.01 | Create shared GitHub repository and directory structure | Folder tree, README, git repo; GitHub remote | Critical | Malindu | — | In progress | PM · local repo done, remote pending |
| T1.02 | Define environment, dependencies and setup commands | requirements.txt (pinned), setup steps in README | High | Malindu | T1.01 | In progress | PM · unpinned list exists |
| T1.03 | Agree on common model input/output conventions | conventions.py + CALCULATION_DICTIONARY.md (D17) | Critical | Malindu | — | Done | PM · DEC D17 |
| T1.04 | Agree date range, risk-free rate, benchmark and ETF universe | D1, D2, D3 approved in DECISIONS.md | Critical | Malindu | T2.06 | Done | PM · D2 implemented, D1/D3 open |
| T1.05 | Record decisions, responsibility owners and review process | DECISIONS.md, AGENTS.md, review rules | High | Malindu | — | Done | PM |
| T1.06 | Map brief Layers 1–5 to code stages; keep the vocabularies separate | PROJECT_KNOWLEDGE.md §1 | High | Malindu | — | Done | REV |
| T1.07 | Settle blocking decisions D3, D5, D6, D7, D12 before portfolio stage | All five APPROVED in DECISIONS.md | Critical | All members | T3.01–T3.04 | Done | DEC |
| T1.08 | Settle remaining decisions D1, D4, D8, D9, D11, D13, D16 | APPROVED in DECISIONS.md | High | All members | T1.07 | Not started | DEC |
| T1.09 | Upload missing Batch04 explainer (slides 61–80); remove duplicate Batch02 | docs/references/explainers complete | Low | Malindu | — | Not started | REV |
| T1.10 | Approve decisions already implied by approved work: D4 5-year horizon (D7 uses it), D11 quarterly (D3 uses it), D13 1,000-day window, D1 full sample, D2 DTB3, D8 EVT method | APPROVED rows in DECISIONS.md | Critical | All members | — | Done | Review 2026-10-28 (all approved 2026-10-28) |
| T1.11 | Approve optimiser design for drawdown limit (CVaR constraint + CDaR or post-check) | Decision D22 | Critical | All members | T4.20 | Done | Review 2026-10-28 |

## T2 — Data pipeline & cleaning
Stage: data · Owner: Raveena · Priority: Core · Target: Week 1

| ID | Subtask | Expected output | Priority | Owner | Depends on | Status | Source |
|---|---|---|---|---|---|---|---|
| T2.01 | Download adjusted prices for all seven allowed ETFs | data/raw/yahoo_adj_close_2026-10-20.csv | Critical | Raveena | — | Done | PM · FJ M04 · BR p.9 |
| T2.02 | Document data source, download date and adjustment choices | raw .meta.json + data/README.md source log | Critical | Raveena | T2.01 | Done | PM · FJ M04 |
| T2.03 | Align calendars, missing observations and common sample | prices_aligned.csv; data_quality_missing.csv | Critical | Raveena | T2.01 | Done | PM · FJ M05 · BR p.9 |
| T2.04 | Calculate daily log returns and verify computations | log_returns.csv + tests | Critical | Raveena | T2.03 | Done | PM · BR p.9 |
| T2.05 | Flag potential outliers without automatically deleting them | outlier_flags_zscore.csv (abs z > 5) | Critical | Raveena | T2.04 | Done | PM · BR p.9 |
| T2.06 | Run ADF tests and export reproducible clean datasets | outputs/tables/adf_results.csv | Critical | Raveena | T2.04 | Done | PM · BR p.9 |
| T2.07 | Move notebook logic into tested data-stage code; prove it reproduces the original files | src/quantedge/data/, regression test (diff ≤ 3e-14) | Critical | Raveena | T2.06 | Done | REV · BR p.9 reproducible |
| T2.08 | Calculate simple returns and state where simple vs log are used | simple_returns.csv; D17 | Critical | Raveena | T2.03 | Done | BR p.9 · FJ M05 |
| T2.09 | Download FRED DTB3, DGS10, CPI; align to trading days without look-ahead | rates_daily.csv, cpi_monthly.csv | Critical | Raveena | T2.03 | Done | BR p.9 · FJ M04 |
| T2.10 | Extra quality checks: stale prices, jumps, reversals, large negatives, variance breaks | data_quality_flags.csv, flag counts, Inclán–Tiao table | Critical | Raveena | T2.04 | Done | BR p.9 |
| T2.11 | Review every flag against market events; document decisions | Flag review table in data/README.md | High | Raveena | T2.10 | Done | BR p.9 'documented, not hidden' |
| T2.12 | Confirm GLD −10.8% on 2026-01-30 against market news | Note in data/README.md | Medium | Raveena | T2.11 | Not started | REV |
| T2.13 | Implement chronological train / validation / test split in code | data/processed/split_labels.csv, outputs/tables/split_summary.csv, data/split.py + 5 tests | Critical | Raveena | T1.07 (D5) | Done | FJ M06 · DEC D5 |
| T2.14 | Download ETF distributions (dividends) for the income objective | data/raw dividends snapshot; distribution yield per ETF | Medium | Raveena | T2.01 | Done | FJ M-N01 · BR p.3 income |
| T2.15 | ETF instrument register: asset class, role, inception, distribution policy (no extra data sources) | docs/ETF_REGISTER.md | Medium | Raveena | — | Not started | FJ M03/M-N01 |
| T2.16 | Team sign-off of data-stage validation log entries | Signed rows in HUMAN_VALIDATION_LOG.md | High | Raveena | T2.11 | Not started | BR p.8 · REV |
| T2.17 | Move quarterly-rebalanced NAV/turnover function from research script into common/conventions with tests | conventions.rebalanced_returns + 4 tests; research script uses it (results identical, turnover −0.08 pp) | High | Malindu | T1.03 | Done | Review: portfolio and benchmark must use identical rebalancing |

## T3 — Client mandate (investment policy)
Stage: mandate · Owner: Sujan · Priority: Core · Target: Week 1

| ID | Subtask | Expected output | Priority | Owner | Depends on | Status | Source |
|---|---|---|---|---|---|---|---|
| T3.01 | Define endowment horizon, investment purpose and liquidity needs | Horizon D4 + liquidity statement in IPS | Critical | Sujan | — | Done | PM · FJ M01 · BR p.4 · D4 PROPOSED 5y (used by D7) |
| T3.02 | Propose justified return and inflation-protection objectives | Return objective D12 (CPI + x%) with evidence | Critical | Sujan | T2.09 | Done | PM · DEC D12 APPROVED (provisional) |
| T3.03 | Set no-short-selling, allocation caps and risk-budget rules | Constraints D6 in config | Critical | Sujan | T3.01 | Done | PM · FJ M02 · BR p.4 |
| T3.04 | Propose VaR, ES and drawdown tolerances | Risk limits D7 (USD and % NAV) | Critical | Sujan | T3.01 | Done | PM · FJ M02 · BR p.4 |
| T3.05 | Document assumptions and secure team agreement | docs/IPS.md consolidating D4, D6, D7, D10, D12 (one source for report + app) | Critical | Sujan | T3.01–T3.08 | Not started | PM |
| T3.06 | Spending rule and cost assumptions (spending rate, turnover cost; ETF fees already in prices) | Cost/spending section in IPS | High | Sujan | T3.02 | In progress | FJ M-N02 · D12 S/C approved; IPS write-up pending |
| T3.07 | Rebalancing policy (frequency, drift band) | D11 approved; config | High | Sujan | T3.01 | Done | DEC D11 PROPOSED quarterly (used by D3 benchmark) |
| T3.08 | Choose benchmarks: CAPM market proxy and policy benchmark | D3 approved; config | Critical | Sujan | — | Done | DEC D3 · BR p.7 |
| T3.09 | Define suitability criteria used by the decision gate | Checklist: return hurdle, ES/DD limits, validation pass | High | Sujan | T3.02, T3.04 | In progress | FJ VD08 · D7 + D12 define criteria; checklist pending |
| T3.10 | Confirm no cash sleeve / derivatives; spending liquidity from AGG | D10 in IPS | High | Sujan | — | Done | DEC D10 |
| T3.11 | Required-vs-expected return table (breakeven inflation, CAPM, income yield, history; ERP and withholding sensitivity) | outputs/tables/required_return_grid.csv, cma_assets.csv, required_vs_expected.csv | Critical | Sujan | T2.09, T2.14 | Done | DEC D12 |
| T3.12 | Choose base ERP and risk-free assumption for expected returns (own-data ERP 9.7%, CI 3.5–15.8%, too wide to use alone) | ERP base + rf choice in DECISIONS.md | Critical | Sujan | T3.11 | Done | DEC D12 |
| T3.13 | Confirm base spending rate, real growth and extra costs (S, G, C); cite the spending benchmark source | D12 values APPROVED | Critical | All members | T3.11 | Done | DEC D12 |
| T3.15 | Highest sustainable spending per portfolio + auto-generated one-page summary | outputs/reports/return_objective_summary.md | High | Sujan | T3.11 | Done | DEC D12 (shortfall policy: lower spending) |
| T3.16 | Revisit S, G, C and ERP after further team research; rerun and compare | Updated D12 values + summary | Medium | All members | T3.13 | Not started | Team 2026-10-28 |
| T3.17 | Research and approve D3 benchmark structure | Research doc §1; D3 APPROVED | Critical | All members | T3.11 | Done | Research 2026-10-28 (analysis done, approval pending) |
| T3.18 | Research and approve D7 provisional risk limits | Research doc §2/§4; D7 APPROVED | Critical | All members | T3.17 | Done | Research 2026-10-28 (analysis done, approval pending) |
| T3.19 | Committee choice on the drawdown ↔ spending trade-off (20% → 2.1%, 25% → 2.8%) | Recorded in D7/D12 | Critical | All members | T3.18 | Done | Research §4 |
| T3.20 | Fix model warnings: daily covariance, per-ETF withholding, risk-free scenarios, separate gold assessment | Research doc §7–§8; cma.py; 2 tests | Critical | Sujan | T3.11 | Done | Team warnings 2026-10-28 |
| T3.21 | Risk tolerance approximation: willingness (mandate wording, peer losses) vs ability (capacity); tolerance = lower of the two | Tolerance statement in research doc §9 + IPS | Critical | Sujan | T3.22 | Done | Team 2026-10-28 (12-factor review) |
| T3.22 | Risk capacity: largest loss the fund can take while keeping spending and real value within floors (analytic + bootstrap with spending) | Capacity table by allocation | Critical | Sujan | T3.11 | Done | 12-factor review #2 |
| T3.23 | Spending continuity after losses: fixed-real-dollar vs %-of-NAV vs smoothing rule over 5-year paths | Spending-rule comparison; proposed rule (D24) | Critical | Sujan | T3.22 | Done | 12-factor review #3 |
| T3.24 | Recovery time after 10/15/20/25% losses: historical and forward (bootstrap) | Recovery-time table | High | Dewmini | T6.12 | Done | 12-factor review #8 |
| T3.25 | Liquidity under stress: funding spending and rebalancing from AGG in a crisis (incl. 2008-10-10 discount) | Liquidity note with $ cost | High | Raveena | T2.11 | Done | 12-factor review #10 |
| T3.26 | Losses beyond history: severity-scaled crisis replays (GFC ×1.25, ×1.5) | Severe-scenario table; feeds D9 | High | Dewmini | T11.02 | Done | 12-factor review #11 |
| T3.27 | Drawdown monitoring and action ladder (amber / red / limit) for memo and app | D23 approved; ladder in config risk_limits.action_ladder | Critical | All members | T3.22 | Done | 12-factor review #12 |
| T3.28 | Re-confirm D7 (drawdown, VaR, ES limits) against tolerance and capacity results | D7 confirmed or revised | Critical | All members | T3.21–T3.27 | Done | 12-factor review |
| T3.14 | Tax assumption: tax-exempt base case, dividend withholding as sensitivity (check interest-related dividend exemption for AGG) | Note in IPS + limitations | Medium | Sujan | T3.11 | Done | DEC D12 |

## T4 — Portfolio construction & selection
Stage: portfolio · Owner: Dewmini · Priority: Core · Target: Weeks 1–2

| ID | Subtask | Expected output | Priority | Owner | Depends on | Status | Source |
|---|---|---|---|---|---|---|---|
| T4.01 | Estimate training returns, covariance matrix and correlations | Training-window μ, Σ, ρ tables | Critical | Dewmini | T2.13 | Not started | PM · FJ PM01 |
| T4.02 | Implement constrained minimum-variance allocation | Min-Var weights + test | Critical | Dewmini | T4.08, T3.03 | Not started | PM · FJ PM02 |
| T4.03 | Implement risk-parity allocation | Risk-parity weights + equal-risk-contribution test | Critical | Dewmini | T4.08 | Not started | PM · FJ PM03 |
| T4.04 | Implement capped maximum-Sharpe allocation | Max-Sharpe weights + test | Critical | Dewmini | T4.08, T3.03 | Not started | PM · FJ PM04 |
| T4.05 | Document Markowitz/CAPM concepts and benchmark assumptions | Methods section draft | Critical | Dewmini | T4.11 | Not started | PM · BR p.7 |
| T4.06 | Compare diversification, concentration and feasible weights | Side-by-side comparison table | Critical | Dewmini | T4.02–T4.10 | Not started | PM · FJ PM07 |
| T4.07 | Provide candidate and proposed final weights with justification | Recommendation input for T20 | Critical | Dewmini | T4.06, T5.05 | Not started | PM |
| T4.08 | Robust inputs: shrinkage covariance (Ledoit–Wolf), cautious expected returns | Estimator module + stability note | High | Dewmini | T4.01 | Not started | FJ PM01/robust frontier · REV |
| T4.09 | Implement minimum-CVaR allocation (Rockafellar–Uryasev) | Min-CVaR weights + test | High | Dewmini | T4.08 | Not started | DEC D20 |
| T4.10 | Implement target-return Markowitz at the D12 hurdle (minimum 6.66% / target 7.19%) with fallback to lowest-risk feasible portfolio | Weights meeting D12 at minimum variance | High | Dewmini | T4.08, T4.18 | Not started | FJ PM05 |
| T4.11 | Efficient frontier with candidates and benchmarks plotted; trade-off table | Frontier figure + return-vs-risk table | Critical | Dewmini | T4.02–T4.10 | Not started | BR p.4 #5 · R16 |
| T4.12 | Feasibility filters: D6 v2 layers (equity 20–45%, GLD ≤ 20%, ≤ 2× benchmark, sector tilts) + D7 limits | Pass/fail per candidate | Critical | Dewmini | T4.02–T4.10 | Not started | FJ PM06 |
| T4.13 | Net-of-cost and turnover test under chosen rebalancing | Turnover, cost drag per candidate | Medium | Dewmini | T3.06, T3.07 | Not started | FJ PM-N03 |
| T4.14 | Diversification metrics: diversification ratio, risk contribution vs weight | Diversification table | High | Dewmini | T4.12 | Not started | BR p.4 'diversification benefits' |
| T4.15 | Weight sensitivity to input changes (sub-period / bootstrap re-estimation) | Weight stability table | Medium | Dewmini | T4.12 | Not started | FJ robust frontier |
| T4.16 | Freeze P1 handoff: candidate weights + metadata file | outputs/p1_candidates.csv (versioned) | Critical | Dewmini | T4.12 | Not started | FJ PM08 |
| T4.17 | Unit tests for all optimisers (constraints respected, known solutions) | tests/unit/test_portfolio_*.py | Critical | Dewmini | T4.02–T4.10 | Not started | BR p.6 software |
| T4.18 | Capital market assumptions estimated on the training window only, for out-of-sample candidates | cma.estimate_as_of; outputs/tables/cma_train*.csv, cma_full*.csv, cma_sets_summary.csv; 4 tests incl. leakage | Critical | Dewmini | T2.13 | Done | Review: current CMA uses full sample |
| T4.19 | Produce two P1 sets: P1-train (frozen, for OOS backtests) and P1-final (full-sample re-fit, same frozen method) | outputs/p1_train.csv, outputs/p1_final.csv | Critical | Dewmini | T4.16, T4.18 | Not started | DEC D5 protocol |
| T4.20 | Optimiser design meeting D6 v2 + D7 (ES as CVaR constraint; drawdown via CDaR or post-check) | Design note + solver choice (cvxpy) | Critical | Dewmini | T4.12 | Not started | Review 2026-10-28 |
| T4.21 | Add every candidate to the required-vs-expected table with sustainable spending | Extended return_objective_summary.md | High | Dewmini | T4.16 | Not started | DEC D12 |
| T4.22 | Decide bond expected-return method for near-zero rates (D25) and apply to both CMA sets | D25 approved; cma.expected_returns applied to both CMA sets, D12 tables, research; 1 test; research doc §8b | Critical | All members | T4.18 | Done | T4.18 finding |
| T4.23 | Required return in training-period terms (2014 breakeven, same S/G/C) for P1-train return targets | return_objective.required_return_as_of; cma_sets_summary.csv: train 6.49% / 5.96% (breakeven 1.68%), full 7.19% / 6.66%; 2 tests | High | Dewmini | T4.18 | Done | D5 + D12 consistency |

## T5 — KPIs & benchmarks
Stage: portfolio · Owner: Raveena · Priority: Supporting · Target: Week 2

| ID | Subtask | Expected output | Priority | Owner | Depends on | Status | Source |
|---|---|---|---|---|---|---|---|
| T5.01 | Implement Sharpe and Sortino metrics consistently | kpi functions + tests | Critical | Raveena | T1.03 | Not started | PM · BR p.7 |
| T5.02 | Compute Treynor and Jensen alpha with market benchmark | β, Treynor, α (annual) | Critical | Raveena | T3.08 (D3 done) | Not started | PM · BR p.7 |
| T5.03 | Compute Information Ratio against the Policy 40/50/10 benchmark (D3) | IR, tracking error | Critical | Raveena | T3.08 | Not started | PM · BR p.7 |
| T5.04 | Compute maximum drawdown and Calmar ratio | MaxDD, Calmar | Critical | Raveena | T1.03 | Not started | PM · BR p.7 |
| T5.05 | Prepare comparative KPI and benchmark results | KPI table: candidates vs benchmarks | Critical | Raveena | T4.16, T5.01–T5.04 | Not started | PM · FJ PM-N02 |
| T5.06 | CAPM expected return and beta per ETF and candidate | CAPM table (security market line) | Critical | Raveena | T3.08 | In progress | FJ PM-N01 · BR p.7 |
| T5.07 | Report KPIs separately for training and out-of-sample periods | Two-period KPI table | High | Raveena | T2.13, T5.05 | Not started | REV leakage |
| T5.08 | Verify KPIs against hand-calculated examples | Unit tests with known answers | High | Raveena | T5.01–T5.04 | Not started | REV |
| T5.09 | KPIs for portfolio and all D3 benchmarks with identical (quarterly) rebalancing and total returns | KPI table incl. benchmarks | High | Raveena | T2.17 | Not started | DEC D3 |

## T6 — VaR with 3 methods
Stage: risk · Owner: Sujan · Priority: Core · Target: Week 2

| ID | Subtask | Expected output | Priority | Owner | Depends on | Status | Source |
|---|---|---|---|---|---|---|---|
| T6.01 | Fix portfolio losses convention and risk horizon | D17 applied; P1 → loss series | Critical | Sujan | T1.03, T4.16 | In progress | PM · FJ R01 · conventions done |
| T6.02 | Implement Historical VaR at 95% and 99% | Function + test | Critical | Sujan | T6.01 | Not started | PM · BR p.7 |
| T6.03 | Implement Parametric VaR at 95% and 99% | Normal + Student-t variants + test | Critical | Sujan | T6.01 | Not started | PM · BR p.7 |
| T6.04 | Implement Monte Carlo VaR at 95% and 99% | Multivariate t / t-copula, fixed seed (D19) | Critical | Sujan | T6.01 | Not started | PM · BR p.7 · DEC D19 |
| T6.05 | Compare all methods on identical portfolios and windows | VaR matrix: candidate × method × level | Critical | Sujan | T6.02–T6.04 | Not started | PM · FJ R-N01 |
| T6.06 | Explain disagreements under calm and stressed conditions | Written comparison | Critical | Sujan | T6.05, T8.11 | Not started | PM · BR p.7 |
| T6.07 | Add 90% level to every VaR method (app requirement) | VaR at 90/95/99 | Critical | Sujan | T6.02–T6.04 | Not started | BR p.5 · R20 |
| T6.08 | Test model assumptions: Jarque–Bera, Ljung–Box on squared returns, QQ plots | Diagnostics table + figures | Critical | Sujan | T6.01 | Not started | BR p.7 · DEC D21 |
| T6.09 | Uncertainty bands: bootstrap CI (historical), MC standard error | CI columns in VaR matrix | Critical | Sujan | T6.02–T6.04 | Not started | BR p.5 · DEC D18 |
| T6.10 | Multi-day horizon by simulation (no silent √t) | 10-day / monthly VaR | Medium | Sujan | T6.04 | Not started | DEC D17 |
| T6.11 | Express VaR in USD on the $10M NAV | USD columns | Critical | Sujan | T6.05 | Not started | FJ R-N01 |
| T6.12 | Forward-looking drawdown probabilities, e.g. P(DD > 25% in 5 years), by block bootstrap | Probability table (reference + frontier portfolios; rerun for final candidates) | High | Sujan | T4.16 | Done | Research gap G1 |

## T7 — Expected Shortfall
Stage: risk · Owner: Sujan · Priority: Core · Target: Week 2

| ID | Subtask | Expected output | Priority | Owner | Depends on | Status | Source |
|---|---|---|---|---|---|---|---|
| T7.01 | Compute Historical ES at 95% and 99% | Function + test | Critical | Sujan | T6.02 | Not started | PM · BR p.7 |
| T7.02 | Compute ES from Parametric and Monte Carlo approaches | Closed-form normal/t ES; MC ES | Critical | Sujan | T6.03, T6.04 | Not started | PM |
| T7.03 | Compare corresponding VaR and ES outcomes | VaR vs ES table + gap | Critical | Sujan | T7.01, T7.02 | Not started | PM |
| T7.04 | Explain expected tail losses and data limitations | Rationale for ES (coherence, tail severity) | Critical | Sujan | T7.03 | Not started | PM · BR p.7 |
| T7.05 | ES at 90% and uncertainty bands | ES at 90/95/99 with CI | Critical | Sujan | T7.01, T7.02 | Not started | BR p.5 · DEC D18 |

## T8 — EVT & GARCH
Stage: risk · Owner: Sujan · Priority: Core · Target: Week 2

| ID | Subtask | Expected output | Priority | Owner | Depends on | Status | Source |
|---|---|---|---|---|---|---|---|
| T8.01 | Implement and diagnose conditional volatility (GARCH) | GARCH(1,1)-t fit + diagnostics | High | Sujan | T6.01 | Not started | PM · FJ R05 |
| T8.02 | Select EVT/GPD exceedance threshold with justification | Threshold choice note (D8) | Critical | Sujan | T8.08 | Not started | PM · BR p.7 |
| T8.03 | Fit tail distribution and test threshold sensitivity | ξ, β across thresholds | Critical | Sujan | T8.02 | Not started | PM · FJ R06 |
| T8.04 | Estimate EVT VaR and ES at high confidence | EVT VaR/ES per candidate | Critical | Sujan | T8.03 | Not started | PM |
| T8.05 | Compare GARCH/EVT and baseline estimates side by side | Comparison table | Critical | Sujan | T8.04, T6.05 | Not started | PM · BR p.5 risk dashboard |
| T8.06 | Record instability, model assumptions and sparse-tail caveats | Limitations entries | Critical | Sujan | T8.03 | Not started | PM |
| T8.07 | Fit EVT on GARCH-filtered residuals (i.i.d. requirement) | GARCH-EVT variant | High | Sujan | T8.01 | Not started | DEC D8 · REV |
| T8.08 | Mean-excess and parameter-stability plots | Threshold diagnostic figures | Critical | Sujan | T6.01 | Not started | DEC D8 · FJ EVT quality gate |
| T8.09 | Confidence intervals for ξ, β and EVT VaR/ES | Profile-likelihood or bootstrap CI | Critical | Sujan | T8.04 | Not started | BR p.5 · DEC D18 |
| T8.10 | Rule for EVT at 90% when the quantile falls below the threshold | Documented rule + app message | High | Sujan | T8.04 | Not started | REV · BR p.5 |
| T8.11 | Evaluate VaR/ES/EVT performance on stress windows (2008, 2020) | Stress-window comparison table | Critical | Sujan | T8.04, T6.05 | Not started | BR p.7 · R18 |
| T8.12 | Feasibility frontier under ERP 3–6% and a resampled frontier | Sensitivity of §4 table | Medium | Sujan | T4.11 | Not started | Research gap G7 |

## T9 — Risk budgeting
Stage: risk · Owner: Sujan · Priority: Supporting · Target: Week 2

| ID | Subtask | Expected output | Priority | Owner | Depends on | Status | Source |
|---|---|---|---|---|---|---|---|
| T9.01 | Define marginal and component VaR methodology | Euler allocation note | Critical | Sujan | T6.05 | Not started | PM · BR p.8 |
| T9.02 | Estimate ETF-level marginal VaR and ES contributions | Component VaR/ES table | Critical | Sujan | T9.01 | Not started | PM |
| T9.03 | Check contribution aggregation and approximations | Sum-to-total test | High | Sujan | T9.02 | Not started | PM |
| T9.04 | Recommend position-size adjustments and rationale | Risk-budget recommendation | Critical | Sujan | T9.03 | Not started | PM · BR p.8 |
| T9.05 | Risk contribution vs capital weight chart | Figure for app and report | High | Sujan | T9.02 | Not started | FJ R07 |
| T9.06 | Set the component-ES concentration limit (draft: no ETF > 40% of ES) | Limit in D7 | High | Sujan | T9.02 | Not started | Research gap G4 |

## T10 — Backtesting
Stage: validation · Owner: Malindu · Priority: Core · Target: Weeks 2–3

| ID | Subtask | Expected output | Priority | Owner | Depends on | Status | Source |
|---|---|---|---|---|---|---|---|
| T10.01 | Define chronological out-of-sample rolling window | D13 window, split from D5 | Critical | Malindu | T2.13, T1.07 | Not started | PM · FJ VD01 |
| T10.02 | Produce date-aligned VaR forecasts without look-ahead | Rolling forecast file (data ≤ t−1) | Critical | Malindu | T10.01, T6.05 | Not started | PM · BR p.7 |
| T10.03 | Count exceptions against the chosen confidence level | Exception series | Critical | Malindu | T10.02 | Not started | PM |
| T10.04 | Perform Kupiec unconditional coverage test | LR, p-value | Critical | Malindu | T10.03 | Not started | PM · BR p.7 |
| T10.05 | Perform Christoffersen independence/coverage tests | LR_ind, LR_cc, p-values (handle n₁₁ = 0) | Critical | Malindu | T10.03 | Not started | PM · BR p.7 |
| T10.06 | Apply Basel traffic light only for appropriate VaR settings | 99%, 250-day zones | Critical | Malindu | T10.03 | Not started | PM · BR p.7 |
| T10.07 | Choose the model on validation data only; freeze before test | Model-selection record | Critical | Malindu | T10.04, T10.05 | Not started | FJ OOS integrity gate |
| T10.08 | Backtest each method and candidate, not only the chosen one | Backtest matrix | High | Malindu | T10.03 | Not started | REV |
| T10.09 | Window-length sensitivity (500 vs 1000 days) | Sensitivity table | Medium | Malindu | T10.04 | Not started | DEC D13 |
| T10.10 | Recompute tests for any user-selected date range (for the app) | Function: tests on a sliced range | Critical | Malindu | T10.04–T10.06 | Not started | BR p.5 sidebar |
| T10.11 | ES / tail-severity check on exceptions | Average exceedance vs predicted ES | Medium | Malindu | T10.03, T7.05 | Not started | FJ VD03 |
| T10.12 | Out-of-sample check of D7 limits (set on train, test on held-out) | Limit stability table | High | Malindu | T2.13 | Not started | Research gap G8 |

## T11 — Stress testing
Stage: validation · Owner: Dewmini · Priority: Core · Target: Weeks 2–3

| ID | Subtask | Expected output | Priority | Owner | Depends on | Status | Source |
|---|---|---|---|---|---|---|---|
| T11.01 | Define precise 2008, COVID 2020 and 2022 periods | Dated windows with sources | Critical | Dewmini | — | In progress | PM · BR p.8 · windows used in scripts/research_d3_d7.py; confirm in D9/T11 |
| T11.02 | Recalculate portfolio performance in historical windows | Replay P&L, max loss, recovery | Critical | Dewmini | T11.01, T4.16 | Not started | PM · FJ VD04 |
| T11.03 | Design one plausible hypothetical macro/market shock | Scenario spec (D9) | Critical | Dewmini | T1.08 (D9) | Not started | PM · BR p.8 |
| T11.04 | Estimate ETF reactions and document assumptions | Factor betas (SPY, DGS10) → ETF shocks | Critical | Dewmini | T11.03, T2.09 | Not started | PM |
| T11.05 | Summarize losses, vulnerabilities and possible adjustments | Stress summary in USD/% NAV | Critical | Dewmini | T11.02, T11.04 | Not started | PM · FJ VD06 |
| T11.06 | Asset-level stress attribution: which ETFs drive the loss | Stress contribution table | High | Dewmini | T11.05 | Not started | FJ VD06 joint-loss |
| T11.07 | Correlation / joint losses under stress vs calm | Crisis correlation matrix | High | Dewmini | T11.02 | Not started | FJ joint-loss stress |
| T11.08 | AGG rate sensitivity estimated from DGS10 (no external duration data) | Empirical rate beta | Medium | Dewmini | T2.09 | Not started | FJ AGG rate-risk · REV |
| T11.09 | ETF liquidity under stress (e.g. AGG −7.1% on 2008-10-10) | Liquidity note for memo | Medium | Dewmini | T2.11 | Not started | FJ exit gate · REV |
| T11.10 | Check every scenario against client risk limits | Breach table | Critical | Dewmini | T11.05, T3.04 | Not started | FJ VD06 |
| T11.11 | Optional: longer-history crises via disclosed proxies (2000–02, 1994) | Proxy scenario losses | Low | Dewmini | T11.02 | Not started | Research gap G2 |

## T12 — Macro & industry risk (optional)
Stage: validation · Owner: Malindu · Priority: Optional · Target: Week 3

| ID | Subtask | Expected output | Priority | Owner | Depends on | Status | Source |
|---|---|---|---|---|---|---|---|
| T12.01 | Identify the important rates, inflation, oil and geopolitical exposures | Exposure list | Medium | Malindu | — | Not started | PM · BR p.4 #9 |
| T12.02 | Research ETF sensitivity to recession and policy shocks | Sensitivity notes | Medium | Malindu | T12.01 | Not started | PM |
| T12.03 | Connect industry exposures with the chosen shock scenario | Input to T11.03 | Medium | Malindu | T12.02 | Not started | PM |
| T12.04 | Write macro-risk notes for the report and stress test | Report section | Medium | Malindu | T12.03 | Not started | PM · BR p.10 counts in decision score |
| T12.05 | Macro context from World Bank / IMF open data only | Cited figures in memo | Low | Malindu | T12.04 | Not started | BR p.9 |

## T13 — Innovation extension
Stage: risk/validation · Owner: Sujan · Priority: Optional · Target: Week 3

| ID | Subtask | Expected output | Priority | Owner | Depends on | Status | Source |
|---|---|---|---|---|---|---|---|
| T13.01 | Choose one additional model and state a testable hypothesis | Entry in INNOVATION_LOG.md | Medium | Sujan | T6.05 | Not started | PM |
| T13.02 | Specify the method and baseline comparison fairly | Method note | Medium | Sujan | T13.01 | Not started | PM |
| T13.03 | Implement innovation without future-data leakage | Code + tests | Medium | Sujan | T13.02 | Not started | PM |
| T13.04 | Backtest innovation and compare standalone methods | Backtest comparison | Medium | Sujan | T13.03, T10.04 | Not started | PM |
| T13.05 | Report gains, failures, limitations and overfitting concerns | Report section | Medium | Sujan | T13.04 | Not started | PM |
| T13.06 | Agree the innovation set (rec. #12) and wavelets decision (rec. #13) | Approved list in DECISIONS.md | Medium | All members | — | Not started | REV |
| T13.07 | Evaluate conditional drawdown-at-risk (CDaR) optimisation as innovation | Innovation log entry + comparison | Medium | Sujan | T4.20 | Not started | Review 2026-10-28 |

## T14 — Streamlit app
Stage: app · Owner: Malindu · Priority: Core · Target: Weeks 2–3

| ID | Subtask | Expected output | Priority | Owner | Depends on | Status | Source |
|---|---|---|---|---|---|---|---|
| T14.01 | Build sidebar: confidence 90/95/99, method and backtest dates | Sidebar wired to outputs | Critical | Malindu | T6.07, T10.10 | Not started | PM · BR p.5 |
| T14.02 | Build ETF weights and cumulative return portfolio panel | Portfolio page | Critical | Malindu | T4.16 | Not started | PM · BR p.5 |
| T14.03 | Add drawdown figure and KPI section | Drawdown + KPI panel | Critical | Malindu | T5.05 | Not started | PM · BR p.5 |
| T14.04 | Create VaR/ES/EVT side-by-side risk dashboard | Risk page, same confidence, gap visible | Critical | Malindu | T8.05 | Not started | PM · BR p.5 |
| T14.05 | Build backtesting results and traffic-light panel | Backtest page | Critical | Malindu | T10.06 | Not started | PM · BR p.5 |
| T14.06 | Build historical/hypothetical stress visualization | Stress page | Critical | Malindu | T11.05 | Not started | PM · BR p.6 |
| T14.07 | Add Assumptions page and test app interactions | Assumptions page + UI tests | Critical | Malindu | T15.05 | Not started | PM · BR p.6 |
| T14.08 | Shared loader: app reads outputs only, cached; no model code in UI | app/components/data.py | High | Malindu | T4.16 | Not started | FJ app 03 · AGENTS.md |
| T14.09 | Decision & tear-sheet page (P3, limits, monitoring triggers) | Decision page | High | Malindu | T20.04 | Not started | FJ app 08 |
| T14.10 | AI disclosure & sources page | Disclosure page | Medium | Malindu | T18.05 | Not started | FJ app 10 |
| T14.11 | Export & reproducibility page (CSV/figures download) | Export page | Low | Malindu | T14.02–T14.06 | Not started | FJ app 11 |
| T14.12 | Plain-language labels for a non-technical committee (units, horizon on every number) | UI copy review | High | Malindu | T14.01–T14.07 | Not started | BR p.5 · masterclass |
| T14.13 | What-if sliders on decision page: spending, growth, costs, ERP → required return, gap, sustainable spending | Decision page widget | Medium | Malindu | T4.21 | Not started | Team request 2026-10-28 |

## T15 — Assumptions & Limitations
Stage: docs/app · Owner: Raveena + Dewmini · Priority: Core · Target: Week 3

| ID | Subtask | Expected output | Priority | Owner | Depends on | Status | Source |
|---|---|---|---|---|---|---|---|
| T15.01 | Document data universe, dates, sourcing and limitations | Data section | Critical | Raveena + Dewmini | T2.11 | In progress | PM · FRED notes written |
| T15.02 | Explain distribution, volatility and dependence assumptions | Model section | Critical | Raveena + Dewmini | T6.08 | Not started | PM |
| T15.03 | Explain unseen shocks, low liquidity and tail-data scarcity | Tail / liquidity section | Critical | Raveena + Dewmini | T8.06, T11.09 | Not started | PM |
| T15.04 | Clarify what backtesting can and cannot establish | Backtest section | Critical | Raveena + Dewmini | T10.07 | Not started | PM |
| T15.05 | Ensure app and report state identical assumptions | App page generated from ASSUMPTIONS_LIMITATIONS.md | Critical | Raveena + Dewmini | T15.01–T15.04 | Not started | PM · FJ limitations audit |
| T15.06 | Add return-objective, benchmark and risk-limit assumptions (CAPM gold, rf level, ERP, USD spending, tax, in-sample calibration) | docs/ASSUMPTIONS_LIMITATIONS.md updated | High | Raveena + Dewmini | — | Done | Review 2026-10-28 |

## T16 — Written deliverables
Stage: decision/docs · Owner: Raveena · Priority: Core · Target: Week 3

| ID | Subtask | Expected output | Priority | Owner | Depends on | Status | Source |
|---|---|---|---|---|---|---|---|
| T16.01 | Outline 7–15 page technical report based on actual results | Report outline | Critical | Raveena | T1.07 | Not started | PM · BR p.6 |
| T16.02 | Complete methods, evidence, tests and limitations writeup | Report draft | Critical | Raveena | T20.04 | Not started | PM |
| T16.03 | Create concise one-page portfolio tear sheet | Tear sheet (<5 min read) | Critical | Raveena | T20.04 | Not started | PM · BR p.6 |
| T16.04 | Write one-page investment committee decision memo | Memo: accept / adjust risk limit / reject (D14) | Critical | Raveena | T20.04 | Not started | PM · BR p.8 |
| T16.05 | Cross-check all numbers between report, memo and app | Number audit (automated where possible) | Critical | Raveena | T16.02–T16.04, T14.* | Not started | PM · FJ calculation audit |
| T16.06 | Data sources and cleaning steps section | Report section from data/README.md | Critical | Raveena | T2.11 | Not started | BR p.6 |
| T16.07 | Report sections: return objective & sustainable spending; benchmark and risk-limit research (appendix) | Report draft sections | High | Raveena | T20.04 | Not started | DEC D3, D7, D12 |

## T17 — Repository & reproducibility
Stage: — · Owner: Malindu · Priority: Core · Target: Week 3

| ID | Subtask | Expected output | Priority | Owner | Depends on | Status | Source |
|---|---|---|---|---|---|---|---|
| T17.01 | Finalize organized, documented GitHub repository | Public / judge-accessible repo | Critical | Malindu | T1.01 | Not started | PM · BR p.6 |
| T17.02 | Pin package versions and supply reproducible setup | Pinned requirements | Critical | Malindu | T1.02 | Not started | PM |
| T17.03 | Provide one-command Streamlit run instructions | `python run_all.py --app` in README | Critical | Malindu | T14.* | In progress | PM · BR p.6 · entry point exists |
| T17.04 | Test clean installation and reproduce key results | Clean-machine test record | Critical | Malindu | T17.02 | Not started | PM |
| T17.05 | Log reproducibility evidence and known environment issues | Reproducibility log | High | Malindu | T17.04 | Not started | PM |
| T17.06 | Decide which reference files to publish (third-party decks) | .gitignore rule: decks kept local, removed from history | Medium | Malindu | — | Done | REV |
| T17.07 | Optional: deploy to Streamlit Community Cloud | Public app URL (D16) | Low | Malindu | T17.04 | Not started | BR p.6 · DEC D16 |
| T17.08 | First git commit and judge-accessible GitHub remote | GitHub remote, branch version-1 pushed; URL in README | Critical | Malindu | T17.06 | Done | BR p.6 · Review |
| T17.09 | Make research evidence reproducible from the one-command run (run_all --research) | run_all flag + README | High | Malindu | T17.03 | Not started | Review: scripts/ not in pipeline |

## T18 — AI disclosure & validation log
Stage: — · Owner: Malindu · Priority: Core · Target: Ongoing

| ID | Subtask | Expected output | Priority | Owner | Depends on | Status | Source |
|---|---|---|---|---|---|---|---|
| T18.01 | Keep a running list of AI tools and their purposes | AI_DISCLOSURE.md rows | Critical | Malindu | — | In progress | PM · BR p.8 |
| T18.02 | Record which code, figures or text used AI assistance | Material components column | Critical | Malindu | — | In progress | PM · BR p.8 |
| T18.03 | Document manual verification, corrections and tests | HUMAN_VALIDATION_LOG.md | Critical | Malindu | — | In progress | PM · BR p.8 |
| T18.04 | Review completeness of the log before submission | Signed-off log | Critical | Malindu | T18.01–T18.03 | Not started | PM |
| T18.05 | Use the brief's four disclosure columns exactly | Tool · Purpose · Human validation · Material components | High | Malindu | — | Not started | BR p.8 |
| T18.06 | Every member can explain each module (judging rule) | Walk-through sessions per stage | High | All members | each stage | Not started | BR p.9 |
| T18.07 | Record Claude Code use to date in the brief's four columns (tool, purpose, human validation, material components) | AI_DISCLOSURE.md entries (team to review) | Critical | Malindu | — | In progress | BR p.8 · Review |
| T18.08 | Team sign-off of every HUMAN_VALIDATION_LOG entry (9 unsigned on 2026-10-28) | Signed log | Critical | All members | — | Not started | BR p.8–9 |

## T19 — Pitch & Q&A prep
Stage: — · Owner: All members · Priority: Conditional · Target: If finalist

| ID | Subtask | Expected output | Priority | Owner | Depends on | Status | Source |
|---|---|---|---|---|---|---|---|
| T19.01 | Create a 10–12 minute presentation storyline and deck | Deck | Medium | All members | T16.04 | Not started | PM · BR p.6 |
| T19.02 | Assign presenters and rehearse timing | Rehearsal plan | Medium | All members | T19.01 | Not started | PM |
| T19.03 | Prepare judges' Q&A on assumptions, VaR and crisis results | Q&A bank | Medium | All members | T19.01 | Not started | PM |
| T19.04 | Run mock Q&A and refine explanations | Mock session notes | Medium | All members | T19.03 | Not started | PM |

## T20 — Decision gate & final recommendation (P3)
Stage: decision · Owner: All members · Priority: Core · Target: Week 3

| ID | Subtask | Expected output | Priority | Owner | Depends on | Status | Source |
|---|---|---|---|---|---|---|---|
| T20.01 | Assemble committee evidence: six panels (allocation, return, loss limit, tail, model trust, governance) | Evidence pack | Critical | All members | T5.05, T8.05, T10.07, T11.10 | Not started | FJ VD07 · masterclass |
| T20.02 | Suitability gate: validated and within client limits? | Pass/fail record per candidate | Critical | All members | T20.01, T3.09 | Not started | FJ VD08 |
| T20.03 | Revise & retest loop when the gate fails | Revision log (what changed, rerun results) | High | All members | T20.02 | Not started | FJ VD09 |
| T20.04 | Final P3 recommendation: weights, horizon, expected real return, downside | outputs/p3_decision | Critical | All members | T20.02 | Not started | FJ VD10 · BR p.8 |
| T20.05 | Monitoring triggers and exit / de-risking rules | Trigger table | High | All members | T20.04 | Not started | FJ VD10 |
| T20.06 | Drawdown ↔ spending trade-off table in memo and app | Memo section + app widget | High | All members | T3.19 | Not started | Research §4 |

## T21 — Quality gates & compliance QA
Stage: — · Owner: Malindu (coordinates) · Priority: Core · Target: Ongoing

| ID | Subtask | Expected output | Priority | Owner | Depends on | Status | Source |
|---|---|---|---|---|---|---|---|
| T21.01 | Compliance check after every stage (R1–R20) | COMPLIANCE_MATRIX.md updated | Critical | Malindu (coordinates) | each stage | In progress | FJ N01 governance · REV |
| T21.02 | Out-of-sample integrity gate: no leakage, frozen test, trial log | Leakage tests + trial log | Critical | Malindu (coordinates) | T2.13 | Not started | FJ OOS integrity gate |
| T21.03 | Calculation audit: units, signs, horizon consistent across stages | Audit checklist vs CALCULATION_DICTIONARY.md | Critical | Malindu (coordinates) | each stage | Not started | FJ calculation audit |
| T21.04 | App / code QA: required panels, one-command run, tests green | QA checklist | Critical | Malindu (coordinates) | T14.* | Not started | FJ app/code QA |
| T21.05 | Update FigJam board to match approved decisions (edit list in docs/research/PROJECT_REVIEW_2026-10-28.md §4) | Board matches MODEL_DESIGN.md | High | Malindu (coordinates) | — | Not started | DEC D14, D20 |
| T21.06 | Add R16–R20 to compliance matrix; update every status with evidence | COMPLIANCE_MATRIX.md | Critical | Malindu | — | Done | Review 2026-10-28 |
| T21.07 | Record innovations to date in the innovation log | INNOVATION_LOG.md | High | Sujan | — | Done | Review 2026-10-28 |
| T21.08 | Generate both Excel trackers from the repo tracker (tracking/export_excel.py) | tracking/exports/*.xlsm | High | Malindu | — | Done | Review 2026-10-28 |
