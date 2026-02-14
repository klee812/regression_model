"""CSV data loading and pivoting from long to wide format."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from regression_model.models import AppConfig, PriceData


def _load_csv(path: str | Path, figis: list[str]) -> pd.DataFrame:
    """Load a long-format CSV (date, figi, close) and pivot to wide format.

    Args:
        path: Filesystem path to the CSV file.
        figis: FIGI identifiers to keep.

    Returns:
        A wide-format DataFrame indexed by date with one column per FIGI.
    """
    df = pd.read_csv(path, parse_dates=["date"])
    df = df[df["figi"].isin(figis)]
    wide = df.pivot(index="date", columns="figi", values="close")
    wide = wide.sort_index()
    return wide[figis]  # enforce column order


def load_all(config: AppConfig) -> PriceData:
    """Load target and driver price CSVs specified in the config.

    Args:
        config: Application configuration with data paths and FIGI lists.

    Returns:
        A ``PriceData`` instance with wide-format target and driver prices.
    """
    targets = _load_csv(config.data.targets_path, config.targets)
    drivers = _load_csv(config.data.drivers_path, config.drivers)
    return PriceData(targets=targets, drivers=drivers)
