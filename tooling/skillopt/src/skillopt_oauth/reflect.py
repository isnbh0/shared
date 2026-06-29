"""Parallel-propose reflection with a deterministic LR-bounded merge.

THE ONE STATED FIDELITY COMPROMISE (spine §4): stock SkillOpt applies minibatch
reflections sequentially against an evolving skill. We parallel-PROPOSE edits
across minibatches against the SAME pre-step skill, then deterministically MERGE
under the global LR edit budget. This changes optimization dynamics slightly but
is the only way to parallelize reflection; the merge enforces the same LR budget.
`reflection_mode: sequential` recovers exact stock behavior.

We WRAP upstream `gradient.run_minibatch_reflect` (the proposer) and never rewrite
its reflection logic. The merge / clamp / apply / schema layer below is ours and is
pure (no LLM, fully deterministic) so it is unit-testable offline.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Awaitable, Callable

from .gate import Scheduler, fanout

VALID_KINDS = ("add", "delete", "replace")
# Deterministic ordering / apply priority: deletes, then replaces, then adds, so
# anchor resolution never depends on proposal order and the LR clamp is stable.
_KIND_ORDER = {"delete": 0, "replace": 1, "add": 2}


# --------------------------------------------------------------------------- #
# Strict edit-op schema
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class EditOp:
    """A single patch edit. `anchor` locates the edit; `text` is the payload.

      add     : insert `text` after the first line containing `anchor`
                ("" anchor => append at end). `text` required.
      delete  : remove the first line containing `anchor`. `anchor` required.
      replace : replace the first line containing `anchor` with `text`.
                `anchor` and `text` required.
    """
    kind: str
    anchor: str
    text: str

    def canonical(self) -> str:
        return json.dumps({"kind": self.kind, "anchor": self.anchor, "text": self.text},
                          sort_keys=True, ensure_ascii=False)

    def op_id(self) -> str:
        return hashlib.sha1(self.canonical().encode("utf-8")).hexdigest()[:12]

    def sort_key(self) -> tuple:
        # Deterministic global ordering: kind priority, then anchor, then text.
        return (_KIND_ORDER[self.kind], self.anchor, self.text)


def validate_op(raw: object) -> EditOp | None:
    """Schema-validate one proposed op. Returns an EditOp, or None if malformed."""
    if not isinstance(raw, dict):
        return None
    kind = raw.get("kind")
    if kind not in VALID_KINDS:
        return None
    anchor = raw.get("anchor", "")
    text = raw.get("text", "")
    if not isinstance(anchor, str) or not isinstance(text, str):
        return None
    if kind in ("add", "replace") and text == "":
        return None
    if kind in ("delete", "replace") and anchor == "":
        return None
    return EditOp(kind=kind, anchor=anchor, text=text)


def parse_edit_ops(raw_stdout: str) -> tuple[list[EditOp], list]:
    """Parse a JSON patch payload into (valid_ops, malformed_items).

    Accepts a bare JSON array of ops or an object `{"edits": [...]}`. A payload
    that is not valid JSON, or not an array/object, is wholly malformed.
    """
    try:
        doc = json.loads(raw_stdout)
    except (json.JSONDecodeError, TypeError):
        return [], [raw_stdout]
    if isinstance(doc, dict):
        items = doc.get("edits", [])
    elif isinstance(doc, list):
        items = doc
    else:
        return [], [raw_stdout]
    valid: list[EditOp] = []
    bad: list = []
    for it in items:
        op = validate_op(it)
        if op is None:
            bad.append(it)
        else:
            valid.append(op)
    return valid, bad


# --------------------------------------------------------------------------- #
# Proposer seam (wraps upstream; LLM-backed in production, faked in tests)
# --------------------------------------------------------------------------- #
ProposeFn = Callable[[str, list[dict]], Awaitable[str]]   # (pre_step_skill, minibatch) -> raw JSON
RepairFn = Callable[[str, str], Awaitable[str]]           # (skill_doc, bad_raw) -> repaired JSON


def make_upstream_propose_fn(*, executor, lr: int, provider: str = "claude") -> ProposeFn:
    """Build a `propose_fn` that calls upstream `gradient.run_minibatch_reflect`.

    We DO NOT reimplement reflection: upstream owns prompt construction and the
    optimizer logic. We only (1) inject an OAuth-CLI-backed `llm` callable so the
    reflect call stays on the subscription session (the single chokepoint, Phase 2;
    no API path exists), and (2) pass the LR edit budget through. The upstream return
    value (a raw JSON patch on stdout) is handed back verbatim for our parse/merge
    layer. The call is synchronous upstream, so we run it off-thread; the Phase-3
    scheduler owns concurrency, applied one level up in `run_reflection`.
    """
    import asyncio

    from skillopt.gradient import run_minibatch_reflect  # upstream, UNMODIFIED

    def _oauth_llm(prompt: str) -> str:
        # Forces the optimizer onto the OAuth CLI; fail-closed executor blocks API.
        return executor.run_cli(provider=provider, prompt=prompt).stdout

    async def _propose(skill_doc: str, minibatch: list[dict]) -> str:
        def _call() -> str:
            return run_minibatch_reflect(
                skill=skill_doc,
                rollouts=minibatch,
                llm=_oauth_llm,
                lr_budget=lr,
            )
        return await asyncio.to_thread(_call)

    return _propose


async def propose_minibatch_edits(*, skill_doc: str, minibatch: list[dict], lr: int,
                                  propose_fn: ProposeFn,
                                  repair_fn: RepairFn | None = None) -> list[EditOp]:
    """Propose edits for ONE minibatch, then parse + schema-validate.

    Malformed payloads get ONE repair retry (if `repair_fn` is supplied) and are
    otherwise dropped. Returns the (still unclamped) proposed ops; the global LR
    budget is enforced later in `merge_edits`.
    """
    raw = await propose_fn(skill_doc, minibatch)
    ops, bad = parse_edit_ops(raw)
    if bad and repair_fn is not None:
        repaired = await repair_fn(skill_doc, raw)
        more, _ = parse_edit_ops(repaired)
        ops.extend(more)
    return ops


# --------------------------------------------------------------------------- #
# Deterministic merge + apply
# --------------------------------------------------------------------------- #
def merge_edits(proposals: list[list[EditOp]], *, lr: int) -> list[EditOp]:
    """Deterministic reducer enforcing the global LR edit budget.

    1. flatten every proposed op across minibatches,
    2. dedup by canonical op identity (`op_id`),
    3. deterministic global ordering (kind priority, anchor, text),
    4. HARD-CLAMP to the current LR — drop everything past the budget.
    """
    seen: set[str] = set()
    flat: list[EditOp] = []
    for ops in proposals:
        for op in ops:
            oid = op.op_id()
            if oid in seen:
                continue
            seen.add(oid)
            flat.append(op)
    flat.sort(key=lambda o: o.sort_key())
    budget = max(0, int(lr))
    return flat[:budget]


def apply_edits(skill_doc: str, ops: list[EditOp]) -> str:
    """Apply ops to produce the candidate skill (deterministic, anchor-substring).

    Application order is fixed — deletes, then replaces, then adds — so anchor
    resolution never depends on proposal order. A schema-valid op whose anchor is
    absent from this doc is a no-op (it could not be located here).
    """
    lines = skill_doc.split("\n")

    def _find(anchor: str) -> int:
        for i, ln in enumerate(lines):
            if anchor in ln:
                return i
        return -1

    ordered = sorted(ops, key=lambda o: o.sort_key())
    for op in ordered:
        if op.kind == "delete":
            i = _find(op.anchor)
            if i != -1:
                del lines[i]
    for op in ordered:
        if op.kind == "replace":
            i = _find(op.anchor)
            if i != -1:
                lines[i] = op.text
    for op in ordered:
        if op.kind == "add":
            if op.anchor == "":
                lines.append(op.text)
            else:
                i = _find(op.anchor)
                lines.insert(i + 1, op.text) if i != -1 else lines.append(op.text)
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Reflection step (parallel-propose + merge, or stock sequential)
# --------------------------------------------------------------------------- #
@dataclass
class ReflectResult:
    candidate_doc: str
    applied_ops: list[EditOp]
    proposals: list[list[EditOp]]


def _minibatches(scored: list[dict], size: int) -> list[list[dict]]:
    if not scored:
        return []
    return [scored[i:i + size] for i in range(0, len(scored), size)]


async def run_reflection(*, skill_doc: str, scored_rollouts: list[dict], lr: int,
                         scheduler: Scheduler, provider: str, minibatch_size: int,
                         propose_fn: ProposeFn, repair_fn: RepairFn | None = None,
                         reflection_mode: str = "parallel") -> ReflectResult:
    """Compose proposal + deterministic merge.

      parallel (default): fan minibatch proposals out (Phase-3 scheduler) against
                          the SAME pre-step skill, merge under the LR budget, apply once.
      sequential        : reproduce stock SkillOpt — apply each minibatch's proposal
                          to the evolving doc in order, decrementing the shared LR
                          budget, stopping when it is exhausted.
    """
    mbs = _minibatches(scored_rollouts, minibatch_size)

    if reflection_mode == "sequential":
        doc = skill_doc
        applied: list[EditOp] = []
        proposals: list[list[EditOp]] = []
        budget = int(lr)
        for mb in mbs:
            if budget <= 0:
                break
            ops = await propose_minibatch_edits(skill_doc=doc, minibatch=mb, lr=budget,
                                                propose_fn=propose_fn, repair_fn=repair_fn)
            proposals.append(ops)
            take = merge_edits([ops], lr=budget)
            doc = apply_edits(doc, take)
            applied.extend(take)
            budget -= len(take)
        return ReflectResult(candidate_doc=doc, applied_ops=applied, proposals=proposals)

    if reflection_mode != "parallel":
        raise ValueError(f"unknown reflection_mode {reflection_mode!r}")

    # parallel-propose: every minibatch proposes against the same pre-step skill.
    factories = [
        (lambda mb=mb: propose_minibatch_edits(skill_doc=skill_doc, minibatch=mb, lr=lr,
                                               propose_fn=propose_fn, repair_fn=repair_fn))
        for mb in mbs
    ]
    proposals = list(await fanout(scheduler, provider, factories))
    applied = merge_edits(proposals, lr=lr)
    candidate = apply_edits(skill_doc, applied)
    return ReflectResult(candidate_doc=candidate, applied_ops=applied, proposals=proposals)
