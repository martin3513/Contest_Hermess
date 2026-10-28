import importlib.util
import json
import os
from pathlib import Path
import tempfile
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor
import unittest
import io
from contextlib import redirect_stdout
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("launcher", Path(__file__).resolve().parents[1] / "start.py")
app = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(app)


class LauncherTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.root_patch = patch.object(app, "ROOT", self.root)
        self.root_patch.start()

    def tearDown(self):
        self.root_patch.stop()
        self.temp.cleanup()

    def prepared(self):
        path = app.initialize("한글 대회", "idea_proposal")
        (path / "input/공고.md").write_text("원본", encoding="utf-8")
        return path

    def test_init_preserves_state_and_original(self):
        path = self.prepared()
        state = path / "_workspace/state.json"
        value = json.loads(state.read_text(encoding="utf-8"))
        value["stage"] = "approval_1"
        app.write_json(state, value)
        before = state.read_bytes()
        app.initialize("한글 대회", "idea_proposal")
        self.assertEqual(before, state.read_bytes())
        self.assertEqual("원본", (path / "input/공고.md").read_text(encoding="utf-8"))

    def test_rejects_invalid_paths(self):
        for name in ("../outside", "a/b", "a\\b", "CON", "NUL.txt", "a.", "a ", "", "a:b"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                app.initialize(name, "idea_proposal")
        self.assertFalse((self.root / "outside").exists())

    def test_profile_change_rejected(self):
        self.prepared()
        with self.assertRaises(ValueError):
            app.initialize("한글 대회", "data_analysis")

    def test_empty_input_does_not_launch(self):
        with patch.object(app, "call_orca") as call, self.assertRaises(ValueError):
            app.launch("빈 대회", "idea_proposal", "codex", "orchestrated")
        call.assert_not_called()

    def test_preview_does_not_launch_or_lock(self):
        with patch.object(app, "call_orca") as call, patch("builtins.print"):
            app.launch("미리보기", "idea_proposal", "claude", "orchestrated", True)
        call.assert_not_called()
        self.assertFalse((app.contest_path("미리보기") / "_workspace/launch-pending.json").exists())

    def test_naming_preview_selects_model_without_ai(self):
        for agent, expected in (("claude", "sonnet"), ("codex", "gpt-6.1-sol")):
            output = io.StringIO()
            with patch.object(app, "call_orca") as call, redirect_stdout(output):
                app.launch("네이밍", "idea_proposal", agent, "orchestrated", True, "naming")
            call.assert_not_called()
            argv = json.loads(output.getvalue())["argv"]
            self.assertEqual(argv[argv.index("--model") + 1], expected)
            self.assertIn("작업 종류는 naming", argv[argv.index("--prompt") + 1])

    def test_status_is_read_only_and_tolerates_bad_json(self):
        path = self.prepared()
        state = path / "_workspace/state.json"
        for content in (state.read_text(encoding="utf-8"), "{invalid"):
            state.write_text(content, encoding="utf-8")
            with patch.object(app, "call_orca") as call, patch("builtins.print"):
                app.show_status("한글 대회")
            call.assert_not_called()
            self.assertEqual(state.read_text(encoding="utf-8"), content)

    def test_watch_refreshes_without_launching(self):
        with patch.object(app, "show_status") as show, patch.object(app.time, "sleep", side_effect=KeyboardInterrupt), patch("builtins.print"):
            with self.assertRaises(KeyboardInterrupt):
                app.watch_status("대회", 5)
            show.assert_called_once_with("대회")
        with self.assertRaises(ValueError):
            app.watch_status(interval=0)

    def test_provider_arguments_receipt_and_duplicate_guard(self):
        for agent in ("claude", "codex"):
            with self.subTest(agent=agent):
                path = self.prepared()
                response = {"ok": True, "result": {"app": {"running": True}}}
                with patch.object(app, "call_orca", return_value=response) as call, patch("builtins.print"):
                    app.launch("한글 대회", "idea_proposal", agent, "orchestrated")
                    argv = call.call_args.args[0]
                    self.assertEqual(argv[:4], ["agent", "launch", "--agent", agent])
                    self.assertIn(f"path:{self.root}", argv)
                    self.assertIn("한글 대회", argv[argv.index("--prompt") + 1])
                    count = call.call_count
                    with self.assertRaises(ValueError):
                        app.launch("한글 대회", "idea_proposal", agent, "orchestrated")
                    self.assertEqual(call.call_count, count)
                    self.assertTrue(list((path / "_workspace/launches").glob("*.json")))
                    app.reset_launch("한글 대회")

    def test_unknown_launch_stays_locked(self):
        path = self.prepared()
        def call(argv):
            if argv[:2] == ["agent", "launch"]:
                raise RuntimeError("connection lost")
            return {"ok": True, "result": {"app": {"running": True}}}
        with patch.object(app, "call_orca", side_effect=call), self.assertRaises(RuntimeError):
            app.launch("한글 대회", "idea_proposal", "codex", "orchestrated")
        self.assertTrue((path / "_workspace/launch-pending.json").exists())
        receipts = list((path / "_workspace/launches").glob("*.json"))
        self.assertEqual(json.loads(receipts[0].read_text(encoding="utf-8"))["status"], "unknown")

    def test_reset_preserves_work(self):
        path = self.prepared()
        pending = path / "_workspace/launch-pending.json"
        pending.write_text('{"status":"receipt-saved"}', encoding="utf-8")
        state = (path / "_workspace/state.json").read_bytes()
        with patch("builtins.print"):
            app.reset_launch("한글 대회")
        self.assertFalse(pending.exists())
        self.assertEqual(state, (path / "_workspace/state.json").read_bytes())
        self.assertTrue(list((path / "_workspace/launches").glob("reset-*.json")))

    def test_simultaneous_launch_only_starts_one_agent(self):
        self.prepared()
        barrier = threading.Barrier(2)
        launches = []
        def call(argv):
            if argv[:3] == ["skills", "get", "orchestration"]:
                barrier.wait(timeout=5)
            if argv[:2] == ["agent", "launch"]:
                launches.append(argv)
            return {"ok": True, "result": {"app": {"running": True}}}
        def start():
            try:
                app.launch("한글 대회", "idea_proposal", "codex", "orchestrated")
                return "started"
            except ValueError:
                return "blocked"
        with patch.object(app, "call_orca", side_effect=call), patch("builtins.print"), ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(start) for _ in range(2)]
            outcomes = sorted(f.result(timeout=10) for f in futures)
        self.assertEqual(outcomes, ["blocked", "started"])
        self.assertEqual(len(launches), 1)

    def test_nested_link_is_rejected(self):
        path = self.prepared()
        launches = path / "_workspace/launches"
        launches.rmdir()
        outside = self.root / "outside"
        outside.mkdir()
        try:
            launches.symlink_to(outside, target_is_directory=True)
        except OSError:
            if os.name != "nt":
                self.skipTest("OS does not permit symlink creation")
            quote = lambda p: "'" + str(p).replace("'", "''") + "'"
            subprocess.run(["powershell", "-NoProfile", "-Command",
                            f"$ErrorActionPreference='Stop'; New-Item -ItemType Junction -Path {quote(launches)} -Target {quote(outside)} | Out-Null"], check=True)
        with self.assertRaises(ValueError):
            app.initialize("한글 대회", "idea_proposal")
        self.assertEqual(list(outside.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
