from __future__ import annotations

import argparse
import os
from pathlib import Path

from .adapters import BisAdapter, BojAdapter, ChinaM2Adapter, EcbAdapter, EiaInventoryAdapter, EiaMerAdapter, EiaPetroleumPriceAdapter, FredAdapter, Series, YahooChartAdapter
from .analysis import energy_gdp_suite, final_reporting_suite, integrated_synthesis_suite, lag_correlations, oil_equity_robustness_suite, oil_equity_suite, physical_realised_price_suite, regression_suite, second_stage_suite, third_stage_suite, uso_suite
from .audit import terminal_summary, write_audit_outputs
from .cache import RawCache
from .canada import build_canadian_outputs
from .charts import make_charts
from .storage import Store, maybe_write_parquet, write_csv
from .output_quality import build_output_quality_dataset, energy_output_quality_tests, output_quality_markdown
from .system_response import (
    build_core_dataset,
    current_state,
    energy_burden_analysis,
    framework_markdown,
    historical_episode_library,
    indicator_catalogue,
    labour_early_warning_analysis,
    make_system_response_charts,
    physical_tightness_analysis,
)
from .transforms import build_monthly_dataset
from .website_data import write_website_chart_data


def final_time_series_chart_notes() -> str:
    return """# Final Time-Series Chart Notes

These charts complement the correlation, lead-lag, and model-selection tables by showing the historical paths of the main oil-system signals.

WTI and Brent are benchmark oil prices. They are the primary oil-price targets in the locked GM2-only lag-5 model.

RAC composite is the average realised crude cost paid by U.S. refiners. It is a physical-realised price layer, not a replacement for WTI or Brent.

USO is investor-accessible oil exposure. Its path captures realised market exposure through a futures ETF structure rather than pure benchmark oil, so it can diverge from WTI and Brent through roll yield, expenses, tracking differences, and fund structure.

GM2 is the leading liquidity impulse. In the final lead chart, GM2 YoY is shifted forward by five months so GM2 from month `t-5` is shown against oil-price momentum in month `t`; this preserves the no-future-leakage lag convention.

Comparative inventory is a physical-market state and residual diagnostic. It is used to interpret deviations from the GM2-implied oil path rather than to replace the locked benchmark forecast.

Mixed-unit charts use z-scores or indexed values so the series can be compared visually on one axis. Regime shading marks the 2008-2009 financial crisis, 2014-2017 shale regime, 2020-2021 Covid/oil futures dislocation, and 2022-2023 war/SPR regime.
"""


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
    eia_prices = EiaPetroleumPriceAdapter(cache)
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
    rac_composite = eia_prices.fetch_monthly_series("R0000____3", "RAC_COMPOSITE")
    rac_domestic = eia_prices.fetch_monthly_series("R1200____3", "RAC_DOMESTIC")
    rac_imported = eia_prices.fetch_monthly_series("R1300____3", "RAC_IMPORTED")
    first_purchase = eia_prices.fetch_monthly_series("F000000__3", "US_CRUDE_FIRST_PURCHASE_PRICE")
    imported_fob_cost = eia_prices.fetch_monthly_series("I000000004", "US_IMPORTED_CRUDE_FOB_COST")
    imported_landed_cost = eia_prices.fetch_monthly_series("I000000008", "US_IMPORTED_CRUDE_LANDED_COST")
    total_energy = eia_mer.fetch_monthly_series("T01.03", "TETCBUS", "US_TOTAL_PRIMARY_ENERGY_CONSUMPTION")
    oil_energy = eia_mer.fetch_monthly_series("T01.03", "PMTCBUS", "US_PETROLEUM_CONSUMPTION")
    petroleum_production = eia_mer.fetch_monthly_series("T03.01", "PAPRPUS", "US_CRUDE_OIL_PRODUCTION")
    refinery_utilization = eia.fetch_weekly_series("WPULEUS3", "US_REFINERY_UTILIZATION", "percent")
    system_fred_ids = [
        "POPTHM", "DNRGRC1M027SBEA", "DSPI", "DSPIC96", "CPIENGSL", "FEDFUNDS", "DRTSCILM", "GDP",
        "IPMAN", "PCEC96", "PNFIC1", "OPHNFB", "AWHMAN", "TEMPHELPS", "LNS12500000", "CE16OV",
        "LNS12032194", "LNS12300060", "CES0500000003", "UMCSENT", "DRCCLACBS", "UNRATE", "USREC",
        "A939RX0Q048SBEA", "A261RX1Q020SBEA", "LB0000031Q020SBEA", "A362RX1A020NBEA",
        "W171RC1Q027SBEA", "A262RX1Q020SBEA", "MEHOINUSA672N", "LES1252881600Q",
        "CXUSHELTERLB0101M", "CXUFOODTOTLLB0101M", "CXUUTILSLB0101M", "VAPGDPFI", "VAPGDPRL",
        "TDSP", "CMDEBT", "DDDM01USA156NWDB", "TSIFRGHT",
    ]
    system_fred = {series_id: fred.fetch(series_id) for series_id in system_fred_ids}
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
        "RAC composite": rac_composite,
        "RAC domestic": rac_domestic,
        "RAC imported": rac_imported,
        "Domestic first purchase price": first_purchase,
        "Imported crude FOB cost": imported_fob_cost,
        "Imported crude landed cost": imported_landed_cost,
        "Total primary energy consumption": total_energy,
        "Petroleum consumption": oil_energy,
        "Crude oil production": petroleum_production,
        "Refinery utilization": refinery_utilization,
    }
    source_series.update({f"System response {series_id}": series for series_id, series in system_fred.items()})

    rows = build_monthly_dataset(
        us_m2, ea_m2, cn_m2, jp_m2, eurusd, cnyusd, jpyusd, cpi, sp500, uso_avg, uso_month_end, wti, brent, inventory,
        rac_composite, rac_domestic, rac_imported, first_purchase, imported_fob_cost, imported_landed_cost,
    )
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
    physical_price_rows, physical_price_findings = physical_realised_price_suite(rows)
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
    system_response_series = {
        **system_fred,
        "PAPRPUS": petroleum_production,
        "WPULEUS3": refinery_utilization,
        "PMTCBUS": oil_energy,
        "TETCBUS": total_energy,
        "INDPRO": indpro,
        "GDPC1": gdpc1,
    }
    system_response_core = build_core_dataset(rows, system_response_series)
    canadian_catalogue, _canadian_payloads = build_canadian_outputs(root, rows, system_response_core, cache)
    system_response_catalogue = indicator_catalogue(system_response_series, system_response_core)
    system_response_current = current_state(system_response_core)
    energy_burden_rows, energy_burden_findings = energy_burden_analysis(system_response_core)
    physical_tightness_rows, physical_tightness_findings = physical_tightness_analysis(system_response_core)
    labour_warning_rows, labour_warning_findings = labour_early_warning_analysis(system_response_core)
    historical_episode_rows, historical_episode_findings = historical_episode_library()
    system_response_framework = framework_markdown(system_response_catalogue, system_response_core)
    output_quality_series = {**system_fred, "GDPC1": gdpc1, "INDPRO": indpro}
    output_quality_rows, output_quality_derived = build_output_quality_dataset(output_quality_series, cpi)
    burden_series = Series("HOUSEHOLD_ENERGY_BURDEN", "percent", "BEA energy PCE / disposable personal income", [(str(row["month"]), float(row["household_energy_expenditure_share"])) for row in system_response_core if row.get("household_energy_expenditure_share") is not None])
    output_quality_correlation_rows = energy_output_quality_tests(output_quality_series, output_quality_derived, total_energy, system_fred["USREC"])
    output_quality_correlation_rows += energy_output_quality_tests(output_quality_series, output_quality_derived, burden_series, system_fred["USREC"], "Household energy-burden growth")
    output_quality_findings = output_quality_markdown(output_quality_rows, output_quality_correlation_rows)
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
    write_csv(analysis_dir / "physical_realised_price_summary.csv", physical_price_rows)
    write_csv(analysis_dir / "energy_gdp_lead_lag.csv", energy_gdp_lead_lag_rows)
    write_csv(analysis_dir / "energy_gdp_model_summary.csv", energy_gdp_model_rows)
    write_csv(analysis_dir / "system_signal_hierarchy.csv", system_signal_rows)
    write_csv(processed_dir / "system_response_core.csv", system_response_core)
    write_csv(analysis_dir / "system_response_indicator_catalogue.csv", system_response_catalogue)
    write_csv(analysis_dir / "system_response_current_state.csv", system_response_current)
    write_csv(analysis_dir / "energy_burden_validation.csv", energy_burden_rows)
    write_csv(analysis_dir / "physical_tightness_summary.csv", physical_tightness_rows)
    write_csv(analysis_dir / "labour_early_warning_summary.csv", labour_warning_rows)
    write_csv(analysis_dir / "historical_episode_library.csv", historical_episode_rows)
    write_csv(analysis_dir / "economic_output_quality.csv", output_quality_rows)
    write_csv(analysis_dir / "energy_output_quality_correlations.csv", output_quality_correlation_rows)
    (analysis_dir / "second_stage_findings.md").write_text(second_stage_findings, encoding="utf-8")
    (analysis_dir / "final_model_interpretation.md").write_text(final_interpretation, encoding="utf-8")
    (analysis_dir / "executive_summary.md").write_text(executive_summary, encoding="utf-8")
    (analysis_dir / "model_card.md").write_text(model_card, encoding="utf-8")
    (analysis_dir / "current_signal_snapshot.md").write_text(signal_snapshot, encoding="utf-8")
    (analysis_dir / "oil_equity_findings.md").write_text(oil_equity_findings, encoding="utf-8")
    (analysis_dir / "oil_equity_robustness.md").write_text(oil_equity_robustness, encoding="utf-8")
    (analysis_dir / "uso_findings.md").write_text(uso_findings, encoding="utf-8")
    (analysis_dir / "physical_realised_price_findings.md").write_text(physical_price_findings, encoding="utf-8")
    (analysis_dir / "energy_gdp_findings.md").write_text(energy_gdp_findings, encoding="utf-8")
    (analysis_dir / "integrated_lead_lag_atlas.md").write_text(integrated_atlas, encoding="utf-8")
    (analysis_dir / "final_system_interpretation.md").write_text(final_system_interpretation, encoding="utf-8")
    (analysis_dir / "final_time_series_chart_notes.md").write_text(final_time_series_chart_notes(), encoding="utf-8")
    (analysis_dir / "system_response_framework.md").write_text(system_response_framework, encoding="utf-8")
    (analysis_dir / "energy_burden_findings.md").write_text(energy_burden_findings, encoding="utf-8")
    (analysis_dir / "physical_tightness_findings.md").write_text(physical_tightness_findings, encoding="utf-8")
    (analysis_dir / "labour_early_warning_findings.md").write_text(labour_warning_findings, encoding="utf-8")
    (analysis_dir / "historical_episode_library.md").write_text(historical_episode_findings, encoding="utf-8")
    (analysis_dir / "economic_output_quality.md").write_text(output_quality_findings, encoding="utf-8")
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
        store.write_rows("physical_realised_price_summary", physical_price_rows)
        store.write_rows("energy_gdp_lead_lag", energy_gdp_lead_lag_rows)
        store.write_rows("energy_gdp_model_summary", energy_gdp_model_rows)
        store.write_rows("system_signal_hierarchy", system_signal_rows)
        store.write_rows("system_response_core", system_response_core)
        store.write_rows("system_response_indicator_catalogue", system_response_catalogue)
        store.write_rows("system_response_current_state", system_response_current)
        store.write_rows("energy_burden_validation", energy_burden_rows)
        store.write_rows("physical_tightness_summary", physical_tightness_rows)
        store.write_rows("labour_early_warning_summary", labour_warning_rows)
        store.write_rows("historical_episode_library", historical_episode_rows)
        store.write_rows("economic_output_quality", output_quality_rows)
        store.write_rows("energy_output_quality_correlations", output_quality_correlation_rows)
        store.write_rows("canadian_indicator_catalogue", canadian_catalogue)
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
        physical_price_rows,
        energy_gdp_lead_lag_rows,
        energy_gdp_model_rows,
        system_signal_rows,
    )
    make_system_response_charts(
        system_response_core,
        system_response_current,
        energy_burden_rows,
        physical_tightness_rows,
        labour_warning_rows,
        historical_episode_rows,
        chart_dir,
    )
    write_website_chart_data(
        root,
        rows,
        lag_rows,
        rolling_extended_rows,
        oil_equity_return_lag_rows,
        energy_gdp_lead_lag_rows,
        system_response_core,
        system_response_current,
        system_response_catalogue,
        output_quality_rows,
        output_quality_correlation_rows,
        historical_episode_rows,
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
