"""Deployment smoke tests used after staging/production revisions are created."""

from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request


def get_json(base_url: str, path: str, bearer_token: str | None = None) -> tuple[int, dict]:
    headers = {"User-Agent": "DemandPulseSmoke/1.0"}
    if bearer_token:
        headers["Authorization"] = f"Bearer {bearer_token}"
    request = urllib.request.Request(f"{base_url.rstrip('/')}{path}", headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        return exc.code, json.loads(body) if body else {}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--require-ready", action="store_true")
    parser.add_argument("--bearer-token", default=None)
    args = parser.parse_args()

    health_status, health = get_json(args.base_url, "/health", args.bearer_token)
    assert health_status == 200 and health.get("status") == "healthy", health
    ready_status, ready = get_json(args.base_url, "/ready", args.bearer_token)
    if args.require_ready:
        assert ready_status == 200 and ready.get("status") == "ready", ready
    info_status, info = get_json(args.base_url, "/model/info", args.bearer_token)
    assert info_status == 200 and isinstance(info.get("models"), list), info
    print(json.dumps({"health": health, "ready": ready, "model_info_count": len(info["models"])}, indent=2))


if __name__ == "__main__":
    main()
