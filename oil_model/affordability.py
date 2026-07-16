from __future__ import annotations

import json
import math
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np

from .adapters import FredAdapter
from .cache import RawCache
from .sources import BisPropertyPriceAdapter, FaoFoodPriceAdapter, SourceObservation, SourceSeries, StatCanAdapter
from .storage import Row, write_csv
from .website_data import _dataset, _series


STATCAN_CPI_SPECS = [
    (41690973, "canada-all-items-cpi", "Canada all-items CPI", "Canada", "All-items"),
    (41690974, "food-cpi", "Canada food CPI", "Canada", "Food"),
    (41690975, "grocery-cpi", "Canada food purchased from stores CPI", "Canada", "Food purchased from stores"),
    (41691046, "restaurant-food-cpi", "Canada food purchased from restaurants CPI", "Canada", "Food purchased from restaurants"),
    (41690976, "meat-cpi", "Canada meat CPI", "Canada", "Meat"),
    (41690992, "dairy-eggs-cpi", "Canada dairy products and eggs CPI", "Canada", "Dairy products and eggs"),
    (41691000, "bakery-cereals-cpi", "Canada bakery and cereal products CPI", "Canada", "Bakery and cereal products (excluding baby food)"),
    (41691011, "fresh-fruit-cpi", "Canada fresh fruit CPI", "Canada", "Fresh fruit"),
    (41691021, "fresh-vegetables-cpi", "Canada fresh vegetables CPI", "Canada", "Fresh vegetables"),
    (41691050, "shelter-cpi", "Canada shelter CPI", "Canada", "Shelter"),
    (41691052, "rent-cpi", "Canada rent CPI", "Canada", "Rent"),
    (41691056, "mortgage-interest-cost", "Canada mortgage interest cost index", "Canada", "Mortgage interest cost"),
    (41691057, "homeowners-replacement-cost", "Canada homeowners' replacement cost index", "Canada", "Homeowners' replacement cost"),
    (41691058, "property-taxes-cpi", "Canada property taxes and special charges CPI", "Canada", "Property taxes and other special charges"),
    (41691919, "ontario-all-items-cpi", "Ontario all-items CPI", "Ontario", "All-items"),
    (41691920, "ontario-food-cpi", "Ontario food CPI", "Ontario", "Food"),
    (41691921, "ontario-grocery-cpi", "Ontario food purchased from stores CPI", "Ontario", "Food purchased from stores"),
    (41691951, "ontario-restaurant-food-cpi", "Ontario food purchased from restaurants CPI", "Ontario", "Food purchased from restaurants"),
    (41691922, "ontario-meat-cpi", "Ontario meat CPI", "Ontario", "Meat"),
    (41691931, "ontario-dairy-eggs-cpi", "Ontario dairy products and eggs CPI", "Ontario", "Dairy products and eggs"),
    (41691937, "ontario-bakery-cereals-cpi", "Ontario bakery and cereal products CPI", "Ontario", "Bakery and cereal products (excluding baby food)"),
    (41691941, "ontario-fresh-fruit-cpi", "Ontario fresh fruit CPI", "Ontario", "Fresh fruit"),
    (41691944, "ontario-fresh-vegetables-cpi", "Ontario fresh vegetables CPI", "Ontario", "Fresh vegetables"),
    (41691952, "ontario-shelter-cpi", "Ontario shelter CPI", "Ontario", "Shelter"),
    (41691954, "ontario-rent-cpi", "Ontario rent CPI", "Ontario", "Rent"),
    (41691956, "ontario-homeowners-replacement-cost", "Ontario homeowners' replacement cost index", "Ontario", "Homeowners' replacement cost"),
    (41691957, "ontario-property-taxes-cpi", "Ontario property taxes and special charges CPI", "Ontario", "Property taxes and other special charges"),
]

STATCAN_NHPI_SPECS = [
    (111955442, "new-housing-price-index", "Canada new housing price index", "Canada", "Total (house and land)"),
    (111955443, "new-housing-house-component", "Canada new housing house component", "Canada", "House only"),
    (111955444, "new-housing-land-component", "Canada new housing land component", "Canada", "Land only"),
    (111955490, "ontario-new-housing-price-index", "Ontario new housing price index", "Ontario", "Total (house and land)"),
    (111955491, "ontario-new-housing-house-component", "Ontario new housing house component", "Ontario", "House only"),
    (111955492, "ontario-new-housing-land-component", "Ontario new housing land component", "Ontario", "Land only"),
    (111955541, "alberta-new-housing-price-index", "Alberta new housing price index", "Alberta", "Total (house and land)"),
    (111955542, "alberta-new-housing-house-component", "Alberta new housing house component", "Alberta", "House only"),
    (111955543, "alberta-new-housing-land-component", "Alberta new housing land component", "Alberta", "Land only"),
    (111955499, "toronto-new-housing-price-index", "Toronto new housing price index", "Toronto", "Total (house and land)"),
    (111955493, "ottawa-new-housing-price-index", "Ottawa-Gatineau Ontario-part new housing price index", "Ottawa-Gatineau, Ontario part", "Total (house and land)"),
    (111955544, "calgary-new-housing-price-index", "Calgary new housing price index", "Calgary", "Total (house and land)"),
    (111955547, "edmonton-new-housing-price-index", "Edmonton new housing price index", "Edmonton", "Total (house and land)"),
]

US_FRED_SPECS = [
    ("CPIAUCSL", "us-all-items-cpi", "U.S. all-items CPI", "index", "seasonally adjusted", "price index"),
    ("CPIUFDNS", "food-cpi", "U.S. food CPI", "index", "not seasonally adjusted", "price index"),
    ("CUSR0000SAF11", "food-at-home-cpi", "U.S. food at home CPI", "index", "seasonally adjusted", "price index"),
    ("CUSR0000SEFV", "food-away-from-home-cpi", "U.S. food away from home CPI", "index", "seasonally adjusted", "price index"),
    ("CUSR0000SAF111", "cereals-bakery-cpi", "U.S. cereals and bakery products CPI", "index", "seasonally adjusted", "price index"),
    ("CUSR0000SAF112", "meat-poultry-fish-eggs-cpi", "U.S. meats, poultry, fish and eggs CPI", "index", "seasonally adjusted", "price index"),
    ("CUSR0000SEFJ", "dairy-cpi", "U.S. dairy and related products CPI", "index", "seasonally adjusted", "price index"),
    ("CUSR0000SAF113", "fruit-vegetables-cpi", "U.S. fruits and vegetables CPI", "index", "seasonally adjusted", "price index"),
    ("CUSR0000SAH1", "shelter-cpi", "U.S. shelter CPI", "index", "seasonally adjusted", "price index"),
    ("CUUR0000SEHA", "rent-cpi", "U.S. rent of primary residence CPI", "index", "not seasonally adjusted", "price index"),
    ("CUSR0000SEHC", "owners-equivalent-rent-cpi", "U.S. owners' equivalent rent CPI", "index", "seasonally adjusted", "price index"),
    ("HPIPONM226S", "fhfa-house-price-index", "FHFA U.S. purchase-only house price index", "index", "seasonally adjusted", "nominal property price"),
    ("CES0500000003", "average-hourly-earnings", "U.S. average hourly earnings", "USD per hour", "seasonally adjusted", "nominal wage"),
    ("A229RX0Q048SBEA", "real-disposable-income-per-capita", "U.S. real disposable personal income per capita", "chained USD per person", "seasonally adjusted annual rate", "real income"),
]

STATCAN_PURCHASING_POWER_SPECS = [
    (62305981, "household-disposable-income", "Household disposable income", "Canada", "quarterly", "millions CAD at annual rates", "seasonally adjusted at annual rates", "nominal annualized flow", "1961-01-01", "36-10-0112-01"),
    (62305982, "household-consumption-expenditure", "Household final consumption expenditure", "Canada", "quarterly", "millions CAD at annual rates", "seasonally adjusted at annual rates", "nominal annualized flow", "1961-01-01", "36-10-0112-01"),
    (62305984, "household-saving-rate", "Household saving rate", "Canada", "quarterly", "percent", "seasonally adjusted at annual rates", "rate", "1961-01-01", "36-10-0112-01"),
    (1, "canada-population-quarterly", "Canada quarterly population estimate", "Canada", "quarterly", "persons", "not seasonally adjusted", "population", "1971-01-01", "17-10-0009-01"),
    (2132579, "average-hourly-wages", "Canada average hourly wage rate", "Canada", "monthly", "CAD per hour", "not seasonally adjusted", "nominal wage", "1997-01-01", "14-10-0063-01"),
    (2132654, "goods-producing-hourly-wages", "Canada goods-producing hourly wage rate", "Canada", "monthly", "CAD per hour", "not seasonally adjusted", "nominal wage", "1997-01-01", "14-10-0063-01"),
    (2132594, "services-producing-hourly-wages", "Canada services-producing hourly wage rate", "Canada", "monthly", "CAD per hour", "not seasonally adjusted", "nominal wage", "1997-01-01", "14-10-0063-01"),
    (2153099, "ontario-average-hourly-wages", "Ontario average hourly wage rate", "Ontario", "monthly", "CAD per hour", "not seasonally adjusted", "nominal wage", "1997-01-01", "14-10-0063-01"),
    (2153174, "ontario-goods-producing-hourly-wages", "Ontario goods-producing hourly wage rate", "Ontario", "monthly", "CAD per hour", "not seasonally adjusted", "nominal wage", "1997-01-01", "14-10-0063-01"),
    (2153114, "ontario-services-producing-hourly-wages", "Ontario services-producing hourly wage rate", "Ontario", "monthly", "CAD per hour", "not seasonally adjusted", "nominal wage", "1997-01-01", "14-10-0063-01"),
    (79311153, "average-weekly-earnings", "Canada average weekly earnings", "Canada", "monthly", "CAD per week", "seasonally adjusted", "nominal earnings", "2001-01-01", "14-10-0223-01"),
    (79311309, "ontario-average-weekly-earnings", "Ontario average weekly earnings", "Ontario", "monthly", "CAD per week", "seasonally adjusted", "nominal earnings", "2001-01-01", "14-10-0223-01"),
]

STATCAN_PROPERTY_AUDIT_SPECS = [
    (1073542616, "six-cma-residential-property-price-index", "Six-CMA residential property price index", "Six-CMA composite", "2017-01-01", "18-10-0169-01", "inactive broad new-and-resale property index"),
    (1073542634, "ottawa-residential-property-price-index", "Ottawa broad residential property price index", "Ottawa-Gatineau, Ontario part", "2017-01-01", "18-10-0169-01", "inactive broad new-and-resale property index"),
    (1073542643, "toronto-residential-property-price-index", "Toronto broad residential property price index", "Toronto", "2017-01-01", "18-10-0169-01", "inactive broad new-and-resale property index"),
    (1073542652, "calgary-residential-property-price-index", "Calgary broad residential property price index", "Calgary", "2017-01-01", "18-10-0169-01", "inactive broad new-and-resale property index"),
    (1353834722, "ottawa-new-condominium-price-index", "Ottawa new condominium apartment price index", "Ottawa-Gatineau, Ontario part", "2017-01-01", "18-10-0273-01", "active new-condominium-only index"),
    (1353834723, "toronto-new-condominium-price-index", "Toronto new condominium apartment price index", "Toronto", "2017-01-01", "18-10-0273-01", "active new-condominium-only index"),
    (1353834724, "calgary-new-condominium-price-index", "Calgary new condominium apartment price index", "Calgary", "2017-01-01", "18-10-0273-01", "active new-condominium-only index"),
    (1353834725, "edmonton-new-condominium-price-index", "Edmonton new condominium apartment price index", "Edmonton", "2017-01-01", "18-10-0273-01", "active new-condominium-only index"),
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
    return 100 * (sum(value < current for value in values) + 0.5 * sum(value == current for value in values)) / len(values) if values else None


def _month_index(date: str) -> int:
    year, month = map(int, date[:7].split("-"))
    return year * 12 + month - 1


def _month_date(index: int) -> str:
    return f"{index // 12:04d}-{index % 12 + 1:02d}-01"


def _lookup(series: SourceSeries) -> dict[str, SourceObservation]:
    return {item.date[:7]: item for item in series.observations}


def _combined_release(*items: SourceObservation) -> str | None:
    releases = [item.release_date for item in items if item.release_date]
    return max(releases) if releases else None


def _yoy(series: SourceSeries, source_id: str, label: str) -> SourceSeries:
    lookup = _lookup(series)
    rows = []
    for item in series.observations:
        prior = lookup.get(_month_date(_month_index(item.date) - 12)[:7])
        if prior and prior.value:
            rows.append(SourceObservation(item.date, 100 * (item.value / prior.value - 1), item.release_date))
    return SourceSeries(source_id, label, "percent", series.geography, series.frequency, series.seasonal_adjustment, "growth rate", "Derived from " + series.source, series.source_url, series.retrieval_date, series.revision_notes, rows)


def _difference(left: SourceSeries, right: SourceSeries, source_id: str, label: str, unit: str = "percentage points") -> SourceSeries:
    other = _lookup(right)
    rows = [SourceObservation(item.date, item.value - other[item.date[:7]].value, _combined_release(item, other[item.date[:7]])) for item in left.observations if item.date[:7] in other]
    return SourceSeries(source_id, label, unit, left.geography, left.frequency, left.seasonal_adjustment, "derived", f"{left.source}; {right.source}", left.source_url, left.retrieval_date, f"Derived difference. {left.revision_notes} {right.revision_notes}", rows)


def _ratio(left: SourceSeries, right: SourceSeries, source_id: str, label: str, *, rebase: bool = False) -> SourceSeries:
    other = _lookup(right)
    common = [(item, other[item.date[:7]]) for item in left.observations if item.date[:7] in other and other[item.date[:7]].value]
    if not common:
        return SourceSeries(source_id, label, "index", left.geography, left.frequency, left.seasonal_adjustment, "derived", f"{left.source}; {right.source}", left.source_url, left.retrieval_date, "No common observations available.", [])
    first_ratio = common[0][0].value / common[0][1].value
    rows = [SourceObservation(item.date, 100 * (item.value / comparison.value) / first_ratio if rebase else 100 * item.value / comparison.value, _combined_release(item, comparison)) for item, comparison in common]
    return SourceSeries(source_id, label, "index", left.geography, left.frequency, left.seasonal_adjustment, "real or relative index", f"{left.source}; {right.source}", left.source_url, left.retrieval_date, f"Derived ratio. {left.revision_notes} {right.revision_notes}", rows)


def _quarterly_average(series: SourceSeries, source_id: str, label: str) -> SourceSeries:
    grouped: dict[str, list[SourceObservation]] = {}
    for item in series.observations:
        year, month = map(int, item.date[:7].split("-"))
        quarter_month = ((month - 1) // 3) * 3 + 1
        grouped.setdefault(f"{year:04d}-{quarter_month:02d}-01", []).append(item)
    rows = []
    for date, items in sorted(grouped.items()):
        if len(items) != 3:
            continue
        releases = [item.release_date for item in items if item.release_date]
        rows.append(SourceObservation(date, sum(item.value for item in items) / 3, max(releases) if releases else None))
    return SourceSeries(source_id, label, series.unit, series.geography, "quarterly", "quarterly average of monthly observations", series.nominal_real, "Derived from " + series.source, series.source_url, series.retrieval_date, f"Only completed quarters with all three monthly observations are included. {series.revision_notes}", rows)


def _per_person(income: SourceSeries, population: SourceSeries, source_id: str, label: str) -> SourceSeries:
    people = _lookup(population)
    rows = [SourceObservation(item.date, item.value * 1_000_000 / people[item.date[:7]].value, _combined_release(item, people[item.date[:7]])) for item in income.observations if item.date[:7] in people and people[item.date[:7]].value]
    return SourceSeries(source_id, label, "annualized CAD per person", "Canada", "quarterly", "seasonally adjusted annual-rate numerator aligned to quarterly population", "nominal annualized per-person income", f"{income.source}; {population.source}", income.source_url, income.retrieval_date, f"Income is a seasonally adjusted annual rate in millions of CAD and is not divided by four; population is the matching quarterly estimate. {income.revision_notes} {population.revision_notes}", rows)


def _rebase(series: SourceSeries, source_id: str, label: str, reference_date: str) -> SourceSeries:
    reference = next((item for item in series.observations if item.date == reference_date), None)
    if reference is None or reference.value == 0:
        raise ValueError(f"{series.label} has no valid reference observation at {reference_date}")
    rows = [SourceObservation(item.date, 100 * item.value / reference.value, item.release_date) for item in series.observations]
    return SourceSeries(source_id, label, f"index, {reference_date[:7]}=100", series.geography, series.frequency, series.seasonal_adjustment, "derived index", "Derived from " + series.source, series.source_url, series.retrieval_date, f"Normalized to 100 at {reference_date}. {series.revision_notes}", rows)


def _deflate(nominal: SourceSeries, cpi: SourceSeries, source_id: str, label: str, unit: str) -> SourceSeries:
    prices = _lookup(cpi)
    rows = [SourceObservation(item.date, item.value / prices[item.date[:7]].value * 100, _combined_release(item, prices[item.date[:7]])) for item in nominal.observations if item.date[:7] in prices and prices[item.date[:7]].value]
    return SourceSeries(source_id, label, unit, nominal.geography, nominal.frequency, nominal.seasonal_adjustment, "real CPI-deflated", f"{nominal.source}; {cpi.source}", nominal.source_url, nominal.retrieval_date, f"Deflated by the aligned all-items CPI; this is a derived CPI-deflated measure, not an official chained-dollar series. {nominal.revision_notes} {cpi.revision_notes}", rows)


def _fred_series(fred: FredAdapter, spec: tuple[str, str, str, str, str, str]) -> SourceSeries:
    series_id, _, label, unit, seasonal, nominal_real = spec
    raw = fred.fetch(series_id)
    observations = [SourceObservation(f"{date[:7]}-01", value, None) for date, value in raw.observations]
    frequency = "quarterly" if series_id == "A229RX0Q048SBEA" else "monthly"
    return SourceSeries(series_id, label, unit, "United States", frequency, seasonal, nominal_real, "Official U.S. source distributed through Federal Reserve Economic Data", f"https://fred.stlouisfed.org/series/{series_id}", datetime.now(UTC).isoformat(timespec="seconds"), "The originating BLS, FHFA, or BEA series may be revised; FRED observations do not provide a complete publication-vintage archive here.", observations)


def _interpretation(series_id: str, percentile: float | None, latest_yoy: float | None, latest_value: float) -> tuple[str, str, str]:
    if any(term in series_id for term in ("to-income", "to-wage", "income-gap", "wage-gap")):
        label = "Stressful" if latest_value > 0 and ("gap" in series_id or "pressure" in series_id) else "Historically elevated" if (percentile or 0) >= 75 else "Easing" if (percentile or 100) <= 25 else "Mixed"
        return "up-is-stressful", label, "A rising affordability ratio or growth gap means the documented cost is increasing relative to income or wages."
    if "real-disposable-income" in series_id or "real-wage" in series_id:
        label = "Supportive" if (latest_yoy or latest_value) > 0 else "Stressful"
        return "up-is-supportive", label, "Rising real income or wages generally increase purchasing power, while household experiences can differ from the average."
    if "saving-rate" in series_id:
        return "context-dependent", "Historically elevated" if (percentile or 0) >= 75 else "Historically depressed" if (percentile or 100) <= 25 else "Mixed", "The saving rate can fall because households are confident or because essential costs are absorbing income; supporting evidence is required."
    if series_id.startswith("fao"):
        label = "Elevated" if (percentile or 0) >= 75 else "Depressed" if (percentile or 100) <= 25 else "Normal"
        return "context-dependent", label, "International food commodity pressure; this is not a global grocery-price index."
    if "house" in series_id or "housing" in series_id or "fhfa" in series_id or "nhpi" in series_id:
        growth = latest_value if series_id.endswith("yoy") else latest_yoy
        label = "Declining" if growth is not None and growth < 0 else "Elevated" if (percentile or 0) >= 75 else "Recovering" if growth is not None and growth > 0 else "Context-dependent"
        return "context-dependent", label, "Property purchase-price changes are not equivalent to current shelter-service costs and are not universally supportive."
    if any(word in series_id for word in ("food", "grocery", "rent", "shelter", "mortgage", "replacement")):
        pressure = latest_value if any(word in series_id for word in ("gap", "pressure")) or series_id.endswith("yoy") else latest_yoy
        label = "Stressful" if pressure is not None and pressure > (0.5 if any(word in series_id for word in ("gap", "pressure")) else 3) else "Easing" if pressure is not None and pressure < (0 if any(word in series_id for word in ("gap", "pressure")) else 2) else "Mixed"
        return "up-is-stressful", label, "Consumer affordability depends on price growth relative to wages or income, not the price index alone."
    return "context-dependent", "Direction unclear", "Interpret with its documented comparison series."


def _payload(series: SourceSeries, indicator_id: str, layer: str, generated_at: str, *, definition: str, comparability: str, future_metadata: list[str] | None = None, formula: str | None = None, components: list[str] | None = None, reference_period: str | None = None, future_status: str = "metadata_only_not_scored") -> dict[str, Any]:
    if not series.observations:
        raise ValueError(f"Affordability indicator {indicator_id} has no observations")
    values = [item.value for item in series.observations if math.isfinite(item.value)]
    latest = series.observations[-1]
    lookup = _lookup(series)
    prior_3 = lookup.get(_month_date(_month_index(latest.date) - 3)[:7])
    prior_12 = lookup.get(_month_date(_month_index(latest.date) - 12)[:7])
    previous = series.observations[-2] if len(series.observations) > 1 else None
    latest_yoy = 100 * (latest.value / prior_12.value - 1) if prior_12 and prior_12.value else None
    percentile = _percentile(values, latest.value)
    direction, label, interpretation = _interpretation(indicator_id, percentile, latest_yoy, latest.value)
    previous_peak = max(values[:-1]) if len(values) > 1 else latest.value
    median = _quantile(values, .5)
    return {
        "schemaVersion": 1,
        "id": indicator_id,
        "field": indicator_id.replace("-", "_"),
        "label": series.label,
        "description": definition,
        "definition": definition,
        "unit": series.unit,
        "frequency": series.frequency,
        "status": "derived" if series.nominal_real in {"derived", "growth rate", "real or relative index"} or series.source.startswith("Derived") or "Derived" in series.source else "measured",
        "layer": layer,
        "geography": series.geography,
        "geographyLevel": "global" if series.geography in {"Global", "World", "Advanced economies", "Emerging market economies"} else "national" if series.geography in {"Canada", "United States"} else "provincial_or_metro",
        "domesticOrExternal": "external" if series.geography in {"Global", "World", "Advanced economies", "Emerging market economies"} else "domestic",
        "directlyComparableAcrossCountries": series.source.startswith("Bank for International Settlements"),
        "comparisonLimitations": comparability,
        "interpretationDirection": direction,
        "interpretationLabel": label,
        "interpretation": interpretation,
        "source": series.source,
        "sourceUrl": series.source_url,
        "sourceIdentifier": series.source_id,
        "sourceDate": latest.release_date or latest.date,
        "retrievalDate": series.retrieval_date,
        "revisionStatus": series.revision_notes,
        "seasonalAdjustment": series.seasonal_adjustment,
        "nominalOrReal": series.nominal_real,
        "startDate": series.observations[0].date,
        "endDate": latest.date,
        "latest": {
            "date": latest.date, "sourceDate": latest.release_date or latest.date, "value": latest.value,
            "previousValue": previous.value if previous else None,
            "oneYearChange": latest.value - prior_12.value if prior_12 else None,
            "threeMonthChange": latest.value - prior_3.value if prior_3 else None,
            "fourQuarterChange": latest.value - prior_12.value if prior_12 else None,
            "monthOverMonthChange": latest.value - previous.value if previous else None,
            "yearOverYearPercentChange": latest_yoy,
            "cumulativeChange": 100 * (latest.value / series.observations[0].value - 1) if series.observations[0].value else None,
            "historicalPercentile": percentile,
            "percentileSince2000": _percentile([item.value for item in series.observations if item.date >= "2000-01-01"], latest.value),
            "distanceFromMedian": latest.value - median if median is not None else None,
            "distanceFromPreviousPeakPercent": 100 * (latest.value / previous_peak - 1) if previous_peak else None,
            "momentumThreeMonth": latest.value - prior_3.value if prior_3 else None,
            "momentumTwelveMonth": latest.value - prior_12.value if prior_12 else None,
            "momentum": "rising" if previous and latest.value > previous.value else "falling" if previous and latest.value < previous.value else "steady",
        },
        "referenceRanges": {"historicalMedian": median, "p10": _quantile(values, .1), "p25": _quantile(values, .25), "p75": _quantile(values, .75), "p90": _quantile(values, .9), "minimum": min(values), "maximum": max(values)},
        "observations": [{"date": item.date, "value": item.value, "sourceDate": item.release_date or item.date} for item in series.observations],
        "transformations": ["raw", "indexed", "yoy", "pct_change", "zscore"],
        "confirmingIndicators": [], "conflictingIndicators": [], "evidenceChecks": [],
        "confidenceLevel": "medium", "evidenceLabel": "Contextual indicator",
        "calculation": {"formula": formula or definition, "explanation": definition, "example": f"Latest observation: {latest.value:.2f} {series.unit} at {latest.date[:7]}."},
        "components": components or [],
        "referencePeriod": reference_period,
        "limitations": [series.revision_notes, comparability],
        "futureClassifierMetadata": {"status": future_status, "candidateSymptoms": future_metadata or []},
        "generatedAt": generated_at,
    }


def _statcan_series(adapter: StatCanAdapter, spec: tuple[int, str, str, str, str], table: str) -> SourceSeries:
    vector, _, label, geography, _ = spec
    return adapter.fetch_vector(vector, label=label, unit="index, 2002=100" if table == "18-10-0004-01" else "index, December 2016=100", geography=geography, start="1914-01-01" if table == "18-10-0004-01" else "1981-01-01", seasonal_adjustment="not seasonally adjusted", nominal_real="consumer price index" if table == "18-10-0004-01" else "nominal property purchase price", revision_notes=f"Statistics Canada table {table} may revise recent and historical observations; classifications and baskets follow the native table.")


def _statcan_purchasing_series(adapter: StatCanAdapter, spec: tuple[Any, ...]) -> SourceSeries:
    vector, _, label, geography, frequency, unit, seasonal, nominal_real, start, table = spec
    annualized = " Values are published at seasonally adjusted annual rates." if "annual rates" in seasonal else ""
    result = adapter.fetch_vector(
        vector, label=label, unit=unit, geography=geography, frequency=frequency,
        seasonal_adjustment=seasonal, nominal_real=nominal_real, start=start,
        revision_notes=f"Statistics Canada table {table} is latest-vintage and may revise recent or historical observations.{annualized}",
    )
    return replace(result, source_url=f"https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid={table.replace('-', '')}")


def _statcan_property_series(adapter: StatCanAdapter, spec: tuple[Any, ...]) -> SourceSeries:
    vector, _, label, geography, start, table, coverage = spec
    inactive = " The series is inactive and ends in 2021 Q4." if "inactive" in coverage else ""
    result = adapter.fetch_vector(
        vector, label=label, unit="index, 2017=100", geography=geography, frequency="quarterly",
        seasonal_adjustment="not seasonally adjusted", nominal_real="nominal property purchase price", start=start,
        revision_notes=f"Statistics Canada table {table}; {coverage}.{inactive} It is not spliced to NHPI, resale, rent, or shelter CPI.",
    )
    return replace(result, source_url=f"https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid={table.replace('-', '')}")


def _generated_series(path: Path, source_id: str) -> SourceSeries:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return SourceSeries(
        source_id, payload["label"], payload["unit"], payload["geography"], payload["frequency"],
        payload["seasonalAdjustment"], payload["nominalOrReal"], payload["source"], payload["sourceUrl"],
        payload.get("generatedAt", datetime.now(UTC).isoformat(timespec="seconds")),
        "Reused from the existing generated Canadian evidence layer without changing its source observations.",
        [SourceObservation(row["date"], float(row["value"]), row.get("sourceDate")) for row in payload["observations"] if row.get("value") is not None],
    )


def _chart_rows(series: dict[str, SourceSeries], mapping: dict[str, str]) -> list[dict[str, Any]]:
    dates = sorted({item.date for source in mapping.values() for item in series[source].observations})
    lookups = {key: {item.date: item.value for item in series[source].observations} for key, source in mapping.items()}
    return [{"date": date, **{key: lookup.get(date) for key, lookup in lookups.items()}} for date in dates]


def _write_chart(root: Path, payload: dict[str, Any]) -> None:
    for path in (root / "website" / "public" / "generated" / f"{payload['id']}.json", root / "website" / "public" / "generated" / "charts" / f"{payload['id']}.json"):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def _correlation(left: list[float], right: list[float]) -> float | None:
    return float(np.corrcoef(left, right)[0, 1]) if len(left) >= 3 and np.std(left) > 0 and np.std(right) > 0 else None


def _transmission_row(pair_id: str, predictor: SourceSeries, target: SourceSeries) -> Row:
    x = {item.date[:7]: item.value for item in predictor.observations}
    y = {item.date[:7]: item.value for item in target.observations}

    def pairs(lag: int, start: str | None = None, end: str | None = None) -> tuple[list[float], list[float]]:
        left, right = [], []
        for target_month, target_value in y.items():
            if start and target_month < start or end and target_month > end:
                continue
            source_month = _month_date(_month_index(target_month) - lag)[:7]
            if source_month in x:
                left.append(x[source_month]); right.append(target_value)
        return left, right

    lag_results = []
    for lag in range(25):
        left, right = pairs(lag)
        lag_results.append((lag, _correlation(left, right), len(left)))
    valid = [row for row in lag_results if row[1] is not None]
    peak = max(valid, key=lambda row: abs(float(row[1]))) if valid else (None, None, 0)
    contemporaneous = next((row[1] for row in lag_results if row[0] == 0), None)
    common = sorted(set(x) & set(y))
    rolling = []
    for end_index in range(59, len(common)):
        months = common[end_index - 59:end_index + 1]
        value = _correlation([x[m] for m in months], [y[m] for m in months])
        if value is not None:
            rolling.append(value)
    distributed_rows = []
    for month, target_value in y.items():
        features = [x.get(_month_date(_month_index(month) - lag)[:7]) for lag in range(13)]
        if all(value is not None for value in features):
            distributed_rows.append(([1.0, *[float(value) for value in features]], target_value))
    coefficient_sum = None
    if len(distributed_rows) >= 30:
        coefficients = np.linalg.lstsq(np.asarray([row[0] for row in distributed_rows]), np.asarray([row[1] for row in distributed_rows]), rcond=None)[0]
        coefficient_sum = float(np.sum(coefficients[1:]))
    pre = pairs(0, end="2019-12")
    post = pairs(0, start="2020-01")
    return {
        "relationship": pair_id,
        "predictor": predictor.label,
        "target": target.label,
        "frequency": "monthly",
        "lag_convention": "positive lag means international commodity price is observed before domestic consumer price",
        "contemporaneous_correlation": contemporaneous,
        "peak_lag_months": peak[0],
        "peak_lag_correlation": peak[1],
        "peak_lag_observations": peak[2],
        "distributed_lag_0_12_coefficient_sum": coefficient_sum,
        "rolling_60m_correlation_mean": sum(rolling) / len(rolling) if rolling else None,
        "pre_2020_correlation": _correlation(*pre),
        "post_2020_correlation": _correlation(*post),
        "start_date": max(predictor.observations[0].date, target.observations[0].date),
        "end_date": min(predictor.observations[-1].date, target.observations[-1].date),
        "limitations": "Bivariate latest-vintage association; baskets, exchange rates, lags, margins, policy, and common shocks differ. Correlation is not causation.",
    }


def _append_manifests(root: Path, payloads: dict[str, list[dict[str, Any]]]) -> None:
    canada_path = root / "website" / "public" / "generated" / "canada" / "manifest.json"
    canada_state_path = root / "website" / "public" / "generated" / "canada" / "current-state.json"
    canada = json.loads(canada_path.read_text(encoding="utf-8"))
    canada_state = json.loads(canada_state_path.read_text(encoding="utf-8"))
    managed_canada = {item["id"] for item in payloads["canada"]} | {"shelter-cpi-index", "ontario-shelter-cpi-index"}
    canada["indicators"] = [item for item in canada["indicators"] if item["id"] not in managed_canada]
    canada_state["layers"] = [row for row in canada_state["layers"] if row["label"] not in {"Food affordability", "Housing purchase prices and shelter costs", "Canadian purchasing power"}]
    existing = {item["id"] for item in canada["indicators"]}
    for item in payloads["canada"]:
        if item["id"] not in existing:
            canada["indicators"].append({"id": item["id"], "file": f"indicators/{item['id']}.json", "label": item["label"], "geography": item["geography"], "layer": item["layer"], "core": False, "latestDate": item["latest"]["date"]})
    for layer, ids in (
        ("Food affordability", ["canada-food-cpi-yoy"] + [item["id"] for item in payloads["canada"] if item["id"] in {"food-cpi", "grocery-cpi", "canada-food-inflation-gap", "canada-grocery-inflation-gap"}]),
        ("Housing purchase prices and shelter costs", [item["id"] for item in payloads["canada"] if item["id"] in {"new-housing-price-index", "bis-canada-real-house-price-index", "rent-cpi", "mortgage-interest-cost", "shelter-cpi", "canada-nhpi-yoy"}]),
        ("Canadian purchasing power", [item["id"] for item in payloads["canada"] if item["id"] in {"real-disposable-income-per-person", "real-wage-growth", "household-saving-rate", "food-to-income", "rent-to-income", "shelter-to-income", "mortgage-interest-to-income", "nhpi-to-income"}]),
    ):
        if not any(row["label"] == layer for row in canada_state["layers"]):
            canada_state["layers"].append({"id": layer.lower().replace(" ", "-"), "label": layer, "indicatorIds": ids})
    canada_path.write_text(json.dumps(canada, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    canada_state_path.write_text(json.dumps(canada_state, indent=2, allow_nan=False) + "\n", encoding="utf-8")

    us_path = root / "website" / "public" / "generated" / "manifest.json"
    us = json.loads(us_path.read_text(encoding="utf-8"))
    managed_us = {item["id"] for item in payloads["us"]}
    us["indicators"] = [item for item in us["indicators"] if item["id"] not in managed_us]
    us["layers"] = [row for row in us["layers"] if row["label"] not in {"Food affordability", "Housing purchase prices and shelter costs"}]
    for group in us["currentState"]["groups"].values():
        group[:] = [item for item in group if item["id"] not in managed_us]
    us["currentState"]["indicatorOrder"] = [field for field in us["currentState"]["indicatorOrder"] if field not in {item["field"] for item in payloads["us"]}]
    existing = {item["id"] for item in us["indicators"]}
    current_ids = {"us-food-cpi-yoy", "us-food-at-home-cpi-yoy", "us-fhfa-house-price-yoy", "us-rent-cpi-yoy", "us-shelter-cpi-yoy"}
    for item in payloads["us"]:
        if item["id"] not in existing:
            us["indicators"].append({"id": item["id"], "file": f"us/indicators/{item['id']}.json", "label": item["label"], "layer": item["layer"], "latestDate": item["latest"]["date"], "evidenceLabel": item["evidenceLabel"]})
        if item["id"] in current_ids:
            entry = {"id": item["id"], "field": item["field"], "label": item["label"], "layer": item["layer"], "interpretationLabel": item["interpretationLabel"], "latestDate": item["latest"]["date"], "historicalPercentile": item["latest"]["historicalPercentile"], "anomalyScore": abs(float(item["latest"]["historicalPercentile"] or 50) - 50)}
            group = "stressful" if item["interpretationLabel"] == "Stressful" else "other"
            if not any(row["id"] == item["id"] for row in us["currentState"]["groups"][group]):
                us["currentState"]["groups"][group].append(entry)
                us["currentState"]["indicatorOrder"].append(item["field"])
    for layer, fields, interpretation in (
        ("Food affordability", [item["field"] for item in payloads["us"] if item["id"] in {"us-food-cpi-yoy", "us-food-at-home-cpi-yoy", "us-food-inflation-gap"}], "Food and grocery prices are consumer prices; compare them with income and international commodity pressure."),
        ("Housing purchase prices and shelter costs", [item["field"] for item in payloads["us"] if item["id"] in {"us-fhfa-house-price-yoy", "us-rent-cpi-yoy", "us-shelter-cpi-yoy"}], "Property purchase prices, rent, and shelter-service inflation answer different questions and remain separate."),
    ):
        if not any(row["label"] == layer for row in us["layers"]):
            us["layers"].append({"id": layer.lower().replace(" ", "-"), "label": layer, "indicatorFields": fields, "interpretation": interpretation, "confidence": "Moderate"})
    latest_dates = [item["latestDate"] for item in us["indicators"]]
    us["currentState"]["latestObservationDate"] = max(latest_dates)
    us["currentState"]["oldestLatestObservationDate"] = min(latest_dates)
    for group in us["currentState"]["groups"].values():
        group.sort(key=lambda item: (-float(item.get("anomalyScore") or 0), item["label"]))
    us_path.write_text(json.dumps(us, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def build_affordability_outputs(root: Path, cache: RawCache) -> tuple[list[dict[str, Any]], list[Row]]:
    generated_at = datetime.now(UTC).isoformat(timespec="seconds")
    fao = FaoFoodPriceAdapter(cache).fetch()
    bis = BisPropertyPriceAdapter(cache).fetch()
    statcan = StatCanAdapter(cache)
    fred = FredAdapter(cache)
    series: dict[str, SourceSeries] = {**fao, **bis}
    for spec in STATCAN_CPI_SPECS:
        series[f"ca_{spec[1]}"] = _statcan_series(statcan, spec, "18-10-0004-01")
    for spec in STATCAN_NHPI_SPECS:
        series[f"ca_{spec[1]}"] = _statcan_series(statcan, spec, "18-10-0205-01")
    for spec in STATCAN_PURCHASING_POWER_SPECS:
        series[f"ca_{spec[1]}"] = _statcan_purchasing_series(statcan, spec)
    for spec in STATCAN_PROPERTY_AUDIT_SPECS:
        series[f"ca_{spec[1]}"] = _statcan_property_series(statcan, spec)
    for spec in US_FRED_SPECS:
        series[f"us_{spec[1]}"] = _fred_series(fred, spec)
    canada_generated = root / "website" / "public" / "generated" / "canada" / "indicators"
    series["ca_energy_cpi_yoy"] = _generated_series(canada_generated / "canada-energy-cpi-yoy.json", "CA_ENERGY_CPI_YOY")
    series["ca_cad_per_usd"] = _generated_series(canada_generated / "cad-per-usd.json", "CA_CAD_PER_USD")
    series["ca_policy_rate"] = _generated_series(canada_generated / "canada-policy-rate.json", "CA_POLICY_RATE")
    series["ca_debt_service"] = _generated_series(canada_generated / "canada-household-debt-service-ratio.json", "CA_DEBT_SERVICE")

    # Quarterly purchasing-power measures retain completed quarters only. No
    # quarterly income observation is copied into monthly rows.
    ca_cpi_q = _quarterly_average(series["ca_canada-all-items-cpi"], "CA_CPI_Q", "Canada all-items CPI, quarterly average")
    ca_food_q = _quarterly_average(series["ca_food-cpi"], "CA_FOOD_Q", "Canada food CPI, quarterly average")
    ca_grocery_q = _quarterly_average(series["ca_grocery-cpi"], "CA_GROCERY_Q", "Canada grocery CPI, quarterly average")
    ca_rent_q = _quarterly_average(series["ca_rent-cpi"], "CA_RENT_Q", "Canada rent CPI, quarterly average")
    ca_shelter_q = _quarterly_average(series["ca_shelter-cpi"], "CA_SHELTER_Q", "Canada shelter CPI, quarterly average")
    ca_mortgage_q = _quarterly_average(series["ca_mortgage-interest-cost"], "CA_MIC_Q", "Canada mortgage-interest-cost index, quarterly average")
    ca_nhpi_q = _quarterly_average(series["ca_new-housing-price-index"], "CA_NHPI_Q", "Canada NHPI, quarterly average")
    income_pp = _per_person(series["ca_household-disposable-income"], series["ca_canada-population-quarterly"], "CA_HDIPC", "Canada household disposable income per person")
    series["ca_household-disposable-income-per-person"] = income_pp
    series["ca_real-disposable-income-per-person"] = _deflate(income_pp, ca_cpi_q, "CA_REAL_HDIPC", "Canada real household disposable income per person", "CPI-deflated annualized CAD per person")

    reference = "2017-01-01"
    income_index = _rebase(income_pp, "CA_HDIPC_INDEX", "Disposable income per person index", reference)
    food_index = _rebase(ca_food_q, "CA_FOOD_Q_INDEX", "Food CPI quarterly index", reference)
    grocery_index = _rebase(ca_grocery_q, "CA_GROCERY_Q_INDEX", "Grocery CPI quarterly index", reference)
    rent_index = _rebase(ca_rent_q, "CA_RENT_Q_INDEX", "Rent CPI quarterly index", reference)
    shelter_index = _rebase(ca_shelter_q, "CA_SHELTER_Q_INDEX", "Shelter CPI quarterly index", reference)
    mortgage_index = _rebase(ca_mortgage_q, "CA_MIC_Q_INDEX", "Mortgage-interest-cost quarterly index", reference)
    nhpi_index = _rebase(ca_nhpi_q, "CA_NHPI_Q_INDEX", "NHPI quarterly index", reference)
    series["ca_income-index"] = income_index
    series["ca_food-quarterly-index"] = food_index
    series["ca_grocery-quarterly-index"] = grocery_index
    series["ca_rent-quarterly-index"] = rent_index
    series["ca_shelter-quarterly-index"] = shelter_index
    series["ca_mortgage-quarterly-index"] = mortgage_index
    series["ca_nhpi-quarterly-index"] = nhpi_index
    series["ca_food-to-income"] = _ratio(food_index, income_index, "CA_FOOD_TO_INCOME", "Canada food-price-to-income index")
    series["ca_grocery-to-income"] = _ratio(grocery_index, income_index, "CA_GROCERY_TO_INCOME", "Canada grocery-price-to-income index")
    series["ca_rent-to-income"] = _ratio(rent_index, income_index, "CA_RENT_TO_INCOME", "Canada rent-to-income index")
    series["ca_shelter-to-income"] = _ratio(shelter_index, income_index, "CA_SHELTER_TO_INCOME", "Canada shelter-to-income index")
    series["ca_mortgage-interest-to-income"] = _ratio(mortgage_index, income_index, "CA_MIC_TO_INCOME", "Canada mortgage-interest-to-income index")
    series["ca_nhpi-to-income"] = _ratio(nhpi_index, income_index, "CA_NHPI_TO_INCOME", "Canada new-house-price-to-income index")
    series["ca_real-nhpi"] = _deflate(ca_nhpi_q, ca_cpi_q, "CA_REAL_NHPI", "Canada real new-house-price index", "real index, CPI-adjusted")

    income_yoy = _yoy(income_pp, "CA_HDIPC_YOY", "Canada disposable income per person growth")
    series["ca_food-income-gap"] = _difference(_yoy(ca_food_q, "CA_FOOD_Q_YOY", "Canada quarterly food CPI growth"), income_yoy, "CA_FOOD_INCOME_GAP", "Canada food income-growth gap")
    series["ca_grocery-income-gap"] = _difference(_yoy(ca_grocery_q, "CA_GROCERY_Q_YOY", "Canada quarterly grocery CPI growth"), income_yoy, "CA_GROCERY_INCOME_GAP", "Canada grocery income-growth gap")
    series["ca_rent-income-gap"] = _difference(_yoy(ca_rent_q, "CA_RENT_Q_YOY", "Canada quarterly rent CPI growth"), income_yoy, "CA_RENT_INCOME_GAP", "Canada rent income-growth gap")
    series["ca_shelter-income-gap"] = _difference(_yoy(ca_shelter_q, "CA_SHELTER_Q_YOY", "Canada quarterly shelter CPI growth"), income_yoy, "CA_SHELTER_INCOME_GAP", "Canada shelter income-growth gap")
    series["ca_mortgage-income-gap"] = _difference(_yoy(ca_mortgage_q, "CA_MIC_Q_YOY", "Canada quarterly mortgage-interest growth"), income_yoy, "CA_MIC_INCOME_GAP", "Canada mortgage-interest income-growth gap")
    series["ca_nhpi-income-gap"] = _difference(_yoy(ca_nhpi_q, "CA_NHPI_Q_YOY", "Canada quarterly NHPI growth"), income_yoy, "CA_NHPI_INCOME_GAP", "Canada NHPI income-growth gap")

    wage_yoy_ca = _yoy(series["ca_average-hourly-wages"], "CA_WAGE_YOY", "Canada hourly wage growth")
    cpi_yoy_ca = _yoy(series["ca_canada-all-items-cpi"], "CA_CPI_YOY_PP", "Canada all-items CPI growth")
    series["ca_nominal-wage-growth"] = wage_yoy_ca
    series["ca_food-monthly-yoy"] = _yoy(series["ca_food-cpi"], "CA_FOOD_YOY_PP", "Canada food CPI growth")
    series["ca_grocery-monthly-yoy"] = _yoy(series["ca_grocery-cpi"], "CA_GROCERY_YOY_PP", "Canada grocery CPI growth")
    series["ca_real-wage-index"] = _ratio(_rebase(series["ca_average-hourly-wages"], "CA_WAGE_INDEX", "Canada hourly wage index", reference), _rebase(series["ca_canada-all-items-cpi"], "CA_CPI_INDEX_PP", "Canada all-items CPI index", reference), "CA_REAL_WAGE_INDEX", "Canada real wage index")
    series["ca_real-wage-growth"] = _difference(wage_yoy_ca, cpi_yoy_ca, "CA_REAL_WAGE_GROWTH", "Canada real wage growth")
    series["ca_food-to-wage"] = _difference(series["ca_food-monthly-yoy"], wage_yoy_ca, "CA_FOOD_WAGE_GAP", "Canada food wage-pressure gap")
    series["ca_grocery-to-wage"] = _difference(series["ca_grocery-monthly-yoy"], wage_yoy_ca, "CA_GROCERY_WAGE_GAP", "Canada grocery wage-pressure gap")
    series["ca_rent-to-wage"] = _difference(_yoy(series["ca_rent-cpi"], "CA_RENT_YOY_PP", "Canada rent CPI growth"), wage_yoy_ca, "CA_RENT_WAGE_GAP", "Canada rent wage-pressure gap")
    series["ca_shelter-to-wage"] = _difference(_yoy(series["ca_shelter-cpi"], "CA_SHELTER_YOY_PP", "Canada shelter CPI growth"), wage_yoy_ca, "CA_SHELTER_WAGE_GAP", "Canada shelter wage-pressure gap")

    broad_index = _rebase(series["ca_six-cma-residential-property-price-index"], "CA_RPPI_INDEX", "Six-CMA residential property price index", reference)
    series["ca_residential-property-price-to-income"] = _ratio(broad_index, income_index, "CA_RPPI_TO_INCOME", "Six-CMA residential-property-price-to-income index")

    # Derived Canadian measures. Income-based measures remain unavailable and are documented rather than estimated.
    series["ca_food_yoy"] = _yoy(series["ca_food-cpi"], "CA_FOOD_CPI_YOY", "Canada food CPI growth")
    series["ca_grocery_yoy"] = _yoy(series["ca_grocery-cpi"], "CA_GROCERY_CPI_YOY", "Canada grocery CPI growth")
    ca_all_yoy = _yoy(series["ca_canada-all-items-cpi"], "CA_ALL_CPI_YOY", "Canada all-items CPI growth")
    series["ca_food_gap"] = _difference(series["ca_food_yoy"], ca_all_yoy, "CA_FOOD_INFLATION_GAP", "Canada food inflation gap")
    series["ca_grocery_gap"] = _difference(series["ca_grocery_yoy"], ca_all_yoy, "CA_GROCERY_INFLATION_GAP", "Canada grocery inflation gap")
    series["ca_real_food"] = _ratio(series["ca_food-cpi"], series["ca_canada-all-items-cpi"], "CA_REAL_FOOD_INDEX", "Canada real food-price index")
    series["ca_nhpi_yoy"] = _yoy(series["ca_new-housing-price-index"], "CA_NHPI_YOY", "Canada new housing price growth")
    series["ca_rent_yoy"] = _yoy(series["ca_rent-cpi"], "CA_RENT_CPI_YOY", "Canada rent CPI growth")
    series["ca_shelter_yoy"] = _yoy(series["ca_shelter-cpi"], "CA_SHELTER_CPI_YOY", "Canada shelter CPI growth")
    series["ca_mortgage_yoy"] = _yoy(series["ca_mortgage-interest-cost"], "CA_MIC_YOY", "Canada mortgage-interest-cost growth")

    # Derived U.S. measures.
    series["us_food_yoy"] = _yoy(series["us_food-cpi"], "US_FOOD_CPI_YOY", "U.S. food CPI growth")
    series["us_home_yoy"] = _yoy(series["us_food-at-home-cpi"], "US_FOOD_HOME_YOY", "U.S. food-at-home CPI growth")
    us_all_yoy = _yoy(series["us_us-all-items-cpi"], "US_ALL_CPI_YOY", "U.S. all-items CPI growth")
    series["us_food_gap"] = _difference(series["us_food_yoy"], us_all_yoy, "US_FOOD_INFLATION_GAP", "U.S. food inflation gap")
    series["us_grocery_gap"] = _difference(series["us_home_yoy"], us_all_yoy, "US_GROCERY_INFLATION_GAP", "U.S. grocery inflation gap")
    series["us_real_food"] = _ratio(series["us_food-cpi"], series["us_us-all-items-cpi"], "US_REAL_FOOD_INDEX", "U.S. real food-price index")
    wage_yoy = _yoy(series["us_average-hourly-earnings"], "US_WAGE_YOY", "U.S. average hourly earnings growth")
    series["us_food_affordability"] = _difference(series["us_food_yoy"], wage_yoy, "US_FOOD_WAGE_GAP", "U.S. food affordability pressure")
    series["us_fhfa_real"] = _ratio(series["us_fhfa-house-price-index"], series["us_us-all-items-cpi"], "US_FHFA_REAL", "Real FHFA house price index")
    series["us_fhfa_yoy"] = _yoy(series["us_fhfa-house-price-index"], "US_FHFA_YOY", "FHFA U.S. house price growth")
    series["us_rent_yoy"] = _yoy(series["us_rent-cpi"], "US_RENT_YOY", "U.S. rent CPI growth")
    series["us_shelter_yoy"] = _yoy(series["us_shelter-cpi"], "US_SHELTER_YOY", "U.S. shelter CPI growth")
    series["us_rent_pressure"] = _difference(series["us_rent_yoy"], wage_yoy, "US_RENT_WAGE_GAP", "U.S. rent pressure")
    series["us_house_income"] = _ratio(series["us_fhfa-house-price-index"], series["us_real-disposable-income-per-capita"], "US_HOUSE_INCOME", "U.S. house-price-to-income index", rebase=True)

    definitions = {
        "food_gap": "Food inflation gap = food CPI YoY - all-items CPI YoY.",
        "grocery_gap": "Grocery inflation gap = food-at-home or food-from-stores CPI YoY - all-items CPI YoY.",
        "real_food": "Real food-price index = food CPI / all-items CPI × 100.",
        "real_house": "Real house-price index = nominal house-price index / all-items CPI × 100.",
        "house_income": "House-price-to-income index = rebased house-price index / rebased real disposable-income-per-person index × 100.",
        "rent_pressure": "Rent pressure = rent CPI growth - average hourly earnings growth.",
    }
    payload_groups: dict[str, list[dict[str, Any]]] = {"global": [], "canada": [], "us": []}

    def add(group: str, key: str, indicator_id: str, layer: str, definition: str, candidates: list[str], *, formula: str | None = None, components: list[str] | None = None, reference_period: str | None = None, future_status: str = "metadata_only_not_scored") -> None:
        payload_groups[group].append(_payload(series[key], indicator_id, layer, generated_at, definition=definition, comparability="Country baskets, weights, index bases, seasonal treatment, and housing institutions differ. Compare growth rates and within-country percentiles before levels.", future_metadata=candidates, formula=formula, components=components, reference_period=reference_period, future_status=future_status))

    for key, indicator_id in (("fao_food_nominal", "fao-food-price-index"), ("fao_food_real", "fao-food-price-index-real"), ("fao_cereals_nominal", "fao-cereals-price-index"), ("fao_cereals_real", "fao-cereals-price-index-real"), ("fao_oils_nominal", "fao-vegetable-oils-price-index"), ("fao_oils_real", "fao-vegetable-oils-price-index-real"), ("fao_dairy_nominal", "fao-dairy-price-index"), ("fao_dairy_real", "fao-dairy-price-index-real"), ("fao_meat_nominal", "fao-meat-price-index"), ("fao_meat_real", "fao-meat-price-index-real"), ("fao_sugar_nominal", "fao-sugar-price-index"), ("fao_sugar_real", "fao-sugar-price-index-real")):
        add("global", key, indicator_id, "International food commodity prices", "FAO international food commodity index, 2014-2016=100; not a global grocery-price index.", ["global commodity food pressure transmitting into retail prices"])
    for key, indicator_id in (("bis_xw_real_house_prices", "bis-real-house-prices"), ("bis_xw_nominal_house_prices", "bis-nominal-house-prices"), ("bis_5r_real_house_prices", "bis-advanced-real-house-prices"), ("bis_4t_real_house_prices", "bis-emerging-real-house-prices"), ("bis_ca_real_house_prices", "bis-canada-real-house-prices"), ("bis_us_real_house_prices", "bis-us-real-house-prices")):
        add("global", key, indicator_id, "International residential property prices", "BIS selected residential property-price index; aggregate coverage is participating economies, not every dwelling worldwide.", ["property-price growth occurring alongside resource or liquidity expansion"])
    for code, name in (("gb", "united-kingdom"), ("de", "germany"), ("cn", "china"), ("in", "india"), ("br", "brazil")):
        add("global", f"bis_{code}_real_house_prices", f"bis-{name}-real-house-prices", "International residential property prices", "BIS selected national real residential property-price index, 2010=100.", ["property-price growth occurring alongside resource or liquidity expansion"])

    ca_keys = [(f"ca_{spec[1]}", spec[1], "Food affordability" if "all-items" in spec[1] or "food" in spec[1] or any(word in spec[1] for word in ("grocery", "meat", "dairy", "bakery", "fruit", "vegetables")) else "Housing purchase prices and shelter costs") for spec in STATCAN_CPI_SPECS]
    ca_keys += [(f"ca_{spec[1]}", spec[1], "Housing purchase prices and shelter costs") for spec in STATCAN_NHPI_SPECS]
    for key, indicator_id, layer in ca_keys:
        add("canada", key, indicator_id, layer, "Published Statistics Canada CPI or New Housing Price Index at native monthly frequency.", ["food prices rising faster than income"] if layer == "Food affordability" else ["house prices diverging from income", "mortgage-interest burden rising"])
    # Canada food CPI YoY already belongs to the established Canadian evidence
    # contract. Reuse it in charts and Current State without overwriting it.
    for key, indicator_id, definition in (("ca_grocery_yoy", "canada-grocery-cpi-yoy", "Food-from-stores CPI year-over-year percent change."), ("ca_food_gap", "canada-food-inflation-gap", definitions["food_gap"]), ("ca_grocery_gap", "canada-grocery-inflation-gap", definitions["grocery_gap"]), ("ca_real_food", "canada-real-food-price-index", definitions["real_food"]), ("ca_nhpi_yoy", "canada-nhpi-yoy", "New Housing Price Index year-over-year percent change."), ("ca_rent_yoy", "canada-rent-cpi-yoy", "Rent CPI year-over-year percent change."), ("ca_shelter_yoy", "canada-shelter-cpi-yoy-affordability", "Shelter CPI year-over-year percent change."), ("ca_mortgage_yoy", "canada-mortgage-interest-cost-yoy", "Mortgage-interest-cost index year-over-year percent change.")):
        layer = "Food affordability" if "food" in indicator_id or "grocery" in indicator_id else "Housing purchase prices and shelter costs"
        add("canada", key, indicator_id, layer, definition, ["food prices rising faster than income"] if layer == "Food affordability" else ["rent rising faster than income", "mortgage-interest burden rising", "house prices diverging from income"])
    add("canada", "bis_ca_nominal_house_prices", "bis-canada-nominal-house-price-index", "Housing purchase prices and shelter costs", "BIS representative national residential property-price index, nominal, 2010=100.", ["property-price growth occurring alongside resource or liquidity expansion"])
    add("canada", "bis_ca_real_house_prices", "bis-canada-real-house-price-index", "Housing purchase prices and shelter costs", "BIS representative national residential property-price index deflated by Canadian CPI, 2010=100.", ["house prices diverging from income"])

    income_sources = {
        "household-disposable-income": "Official quarterly household disposable income, published in millions of CAD at seasonally adjusted annual rates.",
        "household-consumption-expenditure": "Official quarterly household final consumption expenditure, published in millions of CAD at seasonally adjusted annual rates.",
        "household-saving-rate": "Official quarterly household saving as a percentage of household disposable income.",
        "canada-population-quarterly": "Official quarterly Canadian population estimate used only at matching quarter dates.",
        "average-hourly-wages": "Average hourly wage rate for employees aged 15 and older, both full- and part-time, all industries.",
        "goods-producing-hourly-wages": "Average hourly wage rate for employees in goods-producing industries.",
        "services-producing-hourly-wages": "Average hourly wage rate for employees in services-producing industries.",
        "ontario-average-hourly-wages": "Ontario average hourly wage rate for employees aged 15 and older, all industries.",
        "ontario-goods-producing-hourly-wages": "Ontario average hourly wage rate in goods-producing industries.",
        "ontario-services-producing-hourly-wages": "Ontario average hourly wage rate in services-producing industries.",
        "average-weekly-earnings": "SEPH average weekly earnings including overtime for all employees, seasonally adjusted.",
        "ontario-average-weekly-earnings": "Ontario SEPH average weekly earnings including overtime for all employees, seasonally adjusted.",
    }
    for spec in STATCAN_PURCHASING_POWER_SPECS:
        _, indicator_id, _, _, _, _, _, _, _, _ = spec
        add("canada", f"ca_{indicator_id}", indicator_id, "Canadian purchasing power", income_sources[indicator_id], [], components=[f"StatCan vector v{spec[0]}"], future_status="Not yet evaluated")

    for spec in STATCAN_PROPERTY_AUDIT_SPECS:
        _, indicator_id, _, _, _, table, coverage = spec
        add("canada", f"ca_{indicator_id}", indicator_id, "Housing purchase prices and shelter costs", f"Statistics Canada {coverage}; retained separately from NHPI and housing-service costs.", ["residential property prices diverging from income"], components=[table], future_status="Not yet evaluated")

    purchasing_measures = [
        ("household-disposable-income-per-person", "Household disposable income per person", "Household disposable income at an annual rate divided by the matching quarterly population estimate.", "Household disposable income SAAR × 1,000,000 / quarterly population", ["household-disposable-income", "canada-population-quarterly"], []),
        ("real-disposable-income-per-person", "Real household disposable income per person", "CPI-deflated household disposable income per person; this is derived rather than an official chained-dollar series.", "Nominal disposable income per person / quarterly-average all-items CPI × 100", ["household-disposable-income-per-person", "canada-all-items-cpi"], ["real disposable income per person declining"]),
        ("nominal-wage-growth", "Nominal hourly wage growth", "Year-over-year growth in the Canada average hourly wage rate.", "100 × (hourly wage / hourly wage one year earlier - 1)", ["average-hourly-wages"], []),
        ("real-wage-index", "Real wage index", "Average hourly wages relative to all-items CPI, normalized at the fixed reference month.", "Rebased hourly wage index / rebased all-items CPI index × 100", ["average-hourly-wages", "canada-all-items-cpi"], []),
        ("real-wage-growth", "Real wage growth", "Nominal hourly wage growth minus all-items CPI growth.", "Hourly wage YoY - all-items CPI YoY", ["average-hourly-wages", "canada-all-items-cpi"], []),
        ("food-to-income", "Food-price-to-income index", "Quarterly food CPI relative to disposable income per person; rising values indicate food prices gaining on income.", "Rebased quarterly food CPI / rebased disposable income per person × 100", ["food-cpi", "household-disposable-income-per-person"], ["food prices rising faster than disposable income"]),
        ("grocery-to-income", "Grocery-price-to-income index", "Quarterly food-from-stores CPI relative to disposable income per person.", "Rebased quarterly grocery CPI / rebased disposable income per person × 100", ["grocery-cpi", "household-disposable-income-per-person"], ["food prices rising faster than disposable income"]),
        ("food-income-gap", "Food income-growth gap", "Quarterly food inflation minus disposable-income-per-person growth.", "Food CPI YoY - disposable income per person YoY", ["food-cpi", "household-disposable-income-per-person"], ["food prices rising faster than disposable income"]),
        ("grocery-income-gap", "Grocery income-growth gap", "Quarterly grocery inflation minus disposable-income-per-person growth.", "Grocery CPI YoY - disposable income per person YoY", ["grocery-cpi", "household-disposable-income-per-person"], ["food prices rising faster than disposable income"]),
        ("food-to-wage", "Food wage-pressure gap", "Monthly food inflation minus average hourly wage growth.", "Food CPI YoY - average hourly wage YoY", ["food-cpi", "average-hourly-wages"], ["food prices rising faster than wages"]),
        ("grocery-to-wage", "Grocery wage-pressure gap", "Monthly grocery inflation minus average hourly wage growth.", "Grocery CPI YoY - average hourly wage YoY", ["grocery-cpi", "average-hourly-wages"], ["food prices rising faster than wages"]),
        ("rent-to-wage", "Rent wage-pressure gap", "Monthly rent inflation minus average hourly wage growth.", "Rent CPI YoY - average hourly wage YoY", ["rent-cpi", "average-hourly-wages"], ["rent rising faster than income"]),
        ("shelter-to-wage", "Shelter wage-pressure gap", "Monthly shelter inflation minus average hourly wage growth.", "Shelter CPI YoY - average hourly wage YoY", ["shelter-cpi", "average-hourly-wages"], ["shelter costs rising faster than income"]),
        ("rent-to-income", "Rent-to-income index", "Quarterly rent CPI relative to disposable income per person.", "Rebased quarterly rent CPI / rebased disposable income per person × 100", ["rent-cpi", "household-disposable-income-per-person"], ["rent rising faster than income"]),
        ("shelter-to-income", "Shelter-to-income index", "Quarterly shelter CPI relative to disposable income per person.", "Rebased quarterly shelter CPI / rebased disposable income per person × 100", ["shelter-cpi", "household-disposable-income-per-person"], ["shelter costs rising faster than income"]),
        ("mortgage-interest-to-income", "Mortgage-interest-to-income index", "Quarterly mortgage-interest-cost index relative to disposable income per person.", "Rebased quarterly mortgage-interest-cost index / rebased disposable income per person × 100", ["mortgage-interest-cost", "household-disposable-income-per-person"], ["mortgage-interest costs rising faster than income"]),
        ("nhpi-to-income", "New-house-price-to-income index", "Quarterly-average NHPI relative to disposable income per person.", "Rebased quarterly NHPI / rebased disposable income per person × 100", ["new-housing-price-index", "household-disposable-income-per-person"], ["residential property prices diverging from income"]),
        ("real-nhpi", "Real new-house-price index", "Quarterly-average NHPI deflated by quarterly-average all-items CPI.", "Quarterly NHPI / quarterly all-items CPI × 100", ["new-housing-price-index", "canada-all-items-cpi"], []),
        ("rent-income-gap", "Rent income-growth gap", "Quarterly rent inflation minus disposable-income-per-person growth.", "Rent CPI YoY - disposable income per person YoY", ["rent-cpi", "household-disposable-income-per-person"], ["rent rising faster than income"]),
        ("shelter-income-gap", "Shelter income-growth gap", "Quarterly shelter inflation minus disposable-income-per-person growth.", "Shelter CPI YoY - disposable income per person YoY", ["shelter-cpi", "household-disposable-income-per-person"], ["shelter costs rising faster than income"]),
        ("mortgage-income-gap", "Mortgage-interest income-growth gap", "Quarterly mortgage-interest-cost growth minus disposable-income-per-person growth.", "Mortgage-interest-cost YoY - disposable income per person YoY", ["mortgage-interest-cost", "household-disposable-income-per-person"], ["mortgage-interest costs rising faster than income"]),
        ("nhpi-income-gap", "NHPI income-growth gap", "Quarterly new-house-price growth minus disposable-income-per-person growth.", "NHPI YoY - disposable income per person YoY", ["new-housing-price-index", "household-disposable-income-per-person"], ["residential property prices diverging from income"]),
        ("residential-property-price-to-income", "Six-CMA residential-property-price-to-income index", "Archived broad new-and-resale property prices relative to national disposable income per person; the geography mismatch is explicit.", "Rebased Six-CMA RPPI / rebased Canada disposable income per person × 100", ["six-cma-residential-property-price-index", "household-disposable-income-per-person"], ["residential property prices diverging from income"]),
    ]
    for indicator_id, label, definition, formula, components, candidates in purchasing_measures:
        series_key = f"ca_{indicator_id}"
        add("canada", series_key, indicator_id, "Canadian purchasing power", definition, candidates, formula=formula, components=components, reference_period=reference if "index" in label.lower() else None, future_status="Not yet evaluated")

    us_keys = [(f"us_{spec[1]}", f"us-{spec[1]}", "Food affordability" if "food" in spec[1] or any(word in spec[1] for word in ("cereals", "meat", "dairy", "fruit")) else "Housing purchase prices and shelter costs") for spec in US_FRED_SPECS if spec[1] not in {"average-hourly-earnings", "real-disposable-income-per-capita", "us-all-items-cpi"}]
    for key, indicator_id, layer in us_keys:
        add("us", key, indicator_id, layer, "Published BLS consumer-price or FHFA purchase-only house-price index distributed through FRED.", ["global commodity food pressure transmitting into retail prices"] if layer == "Food affordability" else ["rent rising faster than income", "house prices diverging from income"])
    for key, indicator_id, definition in (("us_food_yoy", "us-food-cpi-yoy", "Food CPI year-over-year percent change."), ("us_home_yoy", "us-food-at-home-cpi-yoy", "Food-at-home CPI year-over-year percent change."), ("us_food_gap", "us-food-inflation-gap", definitions["food_gap"]), ("us_grocery_gap", "us-grocery-inflation-gap", definitions["grocery_gap"]), ("us_real_food", "us-real-food-price-index", definitions["real_food"]), ("us_food_affordability", "us-food-affordability-pressure", "Food CPI growth minus average hourly earnings growth; experimental, with components published."), ("us_fhfa_real", "us-real-fhfa-house-price-index", definitions["real_house"]), ("us_fhfa_yoy", "us-fhfa-house-price-yoy", "FHFA house-price index year-over-year percent change."), ("us_rent_yoy", "us-rent-cpi-yoy", "Rent CPI year-over-year percent change."), ("us_shelter_yoy", "us-shelter-cpi-yoy", "Shelter CPI year-over-year percent change."), ("us_rent_pressure", "us-rent-pressure", definitions["rent_pressure"]), ("us_house_income", "us-house-price-to-income-index", definitions["house_income"])):
        layer = "Food affordability" if "food" in indicator_id or "grocery" in indicator_id else "Housing purchase prices and shelter costs"
        add("us", key, indicator_id, layer, definition, ["food prices rising faster than income"] if layer == "Food affordability" else ["rent rising faster than income", "house prices diverging from income"])

    roots = {"global": root / "website" / "public" / "generated" / "global", "canada": root / "website" / "public" / "generated" / "canada", "us": root / "website" / "public" / "generated" / "us"}
    for group, payloads in payload_groups.items():
        directory = roots[group] / "indicators"
        directory.mkdir(parents=True, exist_ok=True)
        for payload in payloads:
            (directory / f"{payload['id']}.json").write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        if group != "canada":
            manifest: dict[str, Any] = {"schemaVersion": 1, "generatedAt": generated_at, "geography": group.title(), "indicators": [{"id": item["id"], "file": f"indicators/{item['id']}.json", "label": item["label"], "layer": item["layer"], "latestDate": item["latest"]["date"]} for item in payloads]}
            if group == "global":
                headline = [item for item in payloads if item["id"] in {"fao-food-price-index", "fao-food-price-index-real", "bis-real-house-prices", "bis-advanced-real-house-prices", "bis-emerging-real-house-prices"}]
                manifest["currentState"] = {"asOf": generated_at, "indicators": [{"id": item["id"], "label": item["label"], "latestDate": item["latest"]["date"], "value": item["latest"]["value"], "unit": item["unit"], "historicalPercentile": item["latest"]["historicalPercentile"], "interpretationLabel": item["interpretationLabel"]} for item in headline]}
            (roots[group] / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    # Interactive chart datasets.
    index_views = ["raw", "indexed", "yoy", "pct_change", "zscore"]
    rate_views = ["raw", "indexed", "zscore"]
    chart_specs = [
        ("affordability-fao-food", "International food commodity prices", "monthly", {"FAO_food": "fao_food_nominal", "Cereals": "fao_cereals_nominal", "Vegetable_oils": "fao_oils_nominal", "Dairy": "fao_dairy_nominal", "Meat": "fao_meat_nominal", "Sugar": "fao_sugar_nominal"}, "FAO commodity indices measure international quotations, not retail grocery bills.", index_views),
        ("affordability-food-transmission", "International commodities and domestic grocery prices", "monthly", {"FAO_food_YoY": "fao_food_nominal_yoy", "Canada_grocery_YoY": "ca_grocery_yoy", "US_food_home_YoY": "us_home_yoy"}, "Compare timing and persistence; exchange rates, processing, transport, labour, margins, taxes, and domestic supply separate commodity and retail prices.", rate_views),
        ("affordability-food-categories", "Commodity categories and domestic retail food prices", "monthly", {"FAO_cereals_YoY": "fao_cereals_nominal_yoy", "Canada_bakery_YoY": "ca_bakery_yoy", "US_bakery_YoY": "us_bakery_yoy", "FAO_dairy_YoY": "fao_dairy_nominal_yoy", "Canada_dairy_YoY": "ca_dairy_yoy", "US_dairy_YoY": "us_dairy_yoy"}, "Commodity categories and retail baskets differ; the chart supports lag inspection rather than one-to-one pass-through claims.", rate_views),
        ("affordability-canada-food", "Canadian food prices and all-items inflation", "monthly", {"Food": "ca_food-cpi", "Groceries": "ca_grocery-cpi", "Restaurants": "ca_restaurant-food-cpi", "All_items": "ca_canada-all-items-cpi"}, "Food, groceries, restaurants, and the all-items basket use distinct Statistics Canada classifications.", index_views),
        ("affordability-canada-housing", "Canadian new housing purchase prices", "monthly", {"Total": "ca_new-housing-price-index", "House": "ca_new-housing-house-component", "Land": "ca_new-housing-land-component"}, "The NHPI measures transaction prices for new residential properties; it is not rent or shelter CPI.", index_views),
        ("affordability-canada-housing-costs", "Canadian property prices and current shelter costs", "monthly", {"NHPI_YoY": "ca_nhpi_yoy", "Rent_YoY": "ca_rent_yoy", "Mortgage_interest_YoY": "ca_mortgage_yoy", "Shelter_YoY": "ca_shelter_yoy"}, "Purchase prices, rent, mortgage interest, and shelter services are shown separately.", rate_views),
        ("affordability-canada-food-context", "Canadian food inflation, energy, and the exchange rate", "monthly", {"Food_YoY": "ca_food_yoy", "Grocery_YoY": "ca_grocery_yoy", "Energy_CPI_YoY": "ca_energy_cpi_yoy", "CAD_per_USD": "ca_cad_per_usd"}, "Food prices may respond to international commodities, energy, currency, domestic supply, processing, and margins; co-movement is not causal proof.", rate_views),
        ("affordability-canada-mortgage-renewal", "Canadian mortgage-renewal pressure components", "monthly", {"Mortgage_interest_YoY": "ca_mortgage_yoy", "Policy_rate": "ca_policy_rate", "Debt_service_ratio": "ca_debt_service"}, "Mortgage-interest cost, the policy rate, and household debt service are a multi-indicator diagnostic, not a single housing-stress score.", rate_views),
        ("affordability-us-housing", "U.S. property prices and shelter costs", "monthly", {"FHFA": "us_fhfa-house-price-index", "Shelter": "us_shelter-cpi", "Rent": "us_rent-cpi", "Owners_equivalent_rent": "us_owners-equivalent-rent-cpi"}, "FHFA measures purchase prices; BLS shelter, rent, and owners' equivalent rent measure housing-service costs.", index_views),
        ("affordability-real-house-prices", "International real residential property prices", "quarterly", {"World": "bis_xw_real_house_prices", "Canada": "bis_ca_real_house_prices", "United_States": "bis_us_real_house_prices", "Advanced": "bis_5r_real_house_prices", "Emerging": "bis_4t_real_house_prices", "Germany": "bis_de_real_house_prices", "China": "bis_cn_real_house_prices", "Brazil": "bis_br_real_house_prices"}, "BIS selected series improve comparability but differ in national source coverage and aggregate weighting.", index_views),
        ("affordability-house-price-income", "U.S. house prices relative to income", "quarterly", {"House_price_to_income": "us_house_income", "BIS_US_real_house": "bis_us_real_house_prices"}, "The U.S. ratio uses real disposable income per person. A comparable Canadian income series is not yet implemented.", index_views),
        ("affordability-us-food-income", "U.S. food prices relative to wages", "monthly", {"Food_YoY": "us_food_yoy", "Food_at_home_YoY": "us_home_yoy", "Wage_YoY": "us_wage_yoy", "Food_minus_wage": "us_food_affordability"}, "The experimental pressure measure publishes food and wage components rather than replacing them with a composite score.", rate_views),
        ("affordability-canada-purchasing-power", "Canadian household income, wages, and saving", "quarterly", {"Disposable_income_per_person": "ca_household-disposable-income-per-person", "Real_disposable_income_per_person": "ca_real-disposable-income-per-person", "Saving_rate": "ca_household-saving-rate"}, "Household income includes broader income and transfers; average wages describe employed workers. Quarterly values remain at their native frequency and are latest-vintage revised data.", ["raw", "indexed", "zscore"]),
        ("affordability-canada-food-income", "Canadian food prices relative to disposable income", "quarterly", {"Food_price_index": "ca_food-quarterly-index", "Grocery_price_index": "ca_grocery-quarterly-index", "Disposable_income_per_person": "ca_income-index", "Food_to_income": "ca_food-to-income", "Grocery_to_income": "ca_grocery-to-income"}, "Monthly consumer-price observations are averaged within completed quarters and compared with quarterly disposable income per person. No monthly income values are invented.", index_views),
        ("affordability-canada-food-wages", "Canadian food prices relative to wages", "monthly", {"Food_YoY": "ca_food-monthly-yoy", "Grocery_YoY": "ca_grocery-monthly-yoy", "Hourly_wage_YoY": "ca_nominal-wage-growth", "Food_wage_gap": "ca_food-to-wage", "Grocery_wage_gap": "ca_grocery-to-wage"}, "Monthly wage-based pressure differs from household-income affordability because wages cover employed workers while disposable income includes other income and transfers.", rate_views),
        ("affordability-canada-housing-income", "Canadian housing costs relative to disposable income", "quarterly", {"NHPI": "ca_nhpi-quarterly-index", "Rent": "ca_rent-quarterly-index", "Shelter": "ca_shelter-quarterly-index", "Mortgage_interest": "ca_mortgage-quarterly-index", "Disposable_income": "ca_income-index"}, "Purchase prices, rent, shelter services, mortgage interest, and income are separate quarterly-aligned series normalized to 100 in 2017 Q1.", index_views),
        ("affordability-canada-housing-ratios", "Canadian housing affordability ratios", "quarterly", {"NHPI_to_income": "ca_nhpi-to-income", "Rent_to_income": "ca_rent-to-income", "Shelter_to_income": "ca_shelter-to-income", "Mortgage_interest_to_income": "ca_mortgage-interest-to-income"}, "Each ratio uses the same fixed 2017 Q1 reference and is published separately; there is no combined housing-stress score.", index_views),
        ("affordability-canada-housing-gaps", "Canadian housing cost and income growth gaps", "quarterly", {"NHPI_gap": "ca_nhpi-income-gap", "Rent_gap": "ca_rent-income-gap", "Shelter_gap": "ca_shelter-income-gap", "Mortgage_interest_gap": "ca_mortgage-income-gap"}, "Positive values mean the specified housing cost grew faster than disposable income per person over the prior year.", rate_views),
        ("affordability-canada-property-income", "Official Canadian residential property evidence and income", "quarterly", {"Six_CMA_broad_RPPI": "ca_six-cma-residential-property-price-index", "Toronto_new_condominiums": "ca_toronto-new-condominium-price-index", "Ottawa_new_condominiums": "ca_ottawa-new-condominium-price-index", "Calgary_new_condominiums": "ca_calgary-new-condominium-price-index", "Edmonton_new_condominiums": "ca_edmonton-new-condominium-price-index", "Disposable_income": "ca_income-index"}, "The broad RPPI is an inactive six-CMA history ending in 2021 Q4. Active condominium series cover new apartments only and are not spliced to it.", index_views),
        ("affordability-canada-wages", "Canada and Ontario wage histories", "monthly", {"Canada_hourly": "ca_average-hourly-wages", "Ontario_hourly": "ca_ontario-average-hourly-wages", "Canada_weekly": "ca_average-weekly-earnings", "Ontario_weekly": "ca_ontario-average-weekly-earnings"}, "Hourly wages are unadjusted LFS estimates; weekly earnings are separate seasonally adjusted SEPH confirmation measures. Their levels should not be compared on one raw axis.", index_views),
    ]
    series["fao_food_nominal_yoy"] = _yoy(series["fao_food_nominal"], "FAO_FOOD_YOY", "FAO Food Price Index growth")
    series["fao_cereals_nominal_yoy"] = _yoy(series["fao_cereals_nominal"], "FAO_CEREALS_YOY", "FAO cereals growth")
    series["fao_dairy_nominal_yoy"] = _yoy(series["fao_dairy_nominal"], "FAO_DAIRY_YOY", "FAO dairy growth")
    series["ca_bakery_yoy"] = _yoy(series["ca_bakery-cereals-cpi"], "CA_BAKERY_YOY", "Canada bakery and cereals CPI growth")
    series["us_bakery_yoy"] = _yoy(series["us_cereals-bakery-cpi"], "US_BAKERY_YOY", "U.S. cereals and bakery CPI growth")
    series["ca_dairy_yoy"] = _yoy(series["ca_dairy-eggs-cpi"], "CA_DAIRY_YOY", "Canada dairy and eggs CPI growth")
    series["us_dairy_yoy"] = _yoy(series["us_dairy-cpi"], "US_DAIRY_YOY", "U.S. dairy CPI growth")
    series["us_wage_yoy"] = wage_yoy
    for dataset_id, title, frequency, mapping, note, transformations in chart_specs:
        rows = _chart_rows(series, mapping)
        chart_series = [_series(key, series[source].label, series[source].unit, series[source].source, "derived" if "yoy" in source or "income" in source else "measured", default_visible=index < 5, frequency=series[source].frequency, transformations=transformations) for index, (key, source) in enumerate(mapping.items())]
        payload = _dataset(dataset_id, title, note, frequency, chart_series, rows, transformations, "Contextual indicator", {"formula": "Published indices and explicitly labelled derived changes; no interpolation across native frequencies.", "notes": note}, "", generated_at, reference_period=("2000-01-01", "2019-12-01"))
        _write_chart(root, payload)

    transmission_pairs = [
        ("FAO overall to Canada groceries", _yoy(series["fao_food_nominal"], "x", "FAO food growth"), series["ca_grocery_yoy"]),
        ("FAO overall to U.S. food at home", _yoy(series["fao_food_nominal"], "x", "FAO food growth"), series["us_home_yoy"]),
        ("FAO cereals to Canada bakery/cereals", _yoy(series["fao_cereals_nominal"], "x", "FAO cereals growth"), _yoy(series["ca_bakery-cereals-cpi"], "x", "Canada bakery/cereals growth")),
        ("FAO cereals to U.S. cereals/bakery", _yoy(series["fao_cereals_nominal"], "x", "FAO cereals growth"), _yoy(series["us_cereals-bakery-cpi"], "x", "U.S. cereals/bakery growth")),
        ("FAO dairy to Canada dairy/eggs", _yoy(series["fao_dairy_nominal"], "x", "FAO dairy growth"), _yoy(series["ca_dairy-eggs-cpi"], "x", "Canada dairy/eggs growth")),
        ("FAO dairy to U.S. dairy", _yoy(series["fao_dairy_nominal"], "x", "FAO dairy growth"), _yoy(series["us_dairy-cpi"], "x", "U.S. dairy growth")),
        ("FAO vegetable oils to Canada food", _yoy(series["fao_oils_nominal"], "x", "FAO vegetable oils growth"), series["ca_food_yoy"]),
        ("FAO vegetable oils to U.S. food at home", _yoy(series["fao_oils_nominal"], "x", "FAO vegetable oils growth"), series["us_home_yoy"]),
    ]
    transmission = [_transmission_row(*pair) for pair in transmission_pairs]
    write_csv(root / "analysis" / "food_price_transmission_summary.csv", transmission)
    (root / "website" / "public" / "generated" / "food-transmission-analysis.json").write_text(json.dumps({"schemaVersion": 1, "generatedAt": generated_at, "lagConvention": "positive lag means the international commodity index is observed before the domestic consumer-price index", "rows": transmission}, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    strongest = max(transmission, key=lambda row: abs(float(row.get("peak_lag_correlation") or 0)))
    findings = f"""# Food And Housing Affordability Evidence

International food commodity prices, domestic consumer food prices, residential property purchase prices, and current shelter costs remain separate evidence layers.

The strongest descriptive food transmission relationship in the implemented set is **{strongest['relationship']}**, with peak lag correlation {float(strongest['peak_lag_correlation']):.3f} at {strongest['peak_lag_months']} months. This is a latest-vintage association, not a causal estimate. Retail transmission also depends on exchange rates, energy and transport, fertilizer and farm inputs, processing, labour, wholesale and retail margins, domestic supply, taxes, and regulation.

Canada's food inflation, grocery inflation, income-growth, and wage-growth gaps are available alongside food-, grocery-, rent-, shelter-, mortgage-interest-, and NHPI-to-income indexes. Quarterly income comparisons include completed quarters only; monthly wage comparisons remain monthly. U.S. food-to-wage, rent-to-wage, real FHFA, and house-price-to-income measures remain published with their components.

BIS world, advanced-economy, and emerging-market property-price aggregates cover participating national series; they are not measurements of every house in the world. Statistics Canada NHPI measures new-property purchase prices, while rent, mortgage-interest cost, replacement cost, and shelter CPI measure distinct current housing costs. The official broad RPPI covers six CMAs and is inactive after 2021 Q4; active new-condominium indexes are narrower and are not spliced to it.
"""
    (root / "analysis" / "food_housing_affordability_findings.md").write_text(findings, encoding="utf-8")
    (root / "analysis" / "food_housing_indicator_catalogue.csv").write_text("", encoding="utf-8")
    catalogue = [{"id": item["id"], "label": item["label"], "geography": item["geography"], "layer": item["layer"], "source": item["source"], "source_identifier": item["sourceIdentifier"], "frequency": item["frequency"], "unit": item["unit"], "start_date": item["startDate"], "latest_date": item["endDate"], "revision_status": item["revisionStatus"], "future_classifier_status": item["futureClassifierMetadata"]["status"]} for group in payload_groups.values() for item in group]
    write_csv(root / "analysis" / "food_housing_indicator_catalogue.csv", catalogue)
    income_catalogue = []
    for spec in STATCAN_PURCHASING_POWER_SPECS:
        vector, indicator_id, label, geography, frequency, unit, seasonal, nominal_real, _, table = spec
        source = series[f"ca_{indicator_id}"]
        income_catalogue.append({
            "indicator_name": label, "source_table": table, "vector_id": f"v{vector}", "definition": income_sources[indicator_id],
            "geography": geography, "frequency": frequency, "unit": unit, "seasonal_adjustment": seasonal,
            "annualized_or_native_flow": "seasonally adjusted annual rate" if "annual rates" in seasonal else "native observation",
            "nominal_or_real": nominal_real, "revision_behaviour": source.revision_notes,
            "start_date": source.observations[0].date, "latest_date": source.observations[-1].date,
            "retrieval_date": source.retrieval_date, "intended_use": "purchasing-power denominator or confirmation series",
            "limitations": "Latest-vintage history; release-time fields are retained but a complete real-time vintage archive is not available.",
        })
    for spec in STATCAN_PROPERTY_AUDIT_SPECS:
        vector, indicator_id, label, geography, _, table, coverage = spec
        source = series[f"ca_{indicator_id}"]
        income_catalogue.append({
            "indicator_name": label, "source_table": table, "vector_id": f"v{vector}", "definition": coverage,
            "geography": geography, "frequency": "quarterly", "unit": "index, 2017=100", "seasonal_adjustment": "not seasonally adjusted",
            "annualized_or_native_flow": "native quarterly index", "nominal_or_real": "nominal property purchase price",
            "revision_behaviour": source.revision_notes, "start_date": source.observations[0].date, "latest_date": source.observations[-1].date,
            "retrieval_date": source.retrieval_date, "intended_use": "broader official property-price audit and historical comparison",
            "limitations": "Broad RPPI is inactive; active NCAPI covers new condominium apartments only. Neither is a Canada- or Ontario-wide resale index.",
        })
    write_csv(root / "analysis" / "canadian_income_indicator_catalogue.csv", income_catalogue)
    audit = f"""# Canadian Income, Wage, And Property-Price Source Audit

## Implemented Sources

- **Table 36-10-0112-01:** household disposable income (`v62305981`), household final consumption expenditure (`v62305982`), and household saving rate (`v62305984`), quarterly from 1961. Income and consumption are seasonally adjusted annual rates in millions of current Canadian dollars.
- **Table 17-10-0009-01:** Canada quarterly population (`v1`) from 1971. It is matched to the same quarter as income; no monthly population or income values are created.
- **Table 14-10-0063-01:** Canada and Ontario average hourly wage rates for all employees (`v2132579`, `v2153099`) and goods/services confirmation series, monthly from 1997, unadjusted for seasonality.
- **Table 14-10-0223-01:** Canada and Ontario average weekly earnings (`v79311153`, `v79311309`), monthly from 2001, seasonally adjusted. These SEPH estimates confirm rather than replace LFS hourly wages.
- **Table 18-10-0169-01:** archived broad residential property price indexes for a six-CMA composite, Ottawa, Toronto, and Calgary from 2017 Q1 through 2021 Q4. The source includes new and resale transactions but is inactive and has no Canada or Ontario aggregate.
- **Table 18-10-0273-01:** active new condominium apartment price indexes for Ottawa, Toronto, Calgary, and Edmonton from 2017 Q1. These cover new condominium apartments only.

## Definitions And Alignment

Disposable income per person divides the annual-rate household-income flow by the matching quarterly population. The result is therefore annualized CAD per person; it is not divided by four. Real disposable income per person is a transparent CPI-deflated derivative because no directly published national quarterly real-per-person series with the required history was identified.

Monthly CPI and housing indexes are averaged from all three months of each completed quarter before comparison with income. Missing or partial quarters are omitted. Quarterly income is never forward-filled or interpolated to monthly frequency. Wage-based affordability remains monthly and is analytically separate because average wages describe employed workers, while household disposable income includes broader income and transfers.

## Property-Price Finding

No active official broad Canada- or Ontario-wide transaction-price index was identified in the audited Statistics Canada tables. NHPI remains the current national new-housing measure. The inactive six-CMA RPPI and active metro new-condominium indexes are published separately and are not spliced into one history.

## Remaining Gaps

No directly published national quarterly real disposable-income-per-person series with the required history was identified. Ontario quarterly household income is available only through newer distributional household-account products with shorter coverage and a different analytical construction, so it is not mixed with the national accounts denominator in this release. A consistent monthly permanent-employee wage history was not added; the LFS all-employee hourly wage remains the primary wage measure and SEPH weekly earnings are a separate confirmation series.

## Later Classifier Candidates

The generated metadata marks, but does not evaluate, candidate evidence for food prices outgrowing disposable income or wages; rent, shelter, and mortgage-interest costs outgrowing income; residential property prices diverging from income; declining real disposable income per person; and a falling saving rate alongside rising essential costs. Calibration and historical validation belong to a later classifier task.

## Revisions And Vintages

All histories are latest-vintage Statistics Canada observations retrieved at pipeline generation. Per-observation release dates are retained where supplied, but the project does not yet hold complete real-time vintages for national accounts, population, or LFS wages. National accounts and population can undergo historical revisions; current LFS wage estimates can also be revised and are composition-sensitive.
"""
    (root / "analysis" / "canadian_income_data_audit.md").write_text(audit, encoding="utf-8")
    _append_manifests(root, payload_groups)
    return [item for group in payload_groups.values() for item in group], transmission
