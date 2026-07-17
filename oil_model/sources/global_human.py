from __future__ import annotations

import csv
import gzip
import io
import zipfile
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

from ..cache import RawCache


WPP_DEMOGRAPHY_URL = "https://population.un.org/wpp/assets/Excel%20Files/1_Indicator%20(Standard)/CSV_FILES/WPP2024_Demographic_Indicators_Medium.csv.gz"
WPP_AGE_URL = "https://population.un.org/wpp/assets/Excel%20Files/1_Indicator%20(Standard)/CSV_FILES/WPP2024_PopulationByAge5GroupSex_Medium.csv.gz"
FAO_SECURITY_URL = "https://bulks-faostat.fao.org/production/Food_Security_Data_E_All_Data_(Normalized).zip"
FAO_DIET_URL = "https://bulks-faostat.fao.org/production/Cost_Affordability_Healthy_Diet_(CoAHD)_E_All_Data_(Normalized).zip"
WHO_DEATHS_URL = "https://cdn.who.int/media/docs/default-source/gho-documents/global-health-estimates/ghe2021_deaths_global_new2.xlsx?sfvrsn=e1f725b1_3"
WHO_DALY_URL = "https://cdn.who.int/media/docs/default-source/gho-documents/global-health-estimates/ghe2021_daly_global_new.xlsx?sfvrsn=cbefe871_3"


FOOD_PAIRS = {
    "undernourishment": (
        "Prevalence of undernourishment (percent) (annual value)",
        "Number of people undernourished (million) (annual value)",
        "Population undernourished",
    ),
    "moderate_or_severe_food_insecurity": (
        "Prevalence of moderate or severe food insecurity in the total population (percent) (annual value)",
        "Number of moderately or severely food insecure people (million) (annual value)",
        "Moderate or severe food insecurity",
    ),
    "severe_food_insecurity": (
        "Prevalence of severe food insecurity in the total population (percent) (annual value)",
        "Number of severely food insecure people (million) (annual value)",
        "Severe food insecurity",
    ),
}

NUTRITION_PAIRS = {
    "child_stunting": (
        "Percentage of children under 5 years of age who are stunted (modelled estimates) (percent)",
        "Number of children under 5 years of age who are stunted (modeled estimates) (million)",
        "Child stunting",
        "Children under 5",
        "Both sexes",
    ),
    "child_wasting": (
        "Percentage of children under 5 years affected by wasting (percent)",
        "Number of children under 5 years affected by wasting (million)",
        "Child wasting",
        "Children under 5",
        "Both sexes",
    ),
    "anaemia_women": (
        "Prevalence of anemia among women of reproductive age (15-49 years) (percent)",
        "Number of women of reproductive age (15-49 years) affected by anemia (million)",
        "Anaemia among women aged 15-49",
        "15-49 years",
        "Female",
    ),
    "low_birth_weight": (
        "Prevalence of low birthweight (percent)",
        "Number of newborns with low birthweight (million)",
        "Low birth weight",
        "Newborns",
        "Both sexes",
    ),
}


def _number(value: str | None) -> tuple[float | None, str | None]:
    if value in (None, "", "..", "..."):
        return None, None
    text = str(value).strip()
    bound = "upper-bound" if text.startswith("<") else "lower-bound" if text.startswith(">") else None
    try:
        return float(text.lstrip("<>")), bound
    except ValueError:
        return None, None


def _fao_rows(path: Path) -> list[dict[str, str]]:
    with zipfile.ZipFile(path) as archive:
        member = next(name for name in archive.namelist() if name.endswith("(Normalized).csv"))
        with archive.open(member) as raw:
            return [row for row in csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8-sig")) if row.get("Area") == "World"]


def _latest_release(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """Keep the newest release when a FAOSTAT bulk file retains overlapping vintages."""
    selected: dict[tuple[str, str, str], dict[str, str]] = {}
    for row in rows:
        key = (row["Item"], row["Year"], row.get("Element", "Value"))
        release = row.get("Release", "")
        current = selected.get(key)
        if current is None or release.startswith("July 2025") or release > current.get("Release", ""):
            selected[key] = row
    return list(selected.values())


def _paired_rows(
    rows: list[dict[str, str]],
    specs: dict[str, tuple[Any, ...]],
    *,
    source: str,
    source_url: str,
    revision: str,
) -> list[dict[str, Any]]:
    by_item_year = {(row["Item"], row["Year"]): row for row in rows if row.get("Element") == "Value"}
    bounds = {(row["Item"], row["Year"], row.get("Element")): row for row in rows if "bound" in row.get("Element", "").lower()}
    output: list[dict[str, Any]] = []
    for indicator, spec in specs.items():
        rate_name, count_name, label, *demographics = spec
        years = sorted({year for item, year in by_item_year if item in {rate_name, count_name}})
        for year in years:
            rate_row = by_item_year.get((rate_name, year), {})
            count_row = by_item_year.get((count_name, year), {})
            rate, rate_bound = _number(rate_row.get("Value"))
            count, count_bound = _number(count_row.get("Value"))
            lower, _ = _number(bounds.get((rate_name, year, "Confidence interval: Lower bound"), {}).get("Value"))
            upper, _ = _number(bounds.get((rate_name, year, "Confidence interval: Upper bound"), {}).get("Value"))
            if rate is None and count is None:
                continue
            denominator = count * 100 / rate if count is not None and rate else None
            flags = sorted({value for value in (rate_row.get("Flag"), count_row.get("Flag")) if value})
            output.append({
                "geography": "World",
                "year": int(year),
                "indicator": indicator,
                "label": label,
                "prevalence_or_rate": rate,
                "rate_unit": "percent",
                "affected_person_count": count,
                "count_unit": "million persons",
                "denominator_population": denominator,
                "denominator_unit": "million persons",
                "age_group": demographics[0] if demographics else "All ages",
                "sex": demographics[1] if len(demographics) > 1 else "Both sexes",
                "estimate_type": "modelled estimate" if "X" in flags else "FAOSTAT estimate",
                "source": source,
                "source_url": source_url,
                "revision": revision,
                "uncertainty_lower": lower,
                "uncertainty_upper": upper,
                "limitations": "Official global aggregate. Rates, counts, and modelled uncertainty intervals may be revised.",
                "rate_bound": rate_bound,
                "count_bound": count_bound,
                "source_flag": ";".join(flags),
            })
    return output


def _xlsx_values(path: Path, sheet: int) -> list[dict[str, str]]:
    with zipfile.ZipFile(path) as archive:
        shared = [
            "".join(node.text or "" for node in item.iter() if node.tag.endswith("}t"))
            for item in ElementTree.fromstring(archive.read("xl/sharedStrings.xml"))
        ]
        root = ElementTree.fromstring(archive.read(f"xl/worksheets/sheet{sheet}.xml"))
    output = []
    for row in root.iter():
        if not row.tag.endswith("}row"):
            continue
        values: dict[str, str] = {}
        for cell in row:
            if not cell.tag.endswith("}c"):
                continue
            raw = next((node.text for node in cell if node.tag.endswith("}v")), None)
            if raw is None:
                continue
            column = "".join(character for character in str(cell.attrib.get("r", "")) if character.isalpha())
            values[column] = shared[int(raw)] if cell.attrib.get("t") == "s" else raw
        output.append(values)
    return output


class GlobalHumanImpactAdapter:
    def __init__(self, cache: RawCache) -> None:
        self.cache = cache
        self.retrieved_at = datetime.now(UTC).isoformat(timespec="seconds")

    def fetch(self) -> dict[str, list[dict[str, Any]]]:
        demography = self._demography(
            self.cache.fetch(WPP_DEMOGRAPHY_URL, "global_human/WPP2024_Demographic_Indicators_Medium.csv.gz"),
            self.cache.fetch(WPP_AGE_URL, "global_human/WPP2024_PopulationByAge5GroupSex_Medium.csv.gz"),
        )
        security_rows = _latest_release(_fao_rows(self.cache.fetch(FAO_SECURITY_URL, "global_human/fao_food_security_normalized.zip")))
        diet_rows = _latest_release(_fao_rows(self.cache.fetch(FAO_DIET_URL, "global_human/fao_healthy_diet_normalized.zip")))
        food_security = _paired_rows(
            security_rows, FOOD_PAIRS, source="FAOSTAT Suite of Food Security Indicators",
            source_url="https://www.fao.org/faostat/en/#data/FS",
            revision="FAOSTAT normalized bulk release retrieved " + self.retrieved_at[:10],
        )
        food_security.extend(self._healthy_diet(diet_rows))
        food_security.extend(self._dietary_energy(security_rows))
        nutrition = _paired_rows(
            security_rows, NUTRITION_PAIRS,
            source="UNICEF/WHO/World Bank Joint Malnutrition Estimates and WHO indicators distributed by FAOSTAT",
            source_url="https://data.unicef.org/resources/dataset/malnutrition-data/",
            revision="FAOSTAT normalized bulk release; underlying inter-agency modelled estimates are revised when source methods or country data change.",
        )
        mortality = self._mortality(
            self.cache.fetch(WHO_DEATHS_URL, "global_human/who_ghe2021_deaths_global.xlsx"),
            self.cache.fetch(WHO_DALY_URL, "global_human/who_ghe2021_daly_global.xlsx"),
        )
        return {"demography": demography, "food_security": food_security, "nutrition": nutrition, "human_impact": mortality}

    def _demography(self, demographic_path: Path, age_path: Path) -> list[dict[str, Any]]:
        base: dict[int, dict[str, Any]] = {}
        with gzip.open(demographic_path, "rt", encoding="utf-8-sig") as handle:
            for row in csv.DictReader(handle):
                if row.get("Location") != "World":
                    continue
                year = int(row["Time"])
                if year > datetime.now(UTC).year:
                    continue
                base[year] = {
                    "total_population": float(row["TPopulation1July"]) / 1000,
                    "annual_population_growth_rate": float(row["PopGrowthRate"]),
                    "annual_population_increase": float(row["PopChange"]) / 1000,
                    "births": float(row["Births"]) / 1000,
                    "estimate_type": "WPP estimate" if year <= 2023 else "WPP medium projection",
                }
        ages: dict[int, dict[str, float]] = defaultdict(lambda: {"under_five": 0.0, "working_age": 0.0})
        with gzip.open(age_path, "rt", encoding="utf-8-sig") as handle:
            for row in csv.DictReader(handle):
                if row.get("Location") != "World":
                    if ages:
                        break
                    continue
                year = int(row["Time"])
                if year not in base:
                    continue
                start = int(row["AgeGrpStart"])
                value = float(row["PopTotal"]) / 1000
                if start == 0:
                    ages[year]["under_five"] += value
                if 15 <= start < 65:
                    ages[year]["working_age"] += value
        output = []
        labels = {
            "total_population": ("Total population", "All ages"),
            "annual_population_growth_rate": ("Annual population growth rate", "All ages"),
            "annual_population_increase": ("Annual population increase", "All ages"),
            "births": ("Births", "Births during year"),
            "under_five": ("Population under age five", "0-4 years"),
            "working_age": ("Working-age population", "15-64 years"),
        }
        for year, values in sorted(base.items()):
            values.update(ages.get(year, {}))
            for indicator, (label, age_group) in labels.items():
                value = values.get(indicator)
                if value is None:
                    continue
                is_rate = indicator == "annual_population_growth_rate"
                output.append({
                    "geography": "World", "year": year, "indicator": indicator, "label": label,
                    "prevalence_or_rate": value if is_rate else None,
                    "rate_unit": "percent annual growth" if is_rate else None,
                    "affected_person_count": None if is_rate else value,
                    "count_unit": None if is_rate else "million persons",
                    "denominator_population": values["total_population"], "denominator_unit": "million persons",
                    "age_group": age_group, "sex": "Both sexes", "estimate_type": values["estimate_type"],
                    "source": "United Nations World Population Prospects 2024", "source_url": "https://population.un.org/wpp/",
                    "revision": "WPP 2024 revision; 2024 onward is the medium projection, not an observed population count.",
                    "uncertainty_lower": None, "uncertainty_upper": None,
                    "limitations": "Urban and rural population are not included in this first release. Population growth is demographic exposure and never hardship by itself.",
                })
        return output

    def _healthy_diet(self, rows: list[dict[str, str]]) -> list[dict[str, Any]]:
        mapping = {
            "Cost of a healthy diet (CoHD), PPP dollar per person per day": "cost_of_healthy_diet",
            "Prevalence of unaffordability (PUA), percent": "healthy_diet_unaffordable",
            "Number of people unable to afford a healthy diet (NUA), million": "healthy_diet_unaffordable",
        }
        by_year: dict[tuple[str, int], dict[str, Any]] = defaultdict(dict)
        releases: dict[tuple[str, int], str] = {}
        for row in rows:
            indicator = mapping.get(row["Item"])
            if not indicator:
                continue
            year = int(row["Year"])
            value, bound = _number(row["Value"])
            target = "cost" if indicator == "cost_of_healthy_diet" else "rate" if row["Unit"] == "%" else "count"
            by_year[(indicator, year)][target] = value
            by_year[(indicator, year)][target + "_bound"] = bound
            releases[(indicator, year)] = row.get("Release", "")
        output = []
        for (indicator, year), values in sorted(by_year.items()):
            is_cost = indicator == "cost_of_healthy_diet"
            output.append({
                "geography": "World", "year": year, "indicator": indicator,
                "label": "Cost of a healthy diet" if is_cost else "Unable to afford a healthy diet",
                "prevalence_or_rate": values.get("cost") if is_cost else values.get("rate"),
                "rate_unit": "international dollars (PPP) per person per day" if is_cost else "percent",
                "affected_person_count": values.get("count"), "count_unit": "million persons" if not is_cost else None,
                "denominator_population": values.get("count") * 100 / values.get("rate") if values.get("count") is not None and values.get("rate") else None,
                "denominator_unit": "million persons", "age_group": "All ages", "sex": "Both sexes",
                "estimate_type": "FAO estimate", "source": "FAOSTAT Cost and Affordability of a Healthy Diet",
                "source_url": "https://www.fao.org/faostat/en/#data/CAHD", "revision": releases.get((indicator, year)),
                "uncertainty_lower": None, "uncertainty_upper": None,
                "limitations": "PPP-dollar cost and affordability estimates are revised across SOFI releases and do not describe one universal retail basket.",
            })
        return output

    def _dietary_energy(self, rows: list[dict[str, str]]) -> list[dict[str, Any]]:
        item = "Dietary energy supply used in the estimation of the prevalence of undernourishment (kcal/cap/day)"
        output = []
        for row in rows:
            if row["Item"] != item:
                continue
            value, _ = _number(row["Value"])
            if value is None:
                continue
            output.append({
                "geography": "World", "year": int(row["Year"]), "indicator": "dietary_energy_supply", "label": "Dietary energy supply per person",
                "prevalence_or_rate": value, "rate_unit": "kcal per person per day", "affected_person_count": None, "count_unit": None,
                "denominator_population": None, "denominator_unit": None, "age_group": "All ages", "sex": "Both sexes",
                "estimate_type": "FAOSTAT estimate", "source": "FAOSTAT Suite of Food Security Indicators", "source_url": "https://www.fao.org/faostat/en/#data/FS",
                "revision": "FAOSTAT normalized bulk release", "uncertainty_lower": None, "uncertainty_upper": None,
                "limitations": "Food supply availability is not the same as equitable household access or individual dietary intake.",
            })
        return output

    def _mortality(self, deaths_path: Path, daly_path: Path) -> list[dict[str, Any]]:
        years = [2021, 2020, 2019, 2015, 2010, 2000]
        output = []
        for measure, path in (("deaths", deaths_path), ("dalys", daly_path)):
            for sheet, year in zip(range(4, 10), years):
                rows = _xlsx_values(path, sheet)
                population = next((float(row["G"]) for row in rows if row.get("A") == "Population (thousands)"), None)
                for row in rows:
                    code = row.get("A")
                    if code not in {"540", "550"} or "G" not in row:
                        continue
                    indicator = "nutritional_deficiency" if code == "540" else "protein_energy_malnutrition"
                    value = float(row["G"])
                    is_death = measure == "deaths"
                    output.append({
                        "geography": "World", "year": year,
                        "indicator": f"{indicator}_{measure}",
                        "label": ("Nutritional-deficiency" if code == "540" else "Protein-energy-malnutrition") + (" deaths" if is_death else " DALYs"),
                        "prevalence_or_rate": value / population * 100 if is_death and population else None,
                        "rate_unit": "deaths per 100,000 persons" if is_death else None,
                        "affected_person_count": value / 1_000 if is_death else value / 1_000_000,
                        "count_unit": "thousand deaths" if is_death else "million DALYs",
                        "denominator_population": population / 1_000 if population else None, "denominator_unit": "million persons",
                        "age_group": "All ages", "sex": "Both sexes", "estimate_type": "WHO modelled estimate",
                        "source": "WHO Global Health Estimates 2021", "source_url": "https://www.who.int/data/global-health-estimates/",
                        "revision": "GHE 2021 release published in 2024; estimates are not comparable with earlier GHE releases.",
                        "uncertainty_lower": None, "uncertainty_upper": None,
                        "limitations": "Direct cause-coded nutritional-deficiency estimates do not capture the wider mortality or disability statistically attributable to undernutrition.",
                    })
        return sorted(output, key=lambda row: (row["indicator"], row["year"]))
