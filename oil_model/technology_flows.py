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
TECHNOLOGY_SOURCE_DIR = Path("data/seed/technology_sources")
CAPABILITY_ARCHIVE_FILE = TECHNOLOGY_SOURCE_DIR / "ai-human-benchmark-data-2026-09-19.csv"
COMPUTE_SCENARIO_FILE = TECHNOLOGY_SOURCE_DIR / "model-production-datacenter-scenarios-2026-10-13.csv"
TRAINING_HARDWARE_FILE = TECHNOLOGY_SOURCE_DIR / "large-model-training-hardware-2026-10-13.csv"
SITE_SCREEN_FILE = Path("data/seed/technology_flow_canadian_site_screen.csv")

# Explicit planning sensitivity, in CAD per MWh. The upper endpoint is anchored
# to Hydro-Québec's proposed C$0.13/kWh rate for new data centres over 5 MW;
# the lower endpoint is an analyst-selected low-cost case, not a utility quote.
ELECTRICITY_PRICE_CAD_PER_MWH = {"low": 50.0, "high": 130.0}
PLANNING_WATER_WUE_L_PER_KWH = 0.3

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


def _archive_rows(root: Path, relative_path: Path) -> list[dict[str, str]]:
    return _read_csv(root / relative_path)


def build_capability_scorecard(root: Path) -> list[dict[str, Any]]:
    """Select dated, condition-labelled results from the presentation archive."""
    archive = _archive_rows(root, CAPABILITY_ARCHIVE_FILE)

    def matching(benchmark: str, version: str, models: set[str] | None = None) -> list[dict[str, str]]:
        return [
            row for row in archive
            if row.get("benchmark") == benchmark
            and row.get("benchmark_version") == version
            and (models is None or row.get("model") in models)
        ]

    def row_payload(row: dict[str, str], *, value: float | None = None, display: str | None = None) -> dict[str, Any]:
        raw_score = _float(row.get("score"))
        score = value if value is not None else raw_score
        is_human_reference = "human" in row.get("model", "").lower()
        return {
            "model": row.get("model", ""),
            "score": score,
            "displayScore": display or (f"{raw_score:g}{'%' if 'percent' in row.get('score_unit', '') else ''}" if raw_score is not None else "not reported"),
            "scoreUnit": row.get("score_unit", ""),
            "evaluationDate": row.get("evaluation_date", "") or "not stated",
            "configuration": "Human reference" if is_human_reference else "; ".join(part for part in [
                f"tools {row['tools_allowed']}" if row.get("tools_allowed") else "",
                f"{row['reasoning_effort']} reasoning" if row.get("reasoning_effort") else "",
                row.get("scaffold", ""),
            ] if part),
            "source": row.get("source_title") or row.get("source_type") or "Source record",
            "sourceUrl": row.get("source_url", ""),
            "confidence": row.get("confidence", ""),
            "notes": row.get("notes", ""),
        }

    families: list[dict[str, Any]] = []

    gpqa_models = {"GPT-6 Astra", "Claude Opus 5", "Gemini 3.8 Flash", "DeepSeek-V4-Pro", "Kimi K3", "Qwen3.8-27B", "Qwen3.5-9B"}
    gpqa_rows = matching("GPQA Diamond", "current-model-card-comparison", gpqa_models)
    gpqa_rows.extend(matching("GPQA Diamond", "gpt-oss-120b-model-card", {"gpt-oss-120b"})[-1:])
    gpqa_rows.extend(matching("GPQA Diamond", "original-diamond-198-table2", {"Human domain experts", "Human skilled non-experts"}))
    gpqa_rows.sort(key=lambda row: _float(row.get("score")) or 0, reverse=True)
    families.append({
        "id": "gpqa-diamond", "category": "Graduate science reasoning", "benchmark": "GPQA Diamond",
        "metricLabel": "Accuracy", "scaleMaximum": 100,
        "scope": "Graduate-level science questions. The human expert reference is 81.3% on the selection-filtered Diamond subset; it is not the 65% expert figure from the full GPQA set.",
        "conditions": "Provider/model-card results; reasoning and tool conditions differ by row. Scores are not a common local-hardware evaluation.",
        "rows": [row_payload(row) for row in gpqa_rows],
    })

    hle_rows = [
        row for row in archive
        if row.get("benchmark") == "Humanity's Last Exam"
        and row.get("source_url") == "https://labs.scale.com/leaderboard/humanitys_last_exam"
        and row.get("tools_allowed") == "false"
    ]
    hle_rows.sort(key=lambda row: _float(row.get("score")) or 0, reverse=True)
    families.append({
        "id": "humanity-last-exam", "category": "Expert knowledge breadth", "benchmark": "Humanity's Last Exam (public set)",
        "metricLabel": "Accuracy", "scaleMaximum": 100,
        "scope": "Expert-authored questions across many academic fields. There is no single published human accuracy baseline for direct comparison.",
        "conditions": "Scale leaderboard snapshot, no tools. Tool-enabled model-card results are kept out of this comparison.",
        "rows": [row_payload(row) for row in hle_rows],
    })

    arc_rows = matching("ARC-AGI-2", "v2_Semi_Private")
    arc_rows = [row for row in arc_rows if row.get("model") in {"GPT-6 Astra", "GPT-5.6 Sol", "Claude Opus 5", "Gemini 3.1 Pro"}]
    human_arc = matching("ARC-AGI-2", "v2-human-calibration-paper", {"ARC human task-level aggregate"})
    arc_rows.extend(human_arc)
    arc_rows.sort(key=lambda row: _float(row.get("score")) or 0, reverse=True)
    families.append({
        "id": "arc-agi-2", "category": "Novel visual abstraction", "benchmark": "ARC-AGI-2",
        "metricLabel": "Task success", "scaleMaximum": 100,
        "scope": "The benchmark paper reports 75% human task-level success; a different human metric, test-pair success, is 66%.",
        "conditions": "Official semi-private evaluations; tool access is enabled. Human and model results use related but not identical evaluation protocols.",
        "rows": [row_payload(row) for row in arc_rows],
    })

    gdp_rows = matching("GDPval", "gold-220-paper-2025")
    gdp_rows.sort(key=lambda row: _float(row.get("score")) or 0, reverse=True)
    families.append({
        "id": "gdpval", "category": "Professional deliverables", "benchmark": "GDPval",
        "metricLabel": "Expert-rated comparisons", "scaleMaximum": 100,
        "scope": "220 work tasks across 44 occupations, compared with deliverables from experienced professionals. The reported 47.6% for Claude Opus 4.1 is win-or-tie; most other values here are win-only.",
        "conditions": "Paired expert grading with tool-enabled systems. A benchmark result is not a measure of deployment productivity or net labour displacement.",
        "rows": [row_payload(row) for row in gdp_rows],
    })

    deepswe_models = {"GPT-6 Astra", "Claude Opus 5", "Gemini 3.8 Flash", "Kimi K3", "Qwen3.8-27B"}
    deepswe_rows = matching("DeepSWE v1.1", "official-2026-comparison", deepswe_models)
    deepswe_rows.extend(matching("DeepSWE v1.1", "Kimi-K3-card", {"Kimi K3"}))
    deepswe_rows.extend(matching("DeepSWE v1.1", "Qwen3.8-card", {"Qwen3.8-27B"}))
    deepswe_rows.sort(key=lambda row: _float(row.get("score")) or 0, reverse=True)
    families.append({
        "id": "deepswe", "category": "Software engineering agents", "benchmark": "DeepSWE v1.1",
        "metricLabel": "Issue resolution", "scaleMaximum": 100,
        "scope": "Coding-agent results on software-engineering tasks; these evaluate a model plus an agent harness, tools and retries, not a single answer from a base model.",
        "conditions": "Provider-reported results with different harness and reasoning settings. Use the source links before making cross-provider comparisons.",
        "rows": [row_payload(row) for row in deepswe_rows],
    })

    mle_rows = matching("MLE-Bench", "official-leaderboard-2026-04-24")
    mle_rows.sort(key=lambda row: _float(row.get("score")) or 0, reverse=True)
    families.append({
        "id": "mlebench", "category": "Machine-learning engineering agents", "benchmark": "MLE-Bench",
        "metricLabel": "Mean medal score across ML competitions", "scaleMaximum": 100,
        "scope": "Submitted agent systems are evaluated on machine-learning engineering competitions. The score summarizes medal performance; it is not a pass rate or proof of independent research discovery.",
        "conditions": "The leaderboard evaluates full agents with tools and scaffolding. The model field names the submitted system, not only its underlying language model.",
        "rows": [row_payload(row) for row in mle_rows],
    })

    metr_names = {
        "claude_3_5_sonnet_20240620_inspect": "Claude 3.5 Sonnet · Jun 2024",
        "claude_4_1_opus_inspect": "Claude 4.1 Opus · Aug 2025",
        "gpt_5_3_codex": "GPT-5.3 Codex · Feb 2026",
        "claude_mythos_preview_early_inspect": "Claude Mythos Preview · Apr 2026",
    }
    metr_rows = [row for row in archive if row.get("benchmark") == "METR time horizon" and row.get("model") in metr_names]
    metr_payload = []
    for row in metr_rows:
        minutes = _float(row.get("score"))
        if minutes is None:
            continue
        payload = row_payload(row, value=minutes / 60, display=f"{minutes / 60:.1f} human-task hours (p50)")
        payload["model"] = metr_names[row["model"]]
        payload["scoreUnit"] = "human-task-hours-p50"
        metr_payload.append(payload)
    metr_payload.sort(key=lambda row: row.get("score") or 0, reverse=True)
    families.append({
        "id": "metr-horizon", "category": "Long-horizon technical agents", "benchmark": "METR task horizon 1.1",
        "metricLabel": "Human task duration at 50% agent success", "scaleMaximum": 24,
        "scope": "The p50 horizon is the estimated duration of tasks the tested agent system completes 50% of the time, measured against human task-time estimates.",
        "conditions": "Agent scaffold results on a suite concentrated in software, machine learning and cybersecurity. This is not standalone-model runtime or a general intelligence measure.",
        "rows": metr_payload,
    })
    return families


def build_compute_scenarios(root: Path) -> list[dict[str, Any]]:
    rows = _archive_rows(root, COMPUTE_SCENARIO_FILE)
    scenarios: list[dict[str, Any]] = []

    def make_scenario(row: dict[str, str], *, label: str | None = None, extrapolated: bool = False) -> dict[str, Any]:
        power_low_kw = _float(row.get("facility_power_low_kw")) or 0
        power_high_kw = _float(row.get("facility_power_high_kw")) or 0
        days = _float(row.get("campaign_days")) or 30
        monthly_mwh_low = power_low_kw * days * 24 / 1000
        monthly_mwh_high = power_high_kw * days * 24 / 1000
        annual_mwh_low = power_low_kw * 8760 / 1000
        annual_mwh_high = power_high_kw * 8760 / 1000
        water_per_day_low = power_low_kw * 24 * PLANNING_WATER_WUE_L_PER_KWH / 1000
        water_per_day_high = power_high_kw * 24 * PLANNING_WATER_WUE_L_PER_KWH / 1000
        capital_low = _float(row.get("capital_cad_low")) or 0
        capital_high = _float(row.get("capital_cad_high")) or 0
        return {
            "scenario": label or row.get("scenario", "Compute scenario"),
            "accelerators": int(float(row.get("accelerators") or 0)),
            "gpuMemoryGb": int(float(row.get("accelerator_memory_gb") or 0)),
            "usableStorageTb": int(float(row.get("usable_storage_tb") or 0)),
            "facilityPowerLowKw": power_low_kw,
            "facilityPowerHighKw": power_high_kw,
            "campaignDays": days,
            "monthlyEnergyLowMwh": monthly_mwh_low,
            "monthlyEnergyHighMwh": monthly_mwh_high,
            "monthlyElectricityCostLowCad": monthly_mwh_low * ELECTRICITY_PRICE_CAD_PER_MWH["low"],
            "monthlyElectricityCostHighCad": monthly_mwh_high * ELECTRICITY_PRICE_CAD_PER_MWH["high"],
            "annualEnergyLowMwh": annual_mwh_low,
            "annualEnergyHighMwh": annual_mwh_high,
            "annualElectricityCostLowCad": annual_mwh_low * ELECTRICITY_PRICE_CAD_PER_MWH["low"],
            "annualElectricityCostHighCad": annual_mwh_high * ELECTRICITY_PRICE_CAD_PER_MWH["high"],
            "waterPerDayLowM3": water_per_day_low,
            "waterPerDayHighM3": water_per_day_high,
            "waterPerMonthLowM3": monthly_mwh_low * 1000 * PLANNING_WATER_WUE_L_PER_KWH / 1000,
            "waterPerMonthHighM3": monthly_mwh_high * 1000 * PLANNING_WATER_WUE_L_PER_KWH / 1000,
            "capitalLowCad": capital_low,
            "capitalHighCad": capital_high,
            "workload": row.get("quarterly_workload", ""),
            "basis": row.get("calculation_basis", ""),
            "capitalExtrapolated": extrapolated,
        }

    for row in rows:
        scenarios.append(make_scenario(row))

    # Scale the largest archived accelerator-tier envelope to a 100 MW campus.
    # This is an intentionally broad planning extrapolation, not an EPC quote.
    frontier = next((row for row in rows if row.get("scenario") == "Frontier pretraining campaign"), None)
    reference = next((row for row in rows if row.get("scenario") == "National teacher lab"), None)
    if frontier and reference:
        low_kw_per_gpu = (_float(reference.get("facility_power_low_kw")) or 0) / int(float(reference.get("accelerators") or 1))
        high_kw_per_gpu = (_float(reference.get("facility_power_high_kw")) or 0) / int(float(reference.get("accelerators") or 1))
        campus_min_gpus = math.floor(100_000 / high_kw_per_gpu)
        campus_max_gpus = math.floor(100_000 / low_kw_per_gpu)
        frontier_gpus = int(float(frontier.get("accelerators") or 1))
        per_gpu_low = (_float(frontier.get("capital_cad_low")) or 0) / frontier_gpus
        per_gpu_high = (_float(frontier.get("capital_cad_high")) or 0) / frontier_gpus
        campus_row = {
            "scenario": "Frontier research campus · 100 MW",
            "accelerators": campus_min_gpus,
            "acceleratorsHigh": campus_max_gpus,
            "accelerator_memory_gb": frontier.get("accelerator_memory_gb", 80),
            "usable_storage_tb": frontier.get("usable_storage_tb", 2000),
            "facility_power_low_kw": 100_000,
            "facility_power_high_kw": 100_000,
            "campaign_days": 30,
            "quarterly_workload": "Large training, evaluation and inference campus; compute-equivalent extrapolated from H100-class planning tier",
            "calculation_basis": "Accelerator count uses 1.3–2.2 kW facility load per accelerator; capital scales the archived 2,048-accelerator cost envelope linearly",
            "capital_cad_low": per_gpu_low * campus_min_gpus,
            "capital_cad_high": per_gpu_high * campus_max_gpus,
        }
        campus = make_scenario(campus_row, extrapolated=True)
        campus["accelerators"] = campus_min_gpus
        campus["acceleratorsHigh"] = campus_max_gpus
        scenarios.append(campus)
    return scenarios


def build_training_run_anchor(root: Path) -> dict[str, Any] | None:
    """Translate one reported frontier run into cluster time and planning costs."""
    model = next((row for row in _archive_rows(root, TRAINING_HARDWARE_FILE) if row.get("model") == "DeepSeek-V3"), None)
    campaign = next((row for row in _archive_rows(root, COMPUTE_SCENARIO_FILE) if row.get("scenario") == "Frontier pretraining campaign"), None)
    if model is None or campaign is None:
        return None
    gpu_hours_millions = _float(model.get("reported_gpu_hours_m"))
    accelerator_count = int(float(campaign.get("accelerators") or 0))
    facility_low_kw = _float(campaign.get("facility_power_low_kw"))
    facility_high_kw = _float(campaign.get("facility_power_high_kw"))
    if gpu_hours_millions is None or accelerator_count <= 0 or facility_low_kw is None or facility_high_kw is None:
        return None
    reported_gpu_hours = gpu_hours_millions * 1_000_000
    cluster_hours = reported_gpu_hours / accelerator_count
    run_energy_low_mwh = facility_low_kw * cluster_hours / 1000
    run_energy_high_mwh = facility_high_kw * cluster_hours / 1000
    return {
        "model": "DeepSeek-V3",
        "reportedAcceleratorHours": reported_gpu_hours,
        "reportedAccelerator": "H800 GPU-hours",
        "equivalentAccelerators": accelerator_count,
        "equivalentClusterDays": cluster_hours / 24,
        "facilityPowerLowKw": facility_low_kw,
        "facilityPowerHighKw": facility_high_kw,
        "energyLowMwh": run_energy_low_mwh,
        "energyHighMwh": run_energy_high_mwh,
        "electricityCostLowCad": run_energy_low_mwh * ELECTRICITY_PRICE_CAD_PER_MWH["low"],
        "electricityCostHighCad": run_energy_high_mwh * ELECTRICITY_PRICE_CAD_PER_MWH["high"],
        "waterLowM3": run_energy_low_mwh * PLANNING_WATER_WUE_L_PER_KWH,
        "waterHighM3": run_energy_high_mwh * PLANNING_WATER_WUE_L_PER_KWH,
        "source": model.get("source", ""),
        "note": "Official report gives H800 GPU-hours. Facility power, water and energy-cost ranges transfer the archived H100-class planning proxy and C$50–130/MWh sensitivity; they are not a reconstruction of DeepSeek's actual electricity use or bill.",
    }


def read_canadian_site_screen(root: Path) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in _archive_rows(root, SITE_SCREEN_FILE):
        water_lpd = _float(row.get("municipal_water_daily_litres"))
        output.append({
            "province": row.get("province", ""),
            "city": row.get("city", ""),
            "hydroFact": row.get("hydro_fact", ""),
            "hydroScaleComparison": row.get("hydro_scale_comparison", ""),
            "hydroSource": row.get("hydro_source", ""),
            "hydroSourceUrl": row.get("hydro_source_url", ""),
            "gridAndPolicyFact": row.get("grid_and_policy_fact", ""),
            "gridAndPolicySource": row.get("grid_and_policy_source", ""),
            "gridAndPolicyUrl": row.get("grid_and_policy_url", ""),
            "municipalWaterDailyLitres": water_lpd,
            "municipalWaterFact": row.get("municipal_water_fact", ""),
            "waterSource": row.get("water_source", ""),
            "waterSourceUrl": row.get("water_source_url", ""),
            "assessment": row.get("screen_assessment", ""),
            "openQuestion": row.get("open_question", ""),
        })
    return output


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
        "capability_scorecard": build_capability_scorecard(root),
        "compute_scenarios": build_compute_scenarios(root),
        "training_run_anchor": build_training_run_anchor(root),
        "canadian_site_screen": read_canadian_site_screen(root),
    }

