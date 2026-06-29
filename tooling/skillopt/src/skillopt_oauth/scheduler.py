"""Bounded async OAuth-CLI scheduler (Phase 3).

STUB STATE: signatures only; constructor and `submit` raise NotImplementedError.
FUTURE (Phase 3): per-provider (per-identity) semaphore pools, token-bucket pacing
below the concurrency cap, a bounded queue (backpressure), exponential backoff + full
jitter on 429 / nonzero exit, a circuit breaker on sustained failures, a retry budget,
and per-call timeouts.
"""
from __future__ import annotations


class ProviderPool:
    def __init__(
        self,
        name: str,
        max_concurrency: int,
        rate_per_min: float,
        max_retries: int = 5,
        base_backoff: float = 2.0,
    ) -> None:
        raise NotImplementedError("ProviderPool is implemented in Phase 3")

    async def submit(self, coro_factory) -> object:
        # FUTURE (Phase 3): semaphore + token-bucket + backoff/jitter + circuit breaker.
        raise NotImplementedError("ProviderPool.submit is implemented in Phase 3")
