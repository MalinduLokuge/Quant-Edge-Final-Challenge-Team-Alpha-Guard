"""Data stage: raw snapshot -> aligned prices, log/simple returns, outlier flags, ADF.

Implements the brief's data-governance rules (p.9). Outputs:
    data/processed/prices_aligned.csv, log_returns.csv, simple_returns.csv, outlier_flags_zscore.csv,
                   data_quality_flags.csv (long: Date, Ticker, check, log_return),
                   rates_daily.csv (DTB3, rf_daily, DGS10, 10y change bp, breakeven 10y/5y), cpi_monthly.csv,
                   distribution_yield_ttm.csv, split_labels.csv (D5: train / validation / test per return date)
    outputs/tables/adf_results.csv, data_quality_missing.csv, data_quality_fred_alignment.csv,
                   data_quality_flag_counts.csv, structural_breaks_inclan_tiao.csv, income_crosscheck.csv,
                   split_summary.csv
"""
from __future__ import annotations

from quantedge.common import config
from quantedge.data import clean, diagnostics, fred, income, ingest, quality, split


def run(refresh: bool = False) -> dict:
    settings = config.load_settings()
    d = settings["data"]

    if refresh:
        snapshot = ingest.download_snapshot(settings["universe"], d["download_start"], d["download_end"], config.DATA_RAW)
        print(f"[data] new snapshot {snapshot.name}; set data.snapshot in settings.yaml to use it by default")
    else:
        snapshot = config.DATA_RAW / d["snapshot"]
    raw = ingest.load_snapshot(snapshot)

    missing = set(settings["universe"]) - set(raw.columns)
    if missing:
        raise ValueError(f"Snapshot is missing tickers: {sorted(missing)}")
    raw = raw[sorted(settings["universe"])]

    prices = clean.align_common_sample(raw)
    results = {
        "prices_aligned": prices,
        "log_returns": clean.log_returns(prices),
        "simple_returns": clean.simple_returns(prices),
    }
    results["outlier_flags_zscore"] = clean.zscore_outlier_flags(results["log_returns"], d["outlier_z_threshold"])
    results["split_labels"] = split.split_labels(
        results["simple_returns"].index, settings["split"]["train_end"], settings["split"]["validation_end"])

    config.DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    config.OUTPUT_TABLES.mkdir(parents=True, exist_ok=True)
    for name, df in results.items():
        df.to_csv(config.DATA_PROCESSED / f"{name}.csv")

    qc = quality.run_checks(prices, results["log_returns"], results["simple_returns"], d["quality"])
    qc["flags"].to_csv(config.DATA_PROCESSED / "data_quality_flags.csv", index=False)
    qc["counts"].to_csv(config.OUTPUT_TABLES / "data_quality_flag_counts.csv")
    qc["breaks"].to_csv(config.OUTPUT_TABLES / "structural_breaks_inclan_tiao.csv")

    split.summary(results["split_labels"]).to_csv(config.OUTPUT_TABLES / "split_summary.csv")

    adf = diagnostics.adf_table(results["log_returns"], d["adf_alpha"])
    adf.to_csv(config.OUTPUT_TABLES / "adf_results.csv")
    clean.missing_before_alignment(raw).to_csv(config.OUTPUT_TABLES / "data_quality_missing.csv")

    # ETF income: trailing-12-month distribution yield (reported separately; already inside total returns)
    if refresh:
        close_path, div_path = ingest.download_income_snapshot(
            settings["universe"], d["download_start"], d["download_end"], config.DATA_RAW)
    else:
        close_path = config.DATA_RAW / d["income_snapshot"]["close"]
        div_path = config.DATA_RAW / d["income_snapshot"]["dividends"]
    close = ingest.load_snapshot(close_path)[prices.columns]
    results["distribution_yield_ttm"] = income.ttm_distribution_yield(ingest.load_dividends(div_path), close, prices.index)
    results["distribution_yield_ttm"].to_csv(config.DATA_PROCESSED / "distribution_yield_ttm.csv")
    income.implied_income_return(prices, close, prices.index).to_frame().join(
        results["distribution_yield_ttm"].mean().rename("avg_ttm_yield")).to_csv(
        config.OUTPUT_TABLES / "income_crosscheck.csv")

    # FRED series, aligned to the ETF trading calendar (as-of, past values only)
    macro = {}
    for series, file in d["fred_snapshots"].items():
        path = fred.download_snapshot(series, config.DATA_EXTERNAL) if refresh else config.DATA_EXTERNAL / file
        macro[series] = fred.load_snapshot(path)
    rates = fred.rates_frame(macro["DTB3"], macro["DGS10"], prices.index, d["fred_max_stale_days"],
                             breakevens={"10y": macro["T10YIE"], "5y": macro["T5YIE"]})
    if rates.drop(columns="dgs10_change_bp").isna().any().any():
        raise ValueError("FRED rates have gaps longer than fred_max_stale_days inside the sample.")
    results["rates_daily"] = rates
    results["cpi_monthly"] = fred.cpi_inflation(macro["CPIAUCSL"])
    results["rates_daily"].to_csv(config.DATA_PROCESSED / "rates_daily.csv")
    results["cpi_monthly"].to_csv(config.DATA_PROCESSED / "cpi_monthly.csv")
    fred.missing_report({k: macro[k] for k in ("DTB3", "DGS10")}, prices.index).to_csv(
        config.OUTPUT_TABLES / "data_quality_fred_alignment.csv")

    print(f"[data] {snapshot.name}: {prices.index.min().date()} to {prices.index.max().date()}, "
          f"{len(prices)} price rows, {int(results['outlier_flags_zscore'].values.sum())} z-score flags, "
          f"{len(qc['flags'])} quality flags; "
          f"FRED DTB3/DGS10 aligned, CPI to {results['cpi_monthly'].index.max().date()}")
    return results
