from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from oil_model.adapters import Series
from oil_model.technology_flows import (
    build_canada_generation_context,
    build_investment_rows,
    build_local_energy_estimates,
    read_facility_forecasts,
    read_local_usage_aggregates,
    read_ollama_workload_snapshot,
    read_us_grid_history,
)


ROOT = Path(__file__).resolve().parents[1]


class TechnologyFlowTests(unittest.TestCase):
    def test_facility_scenarios_stop_at_2030(self) -> None:
        rows = read_facility_forecasts(ROOT)
        ontario_2030 = {(row["scenario"], row["value"]) for row in rows if row["geography"] == "Ontario" and row["year"] == 2030}
        self.assertEqual(ontario_2030, {("low", 5.0), ("reference", 6.41), ("high", 6.4)})
        self.assertLessEqual(max(int(row["year"]) for row in rows), 2030)
        us_history = next(row for row in rows if row["geography"] == "United States" and row["year"] == 2024)
        self.assertEqual(us_history["status"], "historical estimate")

    def test_local_usage_loads_only_monthly_whitelisted_fields(self) -> None:
        rows = read_local_usage_aggregates(ROOT)
        self.assertEqual(len(rows), 2)
        self.assertEqual(sum(int(row["calls"]) for row in rows), 49)
        self.assertEqual(sum(int(row["output_tokens"]) for row in rows), 5386)
        self.assertNotIn("call_id", rows[0])
        self.assertNotIn("host", rows[0])

    def test_archived_workload_snapshot_has_multiple_models_and_reconciles(self) -> None:
        rows = read_ollama_workload_snapshot(ROOT)
        self.assertEqual(len(rows), 4)
        self.assertEqual(sum(int(row["completed_calls"]) for row in rows), 3807)
        self.assertEqual(sum(int(row["prompt_tokens"]) for row in rows), 8996516)
        self.assertEqual(sum(int(row["output_tokens"]) for row in rows), 1316129)
        self.assertEqual({row["snapshot_date"] for row in rows}, {"2026-10-10"})
        self.assertNotIn("host", rows[0])
        self.assertNotIn("call_id", rows[0])

    def test_us_grid_history_has_2020_to_2024_comparison(self) -> None:
        rows = read_us_grid_history(ROOT)
        self.assertEqual([row["year"] for row in rows], [2020, 2021, 2022, 2023, 2024])
        self.assertEqual(rows[-1]["data_center_index"], 182.9)
        self.assertEqual(rows[-1]["electricity_index"], 106.9)
        self.assertEqual(rows[-1]["capacity_index"], 118.2)

    def test_energy_proxy_is_limited_to_7b_to_10b_and_outputs(self) -> None:
        energy = build_local_energy_estimates(read_local_usage_aggregates(ROOT))
        small_model = next(row for row in energy if row["model"] == "qwen3.5:9b")
        larger_model = next(row for row in energy if row["model"] == "swift-qwen3.8:27b")
        self.assertLess(float(small_model["gpu_energy_low_wh"]), float(small_model["gpu_energy_reference_wh"]))
        self.assertLess(float(small_model["gpu_energy_reference_wh"]), float(small_model["gpu_energy_high_wh"]))
        self.assertIsNone(larger_model["gpu_energy_reference_wh"])
        self.assertIn("not estimated", str(larger_model["energy_status"]))

    def test_canada_generation_context_requires_complete_year(self) -> None:
        with TemporaryDirectory() as temporary:
            source = Path(temporary) / "data" / "raw" / "statcan"
            source.mkdir(parents=True)
            points = [
                {"refPer": f"2024-{month:02d}-01", "value": 1_000_000, "securityLevelCode": 0}
                for month in range(1, 13)
            ] + [{"refPer": "2025-01-01", "value": 9_000_000, "securityLevelCode": 0}]
            (source / "vector-44174609.json").write_text(json.dumps([{"status": "SUCCESS", "object": {"vectorDataPoint": points}}]), encoding="utf-8")
            rows = build_canada_generation_context(Path(temporary))
        self.assertEqual(rows, [{
            "year": 2024,
            "generation_twh": 12.0,
            "months": 12,
            "source": "Statistics Canada table 25-10-0015-01, vector 44174609",
            "status": "observed annual total",
        }])

    def test_quarterly_investment_series_align_on_union_of_dates(self) -> None:
        software = Series("software", "Billions of USD", "FRED", [("2020-01", 10.0), ("2020-04", 12.0)])
        computers = Series("computers", "Billions of USD", "FRED", [("2020-04", 4.0), ("2020-07", 5.0)])
        rows = build_investment_rows(software, computers)
        self.assertEqual([row["date"] for row in rows], ["2020-01-01", "2020-04-01", "2020-07-01"])
        self.assertIsNone(rows[0]["computer_peripherals_investment_billion_usd_saar"])
        self.assertEqual(rows[1]["software_investment_billion_usd_saar"], 12.0)
        self.assertEqual(rows[2]["computer_peripherals_investment_billion_usd_saar"], 5.0)


if __name__ == "__main__":
    unittest.main()
