from __future__ import annotations

import argparse
import os
from pathlib import Path

from .adapters import BisAdapter, BojAdapter, ChinaM2Adapter, EcbAdapter, EiaInventoryAdapter, EiaMerAdapter, FredAdapter, YahooChartAdapter
from .analysis import energy_gdp_suite, final_reporting_suite, integrated_synthesis_suite, lag_correlations, oil_equity_robustness_suite, oil_equity_suite, regression_suite, second_stage_suite, third_stage_suite, uso_suite
from .audit import terminal_summary, write_audit_outputs
from .cache import RawCache
from .charts import make_charts
from .storage import Store, maybe_write_parquet, write_csv
from .transforms import build_monthly_dataset


def build(root: Path, refresh: bool = False, bis_url: str | None = None) -> None:
    raw_dir = root / "data" / "raw"
    processed_dir = root / "data" / "processed"
    chart_dir = root / "charts"
    analysis_dir = root / "analysis"

    cache = RawCache(raw_dir, refresh=refresh)
    fred = FredAdapter(cache)
    ecb = EcbAdapter(cache)
    boj = BojAdapter(cache)
    china = ChinaM2Adapter(cache, fred)
    eia = EiaInventoryAdapter(cache)
    eia_mer = EiaMerAdapter(cache)
    yahoo = YahooChartAdapter(cache)
    bis = BisAdapter(cache)

    us_m2 = fred.fetch("M2SL")
    ea_m2 = ecb.fetch_euro_area_m2()
    cn_m2 = china.fetch_china_m2()
    jp_m2 = boj.fetch_japan_m2()
    eurusd = fred.fetch("DEXUSEU", monthly=True)
    cnyusd = fred.fetch("DEXCHUS", monthly=True)
    jpyusd = fred.fetch("DEXJPUS", monthly=True)
    cpi = fred.fetch("CPIAUCSL")
    sp500 = fred.fetch("SP500", monthly=True)
    uso_avg, uso_month_end = yahoo.fetch_adjusted_monthly("USO")
    gdpc1 = fred.fetch("GDPC1")
    indpro = fred.fetch("INDPRO")
    wti = fred.fetch("DCOILWTICO", monthly=True)
    brent = fred.fetch("DCOILBRENTEU", monthly=True)
    inventory = eia.fetch_crude_stocks_ex_spr()
    total_energy = eia_mer.fetch_monthly_series("T01.03", "TETCBUS", "US_TOTAL_PRIMARY_ENERGY_CONSUMPTION")
    oil_energy = eia_mer.fetch_monthly_series("T01.03", "PMTCBUS", "US_PETROLEUM_CONSUMPTION")
    source_series = {
        "US M2": us_m2,
        "Euro area M2": ea_m2,
        "China M2": cn_m2,
        "Japan M2": jp_m2,
        "EURUSD": eurusd,
        "CNY per USD": cnyusd,
        "JPY per USD": jpyusd,
        "U.S. CPI": cpi,
        "S&P 500": sp500,
        "USO adjusted close monthly average": uso_avg,
        "USO adjusted close month-end": uso_month_end,
        "Real GDP": gdpc1,
        "Industrial production": indpro,
        "WTI": wti,
        "Brent": brent,
        "Crude inventory excl SPR": inventory,
        "Total primary energy consumption": total_energy,
        "Petroleum consumption": oil_energy,
    }

    rows = build_monthly_dataset(us_m2, ea_m2, cn_m2, jp_m2, eurusd, cnyusd, jpyusd, cpi, sp500, uso_avg, uso_month_end, wti, brent, inventory)
    rows = [row for row in rows if row.get("month") >= "1986-01"]

    lag_rows = lag_correlations(rows, "WTI_YoY") + lag_correlations(rows, "Brent_YoY")
    regression_rows, rolling_rows = regression_suite(rows)
    interaction_rows, residual_rows, regime_rows, rolling_extended_rows, second_stage_findings = second_stage_suite(rows)
    target_comparison_rows, residual_diagnostic_rows, final_interpretation = third_stage_suite(rows)
    final_findings_rows, executive_summary, model_card, signal_snapshot = final_reporting_suite(
        rows,
        lag_rows,
        rolling_extended_rows,
        residual_diagnostic_rows,
    )
    oil_equity_rows, oil_equity_findings = oil_equity_suite(rows)
    oil_equity_return_lag_rows, oil_equity_robustness = oil_equity_robustness_suite(rows)
    uso_lead_lag_rows, uso_tracking_rows, uso_model_rows, uso_findings = uso_suite(rows)
    energy_gdp_lead_lag_rows, energy_gdp_model_rows, energy_gdp_findings = energy_gdp_suite(
        rows,
        gdpc1,
        indpro,
        total_energy,
        oil_energy,
    )
    system_signal_rows, integrated_atlas, final_system_interpretation = integrated_synthesis_suite(
        lag_rows,
        rolling_extended_rows,
        residual_diagnostic_rows,
        oil_equity_rows,
        energy_gdp_lead_lag_rows,
    )
    bis_rows = bis.fetch_csv_url(bis_url) if bis_url else []

    write_csv(processed_dir / "monthly_dataset.csv", rows)
    write_csv(analysis_dir / "lag_correlations.csv", lag_rows)
    write_csv(analysis_dir / "regression_summary.csv", regression_rows)
    write_csv(analysis_dir / "rolling_validation.csv", rolling_rows)
    write_csv(analysis_dir / "interaction_model_summary.csv", interaction_rows)
    write_csv(analysis_dir / "residual_model_summary.csv", residual_rows)
    write_csv(analysis_dir / "regime_model_summary.csv", regime_rows)
    write_csv(analysis_dir / "rolling_validation_extended.csv", rolling_extended_rows)
    write_csv(analysis_dir / "target_comparison_summary.csv", target_comparison_rows)
    write_csv(analysis_dir / "residual_diagnostic_summary.csv", residual_diagnostic_rows)
    write_csv(analysis_dir / "final_findings_table.csv", final_findings_rows)
    write_csv(analysis_dir / "oil_equity_lead_lag_summary.csv", oil_equity_rows)
    write_csv(analysis_dir / "oil_equity_return_lag_summary.csv", oil_equity_return_lag_rows)
    write_csv(analysis_dir / "uso_lead_lag_summary.csv", uso_lead_lag_rows)
    write_csv(analysis_dir / "uso_tracking_residual_summary.csv", uso_tracking_rows)
    write_csv(analysis_dir / "uso_model_summary.csv", uso_model_rows)
    write_csv(analysis_dir / "energy_gdp_lead_lag.csv", energy_gdp_lead_lag_rows)
    write_csv(analysis_dir / "energy_gdp_model_summary.csv", energy_gdp_model_rows)
    write_csv(analysis_dir / "system_signal_hierarchy.csv", system_signal_rows)
    (analysis_dir / "second_stage_findings.md").write_text(second_stage_findings, encoding="utf-8")
    (analysis_dir / "final_model_interpretation.md").write_text(final_interpretation, encoding="utf-8")
    (analysis_dir / "executive_summary.md").write_text(executive_summary, encoding="utf-8")
    (analysis_dir / "model_card.md").write_text(model_card, encoding="utf-8")
    (analysis_dir / "current_signal_snapshot.md").write_text(signal_snapshot, encoding="utf-8")
    (analysis_dir / "oil_equity_findings.md").write_text(oil_equity_findings, encoding="utf-8")
    (analysis_dir / "oil_equity_robustness.md").write_text(oil_equity_robustness, encoding="utf-8")
    (analysis_dir / "uso_findings.md").write_text(uso_findings, encoding="utf-8")
    (analysis_dir / "energy_gdp_findings.md").write_text(energy_gdp_findings, encoding="utf-8")
    (analysis_dir / "integrated_lead_lag_atlas.md").write_text(integrated_atlas, encoding="utf-8")
    (analysis_dir / "final_system_interpretation.md").write_text(final_system_interpretation, encoding="utf-8")
    if bis_rows:
        write_csv(processed_dir / "bis_total_credit_quarterly.csv", bis_rows)
    maybe_write_parquet(processed_dir / "monthly_dataset.parquet", rows)

    store = Store(root / "data" / "oil_model.sqlite")
    try:
        store.write_rows("monthly_dataset", rows)
        store.write_rows("lag_correlations", lag_rows)
        store.write_rows("regression_summary", regression_rows)
        store.write_rows("rolling_validation", rolling_rows)
        store.write_rows("interaction_model_summary", interaction_rows)
        store.write_rows("residual_model_summary", residual_rows)
        store.write_rows("regime_model_summary", regime_rows)
        store.write_rows("rolling_validation_extended", rolling_extended_rows)
        store.write_rows("target_comparison_summary", target_comparison_rows)
        store.write_rows("residual_diagnostic_summary", residual_diagnostic_rows)
        store.write_rows("final_findings_table", final_findings_rows)
        store.write_rows("oil_equity_lead_lag_summary", oil_equity_rows)
        store.write_rows("oil_equity_return_lag_summary", oil_equity_return_lag_rows)
        store.write_rows("uso_lead_lag_summary", uso_lead_lag_rows)
        store.write_rows("uso_tracking_residual_summary", uso_tracking_rows)
        store.write_rows("uso_model_summary", uso_model_rows)
        store.write_rows("energy_gdp_lead_lag", energy_gdp_lead_lag_rows)
        store.write_rows("energy_gdp_model_summary", energy_gdp_model_rows)
        store.write_rows("system_signal_hierarchy", system_signal_rows)
        if bis_rows:
            store.write_rows("bis_total_credit_quarterly", bis_rows)
    finally:
        store.close()

    make_charts(
        rows,
        lag_rows,
        chart_dir,
        residual_rows,
        rolling_extended_rows,
        target_comparison_rows,
        oil_equity_rows,
        oil_equity_return_lag_rows,
        uso_lead_lag_rows,
        uso_tracking_rows,
        uso_model_rows,
        energy_gdp_lead_lag_rows,
        energy_gdp_model_rows,
        system_signal_rows,
    )
    warnings = write_audit_outputs(root, rows, lag_rows, regression_rows, rolling_rows, source_series)
    print(f"Wrote {len(rows)} monthly rows to {processed_dir / 'monthly_dataset.csv'}")
    print(f"Wrote analysis tables to {analysis_dir}")
    print(f"Wrote charts to {chart_dir}")
    print(terminal_summary(rows, lag_rows, regression_rows, warnings))


def main() -> None:
    parser = argparse.ArgumentParser(description="Build monthly oil/liquidity/inventory datasets and analysis.")
    parser.add_argument("--refresh", action="store_true", help="redownload raw source files instead of using cache")
    parser.add_argument("--root", default=".", help="project root")
    parser.add_argument("--bis-url", default=os.environ.get("BIS_TOTAL_CREDIT_URL"), help="optional BIS CSV/SDMX-CSV URL")
    args = parser.parse_args()
    build(Path(args.root).resolve(), refresh=args.refresh, bis_url=args.bis_url)


if __name__ == "__main__":
    main()
