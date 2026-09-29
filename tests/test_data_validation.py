import pandas as pd
import pytest

from demandpulse.data.validation import (
    DataValidationError,
    validate_duplicate_keys,
    validate_schema,
    validate_train_eval_chronology,
)


def test_invalid_schema_raises():
    with pytest.raises(DataValidationError, match="Missing required columns"):
        validate_schema(["a"], ["a", "b"], allowed_columns=["a", "b"])


def test_duplicate_detection_raises():
    frame = pd.DataFrame(
        {
            "store_id": [1, 1],
            "product_id": [2, 2],
            "dt": pd.to_datetime(["2026-01-01", "2026-01-01"]),
        }
    )
    with pytest.raises(DataValidationError, match="Duplicate"):
        validate_duplicate_keys(frame)


def test_train_eval_chronology():
    train = pd.DataFrame({"dt": pd.to_datetime(["2026-01-01", "2026-01-02"])})
    evaluation = pd.DataFrame({"dt": pd.to_datetime(["2026-01-03"])})
    validate_train_eval_chronology(train, evaluation)
    bad_eval = pd.DataFrame({"dt": pd.to_datetime(["2026-01-02"])})
    with pytest.raises(DataValidationError):
        validate_train_eval_chronology(train, bad_eval)
