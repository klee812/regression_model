"""Market data normalization: corporate actions, dividends, and FX conversion."""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd

from regression_model.models import PriceData


def build_price_table(
    records: Iterable[dict],
) -> tuple[pd.DataFrame, dict[str, str]]:
    """Convert price dicts to a wide DataFrame and currency mapping.

    Args:
        records: Dicts with keys ``identifier``, ``currency``, ``date``, ``price``.

    Returns:
        A tuple of (wide DataFrame indexed by date, {identifier: currency} mapping).
    """
    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"])
    df["price"] = df["price"].astype(float)

    currencies: dict[str, str] = (
        df.groupby("identifier")["currency"].first().to_dict()
    )

    wide = df.pivot(index="date", columns="identifier", values="price")
    wide = wide.sort_index()
    return wide, currencies


def adjust_for_corp_actions(
    prices: pd.DataFrame, records: Iterable[dict]
) -> pd.DataFrame:
    """Apply backward corporate-action adjustments to prices.

    For each event, all prices strictly before ``ex_date`` are multiplied by
    ``ratio_price_adjustment``.  Events are processed from latest to earliest.

    Args:
        prices: Wide price DataFrame (date index, identifier columns).
        records: Dicts with ``identifier``, ``ex_date``, ``ratio_price_adjustment``.

    Returns:
        Adjusted copy of *prices*.
    """
    events = sorted(records, key=lambda r: r["ex_date"], reverse=True)
    if not events:
        return prices.copy()

    prices = prices.copy()
    for evt in events:
        ident = evt["identifier"]
        ex_date = pd.Timestamp(evt["ex_date"])
        ratio = float(evt["ratio_price_adjustment"])
        if ident in prices.columns:
            mask = prices.index < ex_date
            prices.loc[mask, ident] *= ratio
    return prices


def adjust_for_dividends(
    prices: pd.DataFrame, records: Iterable[dict]
) -> pd.DataFrame:
    """Apply backward dividend adjustments to prices.

    For each event, all prices strictly before ``ex_date`` have
    ``div_amount`` subtracted and are then divided by ``ratio_shares_adjustment``.
    Events are processed from latest to earliest.

    Args:
        prices: Wide price DataFrame (date index, identifier columns).
        records: Dicts with ``identifier``, ``ex_date``, ``ratio_shares_adjustment``,
            ``div_amount``.

    Returns:
        Adjusted copy of *prices*.
    """
    events = sorted(records, key=lambda r: r["ex_date"], reverse=True)
    if not events:
        return prices.copy()

    prices = prices.copy()
    for evt in events:
        ident = evt["identifier"]
        ex_date = pd.Timestamp(evt["ex_date"])
        div_amount = float(evt["div_amount"])
        ratio = float(evt["ratio_shares_adjustment"])
        if ident in prices.columns:
            mask = prices.index < ex_date
            prices.loc[mask, ident] = (
                prices.loc[mask, ident] - div_amount
            ) / ratio
    return prices


def convert_to_usd(
    prices: pd.DataFrame,
    currencies: dict[str, str],
    records: Iterable[dict],
) -> pd.DataFrame:
    """Convert non-USD prices to USD using FX rate data.

    Rates are expressed as foreign currency units per 1 USD, so
    ``price_usd = price_local / rate``.  Missing FX dates are forward-filled.

    Args:
        prices: Wide price DataFrame (date index, identifier columns).
        currencies: ``{identifier: currency}`` mapping.
        records: Dicts with ``date``, ``fxsymbol``, ``rate``.

    Returns:
        Prices converted to USD.

    Raises:
        ValueError: If a required currency has no FX data.
    """
    non_usd = {
        ident: ccy
        for ident, ccy in currencies.items()
        if ccy.upper() != "USD" and ident in prices.columns
    }
    if not non_usd:
        return prices.copy()

    fx_df = pd.DataFrame(records)
    if fx_df.empty:
        missing = set(non_usd.values())
        raise ValueError(f"No FX data provided for currencies: {missing}")

    fx_df["date"] = pd.to_datetime(fx_df["date"])
    fx_df["rate"] = fx_df["rate"].astype(float)
    fx_wide = fx_df.pivot(index="date", columns="fxsymbol", values="rate")
    fx_wide = fx_wide.sort_index()

    # Merge FX and price date indices so that FX rates on non-price dates
    # can forward-fill into price dates that follow them.
    combined = fx_wide.index.union(prices.index).sort_values()
    fx_wide = fx_wide.reindex(combined).ffill().loc[prices.index]

    prices = prices.copy()
    for ident, ccy in non_usd.items():
        if ccy not in fx_wide.columns:
            raise ValueError(
                f"No FX rate data for currency '{ccy}' "
                f"(needed by identifier '{ident}')"
            )
        prices[ident] = prices[ident] / fx_wide[ccy]
    return prices


def normalize(
    prices: Iterable[dict],
    corp_actions: Iterable[dict],
    dividends: Iterable[dict],
    fx_rates: Iterable[dict],
    targets: list[str],
    drivers: list[str],
) -> PriceData:
    """Full normalization pipeline: build, adjust, convert, split.

    Args:
        prices: Price record dicts.
        corp_actions: Corporate action record dicts.
        dividends: Dividend record dicts.
        fx_rates: FX rate record dicts.
        targets: Identifier list for target securities.
        drivers: Identifier list for driver securities.

    Returns:
        A ``PriceData`` with adjusted, USD-denominated target and driver prices.
    """
    price_records = list(prices)
    ca_records = list(corp_actions)
    div_records = list(dividends)
    fx_records = list(fx_rates)

    wide, currencies = build_price_table(price_records)
    wide = adjust_for_corp_actions(wide, ca_records)
    wide = adjust_for_dividends(wide, div_records)
    wide = convert_to_usd(wide, currencies, fx_records)

    return PriceData(
        targets=wide[targets],
        drivers=wide[drivers],
    )
