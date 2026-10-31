from __future__ import annotations

import csv
import math
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

from .adapters import Series
from .storage import Row


FACILITY_FORECAST_FILE = Path("data/seed/technology_flow_facility_forecasts.csv")
LOCAL_USAGE_FILE = Path("data/seed/local_ollama_usage_monthly.csv")
OLLAMA_WORKLOAD_SNAPSHOT_FILE = Path("data/seed/technology_flow_ollama_workload_snapshot.csv")
US_GRID_HISTORY_FILE = Path("data/seed/technology_flow_us_grid_history.csv")

# Published TokenPowerBench result for Llama 3.1 8B, vLLM, batch 128, four
# H100 GPUs. The paper reports a 2–3x energy-per-token spread across batch
# sizes; a symmetric 2x band around this result is used as a deliberately
# simple sensitivity range, not as local hardware telemetry.
GPU_JOULES_PER_OUTPUT_TOKEN = {
    "low": 0.14665647847976543 / 2,
    "reference": 0.14665647847976543,
    "high": 0.14665647847976543 * 2,
}
TOKENPOWERBENCH_SOURCE = "TokenPowerBench (AAAI 2026), Llama 3.1 8B released benchmark result"
TOKENPOWERBENCH_URL = "https://github.com/chenxuniu/TokenPowerBench"

BENCHMARK_SCORES: list[Row] = [
    {
        "model": "Qwen3.5-9B base model",
        "benchmark": "GPQA Diamond",
        "score_percent": 81.7,
        "score_status": "model-card result",
        "source": "Qwen3.5-9B official model card",
        "source_url": "https://huggingface.co/Qwen/Qwen3.5-9B",
        "limitation": "Provider-reported base-model benchmark; not a local quantized-build or municipal-task result.",
    },
    {
        "model": "Qwen3.8-27B base model",
        "benchmark": "GPQA Diamond",
        "score_percent": 89.2,
        "score_status": "model-card result",
        "source": "Qwen3.8-27B official model card",
        "source_url": "https://huggingface.co/Qwen/Qwen3.8-27B",
        "limitation": "Provider-reported base-model benchmark; not a local quantized-build or municipal-task result.",
    },
]


def _float(value: object) -> float | None:
    try:
        number = float(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None
    return number if number is not None and math.isfinite(number) else None


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _integer(row: dict[str, str], field: str) -> int:
    value = row.get(field, "")
    try:
        number = int(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"Local usage aggregate has an invalid {field!r} value") from error
    if number < 0:
        raise ValueError(f"Local usage aggregate has a negative {field!r} value")
    return number


def read_facility_forecasts(root: Path) -> list[Row]:
    rows: list[Row] = []
    for item in _read_csv(root / FACILITY_FORECAST_FILE):
        year = int(item["year"])
        if year > 2030:
            continue
        value = _float(item.get("value"))
        if value is None:
            continue
        rows.append({
            "geography": item["geography"],
            "year": year,
            "scenario": item["scenario"],
            "value": value,
            "unit": item["unit"],
            "status": "historical estimate" if item["scenario"] == "observed" else "forecast",
            "source": item["source"],
            "source_url": item["source_url"],
            "source_note": item["source_note"],
        })
    return rows


def read_local_usage_aggregates(root: Path) -> list[Row]:
    """Read only the whitelisted monthly fields; raw Ollama records are never loaded here."""
    rows: list[Row] = []
    for item in _read_csv(root / LOCAL_USAGE_FILE):
        month = item.get("month", "")
        model = item.get("model", "").strip()
        if not re.fullmatch(r"\d{4}-\d{2}", month):
            raise ValueError(f"Local usage aggregate has an invalid month: {month!r}")
        if not model:
            raise ValueError("Local usage aggregate is missing a model label")
        calls = _integer(item, "calls")
        completed = _integer(item, "completed_calls")
        failed = _integer(item, "failed_calls")
        if calls != completed + failed:
            raise ValueError(f"Local usage call totals do not reconcile for {month} / {model}")
        rows.append({
            "month": month,
            "model": model,
            "calls": calls,
            "completed_calls": completed,
            "failed_calls": failed,
            "prompt_tokens": _integer(item, "prompt_tokens"),
            "output_tokens": _integer(item, "output_tokens"),
            "source": "Sanitized monthly Ollama usage aggregate",
            "status": "observed aggregate",
        })
    return sorted(rows, key=lambda row: (str(row["month"]), str(row["model"])))


def read_ollama_workload_snapshot(root: Path) -> list[Row]:
    """Read the presentation's sanitized, deduplicated model-level Ollama totals."""
    rows: list[Row] = []
    for item in _read_csv(root / OLLAMA_WORKLOAD_SNAPSHOT_FILE):
        snapshot_date = item.get("snapshot_date", "")
        model = item.get("model", "").strip()
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", snapshot_date):
            raise ValueError(f"Ollama workload snapshot has an invalid date: {snapshot_date!r}")
        if not model:
            raise ValueError("Ollama workload snapshot is missing a model label")
        rows.append({
            "snapshot_date": snapshot_date,
            "model": model,
            "completed_calls": _integer(item, "completed_calls"),
            "prompt_tokens": _integer(item, "prompt_tokens"),
            "output_tokens": _integer(item, "output_tokens"),
            "prompt_eval_hours": _float(item.get("prompt_eval_hours")),
            "output_eval_hours": _float(item.get("output_eval_hours")),
            "total_runtime_hours": _float(item.get("total_runtime_hours")),
            "scope": "Deduplicated Ollama response metadata across discovered pyash folders",
            "source": "Presentation archive workload audit, retrieved 2026-10-10",
            "status": "observed aggregate",
        })
    if len({str(row["snapshot_date"]) for row in rows}) > 1:
        raise ValueError("Ollama workload snapshot rows must share one snapshot date")
    if len({str(row["model"]) for row in rows}) != len(rows):
        raise ValueError("Ollama workload snapshot has duplicate model labels")
    return sorted(rows, key=lambda row: (-int(row["completed_calls"]), str(row["model"])))


def read_us_grid_history(root: Path) -> list[Row]:
    """Read the presentation's sourced U.S. data-centre and grid index series."""
    rows: list[Row] = []
    for item in _read_csv(root / US_GRID_HISTORY_FILE):
        row: Row = {"year": int(item["year"])}
        for field in (
            "data_center_twh",
            "data_center_index",
            "electricity_sales_twh",
            "electricity_index",
            "summer_capacity_mw",
            "capacity_index",
        ):
            value = _float(item.get(field))
            if value is None:
                raise ValueError(f"U.S. grid history has an invalid {field!r} value")
            row[field] = value
        row["status"] = "historical estimates and reported grid totals"
        row["source"] = "LBNL data-centre estimates; EIA annual electricity and capacity series"
        rows.append(row)
    return sorted(rows, key=lambda row: int(row["year"]))


def _parameter_count_billions(model: str) -> float | None:
    match = re.search(r"(?<!\d)(\d+(?:\.\d+)?)\s*b(?:\b|$)", model.lower())
    return float(match.group(1)) if match else None


def build_local_energy_estimates(usage_rows: list[Row]) -> list[Row]:
    estimates: list[Row] = []
    for row in usage_rows:
        parameters = _parameter_count_billions(str(row["model"]))
        # The 8B reference is used only as a near-size class for 7B–10B local
        # tags. Larger local tags remain visible in workload counts but are
        # not assigned an unsupported energy figure.
        has_reference = parameters is not None and 7 <= parameters <= 10
        output_tokens = int(row["output_tokens"] or 0)
        estimate: dict[str, Any] = {
            "month": row["month"],
            "model": row["model"],
            "output_tokens": output_tokens,
            "energy_status": "benchmark-based estimate" if has_reference else "not estimated: no size-matched published reference",
            "energy_basis": TOKENPOWERBENCH_SOURCE if has_reference else "No compatible published benchmark selected",
            "energy_source_url": TOKENPOWERBENCH_URL if has_reference else "",
            "scope_note": "GPU output-token energy only; prompt processing, CPU, memory, other node loads, and cooling are excluded.",
            "gpu_energy_low_wh": None,
            "gpu_energy_reference_wh": None,
            "gpu_energy_high_wh": None,
        }
        if has_reference:
            for band, joules_per_token in GPU_JOULES_PER_OUTPUT_TOKEN.items():
                estimate[f"gpu_energy_{band}_wh"] = output_tokens * joules_per_token / 3600
        estimates.append(estimate)
    return estimates


def build_investment_rows(software: Series, computers: Series) -> list[Row]:
    names = {
        "software_investment_billion_usd_saar": software,
        "computer_peripherals_investment_billion_usd_saar": computers,
    }
    values = {key: dict(series.observations) for key, series in names.items()}
    dates = sorted(set().union(*(set(series_values) for series_values in values.values())))
    return [
        {"date": f"{date[:7]}-01" if len(date) == 7 else date, **{key: series_values.get(date) for key, series_values in values.items()}}
        for date in dates
    ]


def build_canada_generation_context(root: Path) -> list[Row]:
    source_path = root / "data" / "raw" / "statcan" / "vector-44174609.json"
    if not source_path.exists():
        return []
    import json

    payload = json.loads(source_path.read_text(encoding="utf-8"))
    item = payload[0] if isinstance(payload, list) and payload else payload
    if item.get("status") != "SUCCESS":
        return []
    annual: dict[int, list[float]] = defaultdict(list)
    for point in item.get("object", {}).get("vectorDataPoint", []):
        date = str(point.get("refPer") or "")
        value = _float(point.get("value"))
        if len(date) >= 7 and value is not None and int(point.get("securityLevelCode", 0)) == 0:
            annual[int(date[:4])].append(value)
    return [
        {
            "year": year,
            "generation_twh": sum(values) / 1_000_000,
            "months": len(values),
            "source": "Statistics Canada table 25-10-0015-01, vector 44174609",
            "status": "observed annual total" if len(values) == 12 else "partial year",
        }
        for year, values in sorted(annual.items())
        if len(values) == 12
    ]


def build_technology_flow_outputs(
    root: Path,
    software_investment: Series,
    computer_investment: Series,
) -> dict[str, list[Row]]:
    usage_rows = read_local_usage_aggregates(root)
    return {
        "facility_forecasts": read_facility_forecasts(root),
        "canada_generation": build_canada_generation_context(root),
        "investment": build_investment_rows(software_investment, computer_investment),
        "local_usage": usage_rows,
        "ollama_workload_snapshot": read_ollama_workload_snapshot(root),
        "us_grid_history": read_us_grid_history(root),
        "local_energy": build_local_energy_estimates(usage_rows),
        "benchmarks": [dict(row) for row in BENCHMARK_SCORES],
    }

