"""Lars (Least Angle Regression) strategy."""

from __future__ import annotations

from sklearn.base import BaseEstimator
from sklearn.linear_model import Lars

from regression_model.regression.pipeline import SklearnPipelineStrategy


class LarsStrategy(SklearnPipelineStrategy):
    """Least Angle Regression via a scaled sklearn pipeline."""

    def _make_estimator(self) -> BaseEstimator:
        """Create a ``Lars`` estimator.

        Returns:
            A configured ``Lars`` instance.
        """
        return Lars(**self._kwargs)
