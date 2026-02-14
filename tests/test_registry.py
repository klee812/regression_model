"""Tests for the regression strategy registry."""

from __future__ import annotations

import pytest

from regression_model.regression import registry
from regression_model.regression.elastic_net import ElasticNetStrategy
from regression_model.regression.lars import LarsStrategy
from regression_model.regression.lasso import LassoStrategy
from regression_model.regression.ols import OLSStrategy


def test_all_strategies_registered():
    """All four strategies are available in the registry."""
    assert isinstance(registry.create("ols"), OLSStrategy)
    assert isinstance(registry.create("lasso"), LassoStrategy)
    assert isinstance(registry.create("lars"), LarsStrategy)
    assert isinstance(registry.create("elastic_net"), ElasticNetStrategy)


def test_unknown_method_raises():
    """Requesting an unknown method raises ValueError with available methods."""
    with pytest.raises(ValueError, match="Unknown regression method"):
        registry.create("unknown_method")
