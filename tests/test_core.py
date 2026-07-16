from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from oil_model.adapters import SourceDataError, require_observations
from oil_model.analysis import design_matrix, design_matrix_specs, feature, lagged_pairs
from oil_model.pipeline import build
from oil_model.transforms import build_monthly_dataset, comparative_inventory, yoy


class CoreTests(unittest.TestCase):
    def test_gm2_usd_conversion_requires_all_components(self) -> None:
        rows = build_monthly_dataset(
            fake_series("us", [("2020-01", 1.0)]),
            fake_series("ea", [("2020-01", 2_000_000.0)]),
            fake_series("cn", [("2020-01", 30.0)]),
            fake_series("jp", [("2020-01", 400.0)]),
            fake_series("eurusd", [("2020-01", 1.2)]),
            fake_series("cny", [("2020-01", 6.0)]),
            fake_series("jpy", [("2020-01", 100.0)]),
            fake_series("cpi", [("2020-01", 250.0)]),
            fake_series("sp500", [("2020-01", 3000.0)]),
            fake_series("uso_avg", [("2020-01", 10.0)]),
            fake_series("uso_me", [("2020-01", 10.0)]),
            fake_series("wti", []),
            fake_series("brent", []),
            fake_series("inv", []),
        )
        row = rows[0]
        self.assertEqual(row["US_M2_USD"], 1_000_000_000)
        self.assertEqual(row["EA_M2_USD"], 2_400_000.0)
        self.assertEqual(row["CN_M2_USD"], 5.0)
        self.assertEqual(row["JP_M2_USD"], 4.0)
        self.assertAlmostEqual(row["GM2_USD"], 1_002_400_009.0)
        self.assertEqual(row["US_CPI"], 250.0)

    def test_gm2_usd_aggregation_uses_same_month_fx(self) -> None:
        rows = build_monthly_dataset(
            fake_series("us", [("2020-01", 1.0), ("2020-02", 1.0)]),
            fake_series("ea", [("2020-01", 100.0), ("2020-02", 100.0)]),
            fake_series("cn", [("2020-01", 600.0), ("2020-02", 600.0)]),
            fake_series("jp", [("2020-01", 10_000.0), ("2020-02", 10_000.0)]),
            fake_series("eurusd", [("2020-01", 1.1), ("2020-02", 1.3)]),
            fake_series("cny", [("2020-01", 6.0), ("2020-02", 7.0)]),
            fake_series("jpy", [("2020-01", 100.0), ("2020-02", 125.0)]),
            fake_series("cpi", [("2020-01", 250.0), ("2020-02", 251.0)]),
            fake_series("sp500", [("2020-01", 3000.0), ("2020-02", 3030.0)]),
            fake_series("uso_avg", [("2020-01", 10.0), ("2020-02", 10.5)]),
            fake_series("uso_me", [("2020-01", 10.0), ("2020-02", 10.5)]),
            fake_series("wti", []),
            fake_series("brent", []),
            fake_series("inv", []),
        )
        self.assertAlmostEqual(rows[0]["EA_M2_USD"], 110.0)
        self.assertAlmostEqual(rows[1]["EA_M2_USD"], 130.0)
        self.assertAlmostEqual(rows[0]["CN_M2_USD"], 100.0)
        self.assertAlmostEqual(rows[1]["CN_M2_USD"], 600.0 / 7.0)
        self.assertAlmostEqual(rows[0]["JP_M2_USD"], 100.0)
        self.assertAlmostEqual(rows[1]["JP_M2_USD"], 80.0)

    def test_yoy_calculation(self) -> None:
        values = [100.0] * 12 + [125.0]
        self.assertEqual(yoy(values)[-1], 25.0)

    def test_physical_realised_price_fields(self) -> None:
        months = fake_months(13)
        rows = build_monthly_dataset(
            *[fake_series(name, []) for name in ["us", "ea", "cn", "jp", "eur", "cny", "jpy", "cpi", "sp500", "uso_avg", "uso_end"]],
            fake_series("wti", list(zip(months, [100.0] * 12 + [110.0]))),
            fake_series("brent", list(zip(months, [105.0] * 12 + [115.5]))),
            fake_series("inventory", []),
            rac_composite=fake_series("rac", list(zip(months, [90.0] * 12 + [99.0]))),
            rac_domestic=fake_series("rac_domestic", list(zip(months, [91.0] * 12 + [100.1]))),
            rac_imported=fake_series("rac_imported", list(zip(months, [89.0] * 12 + [97.9]))),
            first_purchase=fake_series("first", list(zip(months, [80.0] * 12 + [88.0]))),
            imported_fob_cost=fake_series("fob", list(zip(months, [95.0] * 12 + [104.5]))),
            imported_landed_cost=fake_series("landed", list(zip(months, [100.0] * 12 + [110.0]))),
        )
        latest = rows[-1]
        self.assertAlmostEqual(latest["RAC_composite_YoY"], 10.0)
        self.assertAlmostEqual(latest["landed_import_cost_YoY"], 10.0)
        self.assertAlmostEqual(latest["RAC_vs_WTI_spread"], -11.0)
        self.assertAlmostEqual(latest["first_purchase_vs_WTI_spread"], -22.0)
        self.assertAlmostEqual(latest["landed_import_vs_Brent_spread"], -5.5)

    def test_lag_generation(self) -> None:
        rows = [
            {"GM2_YoY": 1.0, "WTI_YoY": 10.0},
            {"GM2_YoY": 2.0, "WTI_YoY": 20.0},
            {"GM2_YoY": 3.0, "WTI_YoY": 30.0},
        ]
        self.assertEqual(lagged_pairs(rows, "GM2_YoY", "WTI_YoY", 1), [(1.0, 20.0), (2.0, 30.0)])

    def test_no_future_leakage_in_lagged_gm2_features(self) -> None:
        rows = [
            {"month": "2020-01", "GM2_YoY": 1.0, "WTI_YoY": 10.0},
            {"month": "2020-02", "GM2_YoY": 2.0, "WTI_YoY": 20.0},
            {"month": "2020-03", "GM2_YoY": 999.0, "WTI_YoY": 30.0},
        ]
        x, y, months = design_matrix_specs(rows, "WTI_YoY", [feature("GM2_YoY", 1, "GM2_YoY_lag")])
        self.assertEqual(months, ["2020-02", "2020-03"])
        self.assertEqual(x.tolist(), [[1.0], [2.0]])
        self.assertEqual(y.tolist(), [20.0, 30.0])

    def test_comparative_inventory_uses_prior_five_same_month_values(self) -> None:
        months = [f"{year}-01" for year in range(2015, 2021)]
        values = [100.0, 110.0, 90.0, 105.0, 95.0, 120.0]
        result = comparative_inventory(months, values)
        self.assertIsNone(result[4]["comparative_inventory_kb"])
        self.assertEqual(result[5]["comparative_inventory_kb"], 20.0)
        self.assertEqual(result[5]["CI_monthly_change"], 25.0)

    def test_regression_input_alignment(self) -> None:
        rows = [
            {"GM2_YoY": 1.0, "CI_zscore": 0.1, "WTI_YoY": 10.0},
            {"GM2_YoY": 2.0, "CI_zscore": 0.2, "WTI_YoY": 20.0},
            {"GM2_YoY": 3.0, "CI_zscore": 0.3, "WTI_YoY": 30.0},
        ]
        x, y = design_matrix(rows, "WTI_YoY", [("GM2_YoY", 1), ("CI_zscore", 0)])
        self.assertEqual(x.tolist(), [[1.0, 0.2], [2.0, 0.3]])
        self.assertEqual(y.tolist(), [20.0, 30.0])

    def test_missing_source_handling(self) -> None:
        with self.assertRaises(SourceDataError):
            require_observations("empty", [])

    def test_pipeline_generates_required_outputs_from_clean_raw_cache(self) -> None:
        required_analysis = [
            "interaction_model_summary.csv",
            "residual_model_summary.csv",
            "regime_model_summary.csv",
            "rolling_validation_extended.csv",
            "final_model_interpretation.md",
            "target_comparison_summary.csv",
            "residual_diagnostic_summary.csv",
            "executive_summary.md",
            "model_card.md",
            "final_findings_table.csv",
            "current_signal_snapshot.md",
            "oil_equity_lead_lag_summary.csv",
            "oil_equity_findings.md",
            "oil_equity_robustness.md",
            "oil_equity_return_lag_summary.csv",
            "uso_findings.md",
            "uso_lead_lag_summary.csv",
            "uso_tracking_residual_summary.csv",
            "uso_model_summary.csv",
            "physical_realised_price_findings.md",
            "physical_realised_price_summary.csv",
            "energy_gdp_findings.md",
            "energy_gdp_lead_lag.csv",
            "energy_gdp_model_summary.csv",
            "integrated_lead_lag_atlas.md",
            "system_signal_hierarchy.csv",
            "final_system_interpretation.md",
            "final_time_series_chart_notes.md",
            "system_response_framework.md",
            "system_response_indicator_catalogue.csv",
            "system_response_current_state.csv",
            "energy_burden_findings.md",
            "energy_burden_validation.csv",
            "physical_tightness_findings.md",
            "physical_tightness_summary.csv",
            "labour_early_warning_findings.md",
            "labour_early_warning_summary.csv",
            "historical_episode_library.md",
            "historical_episode_library.csv",
            "economic_output_quality.md",
            "economic_output_quality.csv",
            "energy_output_quality_correlations.csv",
            "canadian_data_audit.md",
            "canadian_indicator_catalogue.csv",
            "food_housing_affordability_findings.md",
            "food_housing_indicator_catalogue.csv",
            "food_price_transmission_summary.csv",
            "canadian_income_data_audit.md",
            "canadian_income_indicator_catalogue.csv",
        ]
        required_charts = [
            "residual_vs_ci_zscore.png",
            "actual_vs_predicted_best_gm2.png",
            "ci_vs_real_oil_price_level.png",
            "target_comparison_rmse.png",
            "final_gm2_oil_lead_chart.png",
            "final_actual_vs_predicted_wti.png",
            "final_residual_ci_diagnostic.png",
            "final_model_framework.png",
            "oil_equity_rolling_correlation.png",
            "oil_equity_lag_correlation.png",
            "oil_equity_return_lag_correlation.png",
            "sp500_vs_wti_yoy.png",
            "oil_equity_regime_scatter.png",
            "uso_vs_wti_yoy.png",
            "uso_wti_return_spread.png",
            "uso_tracking_residual_by_regime.png",
            "uso_gm2_model_comparison.png",
            "physical_realised_prices_vs_benchmarks.png",
            "rac_vs_wti_spread.png",
            "physical_price_ci_relationship.png",
            "energy_vs_gdp_growth.png",
            "energy_intensity_trend.png",
            "gdp_per_energy_trend.png",
            "energy_gdp_lead_lag_heatmap.png",
            "oil_price_burden_vs_real_activity.png",
            "final_lead_lag_network.png",
            "final_signal_timeline_framework.png",
            "final_energy_finance_oil_gdp_map.png",
            "final_oil_price_layers_time_series.png",
            "final_gm2_leads_oil_time_series.png",
            "final_oil_residual_ci_time_series.png",
            "final_energy_gdp_time_series.png",
            "system_response_chain.png",
            "current_state_layers.png",
            "physical_tightness_dashboard.png",
            "energy_burden_dashboard.png",
            "demand_destruction_cycle.png",
            "industrial_transmission.png",
            "labour_early_warning_indicators.png",
            "household_stress_indicators.png",
            "historical_episode_comparison.png",
            "regime_timeline.png",
            "indicator_lag_map.png",
        ]
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            with (
                patch("oil_model.pipeline.FredAdapter", FakeFredAdapter),
                patch("oil_model.pipeline.EcbAdapter", FakeEcbAdapter),
                patch("oil_model.pipeline.BojAdapter", FakeBojAdapter),
                patch("oil_model.pipeline.ChinaM2Adapter", FakeChinaM2Adapter),
                patch("oil_model.pipeline.EiaInventoryAdapter", FakeEiaInventoryAdapter),
                patch("oil_model.pipeline.EiaMerAdapter", FakeEiaMerAdapter),
                patch("oil_model.pipeline.EiaPetroleumPriceAdapter", FakeEiaPetroleumPriceAdapter),
                patch("oil_model.pipeline.YahooChartAdapter", FakeYahooChartAdapter),
                patch("oil_model.pipeline.second_stage_suite", fake_second_stage_suite),
                patch("oil_model.pipeline.third_stage_suite", fake_third_stage_suite),
                patch("oil_model.pipeline.uso_suite", fake_uso_suite),
                patch("oil_model.pipeline.physical_realised_price_suite", fake_physical_realised_price_suite),
                patch("oil_model.pipeline.energy_gdp_suite", fake_energy_gdp_suite),
                patch("oil_model.pipeline.integrated_synthesis_suite", fake_integrated_synthesis_suite),
                patch("oil_model.pipeline.make_charts", fake_make_charts),
                patch("oil_model.pipeline.make_system_response_charts", fake_make_system_response_charts),
                patch("oil_model.pipeline.build_canadian_outputs", fake_build_canadian_outputs),
                patch("oil_model.pipeline.build_affordability_outputs", fake_build_affordability_outputs),
                patch.multiple("oil_model.pipeline", write_evidence_summary=fake_write_evidence_summary, write_presentation_contract=fake_write_presentation_contract),
            ):
                build(root)
            self.assertTrue((root / "data" / "raw").exists())
            for filename in required_analysis:
                self.assertTrue((root / "analysis" / filename).exists(), filename)
            for filename in required_charts:
                self.assertTrue((root / "charts" / filename).exists(), filename)
            for filename in ["manifest.json", "oil-price-layers.json", "gm2-oil-lead.json", "oil-residual-ci.json", "ci-wti-annual.json", "energy-gdp.json", "oil-equities.json", "uso-tracking.json", "lag-results.json", "regimes.json", "events.json", "cross-layer.json", "current-classification.json", "symptom-evaluations.json", "regime-scores.json", "regime-history.json", "evidence-summary.json", "presentation-manifest.json"]:
                self.assertTrue((root / "website" / "public" / "generated" / filename).exists(), filename)
            for filename in ["manifest.json", "current-state.json", "canada-us-comparison.json", "indicators/canada-unemployment-rate.json", "indicators/ontario-unemployment-rate.json"]:
                self.assertTrue((root / "website" / "public" / "generated" / "canada" / filename).exists(), filename)
            for filename in ["affordability-fao-food.json", "affordability-canada-housing.json", "affordability-canada-purchasing-power.json", "affordability-canada-food-income.json", "affordability-canada-housing-ratios.json", "food-transmission-analysis.json"]:
                self.assertTrue((root / "website" / "public" / "generated" / filename).exists(), filename)


def fake_series(name: str, observations: list[tuple[str, float]]):
    from oil_model.adapters import Series

    return Series(name=name, unit="test", source="test", observations=observations)


def fake_months(n: int = 96) -> list[str]:
    months = []
    year, month = 2010, 1
    for _ in range(n):
        months.append(f"{year}-{month:02d}")
        month += 1
        if month == 13:
            year += 1
            month = 1
    return months


def fake_series_range(name: str, base: float, step: float = 1.0):
    return fake_series(name, [(month, base + i * step) for i, month in enumerate(fake_months())])


class FakeFredAdapter:
    def __init__(self, cache):
        self.cache = cache

    def fetch(self, series_id: str, *, monthly: bool = False):
        values = {
            "M2SL": (1_000.0, 4.0),
            "DEXUSEU": (1.1, 0.001),
            "DEXCHUS": (6.5, 0.001),
            "DEXJPUS": (110.0, 0.01),
            "CPIAUCSL": (220.0, 0.2),
            "SP500": (3000.0, 5.0),
            "GDPC1": (18_000.0, 20.0),
            "INDPRO": (100.0, 0.1),
            "DCOILWTICO": (60.0, 0.1),
            "DCOILBRENTEU": (65.0, 0.1),
            "POPTHM": (300_000.0, 100.0),
            "DNRGRC1M027SBEA": (1_000.0, 1.0),
            "DSPI": (18_000.0, 10.0),
            "DSPIC96": (15_000.0, 8.0),
            "CPIENGSL": (220.0, 0.3),
            "FEDFUNDS": (2.0, 0.01),
            "DRTSCILM": (0.0, 0.1),
            "GDP": (20_000.0, 20.0),
            "IPMAN": (100.0, 0.1),
            "PCEC96": (14_000.0, 10.0),
            "PNFIC1": (3_000.0, 4.0),
            "OPHNFB": (100.0, 0.1),
            "AWHMAN": (40.0, 0.001),
            "TEMPHELPS": (2_500.0, 1.0),
            "LNS12500000": (120_000.0, 20.0),
            "CE16OV": (150_000.0, 25.0),
            "LNS12032194": (4_000.0, 1.0),
            "LNS12300060": (78.0, 0.01),
            "CES0500000003": (25.0, 0.03),
            "UMCSENT": (85.0, 0.01),
            "DRCCLACBS": (2.5, 0.001),
            "UNRATE": (5.0, -0.001),
            "USREC": (0.0, 0.0),
            "A939RX0Q048SBEA": (55_000.0, 20.0),
            "A261RX1Q020SBEA": (18_000.0, 20.0),
            "LB0000031Q020SBEA": (17_000.0, 18.0),
            "A362RX1A020NBEA": (15_000.0, 15.0),
            "W171RC1Q027SBEA": (1_000.0, 2.0),
            "A262RX1Q020SBEA": (3_000.0, 3.0),
            "MEHOINUSA672N": (70_000.0, 30.0),
            "LES1252881600Q": (350.0, 0.1),
            "CXUSHELTERLB0101M": (15_000.0, 10.0),
            "CXUFOODTOTLLB0101M": (9_000.0, 5.0),
            "CXUUTILSLB0101M": (4_000.0, 3.0),
            "VAPGDPFI": (8.0, 0.001),
            "VAPGDPRL": (13.0, 0.001),
            "TDSP": (10.0, 0.001),
            "CMDEBT": (18_000.0, 10.0),
            "DDDM01USA156NWDB": (150.0, 0.05),
            "TSIFRGHT": (100.0, 0.05),
        }
        base, step = values[series_id]
        return fake_series_range(series_id, base, step)


class FakeEcbAdapter:
    def __init__(self, cache):
        self.cache = cache

    def fetch_euro_area_m2(self):
        return fake_series_range("ea", 10_000_000.0, 1_000.0)


class FakeBojAdapter:
    def __init__(self, cache):
        self.cache = cache

    def fetch_japan_m2(self):
        return fake_series_range("jp", 1_000_000_000.0, 100_000.0)


class FakeChinaM2Adapter:
    def __init__(self, cache, fred):
        self.cache = cache
        self.fred = fred

    def fetch_china_m2(self):
        return fake_series_range("cn", 20_000_000.0, 2_000.0)


class FakeEiaInventoryAdapter:
    def __init__(self, cache):
        self.cache = cache

    def fetch_crude_stocks_ex_spr(self):
        return fake_series_range("inv", 400_000.0, 100.0)

    def fetch_weekly_series(self, series_id, name, unit):
        return fake_series_range(name, 88.0, 0.01)


class FakeEiaMerAdapter:
    def __init__(self, cache):
        self.cache = cache

    def fetch_monthly_series(self, table_id, msn, name):
        base = 8.0 if msn == "TETCBUS" else 3.0
        return fake_series_range(name, base, 0.01)


class FakeEiaPetroleumPriceAdapter:
    def __init__(self, cache):
        self.cache = cache

    def fetch_monthly_series(self, series_id, name):
        return fake_series_range(name, 55.0, 0.1)


class FakeYahooChartAdapter:
    def __init__(self, cache):
        self.cache = cache

    def fetch_adjusted_monthly(self, symbol):
        return fake_series_range(f"{symbol}_MONTHLY_AVG_ADJ_CLOSE", 10.0, 0.05), fake_series_range(f"{symbol}_MONTH_END_ADJ_CLOSE", 10.0, 0.05)


def fake_second_stage_suite(rows):
    row = {"target": "WTI_YoY", "model": "fake", "lag_months": 1}
    return [row], [row], [row], [row], "# Second stage\n"


def fake_third_stage_suite(rows):
    row = {"target": "WTI_YoY", "model": "fake", "rolling_rmse": 1.0}
    return [row], [row], "# Final\n"


def fake_energy_gdp_suite(rows, gdpc1, indpro, total_energy, oil_energy):
    row = {"section": "fake", "target": "Real_GDP_growth", "model": "fake"}
    return [row], [row], "# Energy GDP\n"


def fake_uso_suite(rows):
    row = {"section": "fake", "target": "USO_YoY", "model": "fake"}
    return [row], [row], [row], "# USO\n"


def fake_physical_realised_price_suite(rows):
    row = {"section": "fake", "target": "RAC_composite_YoY", "model": "fake"}
    return [row], "# Physical realised prices\n"


def fake_integrated_synthesis_suite(lag_rows, rolling_extended_rows, residual_diagnostic_rows, oil_equity_rows, energy_gdp_rows):
    row = {"layer": "fake", "signal": "fake", "target": "fake"}
    return [row], "# Atlas\n", "# System\n"


def fake_build_canadian_outputs(root, global_rows, us_rows, cache):
    from oil_model.storage import write_csv

    write_csv(root / "analysis" / "canadian_indicator_catalogue.csv", [{"indicator_name": "Fake Canada"}])
    (root / "analysis" / "canadian_data_audit.md").write_text("# Canadian Data Audit\n", encoding="utf-8")
    write_csv(root / "data" / "processed" / "canadian_core.csv", [{"indicator_id": "canada-unemployment-rate", "date": "2020-01-01", "value": 5.0}])
    out = root / "website" / "public" / "generated" / "canada"
    indicators = out / "indicators"
    indicators.mkdir(parents=True, exist_ok=True)
    payload = {"schemaVersion": 1, "id": "canada-unemployment-rate", "field": "canada_unemployment_rate", "label": "Canada unemployment", "description": "fake", "unit": "percent", "frequency": "monthly", "status": "measured", "layer": "Labour and households", "geography": "Canada", "geographyLevel": "national", "domesticOrExternal": "domestic", "directlyComparableAcrossCountries": True, "comparisonLimitations": "fake", "interpretationDirection": "context-dependent", "interpretationLabel": "Direction unclear", "interpretation": "fake", "source": "fake", "sourceUrl": "https://example.test", "sourceIdentifier": "fake", "seasonalAdjustment": "seasonally adjusted", "nominalOrReal": "rate", "core": True, "startDate": "2020-01-01", "endDate": "2020-01-01", "latest": {"date": "2020-01-01", "sourceDate": "2020-02-01", "value": 5.0, "previousValue": None, "oneYearChange": None, "threeMonthChange": None, "fourQuarterChange": None, "historicalPercentile": 50.0, "percentileSince2000": 50.0, "distanceFromMedian": 0.0, "momentum": "steady"}, "referenceRanges": {"historicalMedian": 5.0, "p10": 5.0, "p25": 5.0, "p75": 5.0, "p90": 5.0, "minimum": 5.0, "maximum": 5.0}, "observations": [{"date": "2020-01-01", "value": 5.0, "sourceDate": "2020-02-01"}], "confirmingIndicators": [], "conflictingIndicators": [], "evidenceChecks": [], "confidenceLevel": "medium", "evidenceLabel": "Contextual indicator", "calculation": {"formula": "fake", "explanation": "fake", "example": "fake"}, "limitations": ["fake"], "generatedAt": "2020-01-01"}
    (indicators / "canada-unemployment-rate.json").write_text(json.dumps(payload), encoding="utf-8")
    ontario = {**payload, "id": "ontario-unemployment-rate", "field": "ontario_unemployment_rate", "label": "Ontario unemployment", "geography": "Ontario", "geographyLevel": "provincial", "core": False}
    (indicators / "ontario-unemployment-rate.json").write_text(json.dumps(ontario), encoding="utf-8")
    (out / "manifest.json").write_text(json.dumps({"schemaVersion": 1, "defaultGeography": "Canada", "classificationImplemented": True, "indicators": []}), encoding="utf-8")
    (out / "current-state.json").write_text(json.dumps({"status": "Canadian diagnostic status: provisional transparent classification available."}), encoding="utf-8")
    (out / "canada-us-comparison.json").write_text(json.dumps({"datasets": []}), encoding="utf-8")
    (out / "current-classification.json").write_text(json.dumps({"scope": "Canadian", "provisionalClassification": {}, "quarterlyAlignedClassification": {}}), encoding="utf-8")
    (out / "symptom-evaluations.json").write_text(json.dumps({"evaluations": []}), encoding="utf-8")
    (out / "regime-scores.json").write_text(json.dumps({"scores": []}), encoding="utf-8")
    write_csv(root / "analysis" / "canadian_historical_episodes.csv", [{"episode": "Fake"}])
    (root / "analysis" / "canadian_historical_episodes.md").write_text("# Canadian Historical Episodes\n", encoding="utf-8")
    return [{"indicator_name": "Fake Canada"}], [payload, ontario]


def fake_build_affordability_outputs(root, cache):
    from oil_model.storage import write_csv

    generated = root / "website" / "public" / "generated"
    generated.mkdir(parents=True, exist_ok=True)
    fake_chart = {"schemaVersion": "1.1.0", "id": "fake", "title": "Fake affordability", "description": "fake", "plainLanguageSummary": "fake", "howToRead": "fake", "calculation": {"formula": "fake", "explanation": "fake", "example": "fake"}, "patternsToWatch": [], "limitations": [], "sourceNotes": [], "transformation": {"type": "raw", "referenceStart": "2000-01-01", "referenceEnd": "2019-12-01", "mean": None, "standardDeviation": None, "statistics": {}}, "frequency": "monthly", "dateRange": {"start": "2020-01-01", "end": "2020-01-01"}, "series": [{"key": "value", "label": "Value", "unit": "index", "source": "fake", "status": "measured", "defaultVisible": True, "frequency": "monthly", "color": None, "transformations": ["raw"], "finalObservationDate": "2020-01-01"}], "observations": [{"date": "2020-01-01", "value": 100}], "annotations": [], "availableTransformations": ["raw"], "evidenceLabel": "Contextual indicator", "methodology": {"formula": "fake"}, "staticFigure": "", "generatedAt": "2020-01-01"}
    for filename in ["affordability-fao-food.json", "affordability-canada-housing.json", "affordability-canada-purchasing-power.json", "affordability-canada-food-income.json", "affordability-canada-housing-ratios.json"]:
        (generated / filename).write_text(json.dumps({**fake_chart, "id": filename.removesuffix(".json")}), encoding="utf-8")
    (generated / "food-transmission-analysis.json").write_text(json.dumps({"schemaVersion": 1, "rows": []}), encoding="utf-8")
    for geography in ["global", "us"]:
        directory = generated / geography / "indicators"
        directory.mkdir(parents=True, exist_ok=True)
        (generated / geography / "manifest.json").write_text(json.dumps({"schemaVersion": 1, "indicators": []}), encoding="utf-8")
    write_csv(root / "analysis" / "food_price_transmission_summary.csv", [{"relationship": "fake"}])
    write_csv(root / "analysis" / "food_housing_indicator_catalogue.csv", [{"id": "fake"}])
    (root / "analysis" / "food_housing_affordability_findings.md").write_text("# Food And Housing\n", encoding="utf-8")
    write_csv(root / "analysis" / "canadian_income_indicator_catalogue.csv", [{"id": "fake"}])
    (root / "analysis" / "canadian_income_data_audit.md").write_text("# Canadian Income\n", encoding="utf-8")
    return [], []


def fake_write_evidence_summary(root):
    path = root / "website" / "public" / "generated" / "evidence-summary.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"schemaVersion": 1, "generatedAt": "2020-01-01T00:00:00+00:00", "statusDefinitions": {}, "topics": {}}
    path.write_text(json.dumps(payload), encoding="utf-8")
    return payload


def fake_write_presentation_contract(root):
    path = root / "website" / "public" / "generated" / "presentation-manifest.json"
    payload = {"schemaVersion": 1, "refineryVersion": "test", "generatedAt": "2020-01-01T00:00:00+00:00", "routes": {}}
    path.write_text(json.dumps(payload), encoding="utf-8")
    return payload


def fake_make_charts(rows, lag_rows, out_dir, residual_rows=None, rolling_rows=None, target_rows=None, oil_equity_rows=None, oil_equity_return_rows=None, uso_lead_lag_rows=None, uso_tracking_rows=None, uso_model_rows=None, physical_price_rows=None, energy_gdp_rows=None, energy_gdp_model_rows=None, system_signal_rows=None):
    out_dir.mkdir(parents=True, exist_ok=True)
    for filename in [
        "residual_vs_ci_zscore.png",
        "actual_vs_predicted_best_gm2.png",
        "ci_vs_real_oil_price_level.png",
        "target_comparison_rmse.png",
        "final_gm2_oil_lead_chart.png",
        "final_actual_vs_predicted_wti.png",
        "final_residual_ci_diagnostic.png",
        "final_model_framework.png",
        "oil_equity_rolling_correlation.png",
        "oil_equity_lag_correlation.png",
        "oil_equity_return_lag_correlation.png",
        "sp500_vs_wti_yoy.png",
        "oil_equity_regime_scatter.png",
        "uso_vs_wti_yoy.png",
        "uso_wti_return_spread.png",
        "uso_tracking_residual_by_regime.png",
        "uso_gm2_model_comparison.png",
        "physical_realised_prices_vs_benchmarks.png",
        "rac_vs_wti_spread.png",
        "physical_price_ci_relationship.png",
        "energy_vs_gdp_growth.png",
        "energy_intensity_trend.png",
        "gdp_per_energy_trend.png",
        "energy_gdp_lead_lag_heatmap.png",
        "oil_price_burden_vs_real_activity.png",
        "final_lead_lag_network.png",
        "final_signal_timeline_framework.png",
        "final_energy_finance_oil_gdp_map.png",
        "final_oil_price_layers_time_series.png",
        "final_gm2_leads_oil_time_series.png",
        "final_oil_residual_ci_time_series.png",
        "final_energy_gdp_time_series.png",
    ]:
        (out_dir / filename).write_bytes(b"png")


def fake_make_system_response_charts(core, current, energy_validation, physical, labour, episodes, out_dir):
    out_dir.mkdir(parents=True, exist_ok=True)
    for filename in [
        "system_response_chain.png",
        "current_state_layers.png",
        "physical_tightness_dashboard.png",
        "energy_burden_dashboard.png",
        "demand_destruction_cycle.png",
        "industrial_transmission.png",
        "labour_early_warning_indicators.png",
        "household_stress_indicators.png",
        "historical_episode_comparison.png",
        "regime_timeline.png",
        "indicator_lag_map.png",
    ]:
        (out_dir / filename).write_bytes(b"png")


if __name__ == "__main__":
    unittest.main()
