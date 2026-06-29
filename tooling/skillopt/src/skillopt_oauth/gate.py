"""Variance-aware validation gate (Phase 5).

STUB STATE: signature only; raises NotImplementedError.
FUTURE (Phase 5): variance-aware accept on a fixed val split with n-sample
self-consistency, per-epoch A/A sigma calibration, paired re-baseline of the prior
skill under the current model, and a result cache. `mode="strict"` reproduces stock
SkillOpt's single-sample strict-improvement gate.
"""
from __future__ import annotations


def gate_accept(val_old: list[dict], val_new: list[dict], *, metric="mixed",
                sigma_gate: float, M: int, mode="variance") -> bool:
    # variance mode: accept iff mean(val_new) - mean(val_old) > max(2*sigma_gate, 1/M)
    # strict mode:   accept iff mean(val_new) > mean(val_old)
    raise NotImplementedError("gate_accept is implemented in Phase 5")
