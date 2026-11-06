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
        values = dict(output=self.output, recover=True, replace=False, timeout=300,
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


if __name__ == "__main__":
    unittest.main()
