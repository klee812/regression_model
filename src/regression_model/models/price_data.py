"""Container for loaded price data."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass
class PriceData:
    """Wide-format price DataFrames for targets and drivers."""

    targets: pd.DataFrame  # index=date, columns=FIGI
    drivers: pd.DataFrame  # index=date, columns=FIGI
