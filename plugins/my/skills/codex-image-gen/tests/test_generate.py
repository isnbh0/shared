# /// script
# requires-python = ">=3.13"
# dependencies = ["pillow>=11,<13"]
# ///
"""Offline recovery/publication checks. Run with uv run tests/test_generate.py."""

import argparse
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import uuid
import subprocess

from PIL import Image

spec = importlib.util.spec_from_file_location("generate", Path(__file__).parents[1] / "scripts/generate.py")
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.output = self.root / "result.png"
        self.job = Path(str(self.output) + ".imagegen")
        self.job.mkdir()
        self.thread = str(uuid.uuid4())
        self.images = self.root / "generated_images"
        self.source = self.images / self.thread / "original.png"
        self.source.parent.mkdir(parents=True)
        Image.new("RGBA", (7, 5), (30, 60, 90, 0)).save(self.source)
        self.state = dict(output=str(self.output), image_root=str(self.images),
                          model="gpt-6-luna", prompt="a teapot", transparent=True,
                          original_output=None, original_sidecar=None)
        gen.save_json(self.job / "state.json", self.state)
        (self.job / "events.jsonl").write_text(json.dumps(dict(type="thread.started", thread_id=self.thread)) + "\n")
        (self.job / "stderr.log").touch()

    def args(self, **kwargs):
        values = dict(output=self.output, recover=True, replace=False, timeout=300, reference=[],
                      workspace=self.root, prompt_file=None, model="gpt-6-luna", transparent=True)
        return argparse.Namespace(**(values | kwargs))

    def test_recovery_uses_thread_not_agent_path_and_never_generates(self):
        with (self.job / "events.jsonl").open("a") as log:
            log.write(json.dumps(dict(type="item.completed", item=dict(type="agent_message", text="Saved /wrong/path.png"))) + "\n{partial")
        with patch.object(gen.subprocess, "Popen", side_effect=AssertionError("Must not regenerate")):
            result = gen.run(self.args())
        self.assertEqual(result["status"], "ok")
        self.assertEqual((result["width"], result["height"]), (7, 5))
        self.assertEqual(result["transparent_pixels"], 35)
        self.assertEqual(self.output.read_bytes(), self.source.read_bytes())
        self.assertEqual(json.loads(Path(result["metadata_path"]).read_text()), result)

    def test_ambiguous_sources_are_not_selected(self):
        Image.new("RGB", (2, 2)).save(self.source.with_name("other.png"))
        with self.assertRaisesRegex(gen.Failure, "refusing to guess"):
            gen.run(self.args())
        self.assertFalse(self.output.exists())

    def test_other_threads_are_ignored(self):
        other = self.images / str(uuid.uuid4())
        other.mkdir()
        Image.new("RGB", (2, 2)).save(other / "newer.png")
        self.assertEqual(gen.run(self.args())["thread_id"], self.thread)

    def test_claimed_success_without_file_fails(self):
        self.source.unlink()
        with self.assertRaisesRegex(gen.Failure, "No image"):
            gen.run(self.args())

    def test_existing_output_is_preserved_before_generation(self):
        self.output.write_bytes(b"user work")
        prompt = self.root / "brief.txt"
        prompt.write_text("a teapot")
        with patch.object(gen.subprocess, "Popen", side_effect=AssertionError("Must not generate")):
            with self.assertRaisesRegex(gen.Failure, "replacement requires"):
                gen.run(self.args(recover=False, prompt_file=str(prompt)))
        self.assertEqual(self.output.read_bytes(), b"user work")

    def test_late_output_is_preserved(self):
        self.output.write_bytes(b"late arrival")
        with self.assertRaisesRegex(gen.Failure, "Destination changed"):
            gen.run(self.args())
        self.assertEqual(self.output.read_bytes(), b"late arrival")

    def test_interrupted_copy_and_missing_sidecar_recover(self):
        original_publish = gen.publish

        def interrupt_sidecar(path, data, old):
            if path.suffix == ".json":
                raise OSError("interrupted sidecar copy")
            original_publish(path, data, old)

        with patch.object(gen, "publish", side_effect=interrupt_sidecar):
            with self.assertRaises(OSError):
                gen.run(self.args())
        self.source.unlink()  # Published output plus receipt suffice after source cleanup.
        result = gen.run(self.args())
        self.assertEqual(result["status"], "ok")
        self.assertTrue(Path(result["metadata_path"]).exists())

    def test_interruption_before_publication_uses_receipt(self):
        with patch.object(gen, "publish", side_effect=OSError("interrupted image copy")):
            with self.assertRaises(OSError):
                gen.run(self.args())
        self.assertFalse(self.output.exists())
        self.assertEqual(gen.run(self.args())["status"], "ok")

    def test_opaque_result_does_not_claim_transparency(self):
        Image.new("RGB", (7, 5)).save(self.source)
        result = gen.run(self.args())
        self.assertEqual(result["status"], "constraint_failed")
        self.assertFalse(result["has_transparency"])
        self.assertTrue(self.output.exists())

    def test_corrupt_image_is_not_published(self):
        self.source.write_bytes(b"not an image")
        with self.assertRaises(OSError):
            gen.run(self.args())
        self.assertFalse(self.output.exists())

    def test_replacement_requires_unchanged_original(self):
        self.output.write_bytes(b"old work")
        self.state["original_output"] = gen.fingerprint(self.output)
        gen.save_json(self.job / "state.json", self.state)
        self.output.write_bytes(b"new work")
        with self.assertRaisesRegex(gen.Failure, "Destination changed"):
            gen.run(self.args())

    def test_authorized_replacement(self):
        self.output.write_bytes(b"old work")
        self.state["original_output"] = gen.fingerprint(self.output)
        gen.save_json(self.job / "state.json", self.state)
        self.assertEqual(gen.run(self.args())["status"], "ok")
        self.assertEqual(self.output.read_bytes(), self.source.read_bytes())

    def test_nested_runner_is_rejected(self):
        with patch.dict(os.environ, CODEX_IMAGE_GEN_ACTIVE="1"):
            with self.assertRaisesRegex(gen.Failure, "Nested"):
                gen.run(self.args())

    def test_live_process_blocks_recovery(self):
        self.state["pid"] = os.getpid()
        gen.save_json(self.job / "state.json", self.state)
        with self.assertRaisesRegex(gen.Failure, "still alive"):
            gen.run(self.args())

    def test_source_symlink_escape_is_rejected(self):
        outside = self.root / "outside.png"
        self.source.rename(outside)
        self.source.symlink_to(outside)
        with self.assertRaisesRegex(gen.Failure, "escapes"):
            gen.run(self.args())

    def test_job_lock_blocks_concurrent_recovery(self):
        with (self.job / "lock").open("a") as lock:
            gen.fcntl.flock(lock, gen.fcntl.LOCK_EX)
            with self.assertRaisesRegex(gen.Failure, "locked"):
                gen.run(self.args())

    def test_generation_runs_once_with_configured_permissions(self):
        self.state["workspace"] = str(self.root)
        with patch.object(gen.subprocess, "Popen") as popen:
            process = popen.return_value
            process.pid = 98765
            process.returncode = 0

            def complete(*args, **kwargs):
                (self.job / "events.jsonl").write_text(json.dumps(dict(type="thread.started", thread_id=self.thread)) + "\n")

            process.communicate.side_effect = complete
            result = gen.generate(self.job, self.state, 300)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(popen.call_count, 1)
        command = popen.call_args.args[0]
        self.assertNotIn("--dangerously-bypass-approvals-and-sandbox", command)
        self.assertNotIn("--ignore-user-config", command)
        self.assertEqual(command[command.index("-m") + 1], "gpt-6-luna")

    def test_timeout_recovers_image_without_retry(self):
        self.state["workspace"] = str(self.root)
        with patch.object(gen.subprocess, "Popen") as popen, patch.object(gen.os, "killpg"):
            process = popen.return_value
            process.pid = 98765

            def timeout(*args, **kwargs):
                (self.job / "events.jsonl").write_text(json.dumps(dict(type="thread.started", thread_id=self.thread)) + "\n")
                raise subprocess.TimeoutExpired("codex", 1)

            process.communicate.side_effect = timeout
            result = gen.generate(self.job, self.state, 1)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["execution"], "interrupted_or_timed_out")
        self.assertEqual(popen.call_count, 1)

    def test_auth_failure_is_identified_without_retry(self):
        self.state["workspace"] = str(self.root)
        with patch.object(gen.subprocess, "Popen") as popen:
            process = popen.return_value
            process.pid = 98765
            process.returncode = 1

            def fail(*args, **kwargs):
                (self.job / "stderr.log").write_text("Authentication failed: not logged in")

            process.communicate.side_effect = fail
            with self.assertRaises(gen.Failure) as caught:
                gen.generate(self.job, self.state, 300)
        self.assertEqual(caught.exception.code, "authentication_failed")
        self.assertEqual(popen.call_count, 1)


class ReferenceTests(unittest.TestCase):
    args = RecoveryTests.args

    def setUp(self):
        RecoveryTests.setUp(self)
        self.prompt = self.root / "brief.txt"
        self.prompt.write_text("make the sky green")
        self.first = self.root / "source.png"
        self.second = self.root / "style.jpg"
        Image.new("RGBA", (4, 4), (255, 0, 0, 0)).save(self.first)
        Image.new("RGB", (3, 2), (0, 0, 255)).save(self.second)
        self.hashes = [gen.digest(self.first.read_bytes()), gen.digest(self.second.read_bytes())]

    def run_new(self, references, **kwargs):
        output = self.root / "edit.png"
        job = Path(str(output) + ".imagegen")
        rows = [dict(type="thread.started", thread_id=self.thread)]
        with patch.dict(os.environ, {"CODEX_HOME": str(self.root)}), \
                patch.object(gen.subprocess, "Popen") as popen:
            popen.return_value.pid, popen.return_value.returncode = 98765, 0
            popen.return_value.communicate.side_effect = lambda *a, **k: (job / "events.jsonl").write_text(
                "".join(json.dumps(row) + "\n" for row in rows))
            result = gen.run(self.args(output=output, recover=False, prompt_file=str(self.prompt),
                                       reference=references, **kwargs))
        return result, job, popen

    def test_ordered_snapshots_are_passed_to_codex(self):
        result, job, popen = self.run_new([self.first, self.second])
        self.assertEqual(result["status"], "ok")
        snapshots = [Path(r["snapshot"]) for r in result["references"]]
        self.assertEqual([p.name for p in snapshots], ["reference-1.png", "reference-2.jpg"])
        self.assertEqual([r["sha256"] for r in result["references"]], self.hashes)
        self.assertEqual(job.stat().st_mode & 0o777, 0o700)
        self.assertTrue(all(p.stat().st_mode & 0o777 == 0o600 for p in snapshots))
        instruction = popen.return_value.communicate.call_args.args[0].decode()
        self.assertIn(json.dumps([str(p) for p in snapshots]), instruction)
        Image.new("RGB", (9, 9)).save(self.first)
        self.assertEqual(gen.digest(snapshots[0].read_bytes()), self.hashes[0])

    def test_generation_without_references_omits_reference_arguments(self):
        result, _, popen = self.run_new([])
        instruction = popen.return_value.communicate.call_args.args[0].decode()
        self.assertNotIn("referenced_image_paths", instruction)
        self.assertEqual(result["references"], [])

    def test_invalid_references_fail_before_job_creation(self):
        text = self.root / "notes.png"
        text.write_text("not an image")
        bitmap = self.root / "legacy.bmp"
        Image.new("RGB", (2, 2)).save(bitmap)
        output = self.root / "edit.png"
        output.write_bytes(self.first.read_bytes())
        alias = self.root / "alias.png"
        os.link(output, alias)
        cases = [[self.root / "missing.png"], [text], [bitmap], [self.first] * 6,
                 [output], [Path(str(output) + ".json")], [alias]]
        if (self.root / "EDIT.png").exists():  # Case-insensitive volume.
            cases.append([self.root / "EDIT.png"])
        for references in cases:
            with self.subTest(references=references), \
                    patch.object(gen.subprocess, "Popen", side_effect=AssertionError("Must not generate")):
                with self.assertRaises(gen.Failure):
                    gen.run(self.args(output=output, recover=False, replace=True,
                                      prompt_file=str(self.prompt), reference=references))
                self.assertFalse(Path(str(output) + ".imagegen").exists())

    def test_recovery_rejects_new_references(self):
        with self.assertRaisesRegex(gen.Failure, "recorded references"):
            gen.run(self.args(reference=[self.first]))

    def test_snapshots_are_never_recovery_candidates(self):
        Image.new("RGB", (2, 2)).save(self.job / "reference-1.png")
        self.source.unlink()
        with self.assertRaises(gen.Failure) as caught:
            gen.run(self.args())
        self.assertEqual(caught.exception.code, "image_unavailable")

    def test_generation_only_job_from_previous_release_recovers(self):
        result = gen.run(self.args())
        self.assertEqual((result["status"], result["references"]), ("ok", []))


if __name__ == "__main__":
    unittest.main()
