"""Configuration for the regression method and its parameters."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RegressionConfig:
    """Specifies which regression strategy to use and any extra parameters."""

    method: str = "ols"
    params: dict[str, Any] = field(default_factory=dict)
