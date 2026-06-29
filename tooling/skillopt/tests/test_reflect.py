"""Parallel-propose reflection: LR hard-clamp, dedup/ordering determinism,
schema validation + repair/drop, parallel-vs-sequential."""
from __future__ import annotations

import asyncio
import json

import pytest

from skillopt_oauth.reflect import (EditOp, apply_edits, merge_edits, parse_edit_ops,
                                    run_reflection, validate_op)
from conftest import FakeScheduler


def _ops(*specs):
    return [EditOp(kind=k, anchor=a, text=t) for (k, a, t) in specs]


def _scored(n):
    return [{"id": f"t{i}", "hard": 0, "soft": 0.0,
             "stdout": "x", "task": {"id": f"t{i}"}} for i in range(n)]


def test_merge_hard_clamps_to_lr():
    proposals = [_ops(*[("add", "", f"line {i}") for i in range(10)])]
    merged = merge_edits(proposals, lr=4)
    assert len(merged) == 4


def test_merge_dedups_across_minibatches():
    a = _ops(("add", "", "same"), ("add", "", "alpha"))
    b = _ops(("add", "", "same"), ("add", "", "beta"))
    merged = merge_edits([a, b], lr=10)
    texts = sorted(o.text for o in merged)
    assert texts == ["alpha", "beta", "same"]   # "same" collapsed once


def test_merge_ordering_is_deterministic():
    proposals = [_ops(("add", "", "z"), ("delete", "k", ""), ("replace", "k", "q"))]
    m1 = merge_edits(proposals, lr=10)
    m2 = merge_edits(list(reversed(proposals)) or proposals, lr=10)
    assert [o.canonical() for o in m1] == [o.canonical() for o in m2]
    # delete < replace < add priority
    assert [o.kind for o in m1] == ["delete", "replace", "add"]


def test_parse_and_validate_schema():
    good = json.dumps({"edits": [
        {"kind": "add", "anchor": "", "text": "ok"},
        {"kind": "delete", "anchor": "drop me", "text": ""},
        {"kind": "bogus", "anchor": "x", "text": "y"},     # bad kind
        {"kind": "replace", "anchor": "", "text": "z"},    # replace needs anchor
        {"kind": "add", "anchor": "", "text": ""},         # add needs text
    ]})
    ops, bad = parse_edit_ops(good)
    assert [o.kind for o in ops] == ["add", "delete"]
    assert len(bad) == 3
    assert validate_op({"kind": "add", "anchor": "", "text": "t"}) is not None
    assert validate_op("not a dict") is None


def test_malformed_payload_is_repaired_then_applied():
    async def propose_fn(skill_doc, minibatch):
        return "this is not json"                # malformed -> triggers repair

    async def repair_fn(skill_doc, bad_raw):
        return json.dumps({"edits": [{"kind": "add", "anchor": "", "text": "REPAIRED"}]})

    res = asyncio.run(run_reflection(
        skill_doc="HEADER", scored_rollouts=_scored(8), lr=4, scheduler=FakeScheduler(),
        provider="codex", minibatch_size=8, propose_fn=propose_fn, repair_fn=repair_fn))
    assert any(o.text == "REPAIRED" for o in res.applied_ops)


def test_malformed_payload_dropped_without_repair():
    async def propose_fn(skill_doc, minibatch):
        return "garbage{"

    res = asyncio.run(run_reflection(
        skill_doc="HEADER", scored_rollouts=_scored(8), lr=4, scheduler=FakeScheduler(),
        provider="codex", minibatch_size=8, propose_fn=propose_fn, repair_fn=None))
    assert res.applied_ops == []
    assert res.candidate_doc == "HEADER"


def test_parallel_propose_clamps_across_minibatches():
    # 3 minibatches each proposing 5 distinct ops (15 total) -> clamped to lr=4.
    async def propose_fn(skill_doc, minibatch):
        base = minibatch[0]["id"]
        ops = [{"kind": "add", "anchor": "", "text": f"{base}:{i}"} for i in range(5)]
        return json.dumps({"edits": ops})

    res = asyncio.run(run_reflection(
        skill_doc="HEADER", scored_rollouts=_scored(9), lr=4, scheduler=FakeScheduler(),
        provider="codex", minibatch_size=3, propose_fn=propose_fn,
        reflection_mode="parallel"))
    assert len(res.proposals) == 3            # one proposal set per minibatch
    assert len(res.applied_ops) == 4          # hard LR clamp


def test_sequential_mode_respects_budget_and_evolves_doc():
    calls = {"docs": []}

    async def propose_fn(skill_doc, minibatch):
        calls["docs"].append(skill_doc)
        return json.dumps({"edits": [
            {"kind": "add", "anchor": "", "text": f"add-{minibatch[0]['id']}"}]})

    res = asyncio.run(run_reflection(
        skill_doc="HEADER", scored_rollouts=_scored(9), lr=2, scheduler=FakeScheduler(),
        provider="codex", minibatch_size=3, propose_fn=propose_fn,
        reflection_mode="sequential"))
    # Budget 2 -> at most 2 minibatches consumed; doc evolves between proposals.
    assert len(res.applied_ops) == 2
    assert calls["docs"][0] == "HEADER"
    assert calls["docs"][1] != "HEADER"        # second proposal sees the evolved doc


def test_apply_edits_add_delete_replace():
    doc = "alpha\nbeta\ngamma"
    ops = _ops(("delete", "beta", ""), ("replace", "gamma", "GAMMA"),
               ("add", "alpha", "inserted"))
    out = apply_edits(doc, ops)
    assert out == "alpha\ninserted\nGAMMA"
