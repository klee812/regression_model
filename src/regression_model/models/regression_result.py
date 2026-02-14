"""Result container for a single regression fit."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RegressionResult:
    """Output of fitting a regression model for one target."""

    target_figi: str
    betas: dict[str, float]  # driver FIGI -> beta coefficient
    intercept: float
    r_squared: float
    n_observations: int
