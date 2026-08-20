"""Create an immutable SHA-256 manifest for a model bundle before registry export."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("model_dir", type=Path)
    args = parser.parse_args()
    root = args.model_dir.resolve()
    if not root.is_dir():
        raise SystemExit(f"Not a model directory: {root}")
    files = {
        str(path.relative_to(root)): digest(path)
        for path in sorted(root.rglob("*"))
        if path.is_file() and path.name != "model_manifest.json"
    }
    if not files:
        raise SystemExit("No model files found")
    manifest = {"schema_version": 1, "files": files}
    output = root / "model_manifest.json"
    output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
