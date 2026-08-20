from __future__ import annotations

from types import SimpleNamespace

import demandpulse.mlops.registry as registry


def test_candidate_promotion_is_dry_run_by_default(monkeypatch):
    calls = []
    monkeypatch.setattr(registry, "set_model_alias", lambda *args, **kwargs: calls.append((args, kwargs)))
    passed, reasons = registry.promote_candidate(
        "model",
        6,
        candidate_metrics={"WAPE": 0.18, "Bias": 0.01},
        champion_metrics={"WAPE": 0.20, "Bias": 0.02},
        required_tests_passed=True,
        apply=False,
    )
    assert passed is True
    assert reasons == []
    assert calls == []


def test_candidate_promotion_keeps_previous_champion(monkeypatch):
    calls = []
    monkeypatch.setattr(registry, "get_model_version", lambda *args, **kwargs: SimpleNamespace(version="5"))
    monkeypatch.setattr(registry, "set_model_alias", lambda *args, **kwargs: calls.append((args, kwargs)))
    passed, _ = registry.promote_candidate(
        "model",
        6,
        candidate_metrics={"WAPE": 0.18},
        champion_metrics={"WAPE": 0.20},
        required_tests_passed=True,
        apply=True,
    )
    assert passed is True
    assert calls[0][0][1:] == ("previous_champion", "5")
    assert calls[1][0][1:] == ("champion", 6)


def test_rollback_champion_uses_previous_alias(monkeypatch):
    calls = []
    monkeypatch.setattr(registry, "get_model_version", lambda *args, **kwargs: SimpleNamespace(version="4"))
    monkeypatch.setattr(registry, "set_model_alias", lambda *args, **kwargs: calls.append((args, kwargs)))
    version = registry.rollback_champion("model")
    assert version == "4"
    assert calls[0][0][1:] == ("champion", "4")
