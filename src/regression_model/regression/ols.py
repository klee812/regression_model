"""OLS (Ordinary Least Squares) regression strategy."""

from __future__ import annotations

from sklearn.base import BaseEstimator
from sklearn.linear_model import LinearRegression

from regression_model.regression.pipeline import SklearnPipelineStrategy


class OLSStrategy(SklearnPipelineStrategy):
    """Ordinary Least Squares regression via a scaled sklearn pipeline."""

    def _make_estimator(self) -> BaseEstimator:
        """Create a ``LinearRegression`` estimator.

        Returns:
            A configured ``LinearRegression`` instance.
        """
        return LinearRegression(**self._kwargs)
