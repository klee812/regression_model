"""Abstract base class for sklearn Pipeline-based regression strategies."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from regression_model.models import RegressionResult


class SklearnPipelineStrategy(ABC):
    """Base class that wraps an sklearn estimator in a StandardScaler pipeline.

    Subclasses only need to implement ``_make_estimator`` to return the
    concrete sklearn estimator (e.g. ``LinearRegression``, ``Lasso``).

    The pipeline scales features before fitting, then back-transforms
    the learned coefficients to the original (unscaled) feature space
    so that betas are directly interpretable.
    """

    def __init__(self, **kwargs: Any) -> None:
        """Store keyword arguments to forward to the estimator constructor.

        Args:
            **kwargs: Parameters passed to the underlying sklearn estimator.
        """
        self._kwargs = kwargs

    @abstractmethod
    def _make_estimator(self) -> BaseEstimator:
        """Create and return the sklearn estimator instance.

        Returns:
            A configured sklearn estimator.
        """

    def fit(
        self,
        target_figi: str,
        y: pd.Series,
        x: pd.DataFrame,
    ) -> RegressionResult:
        """Fit a scaled pipeline and return back-transformed coefficients.

        Args:
            target_figi: Identifier for the regression target.
            y: Target return series.
            x: Driver return DataFrame.

        Returns:
            A ``RegressionResult`` with coefficients in the original space.
        """
        pipe = Pipeline([
            ("scaler", StandardScaler()),
            ("estimator", self._make_estimator()),
        ])
        pipe.fit(x, y)

        # Back-transform coefficients from scaled space to original space
        scaler: StandardScaler = pipe.named_steps["scaler"]
        estimator = pipe.named_steps["estimator"]

        scale: np.ndarray = scaler.scale_  # type: ignore[assignment]
        mean: np.ndarray = scaler.mean_  # type: ignore[assignment]
        coef_scaled: np.ndarray = estimator.coef_
        intercept_scaled: float = float(estimator.intercept_)

        coef_orig = coef_scaled / scale
        intercept_orig = intercept_scaled - float(np.dot(mean, coef_orig))

        betas = dict(zip(x.columns, coef_orig))
        r_squared = pipe.score(x, y)

        return RegressionResult(
            target_figi=target_figi,
            betas={k: float(v) for k, v in betas.items()},
            intercept=intercept_orig,
            r_squared=float(r_squared),
            n_observations=len(y),
        )
