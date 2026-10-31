"""Testes do limit_guard (stdlib). Rodar: python3 -m unittest -v test_limit_guard.py"""
import io, json, os, pathlib, subprocess, sys, tempfile, time, unittest

SCRIPT = str(pathlib.Path(__file__).with_name("limit_guard.py"))


def run(args, env=None, stdin=None):
    e = dict(os.environ, **(env or {}))
    return subprocess.run([sys.executable, SCRIPT, *args], input=stdin, capture_output=True, text=True, env=e)


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        self.env = {"LIMIT_GUARD_STATE": str(self.tmp / "state"), "LIMIT_GUARD_PROJECTS": str(self.tmp / "proj"),
                    "LIMIT_GUARD_LAUNCHAGENTS": str(self.tmp / "agents"), "LIMIT_GUARD_NO_LAUNCHCTL": "1"}
        (self.tmp / "proj" / "p").mkdir(parents=True)
        self.sid = "abcd1234-0000-0000-0000-000000000000"
        self.t = self.tmp / "proj" / "p" / f"{self.sid}.jsonl"

    def write(self, rows):
        self.t.write_text("\n".join(json.dumps(r) for r in rows) + "\n")


class StatusTests(Base):
    def test_given_compactions_and_rejection_when_status_then_reports_both(self):
        reset = int(time.time()) + 3600
        self.write([
            {"type": "user", "sessionId": self.sid, "cwd": "/x/y"},
            {"type": "assistant", "message": {"model": "m", "usage": {"input_tokens": 10, "cache_read_input_tokens": 90}}},
            {"type": "system", "subtype": "compact_boundary", "timestamp": "t",
             "compactMetadata": {"trigger": "auto", "preTokens": 500, "postTokens": 50}},
            {"type": "user", "isCompactSummary": True, "message": {"content": "x"}},
            {"type": "assistant", "message": {"model": "<synthetic>", "usage": {"input_tokens": 0}},
             "quotaLimits": {"status": "rejected", "resetsAt": reset, "rateLimitType": "five_hour"}}])
        r = json.loads(run(["status", "--session", self.sid], self.env).stdout)
        self.assertEqual(r["compactions"], 1)
        self.assertEqual(r["summary_messages"], 1)
        self.assertEqual(r["context_tokens"], 100)  # a mensagem sintética não conta
        self.assertEqual(r["rejection"]["resets_at"], reset)
        self.assertEqual(r["cwd"], "/x/y")

    def test_given_no_rejection_when_status_then_null(self):
        self.write([{"type": "user", "sessionId": self.sid}])
        self.assertIsNone(json.loads(run(["status", "--session", self.sid], self.env).stdout)["rejection"])


class LevelTests(Base):
    def feed(self, pct):
        rl = {"five_hour": {"used_percentage": pct, "resets_at": int(time.time()) + 600}}
        run(["statusline"], self.env, json.dumps({"session_id": self.sid, "rate_limits": rl, "context_window": {"used_percentage": 40}}))

    def test_given_usage_when_check_then_exit_code_by_level(self):
        for pct, code in ((50, 0), (90, 10), (97, 20)):
            self.feed(pct)
            self.assertEqual(run(["check", "--session", self.sid], self.env).returncode, code)

    def test_given_expired_window_when_check_then_ignored(self):
        rl = {"five_hour": {"used_percentage": 99, "resets_at": int(time.time()) - 5}}
        run(["statusline"], self.env, json.dumps({"session_id": self.sid, "rate_limits": rl}))
        self.assertEqual(run(["check", "--session", self.sid], self.env).returncode, 0)


class ArmTests(Base):
    def test_given_plan_without_apply_then_nothing_written(self):
        self.write([{"type": "user", "sessionId": self.sid, "cwd": "/x/y"}])
        r = run(["arm-resume", "--session", self.sid, "--at", str(int(time.time()) + 100)], self.env)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse((self.tmp / "agents").exists())

    def test_given_apply_then_plist_has_resume_command(self):
        self.write([{"type": "user", "sessionId": self.sid, "cwd": "/x/y"}])
        run(["arm-resume", "--session", self.sid, "--at", str(int(time.time()) + 100), "--apply"], self.env)
        import plistlib
        pl = plistlib.loads((self.tmp / "agents" / f"com.ai-dev-kit.limit-guard.{self.sid[:8]}.plist").read_bytes())
        self.assertIn("run-resume", pl["ProgramArguments"])
        self.assertIn(self.sid, pl["ProgramArguments"])
        self.assertNotIn("--dangerously-skip-permissions", " ".join(pl["ProgramArguments"]))


class WatchTests(Base):
    def test_given_new_rejection_when_watch_then_arms_resume(self):
        self.write([{"type": "user", "sessionId": self.sid, "cwd": "/x/y"}])
        import threading
        def later():
            time.sleep(1.5)
            with open(self.t, "a") as fh:
                fh.write(json.dumps({"type": "assistant", "timestamp": "new", "message": {"model": "<synthetic>"},
                                     "quotaLimits": {"status": "rejected", "resetsAt": int(time.time()) + 600}}) + "\n")
        threading.Thread(target=later).start()
        r = run(["watch", "--session", self.sid, "--hours", "0.01", "--interval", "1"], self.env)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(list((self.tmp / "agents").glob("*.plist")))


class HookTests(Base):
    def test_given_stopfailure_rate_limit_when_hook_then_arms_resume_at_reset(self):
        reset = int(time.time()) + 900
        self.write([{"type": "user", "sessionId": self.sid, "cwd": "/x/y"},
                    {"type": "assistant", "message": {"model": "<synthetic>"},
                     "quotaLimits": {"status": "rejected", "resetsAt": reset, "rateLimitType": "five_hour"}}])
        ev = {"hook_event_name": "StopFailure", "session_id": self.sid, "error": "rate_limit", "cwd": "/x/y",
              "transcript_path": str(self.t)}
        r = run(["hook"], self.env, json.dumps(ev))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(list((self.tmp / "agents").glob("*.plist")))

    def test_given_stopfailure_other_error_when_hook_then_does_nothing(self):
        r = run(["hook"], self.env, json.dumps({"hook_event_name": "StopFailure", "session_id": self.sid, "error": "overloaded"}))
        self.assertEqual(r.returncode, 0)
        self.assertFalse((self.tmp / "agents").exists())

    def test_given_session_start_compact_when_hook_then_context_reminder(self):
        self.write([{"type": "user", "sessionId": self.sid}])
        r = run(["hook"], self.env, json.dumps({"hook_event_name": "SessionStart", "session_id": self.sid, "source": "compact",
                                                  "transcript_path": str(self.t)}))
        out = json.loads(r.stdout)["hookSpecificOutput"]
        self.assertEqual(out["hookEventName"], "SessionStart")
        self.assertIn("hallucination-guard", out["additionalContext"])

    def test_given_high_usage_when_posttooluse_then_warns_once(self):
        rl = {"five_hour": {"used_percentage": 96, "resets_at": int(time.time()) + 600}}
        run(["statusline"], self.env, json.dumps({"session_id": self.sid, "rate_limits": rl}))
        ev = json.dumps({"hook_event_name": "PostToolUse", "session_id": self.sid})
        first, second = run(["hook"], self.env, ev).stdout, run(["hook"], self.env, ev).stdout
        self.assertIn("PARE", json.loads(first)["hookSpecificOutput"]["additionalContext"])
        self.assertEqual(second.strip(), "")


if __name__ == "__main__":
    unittest.main()
