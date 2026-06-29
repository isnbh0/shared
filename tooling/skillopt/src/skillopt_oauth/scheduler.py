"""Bounded async scheduler over OAuth-CLI subprocess jobs.

Every LLM call in the fork is dispatched here as a job. Concurrency is capped
per provider (per OAuth identity) by an ``asyncio.Semaphore``; a token bucket
paces requests below the cap; a bounded admission queue applies backpressure;
failures (rate-limit / nonzero-exit / timeout) are retried with exponential
backoff and full jitter; a circuit breaker pauses a saturated/failing pool; and
sustained rate-limit signals shrink effective concurrency (restored on
recovery). The pool is provider-agnostic: it runs any ``coro_factory`` (a
callable returning a fresh coroutine per attempt). The OAuth executor is wired
in via :func:`cli_job`, which runs the sync ``run_cli`` in a worker thread.

The resilience seam is :func:`classify_cli_result`: it maps a Phase-2
``CliResult`` to success / retryable error / fail-closed error so the same
backpressure stack applies to Phase 4/5 fan-out. A rate-limit or timeout is
retryable; an auth/billing warning on an otherwise-clean exit is fatal
(fail-closed -- retrying would re-run the same metered call).
"""

from __future__ import annotations

import asyncio
import random
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Iterable, Mapping

__all__ = [
    "SchedulerError",
    "RetryableError",
    "RateLimitError",
    "TransientError",
    "AuthBillingError",
    "CircuitOpenError",
    "RetryBudgetExhausted",
    "classify_cli_result",
    "cli_job",
    "ProviderPool",
    "Scheduler",
    "Job",
    "build_scheduler",
]

CoroFactory = Callable[[], Awaitable[Any]]


# --------------------------------------------------------------------------- #
# Errors
# --------------------------------------------------------------------------- #
class SchedulerError(Exception):
    """Base class for scheduler-raised conditions."""


class RetryableError(SchedulerError):
    """A failure the pool should retry under backoff."""


class RateLimitError(RetryableError):
    """A 429 / usage-limit signal; also drives adaptive concurrency shrink."""


class TransientError(RetryableError):
    """A nonzero-exit / transient failure worth retrying."""


class AuthBillingError(SchedulerError):
    """Fail-closed: an auth/billing/usage-limit warning surfaced on a clean exit.

    NOT a :class:`RetryableError`. The Phase-2 executor sets
    ``CliResult.auth_billing_warning`` whenever the call may have slipped onto a
    metered path (or hit a usage limit) even though it exited 0; retrying would
    re-run the same metered call, so the pool must surface this immediately
    rather than spin on it.
    """


class CircuitOpenError(SchedulerError):
    """Raised (fail fast) while the pool's circuit breaker is open."""


class RetryBudgetExhausted(SchedulerError):
    """Raised after ``max_retries`` retryable failures for one submission."""


# --------------------------------------------------------------------------- #
# CLI result classification (Phase-2 CliResult -> success / retryable error)
# --------------------------------------------------------------------------- #
_RATE_LIMIT_MARKERS = (
    "rate limit",
    "rate_limit",
    "429",
    "usage limit",
    "too many requests",
)


def classify_cli_result(result: Any) -> Any:
    """Return ``result`` on success; raise on failure.

    This is the resilience seam Phases 4/5 route their rollout/reflect/judge
    calls through, so backoff / retry / circuit-breaker engage uniformly:

    * ``exit_code == 0`` and no auth/billing warning -> success (returns
      ``result`` unchanged).
    * ``exit_code == 0`` but ``auth_billing_warning`` is truthy ->
      :class:`AuthBillingError` (fatal, fail-closed; not retried -- a metered
      slip or usage limit will not clear on retry).
    * A nonzero exit whose code is 429 or whose stdout/stderr carries a
      rate-limit marker -> :class:`RateLimitError` (retryable; also shrinks
      effective concurrency).
    * Any other nonzero exit -- including the Phase-2 timeout sentinel
      ``exit_code == 124`` -> :class:`TransientError` (retryable).

    Classification is duck-typed on ``.exit_code`` / ``.stdout`` / ``.stderr`` /
    ``.auth_billing_warning`` so it does not import Phase-2 (the Phase-2
    ``CliResult`` routes CLI rate-limit messages to stderr).
    """
    exit_code = int(getattr(result, "exit_code", 0) or 0)
    if exit_code == 0:
        if bool(getattr(result, "auth_billing_warning", False)):
            raise AuthBillingError(
                "auth/billing/usage-limit warning on a clean exit; refusing to "
                "treat as success (fail-closed: a retry would re-run the same "
                "metered call)"
            )
        return result
    text = ((getattr(result, "stdout", "") or "") + "\n"
            + (getattr(result, "stderr", "") or "")).lower()
    if exit_code == 429 or any(m in text for m in _RATE_LIMIT_MARKERS):
        raise RateLimitError(f"rate limited (exit={exit_code})")
    raise TransientError(f"cli failed (exit={exit_code})")


def cli_job(
    executor: Any,
    *,
    provider: str,
    prompt: str,
    skill_path: str | None = None,
    workdir: str | None = None,
    timeout: float = 600.0,
) -> CoroFactory:
    """Build a ``coro_factory`` that runs the sync ``run_cli`` off-loop.

    The executor's ``run_cli`` is a blocking subprocess call, so each attempt
    runs in a worker thread via ``asyncio.to_thread``. The factory returns a
    fresh coroutine per call so the pool can retry it. This is a drop-in for a
    caller previously doing
    ``submit(lambda: asyncio.to_thread(executor.run_cli(...)))`` -- except the
    raw ``CliResult`` is now passed through :func:`classify_cli_result`, so the
    pool's backoff / circuit-breaker engage on rate-limit, timeout, and
    auth/billing signals. On success the underlying ``CliResult`` is returned.
    """

    async def _job() -> Any:
        result = await asyncio.to_thread(
            executor.run_cli,
            provider=provider,
            prompt=prompt,
            skill_path=skill_path,
            workdir=workdir,
            timeout=timeout,
        )
        return classify_cli_result(result)

    return _job


# --------------------------------------------------------------------------- #
# Token bucket (rate_per_min), clock + sleep injectable for a fake clock
# --------------------------------------------------------------------------- #
class _TokenBucket:
    def __init__(
        self,
        rate_per_min: float,
        *,
        capacity: float,
        clock: Callable[[], float],
        sleep: Callable[[float], Awaitable[None]],
    ) -> None:
        self._rate = max(0.0, float(rate_per_min)) / 60.0  # tokens / second
        self._capacity = max(1.0, float(capacity))
        self._tokens = self._capacity
        self._clock = clock
        self._sleep = sleep
        self._last = clock()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        if self._rate <= 0.0:
            return  # unlimited
        async with self._lock:
            while True:
                now = self._clock()
                self._tokens = min(
                    self._capacity, self._tokens + (now - self._last) * self._rate
                )
                self._last = now
                if self._tokens >= 1.0:
                    self._tokens -= 1.0
                    return
                await self._sleep((1.0 - self._tokens) / self._rate)


# --------------------------------------------------------------------------- #
# Concurrency gate: hard ceiling via asyncio.Semaphore; adaptive effective
# limit enforced by parking permits (effective <= max, so the ceiling holds).
# --------------------------------------------------------------------------- #
class _ConcurrencyGate:
    def __init__(self, max_concurrency: int) -> None:
        self._max = int(max_concurrency)
        self._sem = asyncio.Semaphore(self._max)  # the spine's hard ceiling
        self._parked = 0
        self._lock = asyncio.Lock()

    @asynccontextmanager
    async def slot(self):
        await self._sem.acquire()
        try:
            yield
        finally:
            self._sem.release()

    async def reconcile(self, effective: int) -> None:
        """Park/unpark permits so available concurrency == ``effective``."""
        effective = max(1, min(self._max, int(effective)))
        target_parked = self._max - effective
        async with self._lock:
            while self._parked < target_parked:
                await self._sem.acquire()  # hold a permit out of circulation
                self._parked += 1
            while self._parked > target_parked:
                self._sem.release()
                self._parked -= 1


# --------------------------------------------------------------------------- #
# ProviderPool
# --------------------------------------------------------------------------- #
class ProviderPool:
    """A bounded async worker pool for one provider (one OAuth identity).

    Signature conforms to spine §10; keyword-only parameters after ``*`` extend
    it with the resilience knobs the phase requires.
    """

    def __init__(
        self,
        name: str,
        max_concurrency: int,
        rate_per_min: float,
        max_retries: int = 5,
        base_backoff: float = 2.0,
        *,
        max_backoff: float = 60.0,
        burst: float | None = None,
        queue_maxsize: int | None = None,
        per_call_timeout: float = 600.0,
        circuit_breaker_threshold: int = 5,
        circuit_reset_timeout: float = 30.0,
        min_concurrency: int = 1,
        shrink_after: int = 3,
        restore_after: int = 10,
        rng: random.Random | None = None,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        self.name = name
        self.max_concurrency = int(max_concurrency)
        self.rate_per_min = float(rate_per_min)
        self.max_retries = int(max_retries)
        self.base_backoff = float(base_backoff)
        self._max_backoff = float(max_backoff)
        self._per_call_timeout = per_call_timeout
        self._min_concurrency = max(1, int(min_concurrency))
        self._shrink_after = int(shrink_after)
        self._restore_after = int(restore_after)
        self._rng = rng or random.Random()
        self._clock = clock
        self._sleep = sleep

        cap = burst if burst is not None else max(1.0, self.rate_per_min / 60.0)
        self._rate = _TokenBucket(
            self.rate_per_min, capacity=cap, clock=clock, sleep=sleep
        )
        self._gate = _ConcurrencyGate(self.max_concurrency)
        qsize = (
            int(queue_maxsize)
            if queue_maxsize is not None
            else max(1, self.max_concurrency * 8)
        )
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=qsize)  # backpressure
        self._slot_token = object()

        # instrumentation
        self._inflight = 0
        self.max_in_flight = 0
        self._admitted = 0
        self.max_admitted = 0

        # circuit breaker
        self._cb_threshold = int(circuit_breaker_threshold)
        self._cb_reset_timeout = float(circuit_reset_timeout)
        self._cb_state = "closed"  # closed | open | half_open
        self._cb_failures = 0
        self._cb_opened_at = 0.0
        self._cb_probe_active = False

        # adaptive concurrency
        self._effective = self.max_concurrency
        self._rl_streak = 0
        self._ok_streak = 0
        self._bg_tasks: set[asyncio.Task] = set()

    # ---- public introspection -------------------------------------------- #
    @property
    def effective_concurrency(self) -> int:
        return self._effective

    @property
    def circuit_state(self) -> str:
        return self._cb_state

    # ---- submit ----------------------------------------------------------- #
    async def submit(self, coro_factory: CoroFactory) -> Any:
        """Run ``coro_factory`` under the pool's policy; return its result.

        Raises :class:`CircuitOpenError` (fail fast) while the breaker is open,
        or :class:`RetryBudgetExhausted` after exhausting retries.
        """
        is_probe = self._breaker_admit()
        await self._queue.put(self._slot_token)  # blocks when full -> backpressure
        self._admitted += 1
        self.max_admitted = max(self.max_admitted, self._admitted)
        try:
            return await self._run_with_retries(coro_factory)
        finally:
            self._admitted -= 1
            self._queue.get_nowait()
            if is_probe:
                self._cb_probe_active = False

    async def _run_with_retries(self, coro_factory: CoroFactory) -> Any:
        attempt = 0
        last_exc: BaseException | None = None
        while True:
            await self._rate.acquire()
            try:
                async with self._gate.slot():
                    self._inflight += 1
                    self.max_in_flight = max(self.max_in_flight, self._inflight)
                    try:
                        result = await asyncio.wait_for(
                            coro_factory(), self._per_call_timeout
                        )
                    finally:
                        self._inflight -= 1
            except RateLimitError as exc:
                last_exc, is_rl = exc, True
            except (TransientError, asyncio.TimeoutError) as exc:
                last_exc, is_rl = exc, False
            else:
                self._on_success()
                return result

            # failure path
            self._on_failure(is_rl)
            if self._cb_state == "open":
                raise CircuitOpenError(
                    f"{self.name}: circuit opened during retries"
                ) from last_exc
            attempt += 1
            if attempt > self.max_retries:
                raise RetryBudgetExhausted(
                    f"{self.name}: exhausted {self.max_retries} retries"
                ) from last_exc
            await self._sleep(self._backoff_delay(attempt))

    # ---- backoff ---------------------------------------------------------- #
    def _backoff_delay(self, attempt: int) -> float:
        cap = min(self._max_backoff, self.base_backoff * (2 ** (attempt - 1)))
        return self._rng.uniform(0.0, cap)  # full jitter

    # ---- circuit breaker -------------------------------------------------- #
    def _breaker_admit(self) -> bool:
        state = self._cb_state
        if state == "closed":
            return False
        if state == "open":
            elapsed = self._clock() - self._cb_opened_at
            if not self._cb_probe_active and elapsed >= self._cb_reset_timeout:
                self._cb_state = "half_open"
                self._cb_probe_active = True
                return True
            raise CircuitOpenError(f"{self.name}: circuit open")
        # half_open: only the single probe may run
        raise CircuitOpenError(f"{self.name}: circuit half-open (probe in flight)")

    # ---- outcome bookkeeping (sync; safe to call without a running loop) --- #
    def _on_success(self) -> None:
        self._cb_failures = 0
        self._cb_state = "closed"
        self._rl_streak = 0
        self._ok_streak += 1
        if (
            self._ok_streak >= self._restore_after
            and self._effective < self.max_concurrency
        ):
            self._effective = min(self.max_concurrency, self._effective + 1)
            self._ok_streak = 0
            self._schedule_resize()

    def _on_failure(self, is_rate_limit: bool) -> None:
        self._ok_streak = 0
        self._cb_failures += 1
        if self._cb_failures >= self._cb_threshold or self._cb_state == "half_open":
            self._cb_state = "open"
            self._cb_opened_at = self._clock()
        if is_rate_limit:
            self._rl_streak += 1
            if (
                self._rl_streak >= self._shrink_after
                and self._effective > self._min_concurrency
            ):
                self._effective = max(self._min_concurrency, self._effective // 2)
                self._rl_streak = 0
                self._schedule_resize()
        else:
            self._rl_streak = 0

    def _schedule_resize(self) -> None:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return  # no loop (unit-tested synchronously): integer state suffices
        task = loop.create_task(self._gate.reconcile(self._effective))
        self._bg_tasks.add(task)
        task.add_done_callback(self._bg_tasks.discard)

    # ---- cleanup ---------------------------------------------------------- #
    async def aclose(self) -> None:
        for task in list(self._bg_tasks):
            task.cancel()
        for task in list(self._bg_tasks):
            try:
                await task
            except (asyncio.CancelledError, Exception):
                pass
        self._bg_tasks.clear()


# --------------------------------------------------------------------------- #
# Scheduler: one ProviderPool per provider; ordered, concurrency-capped batches
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Job:
    provider: str
    factory: CoroFactory


class Scheduler:
    def __init__(self, pools: Mapping[str, ProviderPool]) -> None:
        self._pools: dict[str, ProviderPool] = dict(pools)

    @property
    def pools(self) -> dict[str, ProviderPool]:
        return dict(self._pools)

    def pool(self, provider: str) -> ProviderPool:
        try:
            return self._pools[provider]
        except KeyError:
            raise ValueError(
                f"no pool for provider {provider!r}; known: {sorted(self._pools)}"
            ) from None

    async def submit(self, provider: str, coro_factory: CoroFactory) -> Any:
        return await self.pool(provider).submit(coro_factory)

    async def run_batch(
        self,
        jobs: Iterable[Job | tuple[str, CoroFactory]],
        *,
        return_exceptions: bool = False,
    ) -> list[Any]:
        """Run many jobs, each routed to its provider's pool and capped there.

        Results are returned IN INPUT ORDER. Jobs for different providers run
        concurrently across pools; within a provider, the pool caps concurrency.
        """
        jobs = list(jobs)
        coros = [
            self.submit(self._provider_of(j), self._factory_of(j)) for j in jobs
        ]
        return await asyncio.gather(*coros, return_exceptions=return_exceptions)

    @staticmethod
    def _provider_of(job: Job | tuple[str, CoroFactory]) -> str:
        return job.provider if isinstance(job, Job) else job[0]

    @staticmethod
    def _factory_of(job: Job | tuple[str, CoroFactory]) -> CoroFactory:
        return job.factory if isinstance(job, Job) else job[1]

    async def aclose(self) -> None:
        for pool in self._pools.values():
            await pool.aclose()


def build_scheduler(
    *,
    providers: Iterable[str] = ("claude", "codex"),
    max_concurrency: int = 4,
    rate_per_min: float = 60.0,
    **pool_kwargs: Any,
) -> Scheduler:
    """Convenience builder: one identically-configured pool per provider."""
    pools = {
        name: ProviderPool(name, max_concurrency, rate_per_min, **pool_kwargs)
        for name in providers
    }
    return Scheduler(pools)
