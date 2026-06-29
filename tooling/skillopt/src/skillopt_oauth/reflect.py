"""Parallel-propose + deterministic-merge reflection (Phase 5).

STUB STATE: signatures only; raises NotImplementedError.
FUTURE (Phase 5): `propose_minibatch` proposes bounded patch ops for one scored
minibatch against the SAME pre-step skill (fan out across minibatches via the
scheduler); `merge_proposals` deterministically merges the proposals under the global
LR edit budget (hard-clamped to LR). `reflection_mode: sequential` recovers exact
stock SkillOpt behavior.
"""
from __future__ import annotations


def propose_minibatch(skill_text: str, scored_minibatch: list[dict], *, lr: int,
                      executor) -> list[dict]:
    """One scored minibatch -> a list of proposed patch ops (schema-validated)."""
    raise NotImplementedError("propose_minibatch is implemented in Phase 5")


def merge_proposals(skill_text: str, proposals: list[list[dict]], *, lr: int) -> str:
    """Deterministically merge per-minibatch proposals under the LR edit budget."""
    raise NotImplementedError("merge_proposals is implemented in Phase 5")
