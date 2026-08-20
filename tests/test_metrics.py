import numpy as np
import pytest

from demandpulse.evaluation.metrics import (
    bias,
    interval_coverage,
    pinball_loss,
    standardized_mean_difference,
    wape,
)


def test_zero_denominator_wape_is_nan():
    assert np.isnan(wape([0, 0], [1, 2]))
    assert np.isnan(bias([0, 0], [1, 2]))


def test_pinball_and_coverage():
    assert pinball_loss([1, 2], [1, 2], 0.5) == 0.0
    assert interval_coverage([1, 2], [0, 1], [2, 3]) == 1.0


def test_invalid_lengths_raise():
    with pytest.raises(ValueError):
        wape([1, 2], [1])


def test_smd_zero_for_equal_groups():
    assert np.isclose(standardized_mean_difference([1, 2, 3], [1, 2, 3]), 0.0)
