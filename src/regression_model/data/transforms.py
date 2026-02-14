"""Price-to-returns transformation with date alignment."""

from __future__ import annotations

from regression_model.models import PriceData, ReturnsData


def prices_to_returns(prices: PriceData) -> ReturnsData:
    """Convert price DataFrames to percent-change returns, align dates, drop NaNs.

    Args:
        prices: Wide-format target and driver price data.

    Returns:
        A ``ReturnsData`` instance with aligned, NaN-free return series.
    """
    target_ret = prices.targets.pct_change().iloc[1:]
    driver_ret = prices.drivers.pct_change().iloc[1:]

    # align on common dates
    common_dates = target_ret.index.intersection(driver_ret.index)
    target_ret = target_ret.loc[common_dates]
    driver_ret = driver_ret.loc[common_dates]

    # drop any rows with NaN
    mask = target_ret.notna().all(axis=1) & driver_ret.notna().all(axis=1)
    target_ret = target_ret.loc[mask]
    driver_ret = driver_ret.loc[mask]

    return ReturnsData(targets=target_ret, drivers=driver_ret)
