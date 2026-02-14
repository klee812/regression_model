"""ElasticNet (L1+L2 regularized) regression strategy."""

from __future__ import annotations

from sklearn.base import BaseEstimator
from sklearn.linear_model import ElasticNet

from regression_model.regression.pipeline import SklearnPipelineStrategy


class ElasticNetStrategy(SklearnPipelineStrategy):
    """ElasticNet regression via a scaled sklearn pipeline."""

    def _make_estimator(self) -> BaseEstimator:
        """Create an ``ElasticNet`` estimator.

        Returns:
            A configured ``ElasticNet`` instance.
        """
        return ElasticNet(**self._kwargs)
