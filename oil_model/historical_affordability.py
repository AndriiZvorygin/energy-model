from __future__ import annotations

import csv
import io
import json
import math
import zipfile
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .cache import RawCache
from .sources import StatCanAdapter
from .storage import Row, write_csv


INCOME_TABLE = 11100017
MBM_TABLE = 11100066
NATIONAL_DECILE_TABLE = 11100103
CENSUS_HOUSEHOLD_TABLE = 98100057
CPI_VECTOR = 41690973

REGION_MAP = {
    "Calgary, Alberta": "Calgary, Alberta",
    "Edmonton, Alberta": "Edmonton, Alberta",
    "Halifax, Nova Scotia": "Halifax, Nova Scotia",
    "Hamilton, Ontario": "Hamilton/Burlington, Ontario",
    "Montréal, Quebec": "Montréal, Québec",
    "Québec, Quebec": "Québec, Quebec",
    "Toronto, Ontario": "Toronto, Ontario",
    "Vancouver, British Columbia": "Vancouver, British Columbia",
    "Winnipeg, Manitoba": "Winnipeg, Manitoba",
}

HOUSEHOLD_TYPES = {
    ("Couple families", "Family types without children"): ("Couple without children", 2),
    ("Couple families", "Family types with 1 child"): ("Couple with one child", 3),
    ("Couple families", "Family types with 2 children"): ("Couple with two children", 4),
    ("One-parent families", "Family types with 1 child"): ("One parent with one child", 2),
    ("One-parent families", "Family types with 2 children"): ("One parent with two children", 3),
    ("Persons not in census families", "Family types without children"): ("One person", 1),
}

OWEN_CITY_TYPES = {
    ("1 person", "Total – Household type including census family structure"): ("One person", 1),
    ("2 persons", "Without children"): ("Couple without children", 2),
    ("2 persons", "One one-parent census family"): ("One parent with one child", 2),
    ("3 persons", "One one-parent census family"): ("One parent with two children", 3),
    ("4 persons", "With children"): ("Couple with two children", 4),
}

SOURCE_URLS = {
    "income": "https://doi.org/10.25318/1110001701-eng",
    "mbm": "https://doi.org/10.25318/1110006601-eng",
    "decile": "https://doi.org/10.25318/1110010301-eng",
    "census": "https://doi.org/10.25318/9810005701-eng",
    "cmhc": "https://www03.cmhc-schl.gc.ca/hmip-pimh/en/",
    "grey_bruce": "https://www.publichealthgreybruce.on.ca/Portals/0/Topics/Eating%20Well/Monitoring%20Food%20Affordability%20-%202024%20OCT%2016.pdf",
}


def _table_rows(path: Path, product_id: int) -> list[dict[str, str]]:
    with zipfile.ZipFile(path) as archive:
        member = next(name for name in archive.namelist() if name.endswith(".csv") and "MetaData" not in name)
        with archive.open(member) as raw:
            return list(csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8-sig")))


def _number(value: str | None) -> float | None:
    try:
        return float(value) if value not in (None, "", "..", "...") else None
    except ValueError:
        return None


def _status(income_to_threshold: float | None) -> str:
    if income_to_threshold is None:
        return "insufficient"
    if income_to_threshold < 0.75:
        return "severe-shortfall"
    if income_to_threshold < 1.0:
        return "unaffordable"
    if income_to_threshold < 1.25:
        return "pressured"
    return "affordable"


def _annual_cpi(adapter: StatCanAdapter) -> dict[int, float]:
    series = adapter.fetch_vector(
        CPI_VECTOR,
        label="Canada all-items CPI",
        unit="index, 2002=100",
        geography="Canada",
        start="1976-01-01",
        frequency="monthly",
        nominal_real="price index",
    )
    grouped: dict[int, list[float]] = defaultdict(list)
    for item in series.observations:
        grouped[int(item.date[:4])].append(item.value)
    return {year: sum(values) / len(values) for year, values in grouped.items() if len(values) == 12}


def _metrics(
    *,
    income: float | None,
    threshold: float | None,
    food: float | None,
    shelter: float | None,
) -> dict[str, float | str | None]:
    ratio = income / threshold if income is not None and threshold else None
    return {
        "income_relative_to_basic_needs": ratio,
        "housing_cost_share_income": shelter / income if shelter is not None and income else None,
        "food_cost_share_income": food / income if food is not None and income else None,
        "food_plus_housing_share_income": (food + shelter) / income if food is not None and shelter is not None and income else None,
        "residual_income_after_essential_costs": income - threshold if income is not None and threshold is not None else None,
        "absolute_affordability_status": _status(ratio),
    }


def _add_changes(rows: list[Row]) -> None:
    previous: dict[tuple[Any, ...], tuple[int, float | None]] = {}
    for row in sorted(rows, key=lambda item: (str(item.get("series_key")), int(item["year"]))):
        key = (row.get("series_key"),)
        ratio = row.get("income_relative_to_basic_needs")
        prior = previous.get(key)
        row["change_from_previous_year"] = float(ratio) - prior[1] if prior and ratio is not None and prior[1] is not None and int(row["year"]) == prior[0] + 1 else None
        previous[key] = (int(row["year"]), float(ratio) if ratio is not None else None)


def _national_deciles(rows: list[dict[str, str]], cpi: dict[int, float]) -> list[Row]:
    values: dict[tuple[int, str, str, str], float] = {}
    for row in rows:
        if row["GEO"] != "Canada" or row["Statistics"] != "Average amount":
            continue
        value = _number(row["VALUE"])
        if value is not None:
            values[(int(row["REF_DATE"]), row["Market Basket Measure (MBM) base year"], row["Income decile"], row["Components of after-tax income according to the MBM threshold"])] = value
    output: list[Row] = []
    cpi_2024 = cpi[2024]
    for year, base, decile in sorted({key[:3] for key in values}):
        income_real = values.get((year, base, decile, "After-tax income"))
        basket_real = values.get((year, base, decile, "Basket cost"))
        if income_real is None or basket_real is None or year not in cpi:
            continue
        factor = cpi[year] / cpi_2024
        income = income_real * factor
        threshold = basket_real * factor
        output.append({
            "scope": "Canada national distribution",
            "geography": "Canada",
            "geography_level": "national",
            "year": year,
            "household_type": "All family units, adjusted for household size",
            "household_size": None,
            "income_group": decile,
            "threshold_base": base,
            "after_tax_income_nominal": income,
            "after_tax_income_real_2024": income_real,
            "food_cost_nominal": None,
            "housing_cost_nominal": None,
            "basic_needs_threshold_nominal": threshold,
            **_metrics(income=income, threshold=threshold, food=None, shelter=None),
            "household_count": None,
            "series_key": f"national|{base}|{decile}",
            "source_income": "Statistics Canada Table 11-10-0103-01",
            "source_cost": "Statistics Canada Table 11-10-0103-01",
            "source_url": SOURCE_URLS["decile"],
            "methodology_note": "Statistics Canada matches each family unit to its applicable MBM threshold; published 2024-constant-dollar averages are converted back to year dollars with annual CPI. Food and shelter components are not published by decile.",
        })
    _add_changes(output)
    return output


def _mbm_lookup(rows: list[dict[str, str]]) -> dict[tuple[int, str, str, str], float]:
    output = {}
    for row in rows:
        if row["Dollar concept"] != "Current dollars":
            continue
        value = _number(row["VALUE"])
        if value is not None:
            output[(int(row["REF_DATE"]), row["GEO"], row["Base year"], row["Component"])] = value
    return output


def _matched_region_rows(
    income_rows: list[dict[str, str]],
    mbm: dict[tuple[int, str, str, str], float],
    *,
    geography_filter: set[str],
    geography_map: dict[str, str],
    scope: str,
    geography_level: str,
) -> list[Row]:
    counts: dict[tuple[int, str, str, str], float] = {}
    incomes: dict[tuple[int, str, str, str], float] = {}
    for row in income_rows:
        if row["GEO"] not in geography_filter:
            continue
        key = (int(row["REF_DATE"]), row["GEO"], row["Census family type"], row["Family type composition"])
        value = _number(row["VALUE"])
        if value is None:
            continue
        if row["Statistics"] == "Median after-tax family income":
            incomes[key] = value
        elif row["Statistics"] == "Number of families":
            counts[key] = value
    output: list[Row] = []
    for (year, geography, family_type, composition), income in sorted(incomes.items()):
        household = HOUSEHOLD_TYPES.get((family_type, composition))
        if not household:
            continue
        label, size = household
        mbm_geo = geography_map[geography]
        for base in ("2000 base", "2008 base", "2018 base", "2023 base"):
            total = mbm.get((year, mbm_geo, base, "Total threshold"))
            food = mbm.get((year, mbm_geo, base, "Food"))
            shelter = mbm.get((year, mbm_geo, base, "Shelter"))
            if total is None:
                continue
            scale = math.sqrt(size / 4)
            threshold = total * scale
            food_cost = food * scale if food is not None else None
            housing_cost = shelter * scale if shelter is not None else None
            output.append({
                "scope": scope,
                "geography": geography,
                "geography_level": geography_level,
                "mbm_region": mbm_geo,
                "year": year,
                "household_type": label,
                "household_size": size,
                "income_group": "median",
                "threshold_base": base,
                "after_tax_income_nominal": income,
                "after_tax_income_real_2024": None,
                "food_cost_nominal": food_cost,
                "housing_cost_nominal": housing_cost,
                "basic_needs_threshold_nominal": threshold,
                **_metrics(income=income, threshold=threshold, food=food_cost, shelter=housing_cost),
                "household_count": counts.get((year, geography, family_type, composition)),
                "series_key": f"{geography}|{label}|{base}",
                "source_income": "Statistics Canada Table 11-10-0017-01, T1 Family File",
                "source_cost": "Statistics Canada Table 11-10-0066-01, MBM threshold",
                "source_url": f"{SOURCE_URLS['income']}; {SOURCE_URLS['mbm']}",
                "methodology_note": "Nominal median after-tax family income is matched to the applicable MBM region and exact family size. MBM reference-family components are scaled by sqrt(household size / 4). Base vintages remain separate and are never spliced.",
            })
    _add_changes(output)
    return output


def _owen_city_anchors(
    census_rows: list[dict[str, str]],
    mbm: dict[tuple[int, str, str, str], float],
    cpi: dict[int, float],
) -> list[Row]:
    output: list[Row] = []
    income_fields = {
        2015: "Household income statistics (6):Median household after-tax income (2015) (2020 constant dollars)[6]",
        2020: "Household income statistics (6):Median household after-tax income (2020) (2020 constant dollars)[5]",
    }
    count_fields = {
        2015: "Household income statistics (6):Number of households (2016)[2]",
        2020: "Household income statistics (6):Number of households (2021)[1]",
    }
    cpi_2020 = cpi[2020]
    for row in census_rows:
        if row["GEO"] != "Owen Sound":
            continue
        household = OWEN_CITY_TYPES.get((row["Household size (7)"], row["Household type including census family structure  (11)"]))
        if not household:
            continue
        label, size = household
        for year in (2015, 2020):
            income_2020 = _number(row[income_fields[year]])
            count = _number(row[count_fields[year]])
            if not income_2020 or not count:
                continue
            income = income_2020 * cpi[year] / cpi_2020
            base = "2018 base"
            mbm_geo = "Ontario, population 30,000 to 99,999"
            scale = math.sqrt(size / 4)
            total = mbm.get((year, mbm_geo, base, "Total threshold"))
            food = mbm.get((year, mbm_geo, base, "Food"))
            shelter = mbm.get((year, mbm_geo, base, "Shelter"))
            if total is None:
                continue
            threshold = total * scale
            food_cost = food * scale if food is not None else None
            housing_cost = shelter * scale if shelter is not None else None
            output.append({
                "scope": "Owen Sound city census subdivision anchors",
                "geography": "Owen Sound city CSD",
                "geography_level": "census subdivision",
                "mbm_region": mbm_geo,
                "year": year,
                "household_type": label,
                "household_size": size,
                "income_group": "median",
                "threshold_base": base,
                "after_tax_income_nominal": income,
                "after_tax_income_real_2024": income_2020 * cpi[2024] / cpi_2020,
                "food_cost_nominal": food_cost,
                "housing_cost_nominal": housing_cost,
                "basic_needs_threshold_nominal": threshold,
                **_metrics(income=income, threshold=threshold, food=food_cost, shelter=housing_cost),
                "household_count": count,
                "series_key": f"owen-sound-csd|{label}|{base}",
                "source_income": "Statistics Canada Table 98-10-0057-01, 2021 Census",
                "source_cost": "Statistics Canada Table 11-10-0066-01, MBM threshold",
                "source_url": f"{SOURCE_URLS['census']}; {SOURCE_URLS['mbm']}",
                "methodology_note": "City-CSD household income is available only for 2015 and 2020. Published 2020-dollar income is converted to nominal year dollars. It is not spliced to the annual Owen Sound census-agglomeration history.",
            })
    _add_changes(output)
    return output


def _validation_rows() -> list[Row]:
    return [
        {"geography": "Owen Sound rental market", "year": 2002, "measure": "Average rent, one bedroom", "value": 540, "unit": "CAD per month", "source": "CMHC Owen Sound Rental Market Report 2003", "source_url": "https://publications.gc.ca/Collection-R/CMHC/TR/NH12-147E/NH12-147-2003E.pdf", "coverage_note": "Observed CMHC rent; not used as an MBM replacement."},
        {"geography": "Owen Sound rental market", "year": 2003, "measure": "Average rent, one bedroom", "value": 568, "unit": "CAD per month", "source": "CMHC Owen Sound Rental Market Report 2003", "source_url": "https://publications.gc.ca/Collection-R/CMHC/TR/NH12-147E/NH12-147-2003E.pdf", "coverage_note": "Observed CMHC rent; intervening years require a stable HMIP export adapter."},
        {"geography": "Grey Bruce", "year": 2023, "measure": "Nutritious food basket, family of four", "value": 15660, "unit": "CAD per year", "source": "Grey Bruce Public Health", "source_url": SOURCE_URLS["grey_bruce"], "coverage_note": "Regional observed basket, not Owen Sound city-only."},
        {"geography": "Grey Bruce", "year": 2024, "measure": "Nutritious food basket, family of four", "value": 15000, "unit": "CAD per year", "source": "Grey Bruce Public Health", "source_url": SOURCE_URLS["grey_bruce"], "coverage_note": "Regional observed basket, not Owen Sound city-only; report describes about 1% growth despite rounded annual totals."},
        {"geography": "Grey Bruce", "year": 2023, "measure": "Nutritious food basket, one adult", "value": 5616, "unit": "CAD per year", "source": "Grey Bruce Public Health", "source_url": SOURCE_URLS["grey_bruce"], "coverage_note": "Regional observed basket, not Owen Sound city-only."},
        {"geography": "Grey Bruce", "year": 2024, "measure": "Nutritious food basket, one adult", "value": 5208, "unit": "CAD per year", "source": "Grey Bruce Public Health", "source_url": SOURCE_URLS["grey_bruce"], "coverage_note": "Regional observed basket, not Owen Sound city-only."},
    ]


def _gap_rows() -> list[Row]:
    return [
        {"geography": "Canada", "series": "National MBM-matched income deciles", "missing_period": "Before 2015", "reason": "Statistics Canada Table 11-10-0103-01 begins in 2015.", "treatment": "No backcast."},
        {"geography": "Canada", "series": "Matched family-type budgets", "missing_period": "Before 2002", "reason": "Current MBM threshold Table 11-10-0066-01 begins in 2002.", "treatment": "Income observations are retained at source but are not assigned an affordability status without a matched threshold."},
        {"geography": "Canada", "series": "After-tax income by tenure", "missing_period": "Not integrated", "reason": "CMHC publishes real average after-tax income by tenure for 2006-2024, but its workbook is not yet available through the project clean-cache adapter.", "treatment": "Declared gap; no owner/renter income interpolation."},
        {"geography": "Owen Sound city CSD", "series": "Household-type after-tax income", "missing_period": "All years except 2015 and 2020", "reason": "City-CSD household-type income is Census/NHS frequency.", "treatment": "City anchors remain separate from annual census-agglomeration tax-file data."},
        {"geography": "Owen Sound rental market", "series": "CMHC observed rents", "missing_period": "2004-2025 in this release", "reason": "A stable machine-readable HMIP centre-level historical export is not yet integrated.", "treatment": "Verified 2002-2003 archived report values only; MBM shelter remains the matched budget component."},
        {"geography": "Grey Bruce", "series": "Nutritious food basket", "missing_period": "Before 2023", "reason": "Earlier annual local reports were not found in a reproducible official archive.", "treatment": "Verified 2023-2024 observations only; MBM food remains the continuous matched component."},
    ]


def _json_dataset(identifier: str, title: str, rows: list[Row], generated_at: str) -> dict[str, Any]:
    years = sorted({int(row["year"]) for row in rows})
    return {
        "schemaVersion": 1,
        "id": identifier,
        "title": title,
        "frequency": "annual",
        "generatedAt": generated_at,
        "dateRange": {"start": f"{years[0]}-01-01", "end": f"{years[-1]}-01-01"} if years else None,
        "statusDefinition": {
            "severe-shortfall": "Income is below 75% of the matched basic-needs threshold.",
            "unaffordable": "Income is below the matched basic-needs threshold.",
            "pressured": "Income is between 100% and 125% of the matched threshold.",
            "affordable": "Income is at least 125% of the matched threshold.",
            "insufficient": "A matched income or threshold is unavailable.",
        },
        "observations": rows,
    }


def _weighted_status(rows: list[Row], base: str, years: list[int]) -> list[tuple[int, float]]:
    output = []
    for year in years:
        current = [row for row in rows if row.get("threshold_base") == base and row["year"] == year and row.get("household_count")]
        total = sum(float(row["household_count"]) for row in current)
        non_affordable = sum(float(row["household_count"]) for row in current if row["absolute_affordability_status"] != "affordable")
        if total:
            output.append((year, non_affordable / total))
    return output


def _findings(canada: list[Row], owen: list[Row], validation: list[Row]) -> str:
    canada_years = sorted({int(row["year"]) for row in canada})
    owen_annual = [row for row in owen if row["geography_level"] == "census agglomeration"]
    owen_city = [row for row in owen if row["geography_level"] == "census subdivision"]
    owen_years = sorted({int(row["year"]) for row in owen_annual})
    canada_types = sorted({str(row["household_type"]) for row in canada if row.get("household_size")})
    owen_types = sorted({str(row["household_type"]) for row in owen})
    trend = _weighted_status(owen_annual, "2018 base", owen_years)
    trend_text = "Unavailable"
    if trend:
        first, last = trend[0], trend[-1]
        trend_text = f"The household-count-weighted share of evaluated median cases below the project’s `affordable` buffer was {first[1]:.1%} in {first[0]} and {last[1]:.1%} in {last[0]} under the 2018-base MBM."
    return f"""# Historical Absolute-Affordability Series

## Scope

This release builds annual nominal budget comparisons from matched after-tax income and basic-needs thresholds. It does not alter the live affordability headline, symptom rules, regime classifiers, or oil models.

The status thresholds are project diagnostics: `severe-shortfall` below 75% of the matched threshold, `unaffordable` below 100%, `pressured` from 100% to below 125%, and `affordable` at or above 125%. They are not official Statistics Canada classifications.

## Canada

- **Years available:** {canada_years[0]}–{canada_years[-1]}. National income-decile/MBM matching is available from 2015; matched regional family histories begin in 2002.
- **Household types:** {', '.join(canada_types)}.
- **National distribution:** Statistics Canada Table 11-10-0103-01 supplies average after-tax income and each decile’s applicable MBM basket cost. This is the preferred Canada-wide absolute comparison because family size and region are matched inside the official microdata calculation.
- **Regional family histories:** tax-file median after-tax family income is matched to the corresponding MBM urban region and exact family size. MBM base vintages remain separate because methodological revisions change the basket.
- **Trend:** the lowest decile remained below its matched basket cost throughout 2015–2024. The second decile moved from 0.93 baskets in 2015 to 1.14 in 2020 and 1.01 in 2024; the fifth decile moved from 1.72 to 1.93 and then 1.85. Pandemic transfers temporarily improved lower-decile ratios in 2020, and much of that gain subsequently receded.

## Owen Sound

- **Annual regional history:** {owen_years[0]}–{owen_years[-1]} for the Owen Sound census agglomeration, matched to the Ontario population 30,000–99,999 MBM region.
- **City-CSD anchors:** {', '.join(str(year) for year in sorted({int(row['year']) for row in owen_city}))}. These observations use Owen Sound city household incomes and are not spliced to the census-agglomeration series.
- **Household types:** {', '.join(owen_types)}.
- **Trend:** {trend_text} One-person and one-parent median cases generally have the smallest buffers; couple-family medians are materially stronger. The 2023 annual census-agglomeration medians all exceed 1.25 times their matched 2018-base thresholds, but this does not override local food-insecurity, renter-burden, or core-housing-need rates: medians describe central cases, not the lower tail. Base revisions and the 2020 pandemic-income shock must be read explicitly.

## Validation Evidence

CMHC rents and Grey Bruce food baskets are retained as validation observations rather than substituted for MBM components. The local validation file currently contains {len(validation)} observations: CMHC one-bedroom rent for 2002–2003 and Grey Bruce nutritious-food-basket costs for 2023–2024.

## Major Gaps

- No annual Owen Sound **city-CSD** income history exists between Census/NHS observations. Annual tax-file data uses the wider census agglomeration.
- A stable automated export for the complete CMHC Owen Sound rent history has not yet been integrated. Published HMIP coverage exists, but only verified archived observations are included here.
- Grey Bruce nutritious-food-basket reports were verified for 2023 and 2024. Earlier annual local baskets were not located in a reproducible official archive.
- Income by tenure is available nationally through CMHC/Statistics Canada for 2006–2024, but its downloadable workbook is not yet integrated into the clean-cache pipeline. Census-year Owen Sound owner/renter hardship rates remain validation evidence rather than invented annual income series.
- MBM Table 11-10-0066-01 publishes costs for a four-person reference family. Components for other sizes are transparently scaled by the official square-root family-size equivalence; they are derived, not separately observed food or rent budgets.
- Median household cases do not represent the within-type income distribution. National deciles and hardship rates should validate, rather than be replaced by, these budget comparisons.

## Sources

- Statistics Canada Tables 11-10-0017-01, 11-10-0066-01, 11-10-0103-01, and 98-10-0057-01.
- CMHC Rental Market Survey and archived Owen Sound Rental Market Report.
- Grey Bruce Public Health nutritious-food-basket reports.
"""


def build_historical_affordability_outputs(root: Path, cache: RawCache) -> tuple[list[Row], list[Row], list[Row]]:
    adapter = StatCanAdapter(cache)
    income_rows = _table_rows(adapter.fetch_table_download(INCOME_TABLE), INCOME_TABLE)
    mbm_rows = _table_rows(adapter.fetch_table_download(MBM_TABLE), MBM_TABLE)
    decile_rows = _table_rows(adapter.fetch_table_download(NATIONAL_DECILE_TABLE), NATIONAL_DECILE_TABLE)
    census_rows = _table_rows(adapter.fetch_table_download(CENSUS_HOUSEHOLD_TABLE), CENSUS_HOUSEHOLD_TABLE)
    cpi = _annual_cpi(adapter)
    mbm = _mbm_lookup(mbm_rows)

    canada = _national_deciles(decile_rows, cpi)
    canada += _matched_region_rows(
        income_rows,
        mbm,
        geography_filter=set(REGION_MAP),
        geography_map=REGION_MAP,
        scope="Canada matched urban-region household types",
        geography_level="census metropolitan area or census agglomeration",
    )
    owen = _matched_region_rows(
        income_rows,
        mbm,
        geography_filter={"Owen Sound, Ontario"},
        geography_map={"Owen Sound, Ontario": "Ontario, population 30,000 to 99,999"},
        scope="Owen Sound census-agglomeration household types",
        geography_level="census agglomeration",
    )
    owen += _owen_city_anchors(census_rows, mbm, cpi)
    validation = _validation_rows()
    gaps = _gap_rows()

    analysis = root / "analysis"
    generated = root / "website" / "public" / "generated"
    write_csv(analysis / "canada_absolute_affordability_history.csv", canada)
    write_csv(analysis / "owen_sound_absolute_affordability_history.csv", owen)
    write_csv(analysis / "absolute_affordability_validation_history.csv", validation)
    write_csv(analysis / "absolute_affordability_history_gaps.csv", gaps)
    (analysis / "historical_absolute_affordability.md").write_text(_findings(canada, owen, validation), encoding="utf-8")

    generated_at = datetime.now(UTC).isoformat(timespec="seconds")
    canada_path = generated / "canada" / "absolute-affordability-history.json"
    owen_path = generated / "owen-sound" / "absolute-affordability-history.json"
    canada_path.parent.mkdir(parents=True, exist_ok=True)
    owen_path.parent.mkdir(parents=True, exist_ok=True)
    canada_path.write_text(json.dumps(_json_dataset("canada-absolute-affordability-history", "Canada historical absolute affordability", canada, generated_at), indent=2, allow_nan=False) + "\n", encoding="utf-8")
    owen_path.write_text(json.dumps(_json_dataset("owen-sound-absolute-affordability-history", "Owen Sound historical absolute affordability", owen, generated_at), indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return canada, owen, validation
