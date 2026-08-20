from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from demandpulse.mlops.model_bundle import hydrate_model_bundle


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_model_bundle_hydration_replaces_stale_files(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    model = source / "demandpulse_lgbm.txt"
    model.write_text("model-v1", encoding="utf-8")
    (source / "model_manifest.json").write_text(
        json.dumps({"files": {"demandpulse_lgbm.txt": _sha(model)}}), encoding="utf-8"
    )
    target = tmp_path / "runtime"
    target.mkdir()
    (target / "stale.txt").write_text("stale", encoding="utf-8")

    hydrate_model_bundle(source.as_uri(), target)

    assert (target / "demandpulse_lgbm.txt").read_text(encoding="utf-8") == "model-v1"
    assert not (target / "stale.txt").exists()


def test_model_bundle_checksum_failure_does_not_replace_current_bundle(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "model.txt").write_text("bad", encoding="utf-8")
    (source / "model_manifest.json").write_text(
        json.dumps({"files": {"model.txt": "0" * 64}}), encoding="utf-8"
    )
    target = tmp_path / "runtime"
    target.mkdir()
    current = target / "current.txt"
    current.write_text("keep", encoding="utf-8")

    with pytest.raises(ValueError, match="checksum"):
        hydrate_model_bundle(source.as_uri(), target)

    assert current.read_text(encoding="utf-8") == "keep"
