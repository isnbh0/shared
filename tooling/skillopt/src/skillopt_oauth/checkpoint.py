"""Write-ahead checkpoint + resume (Phase 5).

STUB STATE: signatures only; raises NotImplementedError.
FUTURE (Phase 5): write-ahead checkpoint after every step (gated skill, LR-schedule
position, gate statistics, scheduler/job state) so an interrupted run resumes from the
last committed step without lost work or duplicate LLM calls.
"""
from __future__ import annotations


class Checkpoint:
    def __init__(self, path: str) -> None:
        raise NotImplementedError("Checkpoint is implemented in Phase 5")

    def save(self, state: dict) -> None:
        raise NotImplementedError("Checkpoint.save is implemented in Phase 5")

    def load(self) -> dict:
        raise NotImplementedError("Checkpoint.load is implemented in Phase 5")
