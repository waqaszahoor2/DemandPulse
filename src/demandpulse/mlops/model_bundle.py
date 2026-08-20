"""Model-bundle hydration for immutable production artifacts."""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from pathlib import Path
from urllib.parse import urlparse

from demandpulse.utils.logging import get_logger

logger = get_logger(__name__)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_manifest(target_dir: Path, *, required: bool = False) -> None:
    """Verify an optional `model_manifest.json` containing relative path -> SHA-256."""
    manifest_path = target_dir / "model_manifest.json"
    if not manifest_path.exists():
        if required:
            raise FileNotFoundError("Production model bundle requires model_manifest.json")
        return
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    files = manifest.get("files", manifest)
    if not isinstance(files, dict):
        raise ValueError("model_manifest.json must define a mapping of files to SHA-256 digests")
    for relative, expected in files.items():
        path = target_dir / str(relative)
        if not path.is_file():
            raise FileNotFoundError(f"Model bundle file missing: {relative}")
        actual = _sha256(path)
        if actual != str(expected):
            raise ValueError(f"Model bundle checksum mismatch for {relative}")


def _download_into(uri: str, destination: Path) -> str:
    parsed = urlparse(uri)
    if parsed.scheme in {"", "file"}:
        source = Path(parsed.path if parsed.scheme == "file" else uri).expanduser().resolve()
        if not source.is_dir():
            raise FileNotFoundError(f"Model bundle directory does not exist: {source}")
        shutil.copytree(source, destination, dirs_exist_ok=True)
        return parsed.scheme or "file"
    if parsed.scheme == "gs":
        try:
            from google.cloud import storage  # type: ignore
        except ImportError as exc:
            raise RuntimeError("google-cloud-storage is required for gs:// model bundles") from exc
        bucket_name = parsed.netloc
        prefix = parsed.path.lstrip("/").rstrip("/")
        if not bucket_name:
            raise ValueError("gs:// model bundle URI must include a bucket name")
        client = storage.Client()
        blobs = list(client.list_blobs(bucket_name, prefix=f"{prefix}/" if prefix else None))
        if not blobs:
            raise FileNotFoundError(f"No model artifacts found at {uri}")
        for blob in blobs:
            relative = blob.name[len(prefix) :].lstrip("/") if prefix else blob.name
            if not relative or relative.endswith("/"):
                continue
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            blob.download_to_filename(str(target))
        return "gs"
    raise ValueError(f"Unsupported model bundle URI scheme: {parsed.scheme}")


def hydrate_model_bundle(uri: str, target_dir: str | Path, *, require_manifest: bool = False) -> Path:
    """Stage, verify, then atomically replace the runtime model directory."""
    target = Path(target_dir).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix="demandpulse-models-", dir=str(target.parent)))
    try:
        scheme = _download_into(uri, staging)
        verify_manifest(staging, required=require_manifest)
        if target.exists():
            shutil.rmtree(target)
        staging.replace(target)
        logger.info("model_bundle_hydrated", extra={"model_bundle_scheme": scheme})
        return target
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
