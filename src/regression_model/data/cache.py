"""Parquet-based price cache for separating slow data generation from regression."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from regression_model.models import PriceData


def save_price_cache(prices: PriceData, path: str | Path) -> None:
    """Persist the full adjusted price table to a Parquet file.

    Concatenates targets and drivers into a single wide DataFrame so the cache
    is independent of any particular targets/drivers split.

    Args:
        prices: Normalized, adjusted, USD-denominated price data.
        path: Destination Parquet file path (created if missing).
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    wide = pd.concat([prices.targets, prices.drivers], axis=1)
    wide.to_parquet(path)
    print(f"Price cache saved to {path} ({wide.shape[1]} instruments, {wide.shape[0]} dates)")


def load_price_cache(
    path: str | Path,
    drivers: list[str],
    targets: list[str] | None = None,
) -> PriceData:
    """Load a price cache and split into targets and drivers.

    Args:
        path: Path to the Parquet file written by ``save_price_cache``.
        drivers: Driver FIGIs — must match columns in the cache.
        targets: Target FIGIs, or ``None`` to use all instruments except drivers.

    Returns:
        A ``PriceData`` instance ready for preprocessing and regression.

    Raises:
        FileNotFoundError: If the cache file does not exist.
        ValueError: If any driver FIGI is missing from the cache.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"Price cache not found: {path}\n"
            "Run 'python -m regression_model prepare config.yaml' first."
        )

    wide = pd.read_parquet(path)

    missing = [d for d in drivers if d not in wide.columns]
    if missing:
        raise ValueError(f"Driver FIGIs not found in cache: {missing}")

    if not targets:
        targets = [c for c in wide.columns if c not in set(drivers)]

    return PriceData(targets=wide[targets], drivers=wide[drivers])
