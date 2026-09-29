"""Safe lightweight load test for staging/local DemandPulse endpoints."""

from __future__ import annotations

import argparse
import asyncio
import time
from dataclasses import dataclass

import httpx


@dataclass
class Result:
    concurrency: int
    requests: int
    successes: int
    errors: int
    throughput_rps: float
    p50_ms: float
    p95_ms: float
    p99_ms: float


async def _one(client: httpx.AsyncClient, url: str, semaphore: asyncio.Semaphore) -> tuple[bool, float]:
    async with semaphore:
        start = time.perf_counter()
        try:
            response = await client.get(url)
            ok = response.status_code == 200
        except httpx.HTTPError:
            ok = False
        return ok, (time.perf_counter() - start) * 1000


async def run_level(
    base_url: str,
    endpoint: str,
    concurrency: int,
    requests: int,
    timeout: float,
    bearer_token: str | None = None,
) -> Result:
    semaphore = asyncio.Semaphore(concurrency)
    url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"
    headers = {"Authorization": f"Bearer {bearer_token}"} if bearer_token else None
    async with httpx.AsyncClient(timeout=timeout, headers=headers) as client:
        started = time.perf_counter()
        outputs = await asyncio.gather(*[_one(client, url, semaphore) for _ in range(requests)])
        elapsed = time.perf_counter() - started
    latencies = sorted(latency for _, latency in outputs)
    successes = sum(ok for ok, _ in outputs)
    errors = requests - successes

    def q(p: float) -> float:
        if not latencies:
            return float("nan")
        index = min(round((len(latencies) - 1) * p), len(latencies) - 1)
        return latencies[index]

    return Result(
        concurrency=concurrency,
        requests=requests,
        successes=successes,
        errors=errors,
        throughput_rps=requests / elapsed if elapsed else float("inf"),
        p50_ms=q(0.50),
        p95_ms=q(0.95),
        p99_ms=q(0.99),
    )


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--endpoint", default="/health")
    parser.add_argument("--requests", type=int, default=50)
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--bearer-token", default=None)
    args = parser.parse_args()
    if args.requests < 1 or args.requests > 1000:
        raise SystemExit("--requests must be between 1 and 1000 for this lightweight test")
    for concurrency in (1, 10, 50):
        result = await run_level(
            args.base_url, args.endpoint, concurrency, args.requests, args.timeout, args.bearer_token
        )
        print(
            f"concurrency={result.concurrency} requests={result.requests} success={result.successes} "
            f"errors={result.errors} throughput_rps={result.throughput_rps:.2f} "
            f"p50_ms={result.p50_ms:.2f} p95_ms={result.p95_ms:.2f} p99_ms={result.p99_ms:.2f}"
        )


if __name__ == "__main__":
    asyncio.run(main())
