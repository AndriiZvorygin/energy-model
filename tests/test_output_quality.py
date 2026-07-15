from oil_model.adapters import Series
from oil_model.output_quality import build_output_quality_dataset


def test_household_command_publishes_components_and_uses_fixed_price_basis() -> None:
    annual = lambda name, value: Series(name, "USD", "fixture", [("2024-01", value)])
    series = {
        "MEHOINUSA672N": annual("income", 80_000),
        "CXUSHELTERLB0101M": annual("shelter", 16_000),
        "CXUFOODTOTLLB0101M": annual("food", 10_000),
        "CXUUTILSLB0101M": annual("utilities", 4_000),
    }
    cpi = Series("CPI", "index", "fixture", [(f"2024-{month:02d}", 100.0) for month in range(1, 13)])
    rows, derived = build_output_quality_dataset(series, cpi)

    assert derived["HouseholdCommand"]["2024-01"] == 50_000
    published = {row["indicator"] for row in rows}
    assert {"MEHOINUSA672N", "CXUSHELTERLB0101M", "CXUFOODTOTLLB0101M", "CXUUTILSLB0101M", "HouseholdCommand"} <= published


def test_incomplete_year_is_not_presented_as_annual_gdp() -> None:
    series = {"GDPC1": Series("GDP", "billions", "fixture", [("2024-01", 1.0), ("2024-04", 2.0), ("2024-07", 3.0), ("2024-10", 4.0), ("2025-01", 5.0)])}
    cpi = Series("CPI", "index", "fixture", [(f"2024-{month:02d}", 100.0) for month in range(1, 13)])
    _, derived = build_output_quality_dataset(series, cpi)

    assert derived["real_gdp_annual"] == {"2024": 2.5}
