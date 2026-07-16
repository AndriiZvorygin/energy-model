from __future__ import annotations

import json
import math
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .cache import RawCache
from .canada_classification import build_canadian_classification_outputs
from .sources import BankOfCanadaAdapter, SourceObservation, SourceSeries, StatCanAdapter
from .storage import Row, write_csv


CANADIAN_SCOPE = "Canadian energy-economic conditions with global oil-market and global-liquidity inputs."

STATCAN_SPECS = [
    # Physical oil and electricity.
    (107757045, "canada-crude-production-growth", "Canadian crude oil production growth", "Barrels", "Canada", "Physical energy conditions", "yoy", True, "domestic", "StatCan 25-10-0063-01", "not seasonally adjusted", "physical quantity", "higher production expands domestic supply capacity but does not automatically improve household affordability"),
    (107757089, "canada-crude-exports-growth", "Canadian crude oil export growth", "Barrels", "Canada", "Physical energy conditions", "yoy", True, "domestic", "StatCan 25-10-0063-01", "not seasonally adjusted", "physical quantity", "exports describe external demand and market access"),
    (107757069, "canada-crude-imports-growth", "Canadian crude oil import growth", "Barrels", "Canada", "Physical energy conditions", "yoy", True, "domestic", "StatCan 25-10-0063-01", "not seasonally adjusted", "physical quantity", "imports reflect regional refinery needs as well as domestic supply"),
    (107757077, "canada-refinery-input-growth", "Crude input to Canadian refineries growth", "Barrels", "Canada", "Physical energy conditions", "yoy", True, "domestic", "StatCan 25-10-0063-01", "not seasonally adjusted", "physical quantity", "refinery inputs proxy domestic crude-processing activity"),
    (107757109, "canada-crude-inventory", "Canadian crude closing inventory", "million barrels", "Canada", "Physical energy conditions", "scale_million", True, "domestic", "StatCan 25-10-0063-01", "not seasonally adjusted", "physical quantity", "inventory levels require seasonal and demand context"),
    (44174609, "canada-electricity-generation-growth", "Canadian electricity generation growth", "percent", "Canada", "Physical energy conditions", "yoy", False, "domestic", "StatCan 25-10-0015-01", "not seasonally adjusted", "physical quantity", "electricity generation is a broad throughput indicator affected by weather and exports"),
    (107757711, "alberta-crude-production-growth", "Alberta crude oil production growth", "percent", "Alberta", "Physical energy conditions", "yoy", False, "domestic", "StatCan 25-10-0063-01", "not seasonally adjusted", "physical quantity", "Alberta provides producing-region context rather than a national household-affordability signal"),
    # Consumer prices.
    (41690973, "canada-cpi-yoy", "Canada all-items CPI growth", "percent", "Canada", "Energy affordability and finance", "yoy", True, "domestic", "StatCan 18-10-0004-01", "not seasonally adjusted", "price index", "broad consumer inflation context"),
    (41691239, "canada-energy-cpi-yoy", "Canada energy CPI growth", "percent", "Canada", "Energy affordability and finance", "yoy", True, "domestic", "StatCan 18-10-0004-01", "not seasonally adjusted", "price index", "higher energy inflation is generally an affordability headwind"),
    (41691136, "canada-gasoline-cpi-yoy", "Canada gasoline CPI growth", "percent", "Canada", "Energy affordability and finance", "yoy", True, "domestic", "StatCan 18-10-0004-01", "not seasonally adjusted", "price index", "gasoline inflation directly affects vehicle-dependent households"),
    (41691066, "canada-fuel-oil-cpi-yoy", "Canada fuel oil CPI growth", "percent", "Canada", "Energy affordability and finance", "yoy", False, "domestic", "StatCan 18-10-0004-01", "not seasonally adjusted", "price index", "fuel-oil exposure is regionally concentrated"),
    (41691065, "canada-natural-gas-cpi-yoy", "Canada natural gas CPI growth", "percent", "Canada", "Energy affordability and finance", "yoy", False, "domestic", "StatCan 18-10-0004-01", "not seasonally adjusted", "price index", "regulated rates and weather complicate interpretation"),
    (41691063, "canada-electricity-cpi-yoy", "Canada electricity CPI growth", "percent", "Canada", "Energy affordability and finance", "yoy", False, "domestic", "StatCan 18-10-0004-01", "not seasonally adjusted", "price index", "provincial regulation and generation mix matter"),
    (41691050, "canada-shelter-cpi-yoy", "Canada shelter CPI growth", "percent", "Canada", "Energy affordability and finance", "yoy", True, "domestic", "StatCan 18-10-0004-01", "not seasonally adjusted", "price index", "shelter costs condition household command over other spending"),
    (41690974, "canada-food-cpi-yoy", "Canada food CPI growth", "percent", "Canada", "Energy affordability and finance", "yoy", False, "domestic", "StatCan 18-10-0004-01", "not seasonally adjusted", "price index", "food prices are an essential-cost context indicator"),
    # Monthly real GDP by industry.
    (65201210, "canada-real-gdp-growth", "Canada monthly real GDP growth", "percent", "Canada", "Production and output", "yoy", True, "domestic", "StatCan 36-10-0434-01", "seasonally adjusted at annual rates", "real chained 2017 dollars", "monthly GDP by industry is the primary high-frequency output measure"),
    (65201263, "canada-manufacturing-gdp-growth", "Canada manufacturing real GDP growth", "percent", "Canada", "Production and output", "yoy", True, "domestic", "StatCan 36-10-0434-01", "seasonally adjusted at annual rates", "real chained 2017 dollars", "manufacturing output provides material production context"),
    (65201236, "canada-mining-oil-gas-gdp-growth", "Canada mining and oil-and-gas real GDP growth", "percent", "Canada", "Production and output", "yoy", True, "domestic", "StatCan 36-10-0434-01", "seasonally adjusted at annual rates", "real chained 2017 dollars", "resource-sector output can diverge from household conditions"),
    (65201368, "canada-retail-gdp-growth", "Canada retail-trade real GDP growth", "percent", "Canada", "Production and output", "yoy", False, "domestic", "StatCan 36-10-0434-01", "seasonally adjusted at annual rates", "real chained 2017 dollars", "retail output helps trace household demand"),
    # National labour.
    (2062815, "canada-unemployment-rate", "Canada unemployment rate", "percent", "Canada", "Labour and households", "raw", True, "domestic", "StatCan 14-10-0287-01", "seasonally adjusted", "rate", "higher unemployment is generally stressful"),
    (2062817, "canada-employment-rate", "Canada employment rate", "percent", "Canada", "Labour and households", "raw", True, "domestic", "StatCan 14-10-0287-01", "seasonally adjusted", "rate", "the employment rate adjusts better than job counts for population growth"),
    (2062816, "canada-participation-rate", "Canada participation rate", "percent", "Canada", "Labour and households", "raw", True, "domestic", "StatCan 14-10-0287-01", "seasonally adjusted", "rate", "participation changes can qualify unemployment movements"),
    (2062952, "canada-prime-age-employment-rate", "Canada prime-age employment rate", "percent", "Canada", "Labour and households", "raw", True, "domestic", "StatCan 14-10-0287-01", "seasonally adjusted", "rate", "prime-age employment reduces retirement and youth-enrolment composition effects"),
    # Ontario labour and CPI context.
    (41691919, "ontario-cpi-yoy", "Ontario all-items CPI growth", "percent", "Ontario", "Energy affordability and finance", "yoy", False, "domestic", "StatCan 18-10-0004-01", "not seasonally adjusted", "price index", "Ontario consumer-price context"),
    (41692051, "ontario-energy-cpi-yoy", "Ontario energy CPI growth", "percent", "Ontario", "Energy affordability and finance", "yoy", False, "domestic", "StatCan 18-10-0004-01", "not seasonally adjusted", "price index", "Ontario energy affordability context"),
    (41691994, "ontario-gasoline-cpi-yoy", "Ontario gasoline CPI growth", "percent", "Ontario", "Energy affordability and finance", "yoy", False, "domestic", "StatCan 18-10-0004-01", "not seasonally adjusted", "price index", "Ontario motor-fuel affordability context"),
    (41691952, "ontario-shelter-cpi-yoy", "Ontario shelter CPI growth", "percent", "Ontario", "Energy affordability and finance", "yoy", False, "domestic", "StatCan 18-10-0004-01", "not seasonally adjusted", "price index", "Ontario housing-cost context"),
    (2063949, "ontario-unemployment-rate", "Ontario unemployment rate", "percent", "Ontario", "Labour and households", "raw", False, "domestic", "StatCan 14-10-0287-01", "seasonally adjusted", "rate", "higher unemployment is generally stressful"),
    (2063951, "ontario-employment-rate", "Ontario employment rate", "percent", "Ontario", "Labour and households", "raw", False, "domestic", "StatCan 14-10-0287-01", "seasonally adjusted", "rate", "employment relative to working-age population"),
    (2063950, "ontario-participation-rate", "Ontario participation rate", "percent", "Ontario", "Labour and households", "raw", False, "domestic", "StatCan 14-10-0287-01", "seasonally adjusted", "rate", "qualifies changes in unemployment"),
    (2064086, "ontario-prime-age-employment-rate", "Ontario prime-age employment rate", "percent", "Ontario", "Labour and households", "raw", False, "domestic", "StatCan 14-10-0287-01", "seasonally adjusted", "rate", "Ontario prime-age labour utilization"),
]

BANK_SPECS = [
    ("V39079", "canada-policy-rate", "Bank of Canada policy rate", "percent", "daily", "not seasonally adjusted", "rate", "average", True, "policy rate conditions financing costs"),
    ("FXUSDCAD", "cad-per-usd", "Canadian dollars per U.S. dollar", "CAD per USD", "daily", "not seasonally adjusted", "exchange rate", "average", True, "a weaker Canadian dollar raises the domestic-currency cost of benchmark oil"),
    ("V41552801", "canada-m2pp-yoy", "Canada M2++ growth", "percent", "monthly", "seasonally adjusted", "nominal money stock", None, False, "domestic money growth is context, distinct from global GM2"),
]


def _quantile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * q
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def _percentile(values: list[float], current: float) -> float | None:
    if not values:
        return None
    return 100 * (sum(value < current for value in values) + 0.5 * sum(value == current for value in values)) / len(values)


def real_oil_price_cad(wti_usd: float, cad_per_usd: float, cpi_index: float) -> float:
    if cpi_index <= 0:
        raise ValueError("Canadian CPI must be positive for real-oil deflation")
    return 100 * wti_usd * cad_per_usd / cpi_index


def population_aligned_employment_rate(employment: float, population: float) -> float:
    if population <= 0:
        raise ValueError("Working-age population must be positive")
    return 100 * employment / population


def _transform(series: SourceSeries, method: str) -> list[SourceObservation]:
    if method == "raw":
        return series.observations
    if method == "scale_million":
        return [SourceObservation(item.date, item.value / 1_000_000, item.release_date) for item in series.observations]
    if method == "yoy":
        lookup = {item.date[:7]: item for item in series.observations}
        output = []
        for item in series.observations:
            year, month = map(int, item.date[:7].split("-"))
            prior = lookup.get(f"{year - 1:04d}-{month:02d}")
            if prior and prior.value:
                output.append(SourceObservation(item.date, 100 * (item.value / prior.value - 1), item.release_date))
        return output
    raise ValueError(f"Unknown Canadian transformation: {method}")


def _payload(spec: dict[str, Any], observations: list[SourceObservation], generated_at: str) -> dict[str, Any]:
    values = [item.value for item in observations if math.isfinite(item.value)]
    if not values:
        raise ValueError(f"Canadian indicator {spec['id']} contains no values")
    latest = observations[-1]
    previous = observations[-2] if len(observations) > 1 else None
    lookup = {item.date[:7]: item.value for item in observations}
    year, month = map(int, latest.date[:7].split("-"))
    prior_3_index = year * 12 + month - 1 - 3
    prior_3 = lookup.get(f"{prior_3_index // 12:04d}-{prior_3_index % 12 + 1:02d}")
    prior_12 = lookup.get(f"{year - 1:04d}-{month:02d}")
    median = _quantile(values, 0.5)
    percentile = _percentile(values, latest.value)
    interpretation = spec["interpretation"]
    evidence_context = {
        "Global oil and liquidity inputs": (["Canadian physical balances", "Canadian affordability indicators"], ["Domestic currency and policy conditions"]),
        "Physical energy conditions": (["Production, trade, refinery inputs and inventories", "Benchmark oil prices"], ["Weak domestic demand or strong export demand"]),
        "Energy affordability and finance": (["Real household income and debt service", "Provincial energy CPI"], ["Regulated-price or exchange-rate effects"]),
        "Production and output": (["Manufacturing and resource GDP", "Employment and hours"], ["Industry-specific disruptions"]),
        "Labour and households": (["Employment rate, participation and job composition", "Monthly real GDP"], ["Population growth and labour-force composition"]),
    }
    default_confirming, default_conflicting = evidence_context.get(spec["layer"], ([], []))
    return {
        "schemaVersion": 1,
        "id": spec["id"],
        "field": spec["id"].replace("-", "_"),
        "label": spec["label"],
        "description": interpretation,
        "unit": spec["unit"],
        "frequency": spec["frequency"],
        "status": "derived" if spec["transformation"] != "raw" else "measured",
        "layer": spec["layer"],
        "geography": spec["geography"],
        "geographyLevel": "global" if spec["geography"] == "Global" else "national" if spec["geography"] in {"Canada", "United States"} else "provincial",
        "inputType": spec["input_type"],
        "domesticOrExternal": spec["input_type"],
        "directlyComparableAcrossCountries": spec.get("comparable", False),
        "comparisonLimitations": spec.get("comparison_limitations", "Definitions, currencies, industrial structure and release timing differ across countries."),
        "core": bool(spec.get("core")),
        "interpretationDirection": spec.get("direction", "context-dependent"),
        "interpretationLabel": "Direction unclear",
        "interpretation": interpretation,
        "source": spec["source"],
        "sourceUrl": spec["source_url"],
        "sourceIdentifier": spec["source_id"],
        "seasonalAdjustment": spec["seasonal_adjustment"],
        "nominalOrReal": spec["nominal_real"],
        "startDate": observations[0].date,
        "endDate": latest.date,
        "latest": {
            "date": latest.date, "sourceDate": latest.release_date or latest.date, "value": latest.value,
            "previousValue": previous.value if previous else None,
            "oneYearChange": latest.value - prior_12 if prior_12 is not None else None,
            "threeMonthChange": latest.value - prior_3 if prior_3 is not None else None,
            "fourQuarterChange": latest.value - prior_12 if prior_12 is not None else None,
            "historicalPercentile": percentile,
            "percentileSince2000": _percentile([item.value for item in observations if item.date >= "2000-01-01"], latest.value),
            "distanceFromMedian": latest.value - median if median is not None else None,
            "momentum": "rising" if previous and latest.value > previous.value else "falling" if previous and latest.value < previous.value else "steady",
        },
        "referenceRanges": {"historicalMedian": median, "p10": _quantile(values, .10), "p25": _quantile(values, .25), "p75": _quantile(values, .75), "p90": _quantile(values, .90), "minimum": min(values), "maximum": max(values)},
        "observations": [{"date": item.date, "value": item.value, "sourceDate": item.release_date or item.date} for item in observations],
        "confirmingIndicators": spec.get("confirming", default_confirming),
        "conflictingIndicators": spec.get("conflicting", default_conflicting),
        "evidenceChecks": [],
        "confidenceLevel": spec.get("confidence", "medium"),
        "evidenceLabel": spec.get("evidence_label", "Contextual indicator"),
        "calculation": {"formula": spec["formula"], "explanation": spec["formula"], "example": f"Latest observation: {latest.value:.2f} {spec['unit']} at {latest.date[:7]}."},
        "limitations": [spec["revision_notes"], spec.get("comparison_limitations", "Cross-country definitions differ.")],
        "generatedAt": generated_at,
    }


def _series_spec(series: SourceSeries, row: tuple[Any, ...]) -> dict[str, Any]:
    vector, indicator_id, label, unit, geography, layer, transformation, core, input_type, table, seasonal, nominal_real, interpretation = row
    product_id = table.split()[1].replace("-", "")
    return {"id": indicator_id, "label": label, "unit": unit, "geography": geography, "layer": layer, "transformation": transformation, "core": core, "input_type": input_type, "source": f"Statistics Canada, {table}", "source_url": f"https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid={product_id}", "source_id": f"v{vector}", "frequency": series.frequency, "seasonal_adjustment": seasonal, "nominal_real": nominal_real, "interpretation": interpretation, "revision_notes": series.revision_notes, "formula": "Year-over-year percent change" if transformation == "yoy" else "Published value divided by 1,000,000" if transformation == "scale_million" else "Published source value"}


def _derived_payloads(global_rows: list[Row], series_by_id: dict[str, SourceSeries], generated_at: str) -> list[dict[str, Any]]:
    payloads = []
    for field, indicator_id, label, layer, unit in [("GM2_YoY", "global-gm2-yoy", "Global M2 growth", "Global oil and liquidity inputs", "percent"), ("WTI_YoY", "global-wti-yoy", "WTI price growth", "Global oil and liquidity inputs", "percent"), ("Brent_YoY", "global-brent-yoy", "Brent price growth", "Global oil and liquidity inputs", "percent")]:
        observations = [SourceObservation(f"{row['month']}-01", float(row[field]), f"{row['month']}-01") for row in global_rows if row.get(field) is not None]
        spec = {"id": indicator_id, "label": label, "unit": unit, "geography": "Global", "layer": layer, "transformation": "raw", "core": True, "input_type": "external", "source": "Existing locked oil-model dataset", "source_url": "https://github.com/AndriiZvorygin/energy-model", "source_id": field, "frequency": "monthly", "seasonal_adjustment": "source-defined", "nominal_real": "growth rate", "interpretation": "External global input retained from the locked oil system.", "revision_notes": "Uses the existing project output unchanged.", "formula": "Existing project year-over-year series"}
        payloads.append(_payload(spec, observations, generated_at))

    wti = {str(row["month"]): float(row["WTI"]) for row in global_rows if row.get("WTI") is not None}
    cpi = {item.date[:7]: item.value for item in series_by_id["canada-cpi-yoy-raw"].observations}
    fx = {item.date[:7]: item.value for item in series_by_id["cad-per-usd-raw"].observations}
    real_level = [SourceObservation(f"{month}-01", real_oil_price_cad(price, fx[month], cpi[month])) for month, price in sorted(wti.items()) if month in fx and month in cpi]
    spec = {"id": "canada-real-wti-cad-yoy", "label": "Real WTI price in Canadian dollars growth", "unit": "percent", "geography": "Canada", "layer": "Energy affordability and finance", "transformation": "yoy", "core": True, "input_type": "external", "source": "FRED WTI, Bank of Canada FXUSDCAD, Statistics Canada CPI", "source_url": "https://www.bankofcanada.ca/valet-api-how-to/", "source_id": "DCOILWTICO / FXUSDCAD / v41690973", "frequency": "monthly", "seasonal_adjustment": "mixed source definitions", "nominal_real": "real CPI-deflated price", "interpretation": "Domestic-currency real oil captures both benchmark oil and CAD movements.", "revision_notes": "CPI and benchmark histories may be revised; daily prices are monthly averaged.", "formula": "100 * YoY[(WTI_USD * CAD_per_USD) / Canada_CPI]"}
    payloads.append(_payload(spec, _transform(SourceSeries("derived", "", "", "Canada", "monthly", "", "", "derived", "", generated_at, "", real_level), "yoy"), generated_at))
    return payloads


def build_canadian_outputs(root: Path, global_rows: list[Row], us_system_rows: list[Row], cache: RawCache) -> tuple[list[Row], list[dict[str, Any]]]:
    generated_at = datetime.now(UTC).isoformat(timespec="seconds")
    statcan = StatCanAdapter(cache)
    bank = BankOfCanadaAdapter(cache)
    payloads: list[dict[str, Any]] = []
    raw_series: dict[str, SourceSeries] = {}
    for row in STATCAN_SPECS:
        vector, indicator_id, label, unit, geography, _, _, _, _, _, seasonal, nominal_real, _ = row
        source_unit = "2002=100" if "cpi" in indicator_id else "Dollars, millions" if "gdp" in indicator_id else "published unit"
        series = statcan.fetch_vector(vector, label=label, unit=source_unit, geography=geography, seasonal_adjustment=seasonal, nominal_real=nominal_real)
        raw_series[indicator_id] = series
        payloads.append(_payload(_series_spec(series, row), _transform(series, row[6]), generated_at))
    raw_series["canada-cpi-yoy-raw"] = raw_series["canada-cpi-yoy"]

    for series_id, indicator_id, label, unit, frequency, seasonal, nominal_real, aggregation, core, interpretation in BANK_SPECS:
        series = bank.fetch_series(series_id, label=label, unit="millions of CAD" if "m2" in indicator_id else unit, frequency=frequency, seasonal_adjustment=seasonal, nominal_real=nominal_real, monthly_aggregation=aggregation)
        raw_series[f"{indicator_id}-raw"] = series
        transformation = "yoy" if indicator_id.endswith("yoy") else "raw"
        spec = {"id": indicator_id, "label": label, "unit": unit, "geography": "Canada", "layer": "Energy affordability and finance", "transformation": transformation, "core": core, "input_type": "domestic", "source": "Bank of Canada Valet API", "source_url": series.source_url, "source_id": series_id, "frequency": "monthly" if aggregation else frequency, "seasonal_adjustment": seasonal, "nominal_real": nominal_real, "interpretation": interpretation, "revision_notes": series.revision_notes, "formula": "Year-over-year percent change" if transformation == "yoy" else f"Monthly {aggregation or 'published'} value"}
        payloads.append(_payload(spec, _transform(series, transformation), generated_at))

    dsr = statcan.fetch_vector(1001696841, label="Canada household debt-service ratio", unit="percent", geography="Canada", frequency="quarterly", seasonal_adjustment="seasonally adjusted at annual rates", nominal_real="ratio")
    dsr_spec = {"id": "canada-household-debt-service-ratio", "label": "Canada household debt-service ratio", "unit": "percent", "geography": "Canada", "layer": "Labour and households", "transformation": "raw", "core": True, "input_type": "domestic", "source": "Statistics Canada, table 11-10-0065-01", "source_url": "https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=1110006501", "source_id": "v1001696841", "frequency": "quarterly", "seasonal_adjustment": "seasonally adjusted at annual rates", "nominal_real": "ratio", "interpretation": "A larger share of household income devoted to debt service reduces financial room.", "revision_notes": dsr.revision_notes, "formula": "Published household debt-service ratio"}
    payloads.append(_payload(dsr_spec, dsr.observations, generated_at))
    payloads.extend(_derived_payloads(global_rows, raw_series, generated_at))

    # Derived labour composition and population-aligned employment growth.
    for geography, employment_id, full_id, part_id, population_id, prefix, core in [
        ("Canada", 2062811, 2062812, 2062813, 2062809, "canada", True),
        ("Ontario", 2063945, 2063946, 2063947, 2063943, "ontario", False),
    ]:
        employment = statcan.fetch_vector(employment_id, label=f"{geography} employment", unit="thousands", geography=geography, seasonal_adjustment="seasonally adjusted", nominal_real="persons")
        full = statcan.fetch_vector(full_id, label=f"{geography} full-time employment", unit="thousands", geography=geography, seasonal_adjustment="seasonally adjusted", nominal_real="persons")
        part = statcan.fetch_vector(part_id, label=f"{geography} part-time employment", unit="thousands", geography=geography, seasonal_adjustment="seasonally adjusted", nominal_real="persons")
        population = statcan.fetch_vector(population_id, label=f"{geography} working-age population", unit="thousands", geography=geography, seasonal_adjustment="seasonally adjusted", nominal_real="persons")
        emp = {item.date[:7]: item for item in employment.observations}; ft = {item.date[:7]: item for item in full.observations}; pop = {item.date[:7]: item for item in population.observations}
        share = [SourceObservation(f"{month}-01", 100 * ft[month].value / item.value, item.release_date) for month, item in emp.items() if month in ft and item.value]
        ratio = [SourceObservation(f"{month}-01", population_aligned_employment_rate(item.value, pop[month].value), item.release_date) for month, item in emp.items() if month in pop and pop[month].value]
        ratio_growth = _transform(SourceSeries("derived", "", "percent", geography, "monthly", "seasonally adjusted", "rate", "derived", "", generated_at, "", ratio), "yoy")
        for indicator_id, label, values, interpretation in [
            (f"{prefix}-full-time-employment-share", f"{geography} full-time employment share", share, "Full-time work as a share of total employment adds job-composition context."),
            (f"{prefix}-employment-relative-population-growth", f"{geography} employment relative to working-age population growth", ratio_growth, "Growth in employment relative to the working-age population accounts for rapid population change."),
        ]:
            spec = {"id": indicator_id, "label": label, "unit": "percent", "geography": geography, "layer": "Labour and households", "transformation": "raw", "core": core, "input_type": "domestic", "source": "Statistics Canada, table 14-10-0287-01", "source_url": "https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=1410028701", "source_id": f"derived from v{employment_id}, v{full_id if 'full-time' in indicator_id else population_id}", "frequency": "monthly", "seasonal_adjustment": "seasonally adjusted", "nominal_real": "rate", "interpretation": interpretation, "revision_notes": employment.revision_notes, "formula": "100 * full-time employment / total employment" if "full-time" in indicator_id else "YoY percent change in (employment / working-age population)"}
            payloads.append(_payload(spec, values, generated_at))
        for indicator_id, label, series in [(f"{prefix}-full-time-employment", f"{geography} full-time employment", full), (f"{prefix}-part-time-employment", f"{geography} part-time employment", part)]:
            spec = {"id": indicator_id, "label": label, "unit": "thousands of persons", "geography": geography, "layer": "Labour and households", "transformation": "raw", "core": False, "input_type": "domestic", "source": "Statistics Canada, table 14-10-0287-01", "source_url": "https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=1410028701", "source_id": f"v{full_id if 'full-time' in indicator_id else part_id}", "frequency": "monthly", "seasonal_adjustment": "seasonally adjusted", "nominal_real": "persons", "interpretation": "Employment level; interpret relative to population growth and the complementary work-status series.", "revision_notes": series.revision_notes, "formula": "Published seasonally adjusted employment level"}
            payloads.append(_payload(spec, series.observations, generated_at))

    payloads.sort(key=lambda item: (item["geography"] != "Global", item["geography"], item["layer"], item["label"]))
    out = root / "website" / "public" / "generated" / "canada"
    indicator_dir = out / "indicators"
    indicator_dir.mkdir(parents=True, exist_ok=True)
    for payload in payloads:
        (indicator_dir / f"{payload['id']}.json").write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    layers = ["Global oil and liquidity inputs", "Physical energy conditions", "Energy affordability and finance", "Production and output", "Labour and households"]
    canada_items = [item for item in payloads if item["geography"] in {"Global", "Canada"}]
    current_state = {
        "schemaVersion": 1, "scope": CANADIAN_SCOPE, "generatedAt": generated_at,
        "status": "Canadian diagnostic status: provisional transparent classification available.",
        "latestObservationDate": max(item["latest"]["date"] for item in canada_items),
        "layers": [{"id": layer.lower().replace(" ", "-"), "label": layer, "indicatorIds": [item["id"] for item in canada_items if item["layer"] == layer]} for layer in layers],
        "notes": ["The Canadian classifier is provisional and uses latest-vintage revised data.", "Ontario and Alberta contributions remain separate; they are not averaged into a neutral national score."],
    }
    manifest = {
        "schemaVersion": 1, "scope": CANADIAN_SCOPE, "generatedAt": generated_at, "defaultGeography": "Canada",
        "geographies": ["Global", "Canada", "Ontario", "Alberta", "United States"],
        "indicators": [{"id": item["id"], "file": f"indicators/{item['id']}.json", "label": item["label"], "geography": item["geography"], "layer": item["layer"], "core": item["core"], "latestDate": item["latest"]["date"]} for item in payloads],
        "currentStateFile": "current-state.json", "classificationImplemented": True,
        "classificationFiles": {
            "current": "current-classification.json",
            "symptoms": "symptom-evaluations.json",
            "regimes": "regime-scores.json",
        },
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (out / "current-state.json").write_text(json.dumps(current_state, indent=2) + "\n", encoding="utf-8")
    long_rows: list[Row] = []
    for item in payloads:
        for observation in item["observations"]:
            long_rows.append({"indicator_id": item["id"], "indicator": item["label"], "geography": item["geography"], "layer": item["layer"], "date": observation["date"], "source_date": observation["sourceDate"], "value": observation["value"], "unit": item["unit"], "source_id": item["sourceIdentifier"]})
    write_csv(root / "data" / "processed" / "canadian_core.csv", long_rows)
    comparison = _comparison_foundation(payloads, us_system_rows, generated_at)
    (out / "canada-us-comparison.json").write_text(json.dumps(comparison, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    catalogue = _catalogue(payloads)
    write_csv(root / "analysis" / "canadian_indicator_catalogue.csv", catalogue)
    (root / "analysis" / "canadian_data_audit.md").write_text(_audit_markdown(payloads), encoding="utf-8")
    build_canadian_classification_outputs(root, payloads, generated_at)
    return catalogue, payloads


def _comparison_foundation(payloads: list[dict[str, Any]], us_rows: list[Row], generated_at: str) -> dict[str, Any]:
    by_id = {item["id"]: item for item in payloads}
    pairs = [
        ("unemployment", "Canada unemployment rate", "canada-unemployment-rate", "U.S. unemployment rate", "unemployment_rate", "percent", "Both are headline unemployment rates, but labour-force definitions and population dynamics differ."),
        ("energy-cpi", "Canada energy CPI growth", "canada-energy-cpi-yoy", "U.S. energy CPI growth", "energy_CPI_YoY", "percent", "Consumption baskets, regulated utility prices and energy systems differ."),
        ("real-gdp", "Canada monthly real GDP growth", "canada-real-gdp-growth", "U.S. real GDP growth", "Real_GDP_growth", "percent", "Canada uses monthly GDP by industry while the U.S. series is quarterly expenditure-side GDP."),
        ("policy-rate", "Bank of Canada policy rate", "canada-policy-rate", "U.S. federal funds rate", "fed_funds_rate", "percent", "Policy frameworks are comparable in purpose but not identical in implementation."),
    ]
    datasets = []
    for pair_id, ca_label, ca_id, us_label, us_field, unit, limitation in pairs:
        ca = {row["date"]: row["value"] for row in by_id[ca_id]["observations"]}
        us = {f"{row['month']}-01": row.get(us_field) for row in us_rows if row.get(us_field) is not None}
        dates = sorted(set(ca) | set(us))
        datasets.append({
            "id": pair_id, "title": f"{ca_label} and {us_label}", "unit": unit,
            "definitionDifference": limitation,
            "canadaPercentile": by_id[ca_id]["latest"]["historicalPercentile"],
            "observations": [{"date": date, "canada": ca.get(date), "unitedStates": us.get(date)} for date in dates],
            "sources": [by_id[ca_id]["source"], "Existing U.S. system-response dataset"],
        })
    return {"schemaVersion": 1, "generatedAt": generated_at, "scope": CANADIAN_SCOPE, "note": "Country percentiles are calculated against each country's own history and are not treated as a shared distribution.", "datasets": datasets}


def _catalogue(payloads: list[dict[str, Any]]) -> list[Row]:
    rows: list[Row] = []
    for item in payloads:
        rows.append({
            "indicator_name": item["label"], "exact_definition": item["calculation"]["formula"], "source_agency": item["source"].split(",")[0], "source_table_or_api_series": item["sourceIdentifier"],
            "geography": item["geography"], "frequency": item["frequency"], "unit": item["unit"], "seasonal_adjustment": item["seasonalAdjustment"], "nominal_or_real": item["nominalOrReal"],
            "start_date": item["startDate"], "latest_date": item["endDate"], "revision_behaviour": item["limitations"][0], "real_time_vintage_availability": "release timestamps retained; full vintage histories not yet stored",
            "us_equivalent": _us_equivalent(item["id"]), "suitability_current_state": "implemented", "suitability_regime_classification": "candidate; calibration pending", "known_limitations": item["comparisonLimitations"],
            "domestic_or_external": item["domesticOrExternal"], "national_or_provincial": item["geographyLevel"], "directly_comparable_across_countries": "yes" if item["directlyComparableAcrossCountries"] else "no", "comparison_limitations": item["comparisonLimitations"],
        })
    for name, source, limitation in [
        ("Western Canadian Select price and WCS-WTI differential", "CER / CCEI candidate", "No stable authoritative public historical API was confirmed for this release."),
        ("Canadian refined-product consumption or sales", "Statistics Canada / CCEI candidate", "Product definitions and table continuity require further audit."),
        ("Canadian refinery utilization", "CER weekly crude-run data", "Weekly runs are available, but a stable utilization denominator and revision-safe API require implementation."),
        ("Canadian natural gas production", "Statistics Canada / CER candidate", "Reliable table identified conceptually; vector selection and unit harmonization remain."),
        ("Household energy-expenditure share", "Statistics Canada household expenditure accounts", "No direct high-frequency household share; an experimental proxy must publish all components."),
        ("Real disposable income per person and household saving rate", "Statistics Canada quarterly household accounts", "Quarterly source and population alignment require a later release-vintage pass."),
        ("Consumer insolvencies", "Office of the Superintendent of Bankruptcy", "Current downloadable historical interface was not integrated; archived StatCan tables are unsuitable for current state."),
        ("Average hourly wages and actual hours worked", "Statistics Canada LFS", "Authoritative series exist, but compact vector extraction and seasonal treatment remain for the next pass."),
        ("Ontario manufacturing and goods-producing employment", "Statistics Canada 14-10-0355-02", "Authoritative monthly series identified; vectors not yet added."),
        ("Ontario real GDP", "Statistics Canada provincial economic accounts", "Quarterly or annual native-frequency series requires a separate release-vintage pass; no monthly interpolation is permitted."),
        ("Canadian oil consumption per person", "Statistics Canada / CCEI candidate", "Requires a consistent petroleum-consumption series and population alignment."),
    ]:
        rows.append({"indicator_name": name, "exact_definition": "proposed", "source_agency": source, "source_table_or_api_series": "pending", "geography": "Canada or Ontario", "frequency": "pending", "unit": "pending", "seasonal_adjustment": "pending", "nominal_or_real": "pending", "start_date": "unavailable", "latest_date": "unavailable", "revision_behaviour": "not audited", "real_time_vintage_availability": "not implemented", "us_equivalent": "varies", "suitability_current_state": "proposed - data gap", "suitability_regime_classification": "not ready", "known_limitations": limitation, "domestic_or_external": "domestic", "national_or_provincial": "pending", "directly_comparable_across_countries": "no", "comparison_limitations": limitation})
    return rows


def _us_equivalent(indicator_id: str) -> str:
    for needle, equivalent in [("unemployment", "UNRATE"), ("employment-rate", "prime-age employment / employment structure"), ("cpi", "CPIAUCSL or CPIENGSL"), ("gdp", "GDPC1 / industry output"), ("policy", "FEDFUNDS"), ("debt-service", "TDSP"), ("crude-production", "PAPRPUS"), ("inventory", "EIA crude stocks")]:
        if needle in indicator_id:
            return equivalent
    return "no exact U.S. equivalent in the current core"


def _audit_markdown(payloads: list[dict[str, Any]]) -> str:
    core = [item for item in payloads if item["core"] and item["geography"] in {"Global", "Canada"}]
    start = min(item["startDate"] for item in core)
    end = max(item["endDate"] for item in core)
    return f"""# Canadian Data Audit

## Scope

{CANADIAN_SCOPE}

This release adds a **provisional transparent Canadian classifier** without modifying the existing U.S. classifier or locked GM2 lag-5 oil model. Household stress remains insufficiently evaluated, and Ontario and Alberta contributions are preserved separately.

## Implemented Core

The Canadian namespace contains **{len(core)} core global/Canadian indicators** plus Ontario and Alberta context. Core date coverage spans `{start}` to `{end}`, but every card retains its own observation and source-release date.

Primary sources are Statistics Canada WDS vectors and the Bank of Canada Valet API. Physical crude balances distinguish production, exports, imports, refinery inputs and inventories. Monthly real GDP by industry is the main high-frequency output measure. Labour uses rates and employment relative to population rather than unemployment alone.

## Revision And Vintage Limitations

Statistics Canada release timestamps are retained per observation, but full historical vintages are not yet archived. Current results are therefore latest-vintage histories with source-date provenance, not a real-time backtest. Monthly GDP, labour, CPI, physical balances and quarterly debt-service data can be revised on different schedules. Bank of Canada observation dates are retained; Valet does not provide a publication-vintage archive in these responses.

## Geography And Comparability

Canada is the domestic default. Ontario inherits global oil/liquidity inputs but uses provincial CPI and labour histories. Alberta appears only as a producing-region comparison. No values from Canada, Ontario, Alberta and the United States are mixed into a regime score. Similar Canadian and U.S. values can have different meanings because energy production, trade, currencies, housing systems, population growth and industrial structure differ.

## Missing Or Proposed

The catalogue identifies unresolved WCS pricing, refined-product consumption, refinery utilization, natural-gas production, household energy expenditure, income/saving, insolvency, wage/hour and Ontario industry-employment series. They remain proposed rather than being filled with commercial data, copied U.S. measures or interpolated provincial observations.

## Provisional Classification

The versioned rules use global GM2 and benchmark oil; Canadian crude production, exports, imports, refinery inputs and inventories; real CAD oil and energy CPI; monthly total/manufacturing/resource GDP; employment, unemployment, prime-age employment and full-time share; and debt service. The next calibration step is real-time-vintage validation and the later addition of wages, hours, household income, expenditure burden and insolvency evidence.
"""
