from __future__ import annotations

import math
from collections import defaultdict

from .adapters import Series
from .storage import Row


def series_map(series: Series) -> dict[str, float]:
    return dict(series.observations)


def yoy(values: list[float | None]) -> list[float | None]:
    out: list[float | None] = []
    for i, value in enumerate(values):
        prev = values[i - 12] if i >= 12 else None
        if value is None or prev in (None, 0):
            out.append(None)
        else:
            out.append((value / prev - 1.0) * 100.0)
    return out


def build_monthly_dataset(
    us_m2: Series,
    ea_m2: Series,
    cn_m2: Series,
    jp_m2: Series,
    eurusd: Series,
    cnyusd: Series,
    jpyusd: Series,
    cpi: Series,
    sp500: Series,
    uso_avg: Series,
    uso_month_end: Series,
    wti: Series,
    brent: Series,
    crude_inventory: Series,
    rac_composite: Series | None = None,
    rac_domestic: Series | None = None,
    rac_imported: Series | None = None,
    first_purchase: Series | None = None,
    imported_fob_cost: Series | None = None,
    imported_landed_cost: Series | None = None,
) -> list[Row]:
    maps = {
        "us_m2": series_map(us_m2),
        "ea_m2_eur": series_map(ea_m2),
        "cn_m2_cny": series_map(cn_m2),
        "jp_m2_jpy": series_map(jp_m2),
        "eurusd": series_map(eurusd),
        "cny_per_usd": series_map(cnyusd),
        "jpy_per_usd": series_map(jpyusd),
        "cpi": series_map(cpi),
        "sp500": series_map(sp500),
        "uso_avg": series_map(uso_avg),
        "uso_month_end": series_map(uso_month_end),
        "wti": series_map(wti),
        "brent": series_map(brent),
        "crude_inventory_kb": series_map(crude_inventory),
        "rac_composite": optional_series_map(rac_composite),
        "rac_domestic": optional_series_map(rac_domestic),
        "rac_imported": optional_series_map(rac_imported),
        "first_purchase": optional_series_map(first_purchase),
        "imported_fob_cost": optional_series_map(imported_fob_cost),
        "imported_landed_cost": optional_series_map(imported_landed_cost),
    }
    months = sorted(set().union(*[set(m) for m in maps.values()]))
    rows: list[Row] = []
    gm2_values: list[float | None] = []
    wti_values: list[float | None] = []
    brent_values: list[float | None] = []
    sp500_values: list[float | None] = []
    uso_values: list[float | None] = []
    inv_values: list[float | None] = []
    physical_values: dict[str, list[float | None]] = {
        name: []
        for name in ["rac_composite", "rac_domestic", "rac_imported", "first_purchase", "imported_fob_cost", "imported_landed_cost"]
    }

    for month in months:
        us = maps["us_m2"].get(month)
        ea = maps["ea_m2_eur"].get(month)
        cn = maps["cn_m2_cny"].get(month)
        jp = maps["jp_m2_jpy"].get(month)
        euro = maps["eurusd"].get(month)
        cny = maps["cny_per_usd"].get(month)
        jpy = maps["jpy_per_usd"].get(month)
        us_usd = us * 1_000_000_000 if us is not None else None
        ea_usd = ea * euro if ea is not None and euro else None
        cn_usd = cn / cny if cn is not None and cny else None
        jp_usd = jp / jpy if jp is not None and jpy else None
        components = [us_usd, ea_usd, cn_usd, jp_usd]
        gm2 = sum(x for x in components if x is not None) if all(x is not None for x in components) else None
        gm2_values.append(gm2)
        wti_values.append(maps["wti"].get(month))
        brent_values.append(maps["brent"].get(month))
        sp500_values.append(maps["sp500"].get(month))
        uso_values.append(maps["uso_month_end"].get(month))
        inv_values.append(maps["crude_inventory_kb"].get(month))
        for name, values in physical_values.items():
            values.append(maps[name].get(month))
        cpi_value = maps["cpi"].get(month)
        sp500_value = maps["sp500"].get(month)
        uso_avg_value = maps["uso_avg"].get(month)
        uso_month_end_value = maps["uso_month_end"].get(month)
        wti_value = maps["wti"].get(month)
        brent_value = maps["brent"].get(month)
        rows.append(
            {
                "month": month,
                "US_M2_USD": us_usd,
                "EA_M2_EUR": ea,
                "EA_M2_USD": ea_usd,
                "CN_M2_CNY": cn,
                "CN_M2_USD": cn_usd,
                "JP_M2_JPY": jp,
                "JP_M2_USD": jp_usd,
                "EURUSD": euro,
                "CNY_per_USD": cny,
                "JPY_per_USD": jpy,
                "US_CPI": cpi_value,
                "GM2_USD": gm2,
                "SP500": sp500_value,
                "USO_monthly_avg_adjusted_close": uso_avg_value,
                "USO_month_end_adjusted_close": uso_month_end_value,
                "WTI": wti_value,
                "Brent": brent_value,
                "RAC_composite": maps["rac_composite"].get(month),
                "RAC_domestic": maps["rac_domestic"].get(month),
                "RAC_imported": maps["rac_imported"].get(month),
                "first_purchase_price": maps["first_purchase"].get(month),
                "imported_crude_FOB_cost": maps["imported_fob_cost"].get(month),
                "imported_landed_cost": maps["imported_landed_cost"].get(month),
                "real_WTI": real_price(wti_value, cpi_value),
                "real_Brent": real_price(brent_value, cpi_value),
                "crude_inventory_kb": maps["crude_inventory_kb"].get(month),
            }
        )

    gm2_yoy = yoy(gm2_values)
    wti_yoy = yoy(wti_values)
    brent_yoy = yoy(brent_values)
    sp500_yoy = yoy(sp500_values)
    uso_yoy = yoy(uso_values)
    physical_yoy = {name: yoy(values) for name, values in physical_values.items()}
    ci_metrics = comparative_inventory(months, inv_values)
    for i, row in enumerate(rows):
        row["GM2_YoY"] = gm2_yoy[i]
        row["SP500_YoY"] = sp500_yoy[i]
        row["SP500_log_return_1m"] = log_return(sp500_values, i)
        row["SP500_forward_3m_return"] = forward_return(sp500_values, i, 3)
        row["SP500_forward_6m_return"] = forward_return(sp500_values, i, 6)
        row["USO_YoY"] = uso_yoy[i]
        row["USO_log_return_1m"] = log_return(uso_values, i)
        row["USO_forward_3m_return"] = forward_return(uso_values, i, 3)
        row["USO_forward_6m_return"] = forward_return(uso_values, i, 6)
        row["WTI_YoY"] = wti_yoy[i]
        row["Brent_YoY"] = brent_yoy[i]
        row["WTI_log_return_1m"] = log_return(wti_values, i)
        row["Brent_log_return_1m"] = log_return(brent_values, i)
        row["RAC_composite_YoY"] = physical_yoy["rac_composite"][i]
        row["RAC_domestic_YoY"] = physical_yoy["rac_domestic"][i]
        row["RAC_imported_YoY"] = physical_yoy["rac_imported"][i]
        row["first_purchase_YoY"] = physical_yoy["first_purchase"][i]
        row["imported_FOB_cost_YoY"] = physical_yoy["imported_fob_cost"][i]
        row["landed_import_cost_YoY"] = physical_yoy["imported_landed_cost"][i]
        row["RAC_vs_WTI_spread"] = diff(row.get("RAC_composite"), row.get("WTI"))
        row["RAC_vs_Brent_spread"] = diff(row.get("RAC_composite"), row.get("Brent"))
        row["first_purchase_vs_WTI_spread"] = diff(row.get("first_purchase_price"), row.get("WTI"))
        row["landed_import_vs_Brent_spread"] = diff(row.get("imported_landed_cost"), row.get("Brent"))
        row["USO_vs_WTI_return_spread"] = diff(row.get("USO_log_return_1m"), row.get("WTI_log_return_1m"))
        row["USO_vs_Brent_return_spread"] = diff(row.get("USO_log_return_1m"), row.get("Brent_log_return_1m"))
        row["USO_tracking_residual"] = diff(row.get("USO_YoY"), row.get("WTI_YoY"))
        row["USO_tracking_residual_vs_Brent"] = diff(row.get("USO_YoY"), row.get("Brent_YoY"))
        row["WTI_deviation_12m_avg"] = trailing_average_deviation(wti_values, i, 12)
        row["Brent_deviation_12m_avg"] = trailing_average_deviation(brent_values, i, 12)
        row["WTI_forward_3m_return"] = forward_return(wti_values, i, 3)
        row["Brent_forward_3m_return"] = forward_return(brent_values, i, 3)
        row["WTI_forward_6m_return"] = forward_return(wti_values, i, 6)
        row["Brent_forward_6m_return"] = forward_return(brent_values, i, 6)
        row.update(ci_metrics[i])
    return rows


def optional_series_map(series: Series | None) -> dict[str, float]:
    return series_map(series) if series is not None else {}


def real_price(price: float | None, cpi: float | None) -> float | None:
    return price / (cpi / 100.0) if price is not None and cpi not in (None, 0) else None


def trailing_average_deviation(values: list[float | None], i: int, window: int) -> float | None:
    if i < window or values[i] is None:
        return None
    history = [v for v in values[i - window : i] if v is not None]
    if len(history) < window:
        return None
    avg = sum(history) / len(history)
    return 100 * (float(values[i]) / avg - 1) if avg else None


def forward_return(values: list[float | None], i: int, horizon: int) -> float | None:
    if i + horizon >= len(values) or values[i] in (None, 0) or values[i + horizon] is None:
        return None
    return 100 * (float(values[i + horizon]) / float(values[i]) - 1)


def log_return(values: list[float | None], i: int) -> float | None:
    if i == 0 or values[i] in (None, 0) or values[i - 1] in (None, 0):
        return None
    return 100 * math.log(float(values[i]) / float(values[i - 1]))


def diff(left: object, right: object) -> float | None:
    if isinstance(left, (int, float)) and isinstance(right, (int, float)) and math.isfinite(float(left)) and math.isfinite(float(right)):
        return float(left) - float(right)
    return None


def comparative_inventory(months: list[str], values: list[float | None]) -> list[Row]:
    history: dict[int, list[float]] = defaultdict(list)
    previous: float | None = None
    out: list[Row] = []
    for month, value in zip(months, values):
        month_num = int(month[5:7])
        prior = history[month_num][-5:]
        if value is None or len(prior) < 5:
            comp = zscore = None
        else:
            avg = sum(prior) / len(prior)
            variance = sum((x - avg) ** 2 for x in prior) / len(prior)
            std = math.sqrt(variance)
            comp = value - avg
            zscore = comp / std if std else None
        change = value - previous if value is not None and previous is not None else None
        out.append({"comparative_inventory_kb": comp, "CI_zscore": zscore, "CI_monthly_change": change})
        if value is not None:
            history[month_num].append(value)
            previous = value
    return out
