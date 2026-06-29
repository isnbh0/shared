"""Hermetic tests for the spex_write_phased scorer, loader, and run_batch."""
from skillopt_oauth.envs.spex_write_phased.scorer import score
from skillopt_oauth.envs.spex_write_phased.adapter import SpexWritePhasedAdapter
from skillopt_oauth.envs.spex_write_phased.dataloader import SpexWritePhasedDataLoader

README_OK = (
    "# Feature\n"
    "## Design Principles\n"
    "## Key Design Decisions\n"
    "## Phase Summary\n"
    "## Progress Tracking\n"
)
PHASE_OK = (
    "## Phase 1: X\n"
    "**Goal:** do the thing\n"
    "**Entry state:** a\n"
    "**Exit state:** b\n"
    "### Implementation Checklist\n"
    "### Required Tests\n"
)


def _spec_ws(base, *, dir_name, readme, phases, name="ws"):
    ws = base / name
    ws.mkdir(parents=True)
    if dir_name:
        sd = ws / dir_name
        sd.mkdir()
        if readme is not None:
            (sd / "README.md").write_text(readme, encoding="utf-8")
        for fname, text in phases:
            (sd / fname).write_text(text, encoding="utf-8")
    return str(ws)


class TestSpexScorer:
    def test_pass_full_structure(self, tmp_path):
        ws = _spec_ws(tmp_path, dir_name="260629-235959-my-spec",
                      readme=README_OK, phases=[("P1-foo.md", PHASE_OK)])
        assert score({"id": "s1"}, {"id": "s1", "stdout": "", "workspace_dir": ws}) == {
            "id": "s1", "hard": 1, "soft": 1.0}

    def test_fail_partial(self, tmp_path):
        ws = _spec_ws(tmp_path, dir_name="260629-235959-my-spec",
                      readme="# F\n## Design Principles\n", phases=[])
        out = score({"id": "s2"}, {"id": "s2", "stdout": "", "workspace_dir": ws})
        # passing: timestamped_dir, readme_present, Design Principles -> 3/12
        assert out["hard"] == 0 and out["soft"] == round(3 / 12, 6)

    def test_fail_no_spec_dir(self, tmp_path):
        ws = _spec_ws(tmp_path, dir_name=None, readme=None, phases=[])
        assert score({"id": "s3"}, {"id": "s3", "stdout": "", "workspace_dir": ws}) == {
            "id": "s3", "hard": 0, "soft": 0.0}

    def test_fail_phase_missing_marker(self, tmp_path):
        bad_phase = ("## Phase 1\n**Goal:** g\n**Entry state:** e\n"
                     "**Exit state:** x\n### Implementation Checklist\n")  # no Required Tests
        ws = _spec_ws(tmp_path, dir_name="260629-235959-spec",
                      readme=README_OK, phases=[("P1-a.md", bad_phase)])
        out = score({"id": "s4"}, {"id": "s4", "stdout": "", "workspace_dir": ws})
        assert out["hard"] == 0 and out["soft"] == round(11 / 12, 6)


class TestSpexLoaderDeterminism:
    def _make_tasks(self, tmp_path):
        d = tmp_path / "tasks"
        (d / "train").mkdir(parents=True)
        (d / "val").mkdir(parents=True)
        (d / "train" / "tasks.jsonl").write_text(
            '{"id":"t-b","type":"spec","prompt":"p","min_phase_files":1}\n'
            '{"id":"t-a","type":"spec","prompt":"p","min_phase_files":1}\n', encoding="utf-8")
        (d / "val" / "tasks.jsonl").write_text(
            '{"id":"v-b","type":"spec","prompt":"p","min_phase_files":1}\n'
            '{"id":"v-a","type":"spec","prompt":"p","min_phase_files":1}\n', encoding="utf-8")
        return d

    def test_val_ids_frozen_across_loads(self, tmp_path):
        d = self._make_tasks(tmp_path)
        ids1 = [t["id"] for t in SpexWritePhasedDataLoader(tasks_dir=d).val_split()]
        ids2 = [t["id"] for t in SpexWritePhasedDataLoader(tasks_dir=d).val_split()]
        assert ids1 == ids2 == ["v-a", "v-b"]


class TestSpexRunBatchShape:
    def test_run_batch_shape(self, tmp_path):
        ws_ok = _spec_ws(tmp_path, dir_name="260629-235959-ok",
                         readme=README_OK, phases=[("P1-x.md", PHASE_OK)], name="ok")
        ws_bad = _spec_ws(tmp_path, dir_name=None, readme=None, phases=[], name="bad")
        tasks = [{"id": "r1"}, {"id": "r2"}]
        rollouts = [{"id": "r1", "stdout": "", "workspace_dir": ws_ok},
                    {"id": "r2", "stdout": "", "workspace_dir": ws_bad}]
        out = SpexWritePhasedAdapter().run_batch(tasks, rollouts=rollouts)
        assert [r["id"] for r in out] == ["r1", "r2"]
        for r in out:
            assert set(r.keys()) == {"id", "hard", "soft"}
            assert r["hard"] in (0, 1)
            assert 0.0 <= r["soft"] <= 1.0
        assert out[0]["hard"] == 1 and out[1]["hard"] == 0
