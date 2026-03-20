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
        records: Dicts with keys ``figi``, ``pricedate``, ``Price``, ``currency``.

    Returns:
        A tuple of (wide DataFrame indexed by date, {figi: currency} mapping).
    """
    df = pd.DataFrame(records)
    df["pricedate"] = pd.to_datetime(df["pricedate"])
    df["Price"] = df["Price"].astype(float)

    currencies: dict[str, str] = (
        df.groupby("figi")["currency"].first().to_dict()
    )

    wide = df.pivot(index="pricedate", columns="figi", values="Price")
    wide = wide.sort_index()
    return wide, currencies


def adjust_for_corp_actions(
    prices: pd.DataFrame, records: Iterable[dict]
) -> pd.DataFrame:
    """Apply backward corporate-action adjustments to prices.

    For each event, all prices strictly before ``XdDate`` are multiplied by
    ``PriceAdjustmentFactor``.  Events are processed from latest to earliest.

    Args:
        prices: Wide price DataFrame (date index, identifier columns).
        records: Dicts with ``figi``, ``XdDate``, ``PriceAdjustmentFactor``.
            Other keys (``Bloomberg``, ``MIC``, ``Name``, ``SecurityType``,
            ``ShareAdjustmentFactor``, ...) are ignored.

    Returns:
        Adjusted copy of *prices*.
    """
    events = sorted(records, key=lambda r: r["XdDate"], reverse=True)
    if not events:
        return prices.copy()

    prices = prices.copy()
    for evt in events:
        ident = evt["figi"]
        ex_date = pd.Timestamp(evt["XdDate"])
        ratio = float(evt["PriceAdjustmentFactor"])
        if ident in prices.columns:
            mask = prices.index < ex_date
            prices.loc[mask, ident] *= ratio
    return prices


def adjust_for_dividends(
    prices: pd.DataFrame, records: Iterable[dict]
) -> pd.DataFrame:
    """Apply backward dividend adjustments to prices.

    For each event, all prices strictly before ``XdDate`` have ``NetAmount``
    subtracted.  Events are processed from latest to earliest.

    Args:
        prices: Wide price DataFrame (date index, identifier columns).
        records: Dicts with ``figi``, ``XdDate``, ``NetAmount``, ``GrossAmount``.
            Optional keys: ``PayDate``, ``AnnounceDate``, ``DividendType``,
            ``Bloomberg``.

    Returns:
        Adjusted copy of *prices*.
    """
    events = sorted(records, key=lambda r: r["XdDate"], reverse=True)
    if not events:
        return prices.copy()

    prices = prices.copy()
    for evt in events:
        ident = evt["figi"]
        ex_date = pd.Timestamp(evt["XdDate"])
        div_amount = float(evt["NetAmount"])
        if ident in prices.columns:
            mask = prices.index < ex_date
            prices.loc[mask, ident] -= div_amount
    return prices


def convert_to_usd(
    prices: pd.DataFrame,
    currencies: dict[str, str],
    records: Iterable[dict],
) -> pd.DataFrame:
    """Convert non-USD prices to USD using FX rate data.

    Rates are looked up by ``fromcurrencycode`` (e.g. "GBP") and assumed to
    express the number of ``fromcurrencycode`` units per 1 USD, so that
    ``price_usd = price_local / rate``.  Missing FX dates are forward-filled.

    Args:
        prices: Wide price DataFrame (date index, identifier columns).
        currencies: ``{identifier: currency}`` mapping.
        records: Dicts with ``pricedate``, ``fromcurrencycode``,
            ``tocurrencycode``, ``value``.

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

    fx_df["pricedate"] = pd.to_datetime(fx_df["pricedate"])
    fx_df["value"] = fx_df["value"].astype(float)
    fx_wide = fx_df.pivot(index="pricedate", columns="fromcurrencycode", values="value")
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
        # KEVIN_CHECK_HERE: assumes value = fromcurrency-per-USD (divide to convert).
        # If your feed is USD-per-fromcurrency, change / to *.
        prices[ident] = prices[ident] / fx_wide[ccy]
    return prices


def build_adjusted_prices(
    prices: Iterable[dict],
    corp_actions: Iterable[dict],
    dividends: Iterable[dict],
    fx_rates: Iterable[dict],
) -> pd.DataFrame:
    """Normalize prices without splitting into targets/drivers.

    Used by the prepare step — FIGI resolution and target/driver split
    happen later at run time.

    Args:
        prices: Price record dicts.
        corp_actions: Corporate action record dicts.
        dividends: Dividend record dicts.
        fx_rates: FX rate record dicts.

    Returns:
        Wide adjusted, USD-denominated DataFrame (date index, ISIN columns).
    """
    wide, currencies = build_price_table(list(prices))
    wide = adjust_for_corp_actions(wide, list(corp_actions))
    wide = adjust_for_dividends(wide, list(dividends))
    wide = convert_to_usd(wide, currencies, list(fx_rates))
    return wide


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

    if not targets:
        targets = [c for c in wide.columns if c not in set(drivers)]

    return PriceData(
        targets=wide[targets],
        drivers=wide[drivers],
    )
