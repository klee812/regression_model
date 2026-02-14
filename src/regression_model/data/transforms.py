"""Price-to-returns transformation with date alignment."""

from __future__ import annotations

from regression_model.models import PriceData, ReturnsData


def prices_to_returns(prices: PriceData) -> ReturnsData:
    """Convert price DataFrames to percent-change returns and align dates.

    The first row (NaN from ``pct_change``) is dropped since it is intrinsic
    to the return calculation.  Any other missing-value handling should be done
    upstream via :func:`regression_model.data.preprocess.handle_missing`.

    Args:
        prices: Wide-format target and driver price data.

    Returns:
        A ``ReturnsData`` instance with aligned return series.
    """
    target_ret = prices.targets.pct_change().iloc[1:]
    driver_ret = prices.drivers.pct_change().iloc[1:]

    # align on common dates
    common_dates = target_ret.index.intersection(driver_ret.index)
    target_ret = target_ret.loc[common_dates]
    driver_ret = driver_ret.loc[common_dates]

    return ReturnsData(targets=target_ret, drivers=driver_ret)
