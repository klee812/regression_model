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

    @classmethod
    def from_dict(cls, target_figi: str, data: dict) -> RegressionResult:
        """Reconstruct a result from a deserialized JSON result block.

        Args:
            target_figi: The FIGI key from the top-level ``results`` dict.
            data: The value dict containing ``betas``, ``intercept``,
                ``r_squared``, and ``n_observations``.

        Returns:
            A populated ``RegressionResult`` instance.
        """
        return cls(
            target_figi=target_figi,
            betas=data["betas"],
            intercept=data["intercept"],
            r_squared=data["r_squared"],
            n_observations=data["n_observations"],
        )
