"""Hermetic tests for the timestamp scorer, loader, and run_batch. No CLI/LLM."""
from skillopt_oauth.envs.timestamp.scorer import score
from skillopt_oauth.envs.timestamp.adapter import TimestampAdapter
from skillopt_oauth.envs.timestamp.dataloader import TimestampDataLoader


def _ws_with(base, names, name="ws"):
    """Build a workspace dir; entries ending in '/' become subdirectories."""
    ws = base / name
    ws.mkdir(parents=True)
    for n in names:
        if n.endswith("/"):
            (ws / n.rstrip("/")).mkdir()
        else:
            (ws / n).write_text("x", encoding="utf-8")
    return str(ws)


class TestTimestampScorer:
    def test_pass_all_stamped(self, tmp_path):
        ws = _ws_with(tmp_path, ["260629-120000-report.md", "260629-120000-figures/"])
        r = {"id": "t1", "stdout": "", "workspace_dir": ws}
        assert score({"id": "t1", "min_artifacts": 2}, r) == {"id": "t1", "hard": 1, "soft": 1.0}

    def test_fail_none_stamped(self, tmp_path):
        ws = _ws_with(tmp_path, ["report.md", "notes.md"])
        out = score({"id": "t2", "min_artifacts": 1}, {"id": "t2", "stdout": "", "workspace_dir": ws})
        assert out["hard"] == 0 and out["soft"] == 0.0

    def test_partial_soft_fraction(self, tmp_path):
        ws = _ws_with(tmp_path, ["260629-120000-a.md", "b.md"])
        out = score({"id": "t3"}, {"id": "t3", "stdout": "", "workspace_dir": ws})
        assert out["hard"] == 0 and out["soft"] == 0.5

    def test_produced_names_override(self):
        r = {"id": "t4", "stdout": "", "workspace_dir": None,
             "produced_names": ["260629-120000-x.md"]}
        assert score({"id": "t4", "min_artifacts": 1}, r) == {"id": "t4", "hard": 1, "soft": 1.0}

    def test_empty_workspace_is_zero(self, tmp_path):
        ws = _ws_with(tmp_path, [])
        assert score({"id": "t5"}, {"id": "t5", "stdout": "", "workspace_dir": ws}) == {
            "id": "t5", "hard": 0, "soft": 0.0}


class TestTimestampLoaderDeterminism:
    def _make_tasks(self, tmp_path):
        d = tmp_path / "tasks"
        (d / "train").mkdir(parents=True)
        (d / "val").mkdir(parents=True)
        (d / "train" / "tasks.jsonl").write_text(
            '{"id":"a","type":"file","prompt":"p","min_artifacts":1}\n'
            '{"id":"c","type":"folder","prompt":"p","min_artifacts":1}\n'
            '{"id":"b","type":"file","prompt":"p","min_artifacts":1}\n', encoding="utf-8")
        (d / "val" / "tasks.jsonl").write_text(
            '{"id":"v2","type":"file","prompt":"p","min_artifacts":1}\n'
            '{"id":"v1","type":"file","prompt":"p","min_artifacts":1}\n', encoding="utf-8")
        return d

    def test_val_ids_frozen_across_loads(self, tmp_path):
        d = self._make_tasks(tmp_path)
        ids1 = [t["id"] for t in TimestampDataLoader(tasks_dir=d).val_split()]
        ids2 = [t["id"] for t in TimestampDataLoader(tasks_dir=d).val_split()]
        assert ids1 == ids2 == ["v1", "v2"]  # stable-sorted, frozen

    def test_train_batch_same_seed_is_stable(self, tmp_path):
        ld = TimestampDataLoader(tasks_dir=self._make_tasks(tmp_path))
        assert [t["id"] for t in ld.sample_train_batch(2, seed=7)] == \
               [t["id"] for t in ld.sample_train_batch(2, seed=7)]

    def test_deterministic_split_is_stable(self):
        pool = [{"id": f"x{i}"} for i in range(20)]
        _, va1 = TimestampDataLoader.deterministic_split(pool, val_fraction=0.3, seed=1)
        tr2, va2 = TimestampDataLoader.deterministic_split(pool, val_fraction=0.3, seed=1)
        assert [t["id"] for t in va1] == [t["id"] for t in va2]
        assert set(t["id"] for t in tr2).isdisjoint(t["id"] for t in va1)


class TestTimestampRunBatchShape:
    def test_run_batch_shape(self, tmp_path):
        ws_ok = _ws_with(tmp_path, ["260629-120000-ok.md"], name="ok")
        ws_bad = _ws_with(tmp_path, ["bad.md"], name="bad")
        tasks = [{"id": "r1", "min_artifacts": 1}, {"id": "r2", "min_artifacts": 1}]
        rollouts = [{"id": "r1", "stdout": "", "workspace_dir": ws_ok},
                    {"id": "r2", "stdout": "", "workspace_dir": ws_bad}]
        out = TimestampAdapter().run_batch(tasks, rollouts=rollouts)
        assert [r["id"] for r in out] == ["r1", "r2"]
        for r in out:
            assert set(r.keys()) == {"id", "hard", "soft"}
            assert r["hard"] in (0, 1)
            assert 0.0 <= r["soft"] <= 1.0
        assert out[0]["hard"] == 1 and out[1]["hard"] == 0

    def test_run_batch_missing_rollout(self):
        out = TimestampAdapter().run_batch([{"id": "z1"}], rollouts=[])
        assert out == [{"id": "z1", "hard": 0, "soft": 0.0}]
