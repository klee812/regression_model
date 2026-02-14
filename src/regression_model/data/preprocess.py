"""Data validation, missing-value handling, and outlier treatment."""

from __future__ import annotations

import numpy as np

from regression_model.models import PriceData, ReturnsData
from regression_model.models.preprocessing_config import PreprocessingConfig


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_prices(prices: PriceData, config: PreprocessingConfig) -> PriceData:
    """Validate price data for positivity, duplicate dates, and sufficient rows.

    Args:
        prices: Wide-format target and driver price data.
        config: Preprocessing configuration.

    Returns:
        The same ``PriceData`` unchanged (raises on invalid data).
    """
    if not config.validate_prices:
        return prices

    for label, df in [("targets", prices.targets), ("drivers", prices.drivers)]:
        # All prices must be positive
        if (df <= 0).any().any():
            bad_cols = df.columns[(df <= 0).any()].tolist()
            raise ValueError(
                f"Non-positive prices found in {label} columns: {bad_cols}"
            )

        # No duplicate dates per FIGI
        if df.index.duplicated().any():
            raise ValueError(f"Duplicate dates found in {label} price index")

    # Sufficient observations
    min_rows = min(len(prices.targets), len(prices.drivers))
    if min_rows < config.min_observations:
        raise ValueError(
            f"Insufficient observations: {min_rows} rows "
            f"(minimum {config.min_observations} required)"
        )

    return prices


# ---------------------------------------------------------------------------
# Missing data
# ---------------------------------------------------------------------------

def handle_missing(prices: PriceData, config: PreprocessingConfig) -> PriceData:
    """Handle missing values in price data according to the configured strategy.

    Args:
        prices: Wide-format target and driver price data.
        config: Preprocessing configuration.

    Returns:
        A new ``PriceData`` with missing values handled.
    """
    method = config.missing_data_handler

    if method == "drop":
        targets = prices.targets.dropna()
        drivers = prices.drivers.dropna()
    elif method == "forward_fill":
        targets = prices.targets.ffill().dropna()
        drivers = prices.drivers.ffill().dropna()
    elif method == "interpolate":
        targets = prices.targets.interpolate(method="linear").dropna()
        drivers = prices.drivers.interpolate(method="linear").dropna()
    else:
        raise ValueError(f"Unknown missing_data_handler: {method!r}")

    return PriceData(targets=targets, drivers=drivers)


# ---------------------------------------------------------------------------
# Outliers (operate on returns)
# ---------------------------------------------------------------------------

def handle_outliers(
    returns: ReturnsData, config: PreprocessingConfig
) -> ReturnsData:
    """Detect and handle outliers in return data.

    Args:
        returns: Aligned return data for targets and drivers.
        config: Preprocessing configuration.

    Returns:
        A new ``ReturnsData`` with outliers handled.
    """
    method = config.outlier_method

    if method == "none":
        return returns

    if method in ("winsorize", "clip"):
        targets = _clip_outliers(returns.targets, config.outlier_threshold)
        drivers = _clip_outliers(returns.drivers, config.outlier_threshold)
        return ReturnsData(targets=targets, drivers=drivers)

    if method == "drop":
        targets, drivers = _drop_outlier_rows(
            returns.targets, returns.drivers, config.outlier_threshold
        )
        return ReturnsData(targets=targets, drivers=drivers)

    raise ValueError(f"Unknown outlier_method: {method!r}")


def _clip_outliers(df, threshold: float):
    """Clip values to [mean - threshold*std, mean + threshold*std] per column."""
    mean = df.mean()
    std = df.std()
    lower = mean - threshold * std
    upper = mean + threshold * std
    return df.clip(lower=lower, upper=upper, axis=1)


def _drop_outlier_rows(targets, drivers, threshold: float):
    """Drop rows where any return exceeds threshold standard deviations."""
    all_returns = targets.join(drivers, how="inner", lsuffix="_t", rsuffix="_d")
    z_scores = (all_returns - all_returns.mean()) / all_returns.std()
    mask = (np.abs(z_scores) <= threshold).all(axis=1)
    return targets.loc[mask], drivers.loc[mask]


# ---------------------------------------------------------------------------
# Convenience wrappers
# ---------------------------------------------------------------------------

def prepare_prices(prices: PriceData, config: PreprocessingConfig) -> PriceData:
    """Validate and clean price data (validation + missing-value handling).

    Args:
        prices: Raw loaded price data.
        config: Preprocessing configuration.

    Returns:
        Cleaned ``PriceData`` ready for return computation.
    """
    prices = validate_prices(prices, config)
    prices = handle_missing(prices, config)
    return prices


def prepare_returns(
    returns: ReturnsData, config: PreprocessingConfig
) -> ReturnsData:
    """Apply outlier handling to computed returns.

    Args:
        returns: Return data from ``prices_to_returns``.
        config: Preprocessing configuration.

    Returns:
        Cleaned ``ReturnsData`` ready for regression.
    """
    return handle_outliers(returns, config)
