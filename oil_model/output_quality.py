from __future__ import annotations

import math
from collections import defaultdict
from typing import Iterable

import numpy as np

from .adapters import Series
from .storage import Row


SERIES_META = {
    "GDPC1": ("Headline measured output", "Real GDP", "billions chained 2017 USD", "quarterly", "measured", "BEA via FRED GDPC1"),
    "A939RX0Q048SBEA": ("Headline measured output", "Real GDP per capita", "chained 2017 USD per person", "quarterly", "measured", "BEA via FRED A939RX0Q048SBEA"),
    "A261RX1Q020SBEA": ("Headline measured output", "Real gross domestic income", "billions chained 2017 USD", "quarterly", "measured", "BEA via FRED A261RX1Q020SBEA"),
    "LB0000031Q020SBEA": ("Headline measured output", "Real final sales to private domestic purchasers", "billions chained 2017 USD", "quarterly", "measured", "BEA via FRED LB0000031Q020SBEA"),
    "A362RX1A020NBEA": ("Net productive capacity", "Official real net domestic product", "billions chained 2017 USD", "annual", "measured", "BEA via FRED A362RX1A020NBEA"),
    "real_ndp_per_capita": ("Net productive capacity", "Real NDP per capita", "chained 2017 USD per person", "annual", "derived", "BEA real NDP / Census population via FRED"),
    "real_gdp_annual": ("Headline measured output", "Real GDP", "billions chained 2017 USD", "annual", "derived", "BEA GDPC1 annual average"),
    "W171RC1Q027SBEA": ("Net productive capacity", "Net domestic investment", "billions USD SAAR", "quarterly", "measured", "BEA via FRED W171RC1Q027SBEA"),
    "A262RX1Q020SBEA": ("Net productive capacity", "Real capital consumption", "billions chained 2017 USD SAAR", "quarterly", "measured", "BEA via FRED A262RX1Q020SBEA"),
    "INDPRO": ("Net productive capacity", "Industrial production", "index 2017=100", "monthly", "measured", "Federal Reserve via FRED INDPRO"),
    "IPMAN": ("Net productive capacity", "Manufacturing output", "index 2017=100", "monthly", "measured", "Federal Reserve via FRED IPMAN"),
    "TSIFRGHT": ("Net productive capacity", "Freight activity", "index 2000=100", "monthly", "measured", "BTS via FRED TSIFRGHT"),
    "MEHOINUSA672N": ("Realized household prosperity", "Real median household income", "2024 USD", "annual", "measured", "U.S. Census Bureau via FRED MEHOINUSA672N"),
    "LES1252881600Q": ("Realized household prosperity", "Real median weekly earnings", "1982-84 CPI-adjusted USD", "quarterly", "measured", "BLS via FRED LES1252881600Q"),
    "AWHMAN": ("Realized household prosperity", "Average weekly manufacturing hours", "hours", "monthly", "measured", "BLS via FRED AWHMAN"),
    "full_time_share": ("Realized household prosperity", "Full-time employment share", "percent of employment", "monthly", "derived", "BLS LNS12500000 / CE16OV via FRED"),
    "CXUSHELTERLB0101M": ("Realized household prosperity", "Average shelter expenditure", "2024 USD per consumer unit", "annual", "derived", "BLS Consumer Expenditure Survey via FRED"),
    "CXUFOODTOTLLB0101M": ("Realized household prosperity", "Average food expenditure", "2024 USD per consumer unit", "annual", "derived", "BLS Consumer Expenditure Survey via FRED"),
    "CXUUTILSLB0101M": ("Realized household prosperity", "Average utilities, fuels, and public services expenditure", "2024 USD per consumer unit", "annual", "derived", "BLS Consumer Expenditure Survey via FRED"),
    "HouseholdCommand": ("Realized household prosperity", "Experimental household command", "2024 USD", "annual", "experimental", "Census/BLS project derivation"),
    "shelter_cost_burden": ("Realized household prosperity", "Shelter-cost burden proxy", "percent of real median household income", "annual", "experimental", "BLS CE / Census project derivation"),
    "food_cost_burden": ("Realized household prosperity", "Food-cost burden proxy", "percent of real median household income", "annual", "experimental", "BLS CE / Census project derivation"),
    "household_energy_cost_burden": ("Realized household prosperity", "Utilities and fuels cost-burden proxy", "percent of real median household income", "annual", "experimental", "BLS CE / Census project derivation"),
    "VAPGDPFI": ("Financialization and asset valuation", "Finance and insurance value-added share", "percent of GDP", "quarterly", "measured", "BEA via FRED VAPGDPFI"),
    "VAPGDPRL": ("Financialization and asset valuation", "Real estate and rental value-added share", "percent of GDP", "quarterly", "measured", "BEA via FRED VAPGDPRL"),
    "TDSP": ("Financialization and asset valuation", "Household debt-service burden", "percent of disposable income", "quarterly", "measured", "Federal Reserve via FRED TDSP"),
    "private_debt_gdp": ("Financialization and asset valuation", "Household debt to GDP", "percent of GDP", "quarterly", "derived", "Federal Reserve CMDEBT / BEA GDP"),
    "DDDM01USA156NWDB": ("Financialization and asset valuation", "Equity-market capitalization", "percent of GDP", "annual", "measured", "World Bank via FRED DDDM01USA156NWDB"),
}


def _number(value: object) -> float | None:
    return float(value) if isinstance(value, (int, float)) and math.isfinite(float(value)) else None


def _iso_date(value: str) -> str:
    if len(value) == 4:
        return f"{value}-01-01"
    if len(value) == 7:
        return f"{value}-01"
    return value


def _annual_average(series: Series, minimum_observations: int = 1) -> dict[str, float]:
    grouped: dict[str, list[float]] = defaultdict(list)
    for date, value in series.observations:
        grouped[date[:4]].append(float(value))
    return {year: sum(values) / len(values) for year, values in grouped.items() if len(values) >= minimum_observations}


def _quarterly_average(series: Series, minimum_observations: int = 3) -> dict[str, float]:
    grouped: dict[str, list[float]] = defaultdict(list)
    for date, value in series.observations:
        year, month = int(date[:4]), int(date[5:7])
        quarter_month = 1 + 3 * ((month - 1) // 3)
        grouped[f"{year:04d}-{quarter_month:02d}"].append(float(value))
    return {date: sum(values) / len(values) for date, values in grouped.items() if len(values) >= minimum_observations}


def build_output_quality_dataset(series: dict[str, Series], cpi: Series) -> tuple[list[Row], dict[str, dict[str, float]]]:
    values = {key: dict(item.observations) for key, item in series.items()}
    cpi_annual = _annual_average(cpi, 12)
    cpi_base = cpi_annual.get("2024") or max(cpi_annual.values())
    derived: dict[str, dict[str, float]] = {}
    for key in ("INDPRO", "IPMAN", "TSIFRGHT"):
        if key in series:
            derived[key] = _quarterly_average(series[key])
    if "GDPC1" in series:
        derived["real_gdp_annual"] = _annual_average(series["GDPC1"], 4)
    if "A362RX1A020NBEA" in values and "POPTHM" in series:
        population = _annual_average(series["POPTHM"], 12)
        derived["real_ndp_per_capita"] = {date: ndp / population[date[:4]] * 1_000_000 for date, ndp in values["A362RX1A020NBEA"].items() if date[:4] in population and population[date[:4]]}
    if "CMDEBT" in values and "GDP" in values:
        derived["private_debt_gdp"] = {date: 100 * debt / values["GDP"][date] for date, debt in values["CMDEBT"].items() if date in values["GDP"] and values["GDP"][date]}

    household: dict[str, dict[str, float]] = {}
    for key in ("CXUSHELTERLB0101M", "CXUFOODTOTLLB0101M", "CXUUTILSLB0101M"):
        household[key] = {}
        for date, amount in values.get(key, {}).items():
            year = date[:4]
            if year in cpi_annual and cpi_annual[year]:
                household[key][date] = amount * cpi_base / cpi_annual[year]
    command: dict[str, float] = {}
    for date, income in values.get("MEHOINUSA672N", {}).items():
        costs = [household[key].get(date) for key in household]
        if all(cost is not None for cost in costs):
            command[date] = income - sum(float(cost) for cost in costs)
    derived.update(household)
    derived["HouseholdCommand"] = command
    if "LNS12500000" in values and "CE16OV" in values:
        derived["full_time_share"] = {date: 100 * amount / values["CE16OV"][date] for date, amount in values["LNS12500000"].items() if date in values["CE16OV"] and values["CE16OV"][date]}
    burden_keys = {
        "shelter_cost_burden": "CXUSHELTERLB0101M",
        "food_cost_burden": "CXUFOODTOTLLB0101M",
        "household_energy_cost_burden": "CXUUTILSLB0101M",
    }
    for output, cost_key in burden_keys.items():
        derived[output] = {date: 100 * cost / values["MEHOINUSA672N"][date] for date, cost in household[cost_key].items() if date in values.get("MEHOINUSA672N", {}) and values["MEHOINUSA672N"][date]}

    rows: list[Row] = []
    for key, meta in SERIES_META.items():
        lens, label, unit, frequency, status, source = meta
        observations = derived.get(key, values.get(key, {}))
        for date, value in sorted(observations.items()):
            rows.append({"date": _iso_date(date), "lens": lens, "indicator": key, "label": label, "value": value, "unit": unit, "frequency": "quarterly" if key in {"INDPRO", "IPMAN", "TSIFRGHT"} else frequency, "status": status, "source": source, "notes": "Latest-vintage observation; individual series remain visible and no composite quality score is calculated."})
    return rows, derived


def _corr(left: Iterable[float], right: Iterable[float]) -> float | None:
    x, y = np.asarray(list(left), dtype=float), np.asarray(list(right), dtype=float)
    if len(x) < 5 or np.std(x) == 0 or np.std(y) == 0:
        return None
    return float(np.corrcoef(x, y)[0, 1])


def _growth(mapping: dict[str, float], periods: int) -> dict[str, float]:
    dates = sorted(mapping)
    return {date: 100 * (mapping[date] / mapping[dates[i - periods]] - 1) for i, date in enumerate(dates) if i >= periods and mapping[dates[i - periods]]}


def energy_output_quality_tests(series: dict[str, Series], derived: dict[str, dict[str, float]], energy_series: Series, recession: Series, energy_label: str = "Total energy consumption growth") -> list[Row]:
    energy_q = _quarterly_average(energy_series)
    energy_growth = _growth(energy_q, 4)
    recession_map = dict(recession.observations)
    candidates = ["GDPC1", "A939RX0Q048SBEA", "A261RX1Q020SBEA", "W171RC1Q027SBEA", "INDPRO", "IPMAN", "LES1252881600Q", "VAPGDPFI", "VAPGDPRL", "TDSP", "private_debt_gdp"]
    rows: list[Row] = []
    for key in candidates:
        source = derived.get(key, dict(series[key].observations) if key in series else {})
        target = _growth(source, 4) if len(source) > 5 else {}
        dates = sorted(set(energy_growth) & set(target))
        if len(dates) < 12:
            continue
        x = [energy_growth[date] for date in dates]
        y = [target[date] for date in dates]
        contemporaneous = _corr(x, y)
        lag_results: list[tuple[int, float, int]] = []
        for lag in range(-4, 5):
            pairs = [(energy_growth[dates[i - lag]], target[date]) for i, date in enumerate(dates) if 0 <= i - lag < len(dates) and dates[i - lag] in energy_growth]
            corr = _corr((pair[0] for pair in pairs), (pair[1] for pair in pairs))
            if corr is not None:
                lag_results.append((lag, corr, len(pairs)))
        best_lag, best_corr, _ = max(lag_results, key=lambda item: abs(item[1])) if lag_results else (0, float("nan"), 0)
        rolling = [_corr(x[i - 19:i + 1], y[i - 19:i + 1]) for i in range(19, len(dates))]
        rolling_valid = [value for value in rolling if value is not None]
        dl_dates = dates[2:]
        matrix = np.asarray([[1.0, energy_growth.get(dates[i], 0), energy_growth.get(dates[i - 1], 0), energy_growth.get(dates[i - 2], 0)] for i in range(2, len(dates))])
        response = np.asarray([target[date] for date in dl_dates])
        beta = np.linalg.lstsq(matrix, response, rcond=None)[0] if len(response) >= 8 else np.full(4, np.nan)
        predictions, actuals, ar_predictions = [], [], []
        for i in range(20, len(dates)):
            train_y = np.asarray(y[:i]); train_x = np.asarray(x[:i])
            fit = np.linalg.lstsq(np.column_stack([np.ones(i), train_x]), train_y, rcond=None)[0]
            predictions.append(float(fit[0] + fit[1] * x[i])); actuals.append(y[i]); ar_predictions.append(y[i - 1])
        rmse = math.sqrt(np.mean((np.asarray(actuals) - np.asarray(predictions)) ** 2)) if actuals else None
        ar_rmse = math.sqrt(np.mean((np.asarray(actuals) - np.asarray(ar_predictions)) ** 2)) if actuals else None
        recession_pairs = [(energy_growth[date], target[date]) for date in dates if recession_map.get(date) == 1]
        expansion_pairs = [(energy_growth[date], target[date]) for date in dates if recession_map.get(date, 0) == 0]
        rows.append({"economic_measure": key, "label": SERIES_META[key][1], "energy_measure": "Total energy consumption growth", "contemporaneous_correlation": contemporaneous, "best_lag_quarters": best_lag, "best_lag_correlation": best_corr, "rolling_20q_correlation_mean": sum(rolling_valid) / len(rolling_valid) if rolling_valid else None, "distributed_lag_sum": float(np.sum(beta[1:])) if np.isfinite(beta).all() else None, "recession_correlation": _corr((p[0] for p in recession_pairs), (p[1] for p in recession_pairs)), "expansion_correlation": _corr((p[0] for p in expansion_pairs), (p[1] for p in expansion_pairs)), "oos_rmse": rmse, "autoregressive_rmse": ar_rmse, "oos_improvement_vs_ar_pct": 100 * (ar_rmse - rmse) / ar_rmse if rmse is not None and ar_rmse else None, "start_date": dates[0], "end_date": dates[-1], "n": len(dates), "limitations": "Latest-vintage bivariate test; frequency alignment, revisions, common cycles and omitted variables prevent causal interpretation."})
        rows[-1]["energy_measure"] = energy_label
        rows[-1].update({"frequency": "quarterly", "best_lag_periods": best_lag, "lag_unit": "quarters", "rolling_window": "20 quarters", "rolling_correlation_mean": rows[-1]["rolling_20q_correlation_mean"]})

    energy_a = _growth(_annual_average(energy_series, 12), 1)
    recession_a: dict[str, float] = defaultdict(float)
    for date, flag in recession.observations:
        recession_a[date[:4]] = max(recession_a[date[:4]], flag)
    for key in ("real_ndp_per_capita", "HouseholdCommand", "DDDM01USA156NWDB"):
        raw = derived.get(key, dict(series[key].observations) if key in series else {})
        annual = {date[:4]: value for date, value in raw.items()}
        target = _growth(annual, 1)
        dates = sorted(set(energy_a) & set(target))
        if len(dates) < 12:
            continue
        x = [energy_a[date] for date in dates]
        y = [target[date] for date in dates]
        lag_results = []
        for lag in range(-3, 4):
            pairs = [(x[i - lag], y[i]) for i in range(len(dates)) if 0 <= i - lag < len(dates)]
            corr = _corr((pair[0] for pair in pairs), (pair[1] for pair in pairs))
            if corr is not None:
                lag_results.append((lag, corr))
        best_lag, best_corr = max(lag_results, key=lambda item: abs(item[1])) if lag_results else (0, float("nan"))
        rolling = [_corr(x[i - 9:i + 1], y[i - 9:i + 1]) for i in range(9, len(dates))]
        rolling_valid = [entry for entry in rolling if entry is not None]
        matrix = np.asarray([[1.0, x[i], x[i - 1]] for i in range(1, len(dates))])
        response = np.asarray(y[1:])
        beta = np.linalg.lstsq(matrix, response, rcond=None)[0]
        predictions, actuals, ar_predictions = [], [], []
        for i in range(10, len(dates)):
            fit = np.linalg.lstsq(np.column_stack([np.ones(i), np.asarray(x[:i])]), np.asarray(y[:i]), rcond=None)[0]
            predictions.append(float(fit[0] + fit[1] * x[i])); actuals.append(y[i]); ar_predictions.append(y[i - 1])
        rmse = math.sqrt(np.mean((np.asarray(actuals) - np.asarray(predictions)) ** 2)) if actuals else None
        ar_rmse = math.sqrt(np.mean((np.asarray(actuals) - np.asarray(ar_predictions)) ** 2)) if actuals else None
        recession_pairs = [(energy_a[date], target[date]) for date in dates if recession_a.get(date) == 1]
        expansion_pairs = [(energy_a[date], target[date]) for date in dates if recession_a.get(date) == 0]
        rows.append({"economic_measure": key, "label": SERIES_META[key][1], "energy_measure": energy_label, "frequency": "annual", "contemporaneous_correlation": _corr(x, y), "best_lag_quarters": None, "best_lag_periods": best_lag, "lag_unit": "years", "best_lag_correlation": best_corr, "rolling_20q_correlation_mean": sum(rolling_valid) / len(rolling_valid) if rolling_valid else None, "distributed_lag_sum": float(np.sum(beta[1:])), "recession_correlation": _corr((p[0] for p in recession_pairs), (p[1] for p in recession_pairs)), "expansion_correlation": _corr((p[0] for p in expansion_pairs), (p[1] for p in expansion_pairs)), "oos_rmse": rmse, "autoregressive_rmse": ar_rmse, "oos_improvement_vs_ar_pct": 100 * (ar_rmse - rmse) / ar_rmse if rmse is not None and ar_rmse else None, "start_date": dates[0], "end_date": dates[-1], "n": len(dates), "limitations": "Annual latest-vintage test; short coverage, revisions, common cycles and omitted variables prevent causal interpretation."})
        rows[-1].update({"rolling_window": "10 years", "rolling_correlation_mean": rows[-1]["rolling_20q_correlation_mean"], "rolling_20q_correlation_mean": None})
    return rows


def output_quality_markdown(rows: list[Row], correlations: list[Row]) -> str:
    latest = max((str(row["date"]) for row in rows), default="not available")
    strongest = max((row for row in correlations if _number(row.get("contemporaneous_correlation")) is not None), key=lambda row: abs(float(row["contemporaneous_correlation"])), default=None)
    strong_text = f"The largest available contemporaneous energy-growth correlation is {float(strongest['contemporaneous_correlation']):.3f} for {strongest['label']}." if strongest else "Coverage is insufficient for a ranked correlation result."
    return f"""# Economic Output Quality

## Research question

This module asks whether energy throughput and energy affordability align differently with headline measured output, net productive capacity, realized household prosperity, and financialization or asset valuation. It does not label financial or service activity as valueless and does not create a single output-quality score.

## Four lenses

1. **Headline measured output:** real GDP, real GDP per capita, real gross domestic income, and real final private domestic sales.
2. **Net productive capacity:** official real net domestic product, net investment, capital consumption, industrial and manufacturing output, and freight activity.
3. **Realized household prosperity:** real median income and earnings, hours and employment structure, plus an experimental household-command measure.
4. **Financialization and asset valuation:** finance and insurance, real estate, household leverage and debt service, and equity valuation are kept separate.

## Household-command experiment

`HouseholdCommand = real median household income - real average shelter expenditure - real average food expenditure - real average utilities/fuels/public-services expenditure`.

All components are published in `economic_output_quality.csv`. This is an experimental proxy, not an official disposable-income measure: it combines a median income with mean consumer-unit expenditures, the utilities category is broader than household energy alone, and household composition differs across sources.

## Initial relationship tests

{strong_text} Each row in `energy_output_quality_correlations.csv` also reports lag correlation, rolling-window stability (20 quarters for quarterly measures or 10 years for annual measures), a distributed-lag coefficient sum, recession and expansion correlations, and expanding out-of-sample performance versus a one-period autoregressive benchmark.

## Interpretation limits

GDP measures current production, not total wealth. Real GDP adjusts for inflation; official real NDP accounts for capital consumption without manually subtracting non-additive chained-dollar components. Asset valuations can diverge from productive capacity, but that divergence is not evidence that finance, insurance, real estate, or services are intrinsically unproductive. Results use latest-vintage observations and are descriptive rather than causal.

Latest observation present in the module: {latest}.

## Data gaps retained explicitly

This first release does not yet include a harmonized productive-capital-stock series, construction output, electricity consumption, a financial-sector profit share, a housing-price-to-income ratio, or an imputed-housing-services share. GDP-by-industry coverage is represented narrowly by separate finance/insurance and real-estate value-added shares rather than a complete industry panel. These are documented next steps, not silently proxied or folded into a composite.
"""
