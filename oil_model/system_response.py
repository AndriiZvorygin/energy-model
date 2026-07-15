from __future__ import annotations

import math
import textwrap
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import numpy as np

from .adapters import Series
from .storage import Row


LAYERS = [
    "Physical energy conditions",
    "Energy affordability and financial conditions",
    "Production, consumption, and investment response",
    "Labour and household consequences",
    "Social and institutional symptoms",
]


def _indicator(
    layer: str,
    indicator_id: str,
    name: str,
    definition: str,
    unit: str,
    frequency: str,
    source: str,
    status: str,
    stress_direction: str,
    likely_lag: str,
    alternatives: str,
    limitations: str,
    revisions: str = "Revised by source; latest-vintage data are not real-time vintages.",
    geography: str = "United States",
    evidence_label: str = "Contextual indicator",
) -> Row:
    return {
        "layer": layer,
        "indicator_id": indicator_id,
        "indicator": name,
        "exact_definition": definition,
        "unit": unit,
        "frequency": frequency,
        "geography": geography,
        "source": source,
        "date_coverage": "Populated from the source cache when implemented",
        "revisions": revisions,
        "status": status,
        "expected_direction_during_energy_stress": stress_direction,
        "likely_lag": likely_lag,
        "alternative_explanations": alternatives,
        "data_quality_limitations": limitations,
        "evidence_label": evidence_label,
    }


def indicator_catalogue(series: dict[str, Series], core_rows: list[Row]) -> list[Row]:
    p, a, e, l, s = LAYERS
    rows = [
        _indicator(p, "petroleum_production_growth", "Petroleum production growth", "YoY growth in EIA U.S. crude-oil production.", "percent", "monthly", "EIA MER T03.01:PAPRPUS", "derived", "down", "0-12 months", "Weather, maintenance, regulation, capital discipline, geology.", "Domestic production is not global supply and monthly values are revised.", evidence_label="Contextual indicator"),
        _indicator(p, "petroleum_consumption_growth", "Petroleum consumption growth", "YoY growth in U.S. petroleum consumption excluding biofuels.", "percent", "monthly", "EIA MER T01.03:PMTCBUS", "derived", "down after tightening", "0-9 months", "Efficiency, substitution, weather, structural change.", "Consumption is an energy-content aggregate and is revised."),
        _indicator(p, "oil_consumption_per_person", "Oil consumption per person", "Monthly petroleum consumption divided by BEA population.", "million Btu per person", "monthly", "EIA PMTCBUS / FRED POPTHM", "derived", "down after affordability stress", "3-12 months", "Efficiency, demographics, travel patterns, electrification.", "Monthly population is estimated; aggregate petroleum includes non-transport uses."),
        _indicator(p, "crude_inventory", "Commercial crude inventory", "Average monthly U.S. commercial crude stocks excluding SPR.", "thousand barrels", "monthly from weekly", "EIA WCESTUS1", "measured", "down", "contemporaneous", "Imports, refinery runs, exports, pipeline timing.", "U.S.-only and monthly averaging hides weekly extremes."),
        _indicator(p, "comparative_inventory", "Comparative inventory", "Current inventory minus the prior five-year same-month mean.", "thousand barrels", "monthly", "Derived from EIA WCESTUS1", "derived", "down / deficit", "contemporaneous", "Changing storage capacity, exports, SPR policy, seasonality shifts.", "Five observations define each seasonal norm; not a global balance.", evidence_label="Validated relationship"),
        _indicator(p, "ci_zscore", "Comparative inventory z-score", "Comparative inventory divided by the prior five-year same-month standard deviation.", "standard deviations", "monthly", "Derived from EIA WCESTUS1", "derived", "down / negative", "contemporaneous", "Same alternatives as comparative inventory.", "Small seasonal reference sample can produce unstable z-scores.", evidence_label="Validated relationship"),
        _indicator(p, "refinery_utilization", "Refinery utilization", "Monthly average of weekly U.S. operable refinery capacity utilization.", "percent", "monthly from weekly", "EIA WPULEUS3", "measured", "up when refining is constrained", "contemporaneous", "Planned maintenance, hurricanes, outages, product demand.", "High utilization can reflect strong demand rather than scarcity."),
        _indicator(p, "spare_capacity_proxy", "Available spare-capacity proxy", "Global immediately available crude production capacity above current output.", "million barrels per day", "monthly", "EIA STEO / IEA / OPEC assessment", "proxy - missing in first release", "down", "0-6 months", "Quota policy, sanctions, quality mismatch.", "Definitions are model-based, revised, and not consistently available without licensed sources.", evidence_label="Experimental proxy", geography="Global"),
        _indicator(p, "futures_curve", "WTI futures-curve structure", "Second-minus-front or 12-month-minus-front WTI futures price.", "dollars per barrel", "daily/monthly", "CME/EIA documented futures series", "proxy - missing in first release", "more backwardation under tightness", "contemporaneous", "Interest, storage, hedging pressure, contract-specific flows.", "A clean redistributable continuous curve is not yet in the cache.", evidence_label="Experimental proxy"),
        _indicator(a, "real_wti", "Real WTI price", "WTI monthly price divided by CPI-U / 100.", "CPI-base dollars per barrel", "monthly", "FRED DCOILWTICO / CPIAUCSL", "derived", "up", "0-9 months", "Dollar moves, geopolitics, financial positioning.", "CPI is a broad deflator and monthly WTI averaging hides peaks.", evidence_label="Validated relationship"),
        _indicator(a, "household_energy_burden", "Household energy expenditure share", "Nominal PCE energy goods and services divided by disposable personal income.", "percent", "monthly SAAR", "BEA via FRED DNRGRC1M027SBEA / DSPI", "derived", "up", "0-12 months", "Weather, efficiency, regulated utility prices, income transfers.", "Aggregate share masks household distribution and both inputs are revised.", evidence_label="Experimental proxy"),
        _indicator(a, "energy_gdp_burden", "Energy expenditure share of GDP", "Nominal PCE energy goods and services divided by nominal GDP.", "percent", "monthly/quarterly aligned", "BEA via FRED DNRGRC1M027SBEA / GDP", "derived", "up", "0-12 months", "Economic composition, weather, efficiency, trade exposure.", "Quarterly GDP is carried within quarter and is not release-vintage safe.", evidence_label="Experimental proxy"),
        _indicator(a, "energy_cpi", "Energy CPI", "CPI-U energy index and its YoY growth.", "index / percent", "monthly", "BLS via FRED CPIENGSL", "measured", "up", "0-6 months", "Utility regulation, taxes, refining margins, weather.", "Volatile basket; weights and seasonal factors can change."),
        _indicator(a, "real_disposable_income", "Real disposable personal income", "Inflation-adjusted aggregate disposable personal income and YoY growth.", "billions chained dollars / percent", "monthly", "BEA via FRED DSPIC96", "measured", "down", "0-12 months", "Fiscal transfers, taxes, wages, non-energy inflation.", "Aggregate measure masks distribution and is revised."),
        _indicator(a, "fed_funds", "Federal funds rate", "Effective federal funds rate.", "percent", "monthly", "Federal Reserve via FRED FEDFUNDS", "measured", "often up during inflation response", "0-24 months", "Monetary policy responds to broad inflation and activity.", "Policy is endogenous, not a pure energy variable."),
        _indicator(a, "credit_tightening", "Bank credit tightening", "Net share of banks tightening C&I loan standards.", "net percent", "quarterly", "Federal Reserve SLOOS via FRED DRTSCILM", "measured", "up", "3-18 months", "Bank capital, defaults, regulation, monetary policy.", "Survey series is quarterly and can be revised."),
        _indicator(a, "gm2_yoy", "Global M2 growth", "YoY growth in USD-converted U.S., euro-area, China and Japan M2.", "percent", "monthly", "Project G4 GM2 aggregate", "derived", "ambiguous; weakening reduces support", "leads oil about 5 months", "FX conversion and jurisdiction-specific money definitions.", "Proxy rather than harmonized global liquidity.", evidence_label="Validated relationship", geography="G4 / global proxy"),
        _indicator(e, "industrial_production", "Industrial production", "Federal Reserve industrial production index and YoY growth.", "index / percent", "monthly", "Federal Reserve via FRED INDPRO", "measured", "down", "3-12 months", "Interest rates, inventories, exports, technology cycles.", "Revised and not a direct energy-causality measure.", evidence_label="Supported historical pattern"),
        _indicator(e, "manufacturing_output", "Manufacturing output", "Industrial production index for manufacturing and YoY growth.", "index / percent", "monthly", "Federal Reserve via FRED IPMAN", "measured", "down", "3-12 months", "Trade, inventory cycles, strikes, sector composition.", "Revised and excludes services."),
        _indicator(e, "real_consumer_spending", "Real consumer spending", "Real personal consumption expenditures and YoY growth.", "billions chained dollars / percent", "monthly", "BEA via FRED PCEC96", "measured", "down", "3-12 months", "Income, wealth, credit, fiscal policy, demographics.", "Aggregate and revised; services can offset goods weakness."),
        _indicator(e, "business_investment", "Business investment", "Real private nonresidential fixed investment and YoY growth.", "billions chained dollars / percent", "quarterly", "BEA via FRED PNFIC1", "measured", "down", "6-24 months", "Rates, taxes, technology, expected demand, policy.", "Quarterly and heavily revised."),
        _indicator(e, "real_gdp", "Real GDP growth", "YoY growth in real gross domestic product.", "percent", "quarterly", "BEA via FRED GDPC1", "derived", "down", "3-18 months", "Broad demand, policy, productivity, trade, inventories.", "Quarterly, revised, and not a real-time vintage."),
        _indicator(e, "productivity", "Labour productivity", "Nonfarm business output per hour and YoY growth.", "index / percent", "quarterly", "BLS via FRED OPHNFB", "measured", "ambiguous / often down", "6-24 months", "Technology, labour hoarding, composition, capital deepening.", "Cyclical denominator effects and substantial revisions."),
        _indicator(l, "average_weekly_hours", "Average weekly hours", "Average weekly hours of production and nonsupervisory manufacturing employees.", "hours", "monthly", "BLS via FRED AWHMAN", "measured", "down", "0-9 months", "Seasonality, strikes, sector mix, productivity.", "Manufacturing-only and revised.", evidence_label="Supported historical pattern"),
        _indicator(l, "temporary_help", "Temporary-help employment", "Payroll employment in temporary help services and YoY growth.", "thousand persons / percent", "monthly", "BLS via FRED TEMPHELPS", "measured", "down", "0-12 months", "Industry restructuring, staffing practices, regulation.", "Pandemic and classification shifts affect comparability.", evidence_label="Supported historical pattern"),
        _indicator(l, "full_time_share", "Full-time employment share", "Usually full-time employed divided by total civilian employment.", "percent", "monthly", "BLS CPS via FRED LNS12500000 / CE16OV", "derived", "down", "3-18 months", "Demographics, education, preferences, sector mix.", "Ratio of independently seasonally adjusted series."),
        _indicator(l, "involuntary_part_time_share", "Involuntary part-time share", "Part-time for economic reasons divided by total civilian employment.", "percent", "monthly", "BLS CPS via FRED LNS12032194 / CE16OV", "derived", "up", "3-18 months", "Labour supply, scheduling practices, classification changes.", "Ratio of independently seasonally adjusted survey estimates."),
        _indicator(l, "prime_age_employment", "Prime-age employment rate", "Employment-population ratio for ages 25-54.", "percent", "monthly", "BLS CPS via FRED LNS12300060", "measured", "down", "3-18 months", "Demographics, care work, disability, migration.", "Survey sampling error and revisions."),
        _indicator(l, "real_wage_growth", "Real hourly wage growth", "YoY growth in average hourly earnings deflated by CPI-U.", "percent", "monthly", "BLS via FRED CES0500000003 / CPIAUCSL", "derived", "down", "0-12 months", "Labour scarcity, composition, non-energy inflation.", "Composition bias; average hourly earnings exclude some workers."),
        _indicator(l, "consumer_sentiment", "Consumer sentiment", "University of Michigan consumer sentiment index.", "index", "monthly", "University of Michigan via FRED UMCSENT", "measured", "down", "0-9 months", "Politics, asset prices, inflation generally, media attention.", "Survey methodology and licensing constrain some uses."),
        _indicator(l, "credit_card_delinquency", "Credit-card delinquency", "Share of credit-card loan balances delinquent at commercial banks.", "percent", "quarterly", "Federal Reserve via FRED DRCCLACBS", "measured", "up", "6-24 months", "Credit standards, borrower mix, interest rates, reporting changes.", "Bank aggregate and quarterly; not household insolvency."),
        _indicator(l, "unemployment_rate", "Headline unemployment", "Civilian unemployment rate.", "percent", "monthly", "BLS via FRED UNRATE", "measured", "up", "6-18 months", "Broad demand, labour supply, participation, policy.", "Often lags turning points and misses employment quality."),
        _indicator(s, "food_insecurity", "Household food insecurity", "Share of households reporting low or very low food security.", "percent", "annual", "USDA Household Food Security report", "proposed - not implemented", "up", "6-24 months", "Housing costs, income, benefits, demographics.", "Annual lag and survey redesigns.", evidence_label="Scenario concept"),
        _indicator(s, "utility_arrears", "Utility arrears or disconnections", "Households behind on energy bills or disconnected for nonpayment.", "count / percent", "monthly/annual", "State regulators / Census household surveys", "proposed - fragmented", "up", "3-18 months", "Billing policy, weather, assistance programs.", "No harmonized long-run national series.", evidence_label="Scenario concept"),
        _indicator(s, "consumer_complaints", "Financial consumer complaints", "Complaints related to debt collection, credit and household finance.", "count / population", "monthly", "Consumer Financial Protection Bureau", "proposed - not implemented", "up", "6-24 months", "Awareness, reporting channels, regulation.", "Counts reflect reporting propensity and taxonomy changes.", evidence_label="Scenario concept"),
        _indicator(s, "institutional_trust", "Institutional trust", "Survey confidence in major institutions.", "survey percent", "annual/biennial", "GSS or comparable public survey", "scenario concept", "down", "12-36 months", "Politics, scandals, media, cohort effects.", "Sparse frequency and weak direct energy identification.", evidence_label="Scenario concept"),
        _indicator(s, "social_disruption", "Social disruption events", "Documented strikes, protests, or disruptions potentially linked to affordability.", "event count", "event-based", "Multiple event datasets", "scenario concept", "up", "variable", "Politics, repression, organization, non-energy grievances.", "Attribution and cross-time consistency are difficult.", evidence_label="Scenario concept"),
    ]

    coverage = {key: _coverage(value) for key, value in series.items()}
    coverage.update(_derived_coverage(core_rows))
    for row in rows:
        if row["indicator_id"] in coverage:
            row["date_coverage"] = coverage[row["indicator_id"]]
    return rows


def _coverage(series: Series) -> str:
    return f"{series.observations[0][0]} to {series.observations[-1][0]}" if series.observations else "unavailable"


def _derived_coverage(rows: list[Row]) -> dict[str, str]:
    mapping = {
        "petroleum_production_growth": "petroleum_production_YoY",
        "petroleum_consumption_growth": "petroleum_consumption_YoY",
        "oil_consumption_per_person": "oil_consumption_per_person_mmbtu",
        "crude_inventory": "crude_inventory_kb",
        "comparative_inventory": "comparative_inventory_kb",
        "ci_zscore": "CI_zscore",
        "refinery_utilization": "refinery_utilization_pct",
        "real_wti": "real_WTI",
        "household_energy_burden": "household_energy_expenditure_share",
        "energy_gdp_burden": "energy_expenditure_share_gdp",
        "energy_cpi": "energy_CPI",
        "real_disposable_income": "real_disposable_income",
        "fed_funds": "fed_funds_rate",
        "credit_tightening": "credit_tightening_pct",
        "gm2_yoy": "GM2_YoY",
        "industrial_production": "Industrial_production_YoY",
        "manufacturing_output": "manufacturing_output_YoY",
        "real_consumer_spending": "real_consumer_spending_YoY",
        "business_investment": "business_investment_YoY",
        "real_gdp": "Real_GDP_growth",
        "productivity": "productivity_YoY",
        "average_weekly_hours": "average_weekly_hours",
        "temporary_help": "temporary_help_YoY",
        "full_time_share": "full_time_employment_share",
        "involuntary_part_time_share": "involuntary_part_time_share",
        "prime_age_employment": "prime_age_employment_rate",
        "real_wage_growth": "real_wage_growth",
        "consumer_sentiment": "consumer_sentiment",
        "credit_card_delinquency": "credit_card_delinquency_rate",
        "unemployment_rate": "unemployment_rate",
    }
    out = {}
    for indicator_id, field in mapping.items():
        dates = [str(row["month"]) for row in rows if _num(row.get(field)) is not None]
        if dates:
            out[indicator_id] = f"{dates[0]} to {dates[-1]}"
    return out


def build_core_dataset(base_rows: list[Row], series: dict[str, Series]) -> list[Row]:
    maps = {key: dict(value.observations) for key, value in series.items()}
    base = {str(row["month"]): row for row in base_rows}
    months = sorted(base)
    quarterly = {"GDP", "DRTSCILM", "PNFIC1", "OPHNFB", "DRCCLACBS", "GDPC1"}
    rows: list[Row] = []

    def value(key: str, month: str) -> float | None:
        if key not in maps:
            return None
        if month in maps[key]:
            return maps[key][month]
        if key in quarterly:
            prior = [period for period in maps[key] if period <= month]
            return maps[key][max(prior)] if prior else None
        return None

    for month in months:
        source = base[month]
        consumption = value("PMTCBUS", month)
        population_thousand = value("POPTHM", month)
        energy_pce = value("DNRGRC1M027SBEA", month)
        dspi = value("DSPI", month)
        nominal_gdp = value("GDP", month)
        earnings = value("CES0500000003", month)
        cpi = _num(source.get("US_CPI"))
        full_time = value("LNS12500000", month)
        employed = value("CE16OV", month)
        involuntary_pt = value("LNS12032194", month)
        row = {
            "month": month,
            "petroleum_production": value("PAPRPUS", month),
            "petroleum_consumption": consumption,
            "oil_consumption_per_person_mmbtu": consumption * 1_000_000 / population_thousand if consumption is not None and population_thousand else None,
            "crude_inventory_kb": source.get("crude_inventory_kb"),
            "comparative_inventory_kb": source.get("comparative_inventory_kb"),
            "CI_zscore": source.get("CI_zscore"),
            "refinery_utilization_pct": value("WPULEUS3", month),
            "WTI": source.get("WTI"),
            "WTI_YoY": source.get("WTI_YoY"),
            "real_WTI": source.get("real_WTI"),
            "household_energy_expenditure_share": 100 * energy_pce / dspi if energy_pce is not None and dspi else None,
            "energy_expenditure_share_gdp": 100 * energy_pce / nominal_gdp if energy_pce is not None and nominal_gdp else None,
            "energy_CPI": value("CPIENGSL", month),
            "real_disposable_income": value("DSPIC96", month),
            "fed_funds_rate": value("FEDFUNDS", month),
            "credit_tightening_pct": value("DRTSCILM", month),
            "GM2_YoY": source.get("GM2_YoY"),
            "industrial_production": value("INDPRO", month),
            "manufacturing_output": value("IPMAN", month),
            "real_consumer_spending": value("PCEC96", month),
            "business_investment": value("PNFIC1", month),
            "real_gdp": value("GDPC1", month),
            "productivity": value("OPHNFB", month),
            "average_weekly_hours": value("AWHMAN", month),
            "temporary_help_employment": value("TEMPHELPS", month),
            "full_time_employment_share": 100 * full_time / employed if full_time is not None and employed else None,
            "involuntary_part_time_share": 100 * involuntary_pt / employed if involuntary_pt is not None and employed else None,
            "prime_age_employment_rate": value("LNS12300060", month),
            "real_hourly_wage": earnings / (cpi / 100) if earnings is not None and cpi else None,
            "consumer_sentiment": value("UMCSENT", month),
            "credit_card_delinquency_rate": value("DRCCLACBS", month),
            "unemployment_rate": value("UNRATE", month),
            "recession_dummy": value("USREC", month),
        }
        rows.append(row)

    yoy_fields = {
        "petroleum_production": "petroleum_production_YoY",
        "petroleum_consumption": "petroleum_consumption_YoY",
        "crude_inventory_kb": "crude_inventory_YoY",
        "real_WTI": "real_WTI_YoY",
        "household_energy_expenditure_share": "household_energy_expenditure_share_YoY_change",
        "energy_CPI": "energy_CPI_YoY",
        "real_disposable_income": "real_disposable_income_YoY",
        "industrial_production": "Industrial_production_YoY",
        "manufacturing_output": "manufacturing_output_YoY",
        "real_consumer_spending": "real_consumer_spending_YoY",
        "business_investment": "business_investment_YoY",
        "real_gdp": "Real_GDP_growth",
        "productivity": "productivity_YoY",
        "average_weekly_hours": "average_weekly_hours_YoY",
        "temporary_help_employment": "temporary_help_YoY",
        "real_hourly_wage": "real_wage_growth",
    }
    for field, output in yoy_fields.items():
        values = [_num(row.get(field)) for row in rows]
        for i, row in enumerate(rows):
            previous = values[i - 12] if i >= 12 else None
            row[output] = 100 * (values[i] / previous - 1) if values[i] is not None and previous not in (None, 0) else None
    return rows


CURRENT_SPECS = [
    ("Physical energy conditions", "petroleum_production_YoY", "Petroleum production growth", "down", "Petroleum consumption; inventories"),
    ("Physical energy conditions", "petroleum_consumption_YoY", "Petroleum consumption growth", "down", "Industrial production; oil burden"),
    ("Physical energy conditions", "oil_consumption_per_person_mmbtu", "Oil consumption per person", "down", "Real spending; petroleum consumption"),
    ("Physical energy conditions", "CI_zscore", "Comparative inventory z-score", "down", "Crude stocks; refinery utilization"),
    ("Physical energy conditions", "refinery_utilization_pct", "Refinery utilization", "up", "Product inventories; crack spreads"),
    ("Energy affordability and financial conditions", "real_WTI_YoY", "Real WTI growth", "up", "Energy CPI; household burden"),
    ("Energy affordability and financial conditions", "household_energy_expenditure_share", "Household energy expenditure share", "up", "Real income; energy CPI"),
    ("Energy affordability and financial conditions", "energy_expenditure_share_gdp", "Energy expenditure share of GDP", "up", "Industrial output; real GDP"),
    ("Energy affordability and financial conditions", "energy_CPI_YoY", "Energy CPI growth", "up", "Real wages; consumer sentiment"),
    ("Energy affordability and financial conditions", "real_disposable_income_YoY", "Real disposable income growth", "down", "Real spending; wages"),
    ("Energy affordability and financial conditions", "fed_funds_rate", "Federal funds rate", "up", "Credit standards; GM2"),
    ("Energy affordability and financial conditions", "credit_tightening_pct", "Credit tightening", "up", "Investment; delinquency"),
    ("Energy affordability and financial conditions", "GM2_YoY", "Global M2 growth", "down", "Oil momentum; credit conditions"),
    ("Production, consumption, and investment response", "Industrial_production_YoY", "Industrial production growth", "down", "Manufacturing; energy use"),
    ("Production, consumption, and investment response", "manufacturing_output_YoY", "Manufacturing output growth", "down", "Weekly hours; business investment"),
    ("Production, consumption, and investment response", "real_consumer_spending_YoY", "Real consumer spending growth", "down", "Income; sentiment"),
    ("Production, consumption, and investment response", "business_investment_YoY", "Business investment growth", "down", "Credit standards; GDP"),
    ("Production, consumption, and investment response", "Real_GDP_growth", "Real GDP growth", "down", "Energy consumption; industrial production"),
    ("Labour and household consequences", "average_weekly_hours_YoY", "Average weekly hours growth", "down", "Temporary help; manufacturing"),
    ("Labour and household consequences", "temporary_help_YoY", "Temporary-help employment growth", "down", "Hours; unemployment"),
    ("Labour and household consequences", "full_time_employment_share", "Full-time employment share", "down", "Involuntary part time; prime-age employment"),
    ("Labour and household consequences", "involuntary_part_time_share", "Involuntary part-time share", "up", "Full-time share; wages"),
    ("Labour and household consequences", "prime_age_employment_rate", "Prime-age employment rate", "down", "Unemployment; hours"),
    ("Labour and household consequences", "real_wage_growth", "Real wage growth", "down", "Energy CPI; sentiment"),
    ("Labour and household consequences", "consumer_sentiment", "Consumer sentiment", "down", "Real income; spending"),
    ("Labour and household consequences", "credit_card_delinquency_rate", "Credit-card delinquency", "up", "Credit standards; real income"),
    ("Labour and household consequences", "unemployment_rate", "Unemployment rate", "up", "Hours; prime-age employment"),
]


def current_state(rows: list[Row]) -> list[Row]:
    out = []
    for layer, field, label, stress_direction, confirming in CURRENT_SPECS:
        available = [(i, row) for i, row in enumerate(rows) if _num(row.get(field)) is not None]
        if not available:
            continue
        i, latest = available[-1]
        prior_candidates = [(j, row) for j, row in available if j < i]
        previous = prior_candidates[-1][1] if prior_candidates else {}
        value = float(latest[field])
        prev = _num(previous.get(field))
        history = [float(row[field]) for _, row in available]
        percentile = 100 * sum(v <= value for v in history) / len(history)
        change = value - prev if prev is not None else None
        stress_rising = change is not None and ((stress_direction == "up" and change > 0) or (stress_direction == "down" and change < 0))
        confidence = "medium" if len(history) >= 120 else "low"
        if field in {"CI_zscore", "GM2_YoY", "Industrial_production_YoY"} and len(history) >= 120:
            confidence = "high"
        out.append({
            "layer": layer,
            "indicator_id": field,
            "indicator": label,
            "latest_value": value,
            "previous_value": prev,
            "change": change,
            "historical_percentile": percentile,
            "direction": "stress increasing" if stress_rising else "stress easing or mixed",
            "source_date": latest["month"],
            "update_frequency": "quarterly" if field in {"energy_expenditure_share_gdp", "credit_tightening_pct", "business_investment_YoY", "Real_GDP_growth", "credit_card_delinquency_rate"} else "monthly",
            "interpretation": _state_interpretation(label, percentile, stress_rising),
            "confirming_indicators": confirming,
            "conflicting_indicators": "Review other indicators in the same layer; no single reading determines the state.",
            "confidence_level": confidence,
            "evidence_label": "Contextual indicator",
        })
    return out


def _state_interpretation(label: str, percentile: float, stress_rising: bool) -> str:
    band = "high" if percentile >= 80 else "low" if percentile <= 20 else "mid-range"
    direction = "moving in the stress-consistent direction" if stress_rising else "not moving in the stress-consistent direction"
    return f"{label} is in its {band} historical range and is {direction}. Interpret with confirming and conflicting evidence."


def energy_burden_analysis(rows: list[Row]) -> tuple[list[Row], str]:
    models = {
        "historical_mean": [],
        "autoregressive": ["Industrial_production_YoY"],
        "macro_only": ["Industrial_production_YoY", "GM2_YoY", "fed_funds_rate"],
        "nominal_oil": ["Industrial_production_YoY", "WTI_YoY"],
        "energy_only": ["Industrial_production_YoY", "household_energy_expenditure_share", "real_WTI_YoY"],
        "energy_plus_financial": ["Industrial_production_YoY", "household_energy_expenditure_share", "GM2_YoY", "fed_funds_rate", "credit_tightening_pct"],
    }
    results = []
    for validation, window in [("expanding", None), ("rolling_120m", 120)]:
        baseline_rmse = None
        for model, features in models.items():
            actual, predicted = _oos_predictions(rows, "Industrial_production_YoY", features, horizon=6, min_train=60, window=window)
            metrics = _forecast_metrics(actual, predicted)
            if model == "autoregressive":
                baseline_rmse = metrics["rmse"]
            results.append({"analysis": "energy_burden", "validation": validation, "target": "Industrial_production_YoY_t_plus_6m", "model": model, "features": "; ".join(features) or "historical mean", **metrics})
        if baseline_rmse:
            for result in results:
                if result["validation"] == validation and _num(result.get("rmse")) is not None:
                    result["rmse_improvement_vs_ar"] = 1 - float(result["rmse"]) / baseline_rmse

    best_by_validation = []
    for validation in ["expanding", "rolling_120m"]:
        candidates = [r for r in results if r["validation"] == validation and _num(r.get("rmse")) is not None]
        best_by_validation.append(min(candidates, key=lambda r: float(r["rmse"])))
    burden = next((r for r in results if r["validation"] == "expanding" and r["model"] == "energy_only"), None)
    nominal = next((r for r in results if r["validation"] == "expanding" and r["model"] == "nominal_oil"), None)
    conclusion = "The first-pass burden model does not yet demonstrate stable material predictive improvement."
    if burden and nominal and float(burden["rmse"]) <= 0.95 * float(nominal["rmse"]) and all(r["model"] in {"energy_only", "energy_plus_financial"} for r in best_by_validation):
        conclusion = "Energy burden improves on nominal oil price alone in both validation views, supporting further vintage-aware testing."
    markdown = f"""# Energy-Burden Diagnostic

## Question

Does energy burden predict six-month-ahead industrial-production growth more consistently than nominal oil-price growth alone?

## First-Pass Result

{conclusion}

The benchmark set includes a historical mean, an autoregressive model, a macro-only model, nominal oil, energy burden, and energy plus financial conditions. Expanding and 120-month rolling predictions train only on target outcomes observable by each prediction date. A variable is not labelled predictive unless improvement is material and stable across validation designs.

## Interpretation

Household energy expenditure share is an aggregate affordability proxy, not a household distribution measure. Quarterly GDP and credit fields are latest-vintage observations aligned to monthly rows and are unsuitable for strict real-time claims without vintage data. The locked GM2 lag-5 WTI/Brent model is unchanged.

## Next Step

Acquire real-time vintages and household-distribution measures, then test recession, spending, investment, and GDP targets separately. Do not combine them into a single stress score.
"""
    return results, markdown


def physical_tightness_analysis(rows: list[Row]) -> tuple[list[Row], str]:
    fields = [
        ("CI_zscore", "down"),
        ("crude_inventory_YoY", "down"),
        ("petroleum_production_YoY", "down"),
        ("petroleum_consumption_YoY", "up"),
        ("refinery_utilization_pct", "up"),
    ]
    out = []
    for field, tight_direction in fields:
        contemporaneous = _correlation([_num(r.get(field)) for r in rows], [_num(r.get("WTI_YoY")) for r in rows])
        best_lag, best_corr, n = _best_lead_correlation(rows, field, "WTI_YoY", 12)
        out.append({"indicator": field, "tightness_direction": tight_direction, "contemporaneous_correlation_with_WTI_YoY": contemporaneous[0], "n_contemporaneous": contemporaneous[1], "best_lead_months_to_WTI_YoY": best_lag, "best_lead_correlation": best_corr, "n_best_lag": n})
    markdown = """# Physical-Tightness Diagnostic

## Scope

This first release displays crude inventories, comparative inventory, production, consumption, and refinery utilization separately. It does not collapse them into one scarcity score.

## Reading The Signals

- Falling inventories with rising prices are consistent with physical tightening when production, imports, refinery runs, and demand confirm the move.
- High refinery utilization can indicate a downstream constraint, but it can also reflect healthy product demand.
- Falling consumption after a price or burden spike may indicate demand destruction; falling prices alone do not prove improving supply.
- U.S. inventory and production are not complete measures of the global balance.

## Missing Data

A documented global spare-capacity series and a redistributable continuous WTI futures curve are not yet in the cache. Both remain experimental catalogue items rather than synthetic values.
"""
    return out, markdown


def labour_early_warning_analysis(rows: list[Row]) -> tuple[list[Row], str]:
    fields = [
        ("average_weekly_hours_YoY", -1),
        ("temporary_help_YoY", -1),
        ("real_wage_growth", -1),
        ("unemployment_rate", 1),
    ]
    out = []
    for field, stress_sign in fields:
        transformed = []
        for row in rows:
            value = _num(row.get(field))
            transformed.append(value * stress_sign if value is not None else None)
        best_lag, best_corr, n = _best_array_lead(
            transformed,
            [_num(r.get("recession_dummy")) for r in rows],
            12,
            strongest_absolute=False,
        )
        ip_lag, ip_corr, ip_n = _best_array_lead(
            transformed,
            [-float(r["Industrial_production_YoY"]) if _num(r.get("Industrial_production_YoY")) is not None else None for r in rows],
            12,
            strongest_absolute=False,
        )
        out.append({"indicator": field, "stress_transform": "negative growth" if stress_sign < 0 else "higher level", "best_lead_months_to_recession": best_lag, "correlation_with_future_recession": best_corr, "n_recession": n, "best_lead_months_to_industrial_weakness": ip_lag, "correlation_with_future_industrial_weakness": ip_corr, "n_industrial": ip_n, "evidence_label": "Supported historical pattern" if field != "unemployment_rate" else "Contextual indicator"})
    markdown = """# Labour Early-Warning Diagnostic

## Hypothesis

Temporary-help employment, average weekly hours, and real wages may reveal labour stress earlier than headline unemployment because firms can reduce hours and flexible staffing before broad layoffs.

## Method

For leads from zero to twelve months, the analysis correlates stress-transformed labour indicators with future NBER recession months and future industrial weakness. This is descriptive lead evidence, not causal proof. The comparison uses latest-vintage data and does not optimize a combined labour score.

## Interpretation

Lead timing is episode-dependent. Hours and temporary help can weaken for sector-specific reasons, real wages can fall because inflation rises even when labour demand is firm, and unemployment can change with participation. Confirm labour warnings with manufacturing, spending, credit, and household indicators.
"""
    return out, markdown


def _oos_predictions(rows: list[Row], target: str, features: list[str], horizon: int, min_train: int, window: int | None) -> tuple[list[float], list[float]]:
    actual, predicted = [], []
    for i in range(len(rows) - horizon):
        y = _num(rows[i + horizon].get(target))
        x = [_num(rows[i].get(field)) for field in features]
        if y is None or any(value is None for value in x):
            continue
        training = []
        last_known_predictor = i - horizon
        for j in range(max(0, last_known_predictor - window + 1) if window else 0, last_known_predictor + 1):
            train_y = _num(rows[j + horizon].get(target))
            train_x = [_num(rows[j].get(field)) for field in features]
            if train_y is not None and all(value is not None for value in train_x):
                training.append((train_x, train_y))
        if len(training) < min_train:
            continue
        if not features:
            prediction = sum(float(item[1]) for item in training) / len(training)
        else:
            matrix = np.array([[1.0, *map(float, item[0])] for item in training])
            vector = np.array([float(item[1]) for item in training])
            coefficients = np.linalg.lstsq(matrix, vector, rcond=None)[0]
            prediction = float(np.array([1.0, *map(float, x)]) @ coefficients)
        actual.append(float(y))
        predicted.append(prediction)
    return actual, predicted


def _forecast_metrics(actual: list[float], predicted: list[float]) -> Row:
    if not actual:
        return {"n_predictions": 0, "rmse": None, "mae": None, "r2": None, "directional_accuracy": None, "sign_accuracy": None}
    errors = np.array(actual) - np.array(predicted)
    variance = float(np.sum((np.array(actual) - np.mean(actual)) ** 2))
    return {
        "n_predictions": len(actual),
        "rmse": float(np.sqrt(np.mean(errors**2))),
        "mae": float(np.mean(np.abs(errors))),
        "r2": 1 - float(np.sum(errors**2)) / variance if variance else None,
        "directional_accuracy": float(np.mean(np.sign(np.diff(actual)) == np.sign(np.diff(predicted)))) if len(actual) > 1 else None,
        "sign_accuracy": float(np.mean(np.sign(actual) == np.sign(predicted))),
    }


def _best_lead_correlation(rows: list[Row], predictor: str, target: str, max_lag: int) -> tuple[int, float | None, int]:
    return _best_array_lead([_num(r.get(predictor)) for r in rows], [_num(r.get(target)) for r in rows], max_lag)


def _best_array_lead(
    predictor: list[float | None],
    target: list[float | None],
    max_lag: int,
    strongest_absolute: bool = True,
) -> tuple[int, float | None, int]:
    candidates = []
    for lag in range(max_lag + 1):
        paired = [(predictor[i - lag], target[i]) for i in range(lag, len(target)) if predictor[i - lag] is not None and target[i] is not None]
        correlation, n = _correlation([p[0] for p in paired], [p[1] for p in paired])
        if correlation is not None:
            candidates.append((lag, correlation, n))
    key = (lambda item: abs(item[1])) if strongest_absolute else (lambda item: item[1])
    return max(candidates, key=key) if candidates else (0, None, 0)


def _correlation(left: Iterable[float | None], right: Iterable[float | None]) -> tuple[float | None, int]:
    paired = [(float(a), float(b)) for a, b in zip(left, right) if a is not None and b is not None and math.isfinite(float(a)) and math.isfinite(float(b))]
    if len(paired) < 3:
        return None, len(paired)
    x, y = zip(*paired)
    if np.std(x) == 0 or np.std(y) == 0:
        return None, len(paired)
    return float(np.corrcoef(x, y)[0, 1]), len(paired)


def _num(value: object) -> float | None:
    return float(value) if isinstance(value, (int, float)) and math.isfinite(float(value)) else None


def historical_episode_library() -> tuple[list[Row], str]:
    episodes = [
        ("1973-1975 oil embargo and recession", "1973-10", "1975-03", "Embargo layered on strong demand and constrained spare capacity", "Physical supply disruption and price spike", "Inflation surge and recession", "Production, hours and employment weakened after the shock", "Geopolitics, wage-price dynamics, monetary policy"),
        ("1979-1982 oil shock and disinflation", "1979-01", "1982-11", "Iranian revolution, supply losses and subsequent monetary tightening", "Physical disruption followed by conservation and new supply", "High burden, inflation and sharp rate increases", "Deep industrial and labour contraction", "Volcker disinflation was a major independent driver"),
        ("1990-1991 Gulf War shock", "1990-07", "1991-03", "Iraq invasion of Kuwait and temporary supply fear", "Brief price spike with coordinated supply response", "Short affordability shock", "Recession and employment weakness overlapped", "Credit-cycle and savings-and-loan stress"),
        ("2007-2009 oil spike and financial crisis", "2007-01", "2009-06", "Strong global demand, tight balances, leverage and housing stress", "WTI spike followed by demand-driven collapse", "Record nominal oil and rising household burden", "Industrial output, hours, temporary help and employment fell", "Housing and banking crisis dominated the downturn"),
        ("2014-2016 shale and OPEC adjustment", "2014-06", "2016-02", "Rapid U.S. supply growth and OPEC market-share strategy", "Supply surplus and inventory accumulation", "Falling energy burden", "Energy investment and producing regions weakened", "Dollar strength and global manufacturing slowdown"),
        ("2020 pandemic collapse", "2020-02", "2021-03", "Mobility restrictions and abrupt demand loss", "Extreme demand destruction and futures dislocation", "Prices collapsed rather than signalling abundance", "Historic output and labour shock", "Public-health restrictions were the initiating cause"),
        ("2021-2023 reopening, war and SPR response", "2021-04", "2023-12", "Reopening demand, constrained supply response, Russia-Ukraine war", "Tight products and crude followed by SPR releases and normalization", "Energy CPI and burden rose sharply", "Real wages compressed before conditions eased", "Supply chains, fiscal support and broad inflation"),
    ]
    rows = []
    for name, start, end, initiating, physical, burden, response, alternatives in episodes:
        rows.append({
            "episode": name,
            "start": start,
            "end": end,
            "initiating_conditions": initiating,
            "physical_energy_indicators": physical,
            "financial_conditions": "See episode-specific GM2, interest-rate and credit series in the core dataset.",
            "energy_burden": burden,
            "inflation_response": "Energy inflation rose before or during stress except in demand-collapse episodes.",
            "industrial_and_gdp_response": response,
            "labour_response": response,
            "household_response": "Real-income, sentiment and delinquency effects varied by policy support and shock duration.",
            "oil_price_peak_and_collapse": "Use WTI/Brent episode paths; exact peak dates are calculated in future episode scoring work.",
            "approximate_lag_sequence": "Physical/price signal -> burden/inflation -> output/spending -> labour/household effects; timing varies by episode.",
            "alternative_explanations": alternatives,
            "evidence_label": "Supported historical pattern",
            "schema_status": "initial structured episode; quantitative sequence test pending",
        })
    markdown = """# Historical Energy-Stress Episode Library

## Purpose

This initial library provides a consistent schema for comparing energy and economic stress episodes. It records initiating conditions, physical signals, affordability, macro transmission, labour and household responses, price reversal, approximate sequencing, and competing explanations.

## Important Caution

The same symptom sequence does not imply the same cause. The 2008 crisis combined an oil-price spike with a housing and banking collapse; 2020 was initiated by public-health restrictions; 2014-2016 was primarily a supply and investment adjustment. Episodes are analogues for structured comparison, not templates or causal identification.

## First-Pass Episodes

The CSV includes 1973-1975, 1979-1982, 1990-1991, 2007-2009, 2014-2016, 2020-2021, and 2021-2023. Quantitative peak dates, lag distributions, and real-time-vintage comparisons are the next implementation step.
"""
    return rows, markdown


def framework_markdown(catalogue: list[Row], core_rows: list[Row]) -> str:
    implemented = sum(not str(row["status"]).startswith(("proposed", "scenario", "proxy - missing")) for row in catalogue)
    latest = max(str(row["month"]) for row in core_rows)
    return f"""# System-Response Diagnostic Framework

## Purpose

The framework helps readers recognize observable symptoms of energy and oil constraints, trace how they can propagate through the economy, distinguish physical scarcity from demand destruction, and compare current conditions with historical episodes.

It is diagnostic and explanatory. It does not create a unified forecasting model, a social-instability score, or a replacement for the locked GM2-only lag-5 WTI/Brent benchmark.

## Five Layers

1. **Physical energy conditions:** production, consumption, inventories, comparative inventory and refinery constraints.
2. **Energy affordability and financial conditions:** real oil, household and GDP energy burden, energy inflation, income, rates, credit and GM2.
3. **Production, consumption, and investment response:** industry, manufacturing, spending, investment, GDP and productivity.
4. **Labour and household consequences:** hours, temporary work, employment structure, wages, sentiment and delinquency.
5. **Social and institutional symptoms:** documented in the catalogue as proposed research only; no social-stress model is implemented.

## Transmission Chain

`Liquidity -> energy demand -> physical tightness -> oil price and energy burden -> inflation and margins -> consumption and investment -> industrial production and GDP -> hours, wages and employment quality -> household and social stress`

Each arrow is a hypothesis to test separately. Correlation describes co-movement, out-of-sample improvement describes predictive usefulness, and neither alone establishes causality.

## First Release

The catalogue contains {len(catalogue)} measured, derived, proxy and proposed indicators; {implemented} have implemented or derived data paths. The monthly-aligned core extends to the latest available source observation ({latest}), but series have different release dates and the final month can be partial. Current-state rows preserve those indicator-specific dates, percentiles, confirming evidence, conflicts and confidence levels.

## Regime Vocabulary

- **A. Expansion and rising demand:** activity and consumption rise without broad physical deficits.
- **B. Physical tightening:** inventories fall, utilization rises, or demand outruns supply.
- **C. Energy affordability stress:** real prices and expenditure burdens rise faster than income.
- **D. Economic transmission:** margins, spending, investment and industrial output weaken.
- **E. Demand destruction:** consumption and activity fall while affordability remains strained.
- **F. Price collapse:** oil falls because demand weakens or supply expands; the cause must be diagnosed.
- **G. Labour and household after-effects:** hours, flexible employment, real wages and credit quality deteriorate.
- **H. Recovery or renewed tightening:** burden eases and activity recovers, or demand re-tightens the physical market.

No automatic regime classifier is promoted in this first pass. Future rules must show contributing indicators, data dates, confidence, conflicting evidence and historical analogues.

## Evidence Labels

- **Validated relationship:** passed the project's established validation or locked-model decision process.
- **Supported historical pattern:** recurs descriptively across episodes but is not a stable forecast claim.
- **Contextual indicator:** useful for interpretation without demonstrated independent predictive value.
- **Experimental proxy:** measurable approximation requiring additional validation.
- **Scenario concept:** proposed layer without an implemented reproducible series.

## Data And Methodological Gaps

- Global spare capacity and a redistributable continuous futures curve are missing.
- Household burden is aggregate and does not reveal distributional exposure.
- Quarterly GDP, investment, credit and delinquency fields are latest-vintage and not release-time safe.
- Current-state percentiles use the available latest-vintage history and are not causal thresholds.
- Social and institutional measures are sparse, definition-sensitive and intentionally deferred.

## Recommended Next Step

Add real-time vintages and reliable global physical-balance measures, then implement transparent multi-indicator regime rules. Only after those rules survive expanding and rolling validation should the project test household-distribution or social-response models.
"""


def make_system_response_charts(
    core: list[Row], current: list[Row], energy_validation: list[Row], physical: list[Row], labour: list[Row], episodes: list[Row], out_dir: Path
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    _chain_chart(out_dir / "system_response_chain.png")
    _current_layers_chart(current, out_dir / "current_state_layers.png")
    _timeseries_panels(core, [("CI_zscore", "CI z-score"), ("petroleum_production_YoY", "Production YoY"), ("petroleum_consumption_YoY", "Consumption YoY"), ("refinery_utilization_pct", "Refinery utilization")], "Physical tightness indicators", out_dir / "physical_tightness_dashboard.png")
    _timeseries_panels(core, [("household_energy_expenditure_share", "Energy / disposable income"), ("energy_expenditure_share_gdp", "Energy / GDP"), ("real_WTI_YoY", "Real WTI YoY"), ("energy_CPI_YoY", "Energy CPI YoY")], "Energy affordability and burden", out_dir / "energy_burden_dashboard.png")
    _cycle_chart(core, out_dir / "demand_destruction_cycle.png")
    _timeseries_panels(core, [("household_energy_expenditure_share", "Energy burden"), ("Industrial_production_YoY", "Industrial production"), ("manufacturing_output_YoY", "Manufacturing"), ("Real_GDP_growth", "Real GDP")], "Industrial transmission", out_dir / "industrial_transmission.png")
    _timeseries_panels(core, [("average_weekly_hours_YoY", "Weekly hours YoY"), ("temporary_help_YoY", "Temporary help YoY"), ("real_wage_growth", "Real wage growth"), ("unemployment_rate", "Unemployment")], "Labour early-warning indicators", out_dir / "labour_early_warning_indicators.png")
    _timeseries_panels(core, [("real_disposable_income_YoY", "Real disposable income"), ("consumer_sentiment", "Consumer sentiment"), ("credit_card_delinquency_rate", "Credit-card delinquency"), ("involuntary_part_time_share", "Involuntary part-time share")], "Household stress indicators", out_dir / "household_stress_indicators.png")
    _episode_chart(core, episodes, out_dir / "historical_episode_comparison.png")
    _regime_timeline(core, episodes, out_dir / "regime_timeline.png")
    _lag_map(physical, labour, out_dir / "indicator_lag_map.png")


def _source_note(fig, text: str) -> None:
    fig.text(0.01, 0.01, text, fontsize=7, color="#57534e")


def _chain_chart(path: Path) -> None:
    fig, ax = plt.subplots(figsize=(14, 5))
    ax.axis("off")
    labels = ["Liquidity", "Energy demand", "Physical tightness", "Price + burden", "Spending + investment", "Industry + GDP", "Labour + households"]
    colors = ["#d97706", "#0f766e", "#2563eb", "#be123c", "#7c3aed", "#475569", "#18181b"]
    for i, (label, color) in enumerate(zip(labels, colors)):
        x = 0.04 + i * 0.14
        ax.text(x, 0.53, label, ha="center", va="center", color="white", fontsize=10, fontweight="bold", bbox={"boxstyle": "round,pad=0.55,rounding_size=0.12", "facecolor": color, "edgecolor": "none"})
        if i < len(labels) - 1:
            ax.annotate("", xy=(x + 0.09, 0.53), xytext=(x + 0.05, 0.53), arrowprops={"arrowstyle": "->", "color": "#78716c", "lw": 1.5})
    ax.set_title("System-response transmission chain", loc="left", fontsize=18, fontweight="bold")
    ax.text(0.04, 0.25, "Each link is tested separately. No unified stress score is used.", fontsize=11, color="#57534e")
    _source_note(fig, "Framework: project system-response hypothesis. Locked oil benchmark remains GM2 YoY lag 5.")
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(path, dpi=180)
    plt.close(fig)


def _current_layers_chart(rows: list[Row], path: Path) -> None:
    selected = rows[:]
    fig, axes = plt.subplots(1, 5, figsize=(19, 8), sharey=False)
    for ax, layer in zip(axes, LAYERS):
        subset = [r for r in selected if r["layer"] == layer]
        if not subset:
            ax.text(0.5, 0.5, "Not implemented", ha="center", va="center")
            ax.axis("off")
            continue
        names = ["\n".join(textwrap.wrap(str(r["indicator"]), width=22)) for r in subset]
        values = [float(r["historical_percentile"]) for r in subset]
        colors = ["#be123c" if r["direction"] == "stress increasing" else "#0f766e" for r in subset]
        ax.barh(range(len(names)), values, color=colors)
        ax.set_yticks(range(len(names)), names, fontsize=7)
        ax.set_xlim(0, 100)
        ax.axvline(50, color="#a8a29e", lw=0.8)
        ax.set_title(layer.replace(" and ", "\n& "), fontsize=9)
        ax.invert_yaxis()
    fig.suptitle("Current indicator layers: historical percentile and direction", fontsize=16, fontweight="bold")
    _source_note(fig, "Red = latest change is stress-consistent; teal = easing or mixed. Percentiles are per indicator, not a composite score.")
    fig.tight_layout(rect=(0, 0.04, 1, 0.94))
    fig.savefig(path, dpi=180)
    plt.close(fig)


def _timeseries_panels(rows: list[Row], fields: list[tuple[str, str]], title: str, path: Path) -> None:
    fig, axes = plt.subplots(len(fields), 1, figsize=(14, 10), sharex=True)
    months = [str(r["month"]) for r in rows]
    x = np.arange(len(rows))
    for ax, (field, label) in zip(axes, fields):
        values = [_num(r.get(field)) for r in rows]
        ax.plot(x, [np.nan if v is None else v for v in values], lw=1.4, color="#0f766e")
        ax.axhline(0, color="#a8a29e", lw=0.7)
        ax.set_ylabel(label, fontsize=8)
        _shade_recessions(ax, rows)
    ticks = np.arange(0, len(months), 60)
    axes[-1].set_xticks(ticks, [months[i][:4] for i in ticks])
    fig.suptitle(title, fontsize=16, fontweight="bold")
    _source_note(fig, "Sources: EIA, BEA, BLS, Federal Reserve and project-derived series. Shading = NBER recession indicator via FRED USREC.")
    fig.tight_layout(rect=(0, 0.04, 1, 0.95))
    fig.savefig(path, dpi=180)
    plt.close(fig)


def _shade_recessions(ax, rows: list[Row]) -> None:
    active = None
    for i, row in enumerate(rows):
        recession = _num(row.get("recession_dummy")) == 1
        if recession and active is None:
            active = i
        if active is not None and (not recession or i == len(rows) - 1):
            ax.axvspan(active, i, color="#d6d3d1", alpha=0.35)
            active = None


def _cycle_chart(rows: list[Row], path: Path) -> None:
    fig, ax = plt.subplots(figsize=(14, 7))
    x = np.arange(len(rows))
    series = [("WTI_YoY", "WTI YoY", "#be123c"), ("petroleum_consumption_YoY", "Petroleum consumption YoY", "#0f766e"), ("Industrial_production_YoY", "Industrial production YoY", "#2563eb")]
    for field, label, color in series:
        ax.plot(x, [np.nan if _num(r.get(field)) is None else float(r[field]) for r in rows], label=label, color=color, lw=1.4)
    _shade_recessions(ax, rows)
    months = [str(r["month"]) for r in rows]
    ticks = np.arange(0, len(rows), 60)
    ax.set_xticks(ticks, [months[i][:4] for i in ticks])
    ax.axhline(0, color="#78716c", lw=0.8)
    ax.legend(ncol=3, frameon=False)
    ax.set_title("Demand destruction: falling oil can accompany worsening activity", loc="left", fontsize=16, fontweight="bold")
    _source_note(fig, "Formula: YoY = 100*(value/value[t-12]-1). Falling oil is diagnosed with consumption and industrial activity, not interpreted alone.")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(path, dpi=180)
    plt.close(fig)


def _episode_chart(rows: list[Row], episodes: list[Row], path: Path) -> None:
    fig, ax = plt.subplots(figsize=(14, 7))
    for episode in episodes:
        subset = [r for r in rows if str(episode["start"]) <= str(r["month"]) <= str(episode["end"]) and _num(r.get("WTI_YoY")) is not None]
        if not subset:
            continue
        values = np.array([float(r["WTI_YoY"]) for r in subset])
        ax.plot(np.arange(len(values)), values, lw=1.4, label=str(episode["episode"])[:28])
    ax.axhline(0, color="#78716c", lw=0.8)
    ax.set_xlabel("Months from episode start")
    ax.set_ylabel("WTI YoY (%)")
    ax.legend(fontsize=7, ncol=2, frameon=False)
    ax.set_title("Historical episode comparison: oil momentum paths", loc="left", fontsize=16, fontweight="bold")
    _source_note(fig, "Episode dates are an initial research schema; paths are not normalized causal estimates.")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(path, dpi=180)
    plt.close(fig)


def _regime_timeline(rows: list[Row], episodes: list[Row], path: Path) -> None:
    fig, ax = plt.subplots(figsize=(14, 5))
    months = [str(r["month"]) for r in rows]
    for i, episode in enumerate(episodes):
        indices = [j for j, month in enumerate(months) if str(episode["start"]) <= month <= str(episode["end"])]
        if indices:
            ax.barh(i, len(indices), left=min(indices), color=plt.cm.Set2(i / max(1, len(episodes) - 1)))
            ax.text(min(indices) + 2, i, str(episode["episode"]), va="center", fontsize=8)
    ticks = np.arange(0, len(rows), 60)
    ax.set_xticks(ticks, [months[i][:4] for i in ticks])
    ax.set_yticks([])
    ax.set_title("Historical episode timeline", loc="left", fontsize=16, fontweight="bold")
    _source_note(fig, "Episode windows organize comparison; they are not automated regime classifications.")
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    fig.savefig(path, dpi=180)
    plt.close(fig)


def _lag_map(physical: list[Row], labour: list[Row], path: Path) -> None:
    labels, lags, correlations, colors = [], [], [], []
    for row in physical:
        labels.append(str(row["indicator"]))
        lags.append(float(row["best_lead_months_to_WTI_YoY"]))
        correlations.append(abs(float(row["best_lead_correlation"] or 0)))
        colors.append("#2563eb")
    for row in labour:
        labels.append(str(row["indicator"]))
        lags.append(float(row["best_lead_months_to_industrial_weakness"]))
        correlations.append(abs(float(row["correlation_with_future_industrial_weakness"] or 0)))
        colors.append("#be123c")
    fig, ax = plt.subplots(figsize=(12, 7))
    y = np.arange(len(labels))
    ax.scatter(lags, y, s=[30 + 250 * c for c in correlations], c=colors, alpha=0.8)
    ax.set_yticks(y, labels)
    ax.set_xlim(-0.5, 12.5)
    ax.set_xlabel("Best descriptive lead (months)")
    ax.set_title("Indicator lag map", loc="left", fontsize=16, fontweight="bold")
    ax.grid(axis="x", alpha=0.25)
    _source_note(fig, "Blue = physical indicator vs WTI YoY; red = labour stress vs industrial weakness. Bubble size = absolute correlation. Descriptive, not causal.")
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(path, dpi=180)
    plt.close(fig)
