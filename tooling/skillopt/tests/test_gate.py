"""Variance-aware gate: accept/reject across the noise band, strict-vs-variance,
self-consistency aggregation, A/A calibration, paired sign test."""
from __future__ import annotations

import asyncio

import pytest

from skillopt_oauth.gate import (aggregate_samples, calibrate_sigma_gate,
                                 evaluate_val, gate_accept, mean_metric, sign_test_p)
from conftest import FakeScheduler, rec


def _const(vals):
    return [rec(f"t{i}", v, v) for i, v in enumerate(vals)]


def test_accepts_when_delta_exceeds_threshold():
    old = _const([0.0] * 5)
    new = _const([1.0] * 5)
    assert gate_accept(old, new, sigma_gate=0.0, M=5, mode="variance") is True


def test_rejects_within_noise_band():
    # Delta = 0.1 but threshold = max(2*0.1, 1/5) = 0.2 -> reject.
    old = _const([0.50] * 5)
    new = _const([0.60] * 5)
    assert gate_accept(old, new, sigma_gate=0.1, M=5, mode="variance") is False


def test_strict_vs_variance_differ_on_borderline():
    # Delta = +0.05, threshold = 0.2: strict accepts, variance rejects.
    old = _const([0.50] * 5)
    new = _const([0.55] * 5)
    assert gate_accept(old, new, sigma_gate=0.1, M=5, mode="strict") is True
    assert gate_accept(old, new, sigma_gate=0.1, M=5, mode="variance") is False


def test_floor_threshold_when_sigma_zero():
    # sigma=0 -> threshold = 1/M. A delta below 1/M is rejected, above is accepted.
    old = _const([0.0] * 4)
    near = [rec(f"t{i}", 0, 0.2) for i in range(4)]   # mixed mean = 0.1 < 1/4=0.25
    assert gate_accept(old, near, sigma_gate=0.0, M=4, mode="variance") is False
    far = [rec(f"t{i}", 0, 0.8) for i in range(4)]     # mixed mean = 0.4 > 0.25
    assert gate_accept(old, far, sigma_gate=0.0, M=4, mode="variance") is True


def test_self_consistency_majority_and_median():
    samples = [rec("x", 1, 0.9), rec("x", 0, 0.4), rec("x", 1, 0.6)]
    agg = aggregate_samples("x", samples)
    assert agg["hard"] == 1            # majority of {1,0,1}
    assert agg["soft"] == 0.6          # median of {0.9,0.4,0.6}


def test_paired_requires_significant_sign_test():
    # Uniform improvement across many tasks -> significant + above threshold.
    old = _const([0.0] * 9)
    new = _const([1.0] * 9)
    assert gate_accept(old, new, sigma_gate=0.0, M=9, mode="paired") is True
    # A single improver among ties is not significant.
    old2 = _const([0.0] * 9)
    new2 = [rec("t0", 1, 1.0)] + [rec(f"t{i}", 0, 0.0) for i in range(1, 9)]
    assert sign_test_p([1.0] + [0.0] * 8) >= 0.05
    assert gate_accept(old2, new2, sigma_gate=0.0, M=9, mode="paired") is False


def test_aa_calibration_is_zero_for_deterministic_scorer():
    val = [{"id": f"t{i}"} for i in range(5)]

    async def rollout_fn(skill_doc, task):
        return {"id": task["id"], "stdout": f"OUT::{task['id']}"}   # deterministic per task

    def scorer(task, rollout):
        return rec(task["id"], 1, 1.0)         # deterministic score

    sigma = asyncio.run(calibrate_sigma_gate(
        skill_doc="S", val_tasks=val, n_samples=3, scheduler=FakeScheduler(),
        provider="claude", rollout_fn=rollout_fn, scorer=scorer, metric="mixed"))
    assert sigma == 0.0


def test_evaluate_val_uses_cache_and_freezes_split():
    from skillopt_oauth.gate import ResultCache
    val = [{"id": "a"}, {"id": "b"}]
    seen = {"n": 0}

    async def rollout_fn(skill_doc, task):
        seen["n"] += 1
        return {"id": task["id"], "stdout": "ok"}

    def scorer(task, rollout):
        return rec(task["id"], 1, 1.0)

    cache = ResultCache()
    recs1 = asyncio.run(evaluate_val(skill_doc="S", val_tasks=val, n_samples=3,
                                     scheduler=FakeScheduler(), provider="claude",
                                     rollout_fn=rollout_fn, scorer=scorer, cache=cache))
    first = seen["n"]
    recs2 = asyncio.run(evaluate_val(skill_doc="S", val_tasks=val, n_samples=3,
                                     scheduler=FakeScheduler(), provider="claude",
                                     rollout_fn=rollout_fn, scorer=scorer, cache=cache))
    assert seen["n"] == first                 # second eval fully cached, zero rollouts
    assert mean_metric(recs1) == mean_metric(recs2) == 1.0
    assert [r["id"] for r in recs1] == ["a", "b"]
