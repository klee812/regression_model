"""Protocol defining the regression strategy interface."""

from __future__ import annotations

from typing import Protocol

import pandas as pd

from regression_model.models import RegressionResult


class RegressionStrategy(Protocol):
    """Interface that all regression strategies must satisfy."""

    def fit(
        self,
        target_figi: str,
        y: pd.Series,
        x: pd.DataFrame,
    ) -> RegressionResult:
        """Fit the model and return a result.

        Args:
            target_figi: Identifier for the regression target.
            y: Target return series.
            x: Driver return DataFrame.

        Returns:
            A ``RegressionResult`` with fitted coefficients and diagnostics.
        """
        ...
