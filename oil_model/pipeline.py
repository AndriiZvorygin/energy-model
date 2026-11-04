from __future__ import annotations

import argparse
import os
from pathlib import Path

from .adapters import BisAdapter, BojAdapter, ChinaM2Adapter, EcbAdapter, EiaInventoryAdapter, EiaMerAdapter, EiaPetroleumPriceAdapter, FredAdapter, Series, YahooChartAdapter
from .analysis import energy_gdp_suite, final_reporting_suite, integrated_synthesis_suite, lag_correlations, oil_equity_robustness_suite, oil_equity_suite, physical_realised_price_suite, regression_suite, second_stage_suite, third_stage_suite, uso_suite
from .affordability import build_affordability_outputs
from .historical_affordability import build_historical_affordability_outputs
from .global_human import build_global_human_outputs
from .evidence_summary import write_evidence_summary
from .presentation import write_presentation_contract
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
from .technology_flows import build_technology_flow_outputs
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
        "B935RC1Q027SBEA", "B985RC1Q027SBEA",
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
    technology_flow_outputs = build_technology_flow_outputs(
        root,
        system_fred["B985RC1Q027SBEA"],
        system_fred["B935RC1Q027SBEA"],
    )
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
    technology_site_analysis_rows = [
        {
            **row,
            "powerSources": "|".join(f"{source['title']}=>{source['url']}" for source in row.get("powerSources", [])),
            "communicationsSources": "|".join(f"{source['title']}=>{source['url']}" for source in row.get("communicationsSources", [])),
        }
        for row in technology_flow_outputs["canadian_site_screen"]
    ]

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
    write_csv(analysis_dir / "technology_flow_facility_forecasts.csv", technology_flow_outputs["facility_forecasts"])
    write_csv(analysis_dir / "technology_flow_canada_electricity.csv", technology_flow_outputs["canada_generation"])
    write_csv(analysis_dir / "technology_flow_investment_proxies.csv", technology_flow_outputs["investment"])
    write_csv(analysis_dir / "technology_flow_local_usage.csv", technology_flow_outputs["local_usage"])
    write_csv(analysis_dir / "technology_flow_ollama_workload_snapshot.csv", technology_flow_outputs["ollama_workload_snapshot"])
    write_csv(analysis_dir / "technology_flow_us_grid_history.csv", technology_flow_outputs["us_grid_history"])
    write_csv(analysis_dir / "technology_flow_local_energy_estimates.csv", technology_flow_outputs["local_energy"])
    write_csv(analysis_dir / "technology_flow_benchmark_scores.csv", technology_flow_outputs["benchmarks"])
    write_csv(analysis_dir / "technology_flow_compute_scenarios.csv", technology_flow_outputs["compute_scenarios"], lineterminator="\n")
    write_csv(analysis_dir / "technology_flow_training_run_anchor.csv", [technology_flow_outputs["training_run_anchor"]] if technology_flow_outputs["training_run_anchor"] else [], lineterminator="\n")
    write_csv(analysis_dir / "technology_flow_canadian_site_screen.csv", technology_site_analysis_rows, lineterminator="\n")
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
    (analysis_dir / "technology_flows_methodology.md").write_text(
        """# AI and technology flows: v1 scope and method

The module compares task-specific AI capability, compute requirements, facility electricity and water, Canadian siting candidates, data-centre demand, and broad digital-infrastructure investment proxies. The forecast horizon ends in 2030. It is separate from the locked oil benchmark and its classifiers.

The user-provided analysis deck and transcript guide the flow questions and geography. Published source data and local aggregate usage supply the numeric observations; slide values are not treated as measured data.

U.S. software and computer/peripheral private fixed investment are broad BEA investment proxies distributed by FRED. Neither series isolates AI spending or identifies the destination of investment.

Ontario data-centre net annual energy demand uses the low, reference, and high-demand series in Figures 1–3 of the IESO 2026 APO Demand Forecast Module workbook. Values are retained as published for 2027–2030. They are forecasts, not observed load. U.S. data-centre totals show LBNL historical estimates for 2020–2024 and the 2030 reference and compounded-uncertainty cases; no annual forecast path is interpolated between 2024 and 2030. A separate 2020–2024 index chart compares the presentation archive's data-centre estimates with EIA electricity sales and summer capacity series. The index starts at 100 in 2020 and shows growth rates, not equivalent absolute loads.

Canadian electricity generation is annualized from Statistics Canada vector 44174609 by summing twelve monthly observations and converting MWh to TWh. It provides national grid context and is not a data-centre load estimate. Grey-Bruce/Owen Sound has no local data-centre load series in this v1 source set; the local Ollama workload is not assigned a physical server location.

Local Ollama activity represents inference. The current deployment series comes from a monthly aggregate containing only model label, call counts, and prompt/output token counts. A separate presentation-archive snapshot reports 3,807 deduplicated response records across discovered pyash folders as of 2026-10-10, split across four model tags. It is a cross-sectional aggregate, not a monthly time series. The source audit deduplicated by model, creation time, and response counters. Facility-level data-centre scenarios combine training, inference, and other data-centre uses; the source set does not separate those loads. Raw prompts, responses, IDs, endpoints, host labels, hashes, and per-call timestamps are not part of the aggregate or website data. Regenerate the current monthly aggregate with `node scripts/export_local_ollama_usage.mjs --usage-dir <path>` when a new local snapshot is wanted.

The energy sensitivity applies the authors' released TokenPowerBench result for Llama 3.1 8B on vLLM at batch 128 across four H100 GPUs: 0.1467 GPU joules per generated output token. Low/high bounds are half and twice that reference, reflecting the paper's reported 2–3x batch-size spread. The estimate is used only for local model labels in the 7B–10B class. It is an illustrative GPU-only transfer, not measured local electricity: it excludes prompt processing, CPU, memory, other node loads, and cooling. Other local model sizes remain unestimated.

The capability scorecard uses the dated presentation archive retrieved 2026-09-19. It preserves the benchmark version, evaluation date, tool access, reasoning effort, scaffold, source URL, and row-specific notes. GPQA Diamond, Humanity's Last Exam, ARC-AGI-2, GDPval, DeepSWE, MLE-Bench, and METR results retain their own units and conditions; no composite capability score is computed. Human references are benchmark-specific and not interchangeable. METR rows describe an agent-system task horizon, not a standalone model or general intelligence.

Compute facility planning scenarios come from the presentation archive's 2026-10-13 table. Local, regional, national teacher, and 2,048-accelerator training tiers retain their H100-class proxy assumptions and source capital ranges. A DeepSeek-V3 run reported 2.788 million H800 GPU-hours; the 2,048-accelerator duration and energy cost are a translated planning comparison, not a reconstruction of that run's actual facility. A 100 MW campus is an explicitly linear extrapolation from the archived scenarios. Monthly and annual energy-only cost estimates use C$50–130/MWh sensitivity inputs; C$130/MWh is anchored to Hydro-Québec's proposed large-data-centre rate and C$50/MWh is an analyst-selected low case. Estimates exclude demand charges, taxes, transmission upgrades, and connection fees. These are not utility quotes. Water estimates use 0.3 L/kWh and are cooling-design sensitivities, not measured consumption.

The Canadian site screen pairs 2025 provincial hydroelectric generation/capability facts with city municipal water context for Montréal, Winnipeg, and Prince George. The 100 MW example implies 0.72 million litres/day at the planning WUE. City-wide treatment output or provincial hydro generation is not proof of available water allocation, firm power, or interconnection capacity. The rows identify candidate regions for feasibility work only. A utility/system-impact study, water-source assessment, permits, land, transmission and community/Indigenous engagement would be needed before asserting a site can host the load.

Local Ollama workload remains a measured small-scale example. Human-time savings and useful-task output are not inferred from token counts; v1 exposes no task-level productivity score.
""",
        encoding="utf-8",
    )
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
        store.write_rows("technology_flow_facility_forecasts", technology_flow_outputs["facility_forecasts"])
        store.write_rows("technology_flow_canada_electricity", technology_flow_outputs["canada_generation"])
        store.write_rows("technology_flow_investment_proxies", technology_flow_outputs["investment"])
        store.write_rows("technology_flow_local_usage", technology_flow_outputs["local_usage"])
        store.write_rows("technology_flow_ollama_workload_snapshot", technology_flow_outputs["ollama_workload_snapshot"])
        store.write_rows("technology_flow_us_grid_history", technology_flow_outputs["us_grid_history"])
        store.write_rows("technology_flow_local_energy_estimates", technology_flow_outputs["local_energy"])
        store.write_rows("technology_flow_benchmark_scores", technology_flow_outputs["benchmarks"])
        store.write_rows("technology_flow_compute_scenarios", technology_flow_outputs["compute_scenarios"])
        store.write_rows("technology_flow_training_run_anchor", [technology_flow_outputs["training_run_anchor"]] if technology_flow_outputs["training_run_anchor"] else [])
        store.write_rows("technology_flow_canadian_site_screen", technology_flow_outputs["canadian_site_screen"])
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
        technology_flow_outputs,
    )
    build_affordability_outputs(root, cache)
    build_historical_affordability_outputs(root, cache)
    build_global_human_outputs(root, cache)
    write_evidence_summary(root)
    write_presentation_contract(root)
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
