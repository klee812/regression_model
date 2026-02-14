"""Lasso (L1-regularized) regression strategy."""

from __future__ import annotations

from sklearn.base import BaseEstimator
from sklearn.linear_model import Lasso

from regression_model.regression.pipeline import SklearnPipelineStrategy


class LassoStrategy(SklearnPipelineStrategy):
    """Lasso regression via a scaled sklearn pipeline."""

    def _make_estimator(self) -> BaseEstimator:
        """Create a ``Lasso`` estimator.

        Returns:
            A configured ``Lasso`` instance.
        """
        return Lasso(**self._kwargs)
