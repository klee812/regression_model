"""Configuration for optional identifier resolution via openfigi_cache."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class IdentifierResolutionConfig:
    """Controls how non-FIGI identifiers are resolved to FIGIs before loading.

    Set ``enabled=True`` and install ``regression-model[resolution]`` to use.
    """

    enabled: bool = False
    cache_path: str = ".figi_cache.json"
    id_type: str = "TICKER"
    exch_code: str | None = None
    mic_code: str | None = None
    currency: str | None = None
    overrides: dict[str, dict] = field(default_factory=dict)
    on_failure: str = "raise"  # "raise" | "warn" | "skip"
