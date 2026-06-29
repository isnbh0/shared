"""Write-ahead checkpoint: atomic write, full round-trip, RNG reproducibility."""
from __future__ import annotations

import random

from skillopt_oauth.checkpoint import TrainState, resume, write_checkpoint
from skillopt_oauth.gate import cache_key, skill_hash


def test_checkpoint_roundtrip_and_atomic(tmp_path):
    st = TrainState(skill_doc="DOC", epoch=1, step=7, step_in_epoch=2, data_cursor=80,
                    best_score=0.83, best_skill_doc="BEST", sigma_gate=0.05)
    r = random.Random(123)
    for _ in range(5):
        r.random()
    st.set_rng(r)
    key = cache_key(skill_hash("DOC"), "t1", "claude", "claude")
    st.cache.put(key, {"id": "t1", "hard": 1, "soft": 0.9})

    p = tmp_path / "ck.json"
    write_checkpoint(str(p), st)
    assert p.exists()
    assert not list(tmp_path.glob("*.tmp*"))        # atomic: no temp file left behind

    back = resume(str(p))
    assert back is not None
    assert (back.skill_doc, back.step, back.epoch, back.step_in_epoch) == ("DOC", 7, 1, 2)
    assert back.data_cursor == 80
    assert back.best_score == 0.83 and back.best_skill_doc == "BEST"
    assert back.sigma_gate == 0.05
    assert key in back.cache and back.cache.get(key)["soft"] == 0.9
    # RNG state survives the round-trip exactly.
    assert back.get_rng().random() == st.get_rng().random()


def test_resume_returns_none_when_missing(tmp_path):
    assert resume(str(tmp_path / "nope.json")) is None
