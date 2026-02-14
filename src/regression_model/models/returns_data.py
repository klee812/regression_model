"""Container for computed returns data."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass
class ReturnsData:
    """Percent-change returns with aligned dates for targets and drivers."""

    targets: pd.DataFrame
    drivers: pd.DataFrame
