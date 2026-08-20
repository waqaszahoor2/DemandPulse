from demandpulse.data.sampling import series_bucket, series_selected


def test_sampling_is_deterministic_and_series_level():
    decisions = [series_selected(10, 20, 30.0) for _ in range(10)]
    assert len(set(decisions)) == 1
    assert series_bucket(10, 20) == series_bucket(10, 20)


def test_sampling_extremes():
    assert series_selected(1, 1, 100.0)
    assert not series_selected(1, 1, 0.0)
