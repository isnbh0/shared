"""Hermetic, fast tests for the bounded async scheduler.

No real sleeps (backoff and token-bucket waits go through an injected fake
clock), no network, no real OAuth. The provider-agnostic pool behaviors are
driven by in-process coroutine factories for full determinism; stub-driven
integration tests exercise the executor -> to_thread -> subprocess wiring and
skip gracefully if the Phase-2 artifacts are unavailable.
"""

from __future__ import annotations

import asyncio
import os
import random
from pathlib import Path

import pytest

from skillopt_oauth.scheduler import (
    CircuitOpenError,
    Job,
    ProviderPool,
    RateLimitError,
    RetryBudgetExhausted,
    Scheduler,
    SchedulerError,
    TransientError,
    cli_job,
    classify_cli_result,
)

STUB = Path(__file__).resolve().parent / "fixtures" / "stub_cli.py"


# --------------------------------------------------------------------------- #
# Test doubles
# --------------------------------------------------------------------------- #
class FakeClock:
    """Simulated monotonic time. ``sleep`` advances ``now`` instantly."""

    def __init__(self, start: float = 0.0) -> None:
        self.now = start
        self.sleeps: list[float] = []

    def time(self) -> float:
        return self.now

    async def sleep(self, delay: float) -> None:
        self.sleeps.append(delay)
        self.now += max(0.0, delay)
        await asyncio.sleep(0)  # yield so other tasks can progress


async def _instant_sleep(_delay: float) -> None:
    await asyncio.sleep(0)


class _StubResult:
    def __init__(self, exit_code: int, stdout: str = "") -> None:
        self.exit_code = exit_code
        self.stdout = stdout


# --------------------------------------------------------------------------- #
# classify_cli_result
# --------------------------------------------------------------------------- #
def test_classify_cli_result():
    ok = _StubResult(0, "rollout body")
    assert classify_cli_result(ok) is ok
    with pytest.raises(RateLimitError):
        classify_cli_result(_StubResult(1, "HTTP 429 rate limit exceeded"))
    with pytest.raises(RateLimitError):
        classify_cli_result(_StubResult(429, "boom"))
    with pytest.raises(TransientError):
        classify_cli_result(_StubResult(2, "segfault"))


# --------------------------------------------------------------------------- #
# Concurrency ceiling is never exceeded (and is actually reached)
# --------------------------------------------------------------------------- #
def test_concurrency_ceiling_never_exceeded():
    asyncio.run(_concurrency_ceiling())


async def _concurrency_ceiling():
    max_c, n = 4, 16
    pool = ProviderPool("claude", max_c, rate_per_min=1e9, per_call_timeout=5.0)
    release = asyncio.Event()
    live = {"n": 0, "peak": 0}

    async def job():
        live["n"] += 1
        live["peak"] = max(live["peak"], live["n"])
        await release.wait()
        live["n"] -= 1
        return "ok"

    task = asyncio.ensure_future(
        asyncio.gather(*(pool.submit(lambda: job()) for _ in range(n)))
    )
    for _ in range(100):
        await asyncio.sleep(0)
        if pool.max_in_flight >= max_c:
            break

    assert live["peak"] == max_c          # cap actually reached
    assert pool.max_in_flight == max_c
    assert pool.max_in_flight <= max_c    # never exceeded

    release.set()
    results = await task
    assert results == ["ok"] * n
    assert pool.max_in_flight <= max_c
    await pool.aclose()


# --------------------------------------------------------------------------- #
# Bounded admission queue applies backpressure
# --------------------------------------------------------------------------- #
def test_bounded_queue_applies_backpressure():
    asyncio.run(_bounded_queue_backpressure())


async def _bounded_queue_backpressure():
    pool = ProviderPool(
        "claude",
        max_concurrency=1,
        rate_per_min=1e9,
        queue_maxsize=3,
        per_call_timeout=5.0,
        circuit_breaker_threshold=100,
    )
    release = asyncio.Event()

    async def job():
        await release.wait()
        return "ok"

    n = 8
    task = asyncio.ensure_future(
        asyncio.gather(*(pool.submit(lambda: job()) for _ in range(n)))
    )
    for _ in range(100):
        await asyncio.sleep(0)

    assert pool.max_admitted <= 3   # only queue_maxsize admitted past backpressure
    assert pool.max_in_flight <= 1

    release.set()
    results = await task
    assert results == ["ok"] * n
    assert pool.max_admitted == 3   # bound was saturated
    await pool.aclose()


# --------------------------------------------------------------------------- #
# Token bucket caps the rate (fake clock)
# --------------------------------------------------------------------------- #
def test_token_bucket_caps_rate():
    asyncio.run(_token_bucket_caps_rate())


async def _token_bucket_caps_rate():
    fc = FakeClock()
    pool = ProviderPool(
        "claude",
        max_concurrency=8,
        rate_per_min=60.0,  # 1 / second
        burst=1.0,
        per_call_timeout=100.0,
        clock=fc.time,
        sleep=fc.sleep,
    )

    async def job():
        return "ok"

    n = 5
    results = await asyncio.gather(*(pool.submit(lambda: job()) for _ in range(n)))
    assert results == ["ok"] * n
    # burst=1 -> first immediate, the next 4 each wait ~1s of simulated time
    assert fc.now == pytest.approx(4.0, abs=1e-6)
    assert len(fc.sleeps) == 4
    assert all(s == pytest.approx(1.0, abs=1e-6) for s in fc.sleeps)
    await pool.aclose()


# --------------------------------------------------------------------------- #
# Backoff retries a rate-limited job then succeeds (fake clock, seeded jitter)
# --------------------------------------------------------------------------- #
def test_backoff_retries_rate_limit_then_succeeds():
    asyncio.run(_backoff_retries())


async def _backoff_retries():
    fc = FakeClock()
    pool = ProviderPool(
        "claude",
        max_concurrency=2,
        rate_per_min=1e9,           # token bucket never blocks
        max_retries=5,
        base_backoff=2.0,
        max_backoff=60.0,
        per_call_timeout=100.0,
        circuit_breaker_threshold=100,
        rng=random.Random(1234),
        clock=fc.time,
        sleep=fc.sleep,
    )
    calls = {"n": 0}

    async def job():
        calls["n"] += 1
        if calls["n"] <= 2:
            raise RateLimitError("429")
        return "done"

    result = await pool.submit(lambda: job())
    assert result == "done"
    assert calls["n"] == 3              # 2 failures + 1 success
    assert len(fc.sleeps) == 2          # 2 backoff waits (instant under fake clock)
    assert 0.0 <= fc.sleeps[0] <= 2.0   # full jitter, attempt 1 cap = base * 2^0
    assert 0.0 <= fc.sleeps[1] <= 4.0   # full jitter, attempt 2 cap = base * 2^1
    await pool.aclose()


# --------------------------------------------------------------------------- #
# Circuit breaker: opens after K, fails fast, recovers via half-open probe
# --------------------------------------------------------------------------- #
def test_circuit_breaker_opens_then_fails_fast_then_recovers():
    asyncio.run(_circuit_breaker())


async def _circuit_breaker():
    fc = FakeClock()
    pool = ProviderPool(
        "claude",
        max_concurrency=2,
        rate_per_min=1e9,
        max_retries=0,
        circuit_breaker_threshold=3,
        circuit_reset_timeout=30.0,
        per_call_timeout=100.0,
        clock=fc.time,
        sleep=fc.sleep,
    )

    async def failing():
        raise TransientError("boom")

    for _ in range(3):                       # K=3 failures open the breaker
        with pytest.raises(SchedulerError):
            await pool.submit(lambda: failing())
    assert pool.circuit_state == "open"

    probe = {"n": 0}

    async def ok_job():
        probe["n"] += 1
        return "ok"

    with pytest.raises(CircuitOpenError):    # fail fast: job not invoked
        await pool.submit(lambda: ok_job())
    assert probe["n"] == 0

    fc.now += 30.0                           # reset timeout elapses
    assert await pool.submit(lambda: ok_job()) == "ok"  # half-open probe succeeds
    assert probe["n"] == 1
    assert pool.circuit_state == "closed"
    await pool.aclose()


# --------------------------------------------------------------------------- #
# Per-call timeout fires on a slow job
# --------------------------------------------------------------------------- #
def test_per_call_timeout_fires_on_slow():
    asyncio.run(_per_call_timeout())


async def _per_call_timeout():
    pool = ProviderPool(
        "claude",
        max_concurrency=2,
        rate_per_min=1e9,
        max_retries=1,
        per_call_timeout=0.02,       # tiny real timeout; backoff is faked instant
        circuit_breaker_threshold=100,
        sleep=_instant_sleep,
    )
    attempts = {"n": 0}

    async def slow():
        attempts["n"] += 1
        await asyncio.Event().wait()  # blocks; wait_for cancels at per_call_timeout

    with pytest.raises(RetryBudgetExhausted):
        await pool.submit(lambda: slow())
    assert attempts["n"] == 2         # initial attempt + 1 retry, both timed out
    await pool.aclose()


# --------------------------------------------------------------------------- #
# Adaptive concurrency shrink on sustained rate-limit, restore on recovery
# --------------------------------------------------------------------------- #
def test_adaptive_shrink_and_restore():
    pool = ProviderPool(
        "claude",
        max_concurrency=8,
        rate_per_min=1e9,
        min_concurrency=2,
        shrink_after=3,
        restore_after=4,
        circuit_breaker_threshold=10_000,
    )
    assert pool.effective_concurrency == 8

    for _ in range(3):
        pool._on_failure(is_rate_limit=True)
    assert pool.effective_concurrency == 4     # halved after 3 rate-limit signals

    for _ in range(3):
        pool._on_failure(is_rate_limit=True)
    assert pool.effective_concurrency == 2     # halved again

    for _ in range(3):
        pool._on_failure(is_rate_limit=True)
    assert pool.effective_concurrency == 2     # floored at min_concurrency

    for _ in range(8):
        pool._on_success()
    assert pool.effective_concurrency == 4     # +1 per 4 successes -> two steps


# --------------------------------------------------------------------------- #
# run_batch returns results IN ORDER across providers
# --------------------------------------------------------------------------- #
def test_run_batch_preserves_order():
    asyncio.run(_run_batch_order())


async def _run_batch_order():
    sched = Scheduler(
        {
            "claude": ProviderPool("claude", 2, rate_per_min=1e9, per_call_timeout=5.0),
            "codex": ProviderPool("codex", 2, rate_per_min=1e9, per_call_timeout=5.0),
        }
    )

    def make(i: int):
        async def job():
            await asyncio.sleep(0)
            return i

        return job

    jobs = [Job("claude" if i % 2 == 0 else "codex", make(i)) for i in range(10)]
    results = await sched.run_batch(jobs)
    assert results == list(range(10))
    await sched.aclose()


# --------------------------------------------------------------------------- #
# Stub-driven integration: executor -> to_thread -> subprocess wiring
# --------------------------------------------------------------------------- #
def _make_executor():
    try:
        from skillopt_oauth.executor import OAuthCLIExecutor
    except Exception as exc:  # pragma: no cover - depends on Phase 2
        pytest.skip(f"Phase 2 executor unavailable: {exc}")
    if not STUB.exists():
        pytest.skip("Phase 2 stub_cli.py fixture not present")
    STUB.chmod(0o755)
    # ``oauth_probe`` is injected so the fail-closed OAuth preflight stays
    # hermetic (no real credential store / keychain) -- matching the Phase-2
    # test suite. The stub doubles as both bins; nothing here touches the net.
    return OAuthCLIExecutor(
        claude_bin=str(STUB), codex_bin=str(STUB), forbid_api_keys=False,
        oauth_probe=lambda provider: "oauth",
    )


def _clear_api_keys(monkeypatch):
    for key in list(os.environ):
        if key.endswith("_API_KEY"):
            monkeypatch.delenv(key, raising=False)


def test_integration_stub_batch_respects_ceiling(monkeypatch):
    asyncio.run(_integration_stub_batch(monkeypatch))


async def _integration_stub_batch(monkeypatch):
    monkeypatch.setenv("STUB_MODE", "ok")
    _clear_api_keys(monkeypatch)
    executor = _make_executor()
    pool_size, n = 3, 9
    sched = Scheduler(
        {"claude": ProviderPool("claude", pool_size, rate_per_min=1e9,
                                per_call_timeout=30.0)}
    )
    jobs = [
        Job("claude", cli_job(executor, provider="claude", prompt=f"rollout {i}"))
        for i in range(n)
    ]
    results = await sched.run_batch(jobs)
    assert len(results) == n
    assert all(getattr(r, "exit_code", 0) == 0 for r in results)
    assert sched.pool("claude").max_in_flight <= pool_size
    await sched.aclose()


def test_integration_stub_rate_limit_then_succeeds(monkeypatch, tmp_path):
    asyncio.run(_integration_rate_limit(monkeypatch, tmp_path))


async def _integration_rate_limit(monkeypatch, tmp_path):
    counter = tmp_path / "counter.txt"
    monkeypatch.setenv("STUB_MODE", "flaky")
    monkeypatch.setenv("STUB_COUNTER_FILE", str(counter))
    monkeypatch.setenv("STUB_FAIL_TIMES", "2")
    _clear_api_keys(monkeypatch)
    executor = _make_executor()
    fc = FakeClock()
    pool = ProviderPool(
        "claude",
        max_concurrency=2,
        rate_per_min=1e9,
        max_retries=5,
        base_backoff=2.0,
        per_call_timeout=30.0,
        circuit_breaker_threshold=100,
        clock=fc.time,
        sleep=fc.sleep,
    )
    result = await pool.submit(
        cli_job(executor, provider="claude", prompt="rollout")
    )
    assert getattr(result, "exit_code", 0) == 0
    assert len(fc.sleeps) == 2  # two rate-limit retries backed off (instant)
    await pool.aclose()
