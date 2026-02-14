"""Registry of available regression strategies.

Maps string method names (used in config files) to strategy classes.
"""

from __future__ import annotations

from typing import Any

from regression_model.regression.base import RegressionStrategy
from regression_model.regression.elastic_net import ElasticNetStrategy
from regression_model.regression.lars import LarsStrategy
from regression_model.regression.lasso import LassoStrategy
from regression_model.regression.ols import OLSStrategy

_REGISTRY: dict[str, type] = {
    "ols": OLSStrategy,
    "lasso": LassoStrategy,
    "lars": LarsStrategy,
    "elastic_net": ElasticNetStrategy,
}


def create(method: str, **kwargs: Any) -> RegressionStrategy:
    """Instantiate a regression strategy by name.

    Args:
        method: The regression method name (e.g. ``"ols"``, ``"lasso"``).
        **kwargs: Parameters forwarded to the strategy constructor.

    Returns:
        A configured regression strategy instance.

    Raises:
        ValueError: If *method* is not in the registry.
    """
    cls = _REGISTRY.get(method)
    if cls is None:
        available = ", ".join(sorted(_REGISTRY))
        raise ValueError(f"Unknown regression method {method!r}. Available: {available}")
    return cls(**kwargs)
