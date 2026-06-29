"""Shared hermetic test fakes for the Phase-5 loop."""
from __future__ import annotations

import pytest


class FakeScheduler:
    """In-process stand-in for the Phase-3 scheduler: just awaits each factory.

    Honors the only method Phase 5 uses: `submit(provider, coro_factory)`. Records
    per-provider call counts so tests can assert routing.
    """

    def __init__(self):
        self.calls: dict[str, int] = {}

    async def submit(self, provider, coro_factory):
        self.calls[provider] = self.calls.get(provider, 0) + 1
        return await coro_factory()


@pytest.fixture
def scheduler():
    return FakeScheduler()


def rec(task_id, hard, soft):
    """Build a scored record the gate understands."""
    return {"id": task_id, "hard": hard, "soft": soft}
