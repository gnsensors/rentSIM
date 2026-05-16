"""
Shenandoah Valley VA — Monthly Rent Estimator
==============================================
Estimates monthly LTR rent from property value for:
  - Woodstock, VA      (Shenandoah County)
  - Strasburg, VA      (Shenandoah County)
  - Front Royal, VA    (Warren County)
  - Winchester, VA     (independent city / Frederick County)
"""

import random
from typing import Literal

Market = Literal["woodstock", "strasburg", "front_royal", "winchester"]
Bedrooms = Literal[1, 2, 3, 4, 5]

_MARKETS: dict[str, tuple[float, int, int, str]] = {
    "woodstock":   (0.00560, 900,  3_200, "Woodstock, VA (Shenandoah County)"),
    "strasburg":   (0.00520, 850,  2_800, "Strasburg, VA (Shenandoah County)"),
    "front_royal": (0.00600, 950,  3_500, "Front Royal, VA (Warren County)"),
    "winchester":  (0.00470, 950,  3_800, "Winchester, VA (City/Frederick County)"),
}

_BEDROOM_FACTORS: dict[int, float] = {
    1: 0.65,
    2: 0.82,
    3: 1.00,
    4: 1.22,
    5: 1.40,
}

_MARKET_KEYS    = list(_MARKETS.keys())
_MARKET_WEIGHTS = [0.25, 0.25, 0.25, 0.25]
_BEDROOM_KEYS    = list(_BEDROOM_FACTORS.keys())
_BEDROOM_WEIGHTS = [0.08, 0.22, 0.45, 0.20, 0.05]


def estimate_monthly_rent(
    property_value: float,
    market: Market,
    bedrooms: Bedrooms = 3,
) -> dict:
    market_key = market.lower().replace(" ", "_")
    if market_key not in _MARKETS:
        raise ValueError(f"Unknown market '{market}'. Choose from: {list(_MARKETS.keys())}")
    if bedrooms not in _BEDROOM_FACTORS:
        raise ValueError(f"Bedrooms must be 1-5, got {bedrooms}")

    yield_pct, floor_rent, ceiling_rent, label = _MARKETS[market_key]
    bd_factor = _BEDROOM_FACTORS[bedrooms]

    base_raw  = property_value * yield_pct
    base_rent = int(round(max(floor_rent, min(ceiling_rent, base_raw)) / 25) * 25)

    adjusted_raw  = base_rent * bd_factor
    bd_floor      = int(floor_rent * bd_factor)
    bd_ceil       = int(ceiling_rent * bd_factor)
    adjusted_rent = int(round(max(bd_floor, min(bd_ceil, adjusted_raw)) / 25) * 25)

    monthly_rent = adjusted_rent
    annual_rent  = monthly_rent * 12
    gross_yield  = round(annual_rent / property_value * 100, 2)
    range_low    = int(round(monthly_rent * 0.90 / 25) * 25)
    range_high   = int(round(monthly_rent * 1.15 / 25) * 25)

    market_notes = {
        "woodstock":   "Rural Shenandoah Valley. Limited rental inventory keeps vacancy low. 3BR homes listed $1,400-$2,800; avg $1,830.",
        "strasburg":   "Small town, lowest rents in group. 3BR listings $1,400-$1,600. Median home $312K (Redfin 2025).",
        "front_royal": "Highest rent yield — NOVA commuter demand via I-66/US-340. 3BR avg $1,921 (Rentometer).",
        "winchester":  "Most urban market; largest renter pool. 3BR avg $1,800-$1,900; median $380K home (Redfin 2026).",
    }

    return {
        "market_label":    label,
        "market_key":      market_key,
        "property_value":  property_value,
        "bedrooms":        bedrooms,
        "base_rent":       base_rent,
        "monthly_rent":    monthly_rent,
        "annual_rent":     annual_rent,
        "gross_yield_pct": gross_yield,
        "rent_range_low":  range_low,
        "rent_range_high": range_high,
        "notes":           market_notes[market_key],
    }


def get_rent(house_price: float) -> tuple[int, dict]:
    market   = random.choices(_MARKET_KEYS,  weights=_MARKET_WEIGHTS)[0]
    bedrooms = random.choices(_BEDROOM_KEYS, weights=_BEDROOM_WEIGHTS)[0]
    result   = estimate_monthly_rent(house_price, market, bedrooms)
    monthly_rent = result["monthly_rent"]
    data = {k: v for k, v in result.items() if k != "monthly_rent"}
    return monthly_rent, data
