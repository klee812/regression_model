"""Parquet-based price cache for separating slow data generation from regression."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from regression_model.models import PriceData


def save_price_cache(wide: pd.DataFrame, path: str | Path) -> None:
    """Persist the full adjusted price DataFrame to a Parquet file.

    Args:
        wide: Adjusted, USD-denominated wide DataFrame (date index, ISIN columns).
        path: Destination Parquet file path (created if missing).
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    wide.to_parquet(path)
    print(f"Price cache saved to {path} ({wide.shape[1]} instruments, {wide.shape[0]} dates)")


def load_price_cache(
    path: str | Path,
    drivers: list[str],
    targets: list[str] | None = None,
) -> PriceData:
    """Load the price cache and split into targets and drivers.

    Args:
        path: Path to the Parquet file written by ``save_price_cache``.
        drivers: Driver ISINs — must match columns in the cache.
        targets: Target ISINs, or ``None`` to use all instruments except drivers.

    Returns:
        A ``PriceData`` instance ready for preprocessing and regression.

    Raises:
        FileNotFoundError: If the cache file does not exist.
        ValueError: If any driver is missing from the cache.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"Price cache not found: {path}\n"
            "Run 'python -m regression_model prepare' first."
        )

    wide = pd.read_parquet(path)

    missing = [d for d in drivers if d not in wide.columns]
    if missing:
        raise ValueError(f"Drivers not found in cache: {missing}")

    if not targets:
        targets = [c for c in wide.columns if c not in set(drivers)]

    return PriceData(targets=wide[targets], drivers=wide[drivers])


if __name__ == "__main__":
    # ── PyCharm debug entry point ─────────────────────────────────
    # Run this file directly to step through cache load.
    from regression_model.config import load_config
    from regression_model.settings import DEFAULT_CONFIG_PATH
    _config = load_config(DEFAULT_CONFIG_PATH)
    _result = load_price_cache(_config.cache_path, _config.drivers, _config.targets)
    print(_result)
