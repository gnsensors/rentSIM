"""
Shenandoah Valley VA — Monthly Rent Estimator
==============================================
Estimates monthly LTR rent from property value for:
  - Woodstock, VA      (Shenandoah County)
  - Strasburg, VA      (Shenandoah County)
  - Front Royal, VA    (Warren County)
  - Winchester, VA     (independent city / Frederick County)

Market data sources (2025-2026):
  - Woodstock:   median home $337K, median rent $1,575 (HotPads/Long&Foster/ApartmentHomeLiving)
                 3BR homes $1,400-$2,800, avg $1,830
  - Strasburg:   median home $312K (Redfin Sep 2025), avg rent $999-$1,200
                 3BR renovated homes listed at $1,400-$1,600
  - Front Royal: median home ~$300K, 3BR avg $1,921 (Rentometer),
                 median all-types $1,800 (Zumper Apr 2026)
  - Winchester:  median home $380K (Redfin Feb 2026), 3BR avg $1,800-$1,900
                 median rent $1,597-$1,801 (RentHop/Zillow 2025-2026)

Methodology:
  Each market is modeled with a gross rent multiplier (GRM) derived from
  observed median home price / median monthly rent pairs, then capped and
  floored at realistic market extremes. A bedroom-count adjustment shifts
  the base estimate up or down. Results are rounded to nearest $25.

  GRM = Annual Rent / Property Value  (inverse = rent yield)
  Estimated rent = Property Value * rent_yield

  Observed rent yields by market:
    Woodstock:   ~0.56% / month  ($1,575 / $337K)  — rural, limited supply
    Strasburg:   ~0.52% / month  ($1,100 / $215K median actuals)
    Front Royal: ~0.60% / month  ($1,800 / $300K)  — stronger demand, NOVA commuters
    Winchester:  ~0.47% / month  ($1,800 / $380K)  — most urban, most expensive
"""

import random
from typing import Literal

Market = Literal["woodstock", "strasburg", "front_royal", "winchester"]
Bedrooms = Literal[1, 2, 3, 4, 5]


# ── Market parameters ────────────────────────────────────────────────────────
# Each entry: (monthly_rent_yield, floor_rent, ceiling_rent, label)
# rent_yield = monthly rent as % of property value (based on observed data)
# floor/ceiling = absolute min/max regardless of property value

_MARKETS: dict[str, tuple[float, int, int, str]] = {
    "woodstock":   (0.00560, 900,  3_200, "Woodstock, VA (Shenandoah County)"),
    "strasburg":   (0.00520, 850,  2_800, "Strasburg, VA (Shenandoah County)"),
    "front_royal": (0.00600, 950,  3_500, "Front Royal, VA (Warren County)"),
    "winchester":  (0.00470, 950,  3_800, "Winchester, VA (City/Frederick County)"),
}

# ── Bedroom adjustment factors (relative to 3BR baseline) ───────────────────
# 3BR = 1.00 (baseline — most common rental unit in these markets)
_BEDROOM_FACTORS: dict[int, float] = {
    1: 0.65,   # 1BR ~65% of 3BR rent
    2: 0.82,   # 2BR ~82% of 3BR rent
    3: 1.00,   # 3BR baseline
    4: 1.22,   # 4BR ~22% premium
    5: 1.40,   # 5BR ~40% premium
}

# ── Sampling weights for get_rent() ─────────────────────────────────────────
# Market weights: equal across the four markets
_MARKET_KEYS    = list(_MARKETS.keys())
_MARKET_WEIGHTS = [0.25, 0.25, 0.25, 0.25]

# Bedroom weights: reflect real-world rental distribution (3BR most common)
_BEDROOM_KEYS    = list(_BEDROOM_FACTORS.keys())          # [1, 2, 3, 4, 5]
_BEDROOM_WEIGHTS = [0.08, 0.22, 0.45, 0.20, 0.05]


def estimate_monthly_rent(
    property_value: float,
    market: Market,
    bedrooms: Bedrooms = 3,
    verbose: bool = False,
) -> dict:
    """
    Estimate monthly long-term rental income for a single-family home.

    Parameters
    ----------
    property_value : float
        Purchase / assessed value of the property in USD.
    market : str
        One of: 'woodstock', 'strasburg', 'front_royal', 'winchester'
    bedrooms : int
        Number of bedrooms (1-5). Default 3.
    verbose : bool
        If True, print a formatted summary.

    Returns
    -------
    dict with keys:
        market_label     : str   — human-readable market name
        property_value   : float — input value
        bedrooms         : int   — bedroom count used
        base_rent        : int   — 3BR baseline estimate
        adjusted_rent    : int   — bedroom-adjusted estimate
        monthly_rent     : int   — final rounded estimate (same as adjusted_rent)
        annual_rent      : int   — monthly * 12
        gross_yield_pct  : float — annual rent / property value * 100
        rent_range_low   : int   — conservative estimate (-10%)
        rent_range_high  : int   — optimistic estimate (+15%)
        notes            : str   — market context

    Examples
    --------
    >>> result = estimate_monthly_rent(300_000, "woodstock", bedrooms=3)
    >>> result["monthly_rent"]
    1675

    >>> estimate_monthly_rent(400_000, "winchester", bedrooms=4, verbose=True)
    """
    market_key = market.lower().replace(" ", "_")
    if market_key not in _MARKETS:
        raise ValueError(
            f"Unknown market '{market}'. "
            f"Choose from: {list(_MARKETS.keys())}"
        )
    if bedrooms not in _BEDROOM_FACTORS:
        raise ValueError(f"Bedrooms must be 1-5, got {bedrooms}")

    yield_pct, floor_rent, ceiling_rent, label = _MARKETS[market_key]
    bd_factor = _BEDROOM_FACTORS[bedrooms]

    # Base estimate (3BR)
    base_raw = property_value * yield_pct
    base_rent = int(round(max(floor_rent, min(ceiling_rent, base_raw)) / 25) * 25)

    # Bedroom-adjusted estimate
    adjusted_raw = base_rent * bd_factor
    # Re-apply floor/ceiling with bedroom scaling
    bd_floor = int(floor_rent * bd_factor)
    bd_ceil  = int(ceiling_rent * bd_factor)
    adjusted_rent = int(round(max(bd_floor, min(bd_ceil, adjusted_raw)) / 25) * 25)

    monthly_rent  = adjusted_rent
    annual_rent   = monthly_rent * 12
    gross_yield   = round(annual_rent / property_value * 100, 2)
    range_low     = int(round(monthly_rent * 0.90 / 25) * 25)
    range_high    = int(round(monthly_rent * 1.15 / 25) * 25)

    market_notes = {
        "woodstock":   "Rural Shenandoah Valley. Limited rental inventory keeps vacancy low. "
                       "3BR homes listed $1,400-$2,800; avg $1,830. Strong I-81 corridor demand.",
        "strasburg":   "Small town, lowest rents in group. Fewer comparable rentals; "
                       "3BR listings $1,400-$1,600. Median home $312K (Redfin 2025).",
        "front_royal": "Highest rent yield in group — NOVA commuter demand via I-66/US-340. "
                       "3BR avg $1,921 (Rentometer); median all-types $1,800 (Zumper Apr 2026).",
        "winchester":  "Most urban market; largest renter pool but also most supply. "
                       "3BR avg $1,800-$1,900; median $380K home price (Redfin Feb 2026).",
    }

    result = {
        "market_label":    label,
        "property_value":  property_value,
        "bedrooms":        bedrooms,
        "base_rent":       base_rent,
        "adjusted_rent":   adjusted_rent,
        "monthly_rent":    monthly_rent,
        "annual_rent":     annual_rent,
        "gross_yield_pct": gross_yield,
        "rent_range_low":  range_low,
        "rent_range_high": range_high,
        "notes":           market_notes[market_key],
    }

    if verbose:
        _print_summary(result)

    return result


def _print_summary(r: dict) -> None:
    print(f"\n{'='*58}")
    print(f"  {r['market_label']}")
    print(f"{'='*58}")
    print(f"  Property Value  : ${r['property_value']:>10,.0f}")
    print(f"  Bedrooms        : {r['bedrooms']}")
    print(f"  ─────────────────────────────────────────────────")
    print(f"  Estimated Rent  : ${r['monthly_rent']:>10,.0f} / month")
    print(f"  Rent Range      : ${r['rent_range_low']:,.0f} – ${r['rent_range_high']:,.0f} / month")
    print(f"  Annual Rent     : ${r['annual_rent']:>10,.0f}")
    print(f"  Gross Yield     : {r['gross_yield_pct']:>9.2f}%")
    print(f"  ─────────────────────────────────────────────────")
    print(f"  Note: {r['notes'][:52]}")
    print(f"        {r['notes'][52:]}")
    print()


def compare_markets(
    property_value: float,
    bedrooms: Bedrooms = 3,
) -> None:
    """
    Print a side-by-side comparison across all four markets
    for a given property value and bedroom count.

    Parameters
    ----------
    property_value : float
        Property value in USD.
    bedrooms : int
        Number of bedrooms (1-5).

    Example
    -------
    >>> compare_markets(300_000, bedrooms=3)
    """
    print(f"\n{'='*68}")
    print(f"  RENT COMPARISON — ${property_value:,.0f} property, {bedrooms} bedrooms")
    print(f"{'='*68}")
    print(f"  {'Market':<32} {'Rent/mo':>9}  {'Range':>22}  {'Yield':>6}")
    print(f"  {'-'*32} {'-'*9}  {'-'*22}  {'-'*6}")
    for mkt in ["woodstock", "strasburg", "front_royal", "winchester"]:
        r = estimate_monthly_rent(property_value, mkt, bedrooms)
        rng = f"${r['rent_range_low']:,} – ${r['rent_range_high']:,}"
        print(
            f"  {r['market_label']:<32} ${r['monthly_rent']:>8,}  "
            f"{rng:>22}  {r['gross_yield_pct']:>5.2f}%"
        )
    print()


def get_rent(house_price: float) -> tuple[int, dict]:
    """
    Return a randomized rent estimate for a property at the given price.

    Market and bedroom count are sampled from weighted distributions that
    reflect the real-world mix in the Shenandoah Valley rental market.

    Parameters
    ----------
    house_price : float
        Purchase / assessed value of the property in USD.

    Returns
    -------
    (monthly_rent, data)
        monthly_rent : int  — estimated monthly rent in USD
        data         : dict — all other fields from estimate_monthly_rent()
                       including market_label, bedrooms, annual_rent,
                       gross_yield_pct, rent_range_low, rent_range_high, notes

    Example
    -------
    >>> rent, data = get_rent(300_000)
    >>> print(rent, data["market_label"], data["bedrooms"])
    """
    market   = random.choices(_MARKET_KEYS,   weights=_MARKET_WEIGHTS)[0]
    bedrooms = random.choices(_BEDROOM_KEYS,  weights=_BEDROOM_WEIGHTS)[0]
    result   = estimate_monthly_rent(house_price, market, bedrooms)
    monthly_rent = result["monthly_rent"]
    data = {k: v for k, v in result.items() if k != "monthly_rent"}
    return monthly_rent, data


# ── Demo ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n── Single property estimate ─────────────────────────────────")
    estimate_monthly_rent(300_000, "woodstock", bedrooms=3, verbose=True)

    print("\n── Portfolio scenario: 5 × $300K across markets ─────────────")
    compare_markets(300_000, bedrooms=3)

    print("\n── How rent scales with property value (Winchester, 3BR) ────")
    print(f"  {'Value':>10}  {'Rent/mo':>9}  {'Yield':>6}")
    print(f"  {'-'*10}  {'-'*9}  {'-'*6}")
    for val in [200_000, 250_000, 300_000, 350_000, 400_000, 450_000, 500_000]:
        r = estimate_monthly_rent(val, "winchester", bedrooms=3)
        print(f"  ${val:>9,}  ${r['monthly_rent']:>8,}  {r['gross_yield_pct']:>5.2f}%")

    print("\n── Bedroom scaling (Woodstock, $300K property) ──────────────")
    print(f"  {'Bedrooms':>8}  {'Rent/mo':>9}  {'Annual':>10}")
    print(f"  {'-'*8}  {'-'*9}  {'-'*10}")
    for bd in [1, 2, 3, 4, 5]:
        r = estimate_monthly_rent(300_000, "woodstock", bedrooms=bd)
        print(f"  {bd:>8}  ${r['monthly_rent']:>8,}  ${r['annual_rent']:>9,}")
