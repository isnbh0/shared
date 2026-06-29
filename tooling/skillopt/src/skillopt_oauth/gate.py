"""Variance-aware validation gate for SkillOpt-OAuth.

The CLI execution layer has no temperature/seed knob, so a single-sample
strict-`>` gate would accept measurement noise and let the skill degrade. This
module hardens the gate (spine §6), ordered by leverage:

  1. deterministic-first scoring — Phase 4 scorers feed this module verbatim;
  2. fixed validation split — Phase 4 dataloader freezes val IDs; never resampled here;
  3. n-sample self-consistency — `aggregate_samples`: hard = majority vote, soft = median;
  4. variance-aware accept threshold — Δ > max(2·σ_gate, 1/M);
  5. per-epoch A/A calibration of σ_gate (`calibrate_sigma_gate`);
  6. paired re-baseline of the prior skill under the *current* model (`rebaseline`);
  7. a `ResultCache` keyed by (skill_hash, task_id, model, provider).

`gate_accept(..., mode="strict")` recovers stock SkillOpt's single-sample `>` gate.
"""
from __future__ import annotations

import asyncio
import hashlib
import math
import statistics
from dataclasses import dataclass, field
from typing import Awaitable, Callable, Protocol

Record = dict  # {"id": str, "hard": 0|1, "soft": float in [0, 1]}


# --------------------------------------------------------------------------- #
# Scheduler seam (Phase 3). Phase 5 depends only on this minimal protocol so it
# stays decoupled from the concrete ProviderPool/Scheduler internals and can be
# driven by an in-process fake in tests.
# --------------------------------------------------------------------------- #
class Scheduler(Protocol):
    async def submit(self, provider: str, coro_factory: Callable[[], Awaitable]) -> object:
        """Run a coroutine factory under the named provider's pool, returning its result."""
        ...


async def fanout(scheduler: "Scheduler", provider: str,
                 factories: list[Callable[[], Awaitable]]) -> list:
    """Run many coroutine factories through one provider pool, preserving order."""
    if not factories:
        return []
    return await asyncio.gather(*[scheduler.submit(provider, f) for f in factories])


# --------------------------------------------------------------------------- #
# Metric helpers
# --------------------------------------------------------------------------- #
def metric_value(rec: Record, metric: str = "mixed") -> float:
    """Project a scored record onto a scalar in [0, 1]."""
    if metric == "hard":
        return float(rec["hard"])
    if metric == "soft":
        return float(rec["soft"])
    if metric == "mixed":
        return 0.5 * float(rec["hard"]) + 0.5 * float(rec["soft"])
    raise ValueError(f"unknown metric {metric!r}")


def _by_id(records: list[Record]) -> list[Record]:
    return sorted(records, key=lambda r: r["id"])


def mean_metric(records: list[Record], metric: str = "mixed") -> float:
    if not records:
        return 0.0
    return statistics.fmean(metric_value(r, metric) for r in records)


# --------------------------------------------------------------------------- #
# n-sample self-consistency
# --------------------------------------------------------------------------- #
def aggregate_samples(task_id: str, samples: list[Record]) -> Record:
    """Collapse n per-sample scorer outputs for ONE task into one record.

    hard = majority vote (n should be odd, n>=3 for residual LLM-ness),
    soft = median. Deterministic given the samples.
    """
    if not samples:
        raise ValueError("aggregate_samples requires at least one sample")
    hard_votes = [int(s["hard"]) for s in samples]
    hard = 1 if sum(hard_votes) * 2 > len(hard_votes) else 0
    soft = statistics.median(float(s["soft"]) for s in samples)
    return {"id": task_id, "hard": hard, "soft": soft, "n": len(samples)}


# --------------------------------------------------------------------------- #
# Result cache keyed by (skill_hash, task_id, model, provider)
# --------------------------------------------------------------------------- #
def skill_hash(skill_doc: str) -> str:
    return hashlib.sha256(skill_doc.encode("utf-8")).hexdigest()[:16]


def cache_key(skill_h: str, task_id: str, model: str, provider: str) -> str:
    return f"{skill_h}|{task_id}|{model}|{provider}"


@dataclass
class ResultCache:
    """Aggregate val records keyed by (skill_hash, task_id, model, provider).

    The key includes model+provider so a genuine model/CLI drift (or a different
    routing provider) misses the cache and is re-measured — the cache never masks
    drift, it only avoids redundant identical evals within a run.
    """
    _store: dict[str, Record] = field(default_factory=dict)

    def get(self, key: str) -> Record | None:
        return self._store.get(key)

    def put(self, key: str, rec: Record) -> None:
        self._store[key] = rec

    def __contains__(self, key: str) -> bool:
        return key in self._store

    def __len__(self) -> int:
        return len(self._store)

    def to_dict(self) -> dict:
        return dict(self._store)

    @classmethod
    def from_dict(cls, d: dict | None) -> "ResultCache":
        return cls(dict(d or {}))


# --------------------------------------------------------------------------- #
# Validation evaluation (embarrassingly parallel, frozen split)
# --------------------------------------------------------------------------- #
RolloutFn = Callable[[str, dict], Awaitable[dict]]  # (skill_doc, task) -> rollout dict {id, stdout, workspace_dir}
Scorer = Callable[[dict, dict], Record]             # (task, rollout) -> {id, hard, soft}  (P4 canonical)


async def evaluate_val(*, skill_doc: str, val_tasks: list[dict], n_samples: int,
                       scheduler: "Scheduler", provider: str, rollout_fn: RolloutFn,
                       scorer: Scorer, cache: ResultCache | None = None,
                       model: str = "claude") -> list[Record]:
    """Evaluate a skill over the FROZEN val split with n-sample self-consistency.

    Every (task, sample) rollout is fanned out through the provider pool at once
    (validation is embarrassingly parallel, capped by the pool, spine §4). Results
    are cached at the aggregate level by (skill_hash, task_id, model, provider) so
    re-baselining the prior skill is cheap and identical across calls.
    """
    skill_h = skill_hash(skill_doc)
    out: list[Record | None] = []
    pending: list[tuple[int, dict]] = []
    for i, task in enumerate(val_tasks):
        key = cache_key(skill_h, task["id"], model, provider)
        if cache is not None and key in cache:
            out.append(cache.get(key))
        else:
            out.append(None)
            pending.append((i, task))

    if pending:
        factories: list[Callable[[], Awaitable]] = []
        spans: list[tuple[int, dict, int, int]] = []
        for idx, task in pending:
            start = len(factories)
            for _ in range(n_samples):
                factories.append(lambda s=skill_doc, t=task: rollout_fn(s, t))
            spans.append((idx, task, start, start + n_samples))
        rollouts = await fanout(scheduler, provider, factories)
        for idx, task, start, end in spans:
            samples = [scorer(task, rollouts[j]) for j in range(start, end)]
            rec = aggregate_samples(task["id"], samples)
            out[idx] = rec
            if cache is not None:
                cache.put(cache_key(skill_h, task["id"], model, provider), rec)
    return [r for r in out if r is not None]


# --------------------------------------------------------------------------- #
# A/A calibration of the gate noise floor σ_gate (re-measured per epoch)
# --------------------------------------------------------------------------- #
async def calibrate_sigma_gate(*, skill_doc: str, val_tasks: list[dict], n_samples: int,
                               scheduler: "Scheduler", provider: str, rollout_fn: RolloutFn,
                               scorer: Scorer, metric: str = "mixed",
                               model: str = "claude") -> float:
    """A/A test: evaluate the SAME skill over val twice, σ = std of per-task delta.

    Re-run once per epoch. Caching is bypassed (cache=None) so the two runs are
    genuinely re-measured — otherwise the second run would return the cached first
    run and σ would be trivially 0. With fully deterministic scorers σ collapses to
    0 and the 1/M floor dominates the accept threshold, exactly as intended.
    """
    run_a = await evaluate_val(skill_doc=skill_doc, val_tasks=val_tasks, n_samples=n_samples,
                               scheduler=scheduler, provider=provider, rollout_fn=rollout_fn,
                               scorer=scorer, cache=None, model=model)
    run_b = await evaluate_val(skill_doc=skill_doc, val_tasks=val_tasks, n_samples=n_samples,
                               scheduler=scheduler, provider=provider, rollout_fn=rollout_fn,
                               scorer=scorer, cache=None, model=model)
    a = {r["id"]: metric_value(r, metric) for r in run_a}
    b = {r["id"]: metric_value(r, metric) for r in run_b}
    deltas = [a[i] - b[i] for i in a if i in b]
    if len(deltas) < 2:
        return 0.0
    return statistics.pstdev(deltas)


# --------------------------------------------------------------------------- #
# Paired re-baseline: re-eval the prior skill under the CURRENT model each gate
# --------------------------------------------------------------------------- #
async def rebaseline(*, prior_skill_doc: str, val_tasks: list[dict], n_samples: int,
                     scheduler: "Scheduler", provider: str, rollout_fn: RolloutFn,
                     scorer: Scorer, cache: ResultCache | None = None,
                     model: str = "claude") -> list[Record]:
    """Re-evaluate the PRIOR (currently-accepted) skill under the CURRENT model.

    Never trust a stale stored score (spine §6.5): silent model/CLI drift would
    corrupt the gate. Cached by (skill_hash, task_id, model, provider), so the
    baseline is recomputed for free only when the model/provider actually changes.
    """
    return await evaluate_val(skill_doc=prior_skill_doc, val_tasks=val_tasks,
                              n_samples=n_samples, scheduler=scheduler, provider=provider,
                              rollout_fn=rollout_fn, scorer=scorer, cache=cache, model=model)


# --------------------------------------------------------------------------- #
# The gate
# --------------------------------------------------------------------------- #
def _binom_tail(n: int, k: int) -> float:
    """P(X >= k) for X ~ Binomial(n, 0.5)."""
    return sum(math.comb(n, i) for i in range(k, n + 1)) / (2 ** n)


def sign_test_p(deltas: list[float], eps: float = 1e-9) -> float:
    """Two-sided exact binomial sign-test p-value for paired deltas (no scipy)."""
    pos = sum(1 for d in deltas if d > eps)
    neg = sum(1 for d in deltas if d < -eps)
    n = pos + neg
    if n == 0:
        return 1.0
    k = max(pos, neg)
    return min(1.0, 2.0 * _binom_tail(n, k))


def gate_accept(val_old: list[dict], val_new: list[dict], *, metric: str = "mixed",
                sigma_gate: float, M: int, mode: str = "variance") -> bool:
    """Decide whether to accept the candidate skill (spine §10 signature, verbatim).

      variance: accept iff mean(val_new) - mean(val_old) > max(2*sigma_gate, 1/M)
      strict:   accept iff mean(val_new) > mean(val_old)        (stock SkillOpt)
      paired:   variance threshold AND a paired sign test at p < 0.05

    `val_old` / `val_new` are lists of scored records; paired mode aligns them by id.
    """
    old = _by_id(val_old)
    new = _by_id(val_new)
    mo = mean_metric(old, metric)
    mn = mean_metric(new, metric)

    if mode == "strict":
        return mn > mo

    threshold = max(2.0 * sigma_gate, 1.0 / M)
    if mode == "variance":
        return (mn - mo) > threshold

    if mode == "paired":
        if (mn - mo) <= threshold:
            return False
        old_by = {r["id"]: metric_value(r, metric) for r in old}
        new_by = {r["id"]: metric_value(r, metric) for r in new}
        deltas = [new_by[i] - old_by[i] for i in new_by if i in old_by]
        return sign_test_p(deltas) < 0.05

    raise ValueError(f"unknown gate mode {mode!r}")
