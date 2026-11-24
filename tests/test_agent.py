import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

CLI = Path(__file__).resolve().parents[1] / "tools/agent.py"


class ToolkitTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.project = self.root / "project"
        self.project.mkdir()
        self.git("init", "-q")
        self.git("config", "user.email", "test@example.invalid")
        self.git("config", "user.name", "Toolkit Test")
        (self.project / "README.md").write_text("test\n")
        self.git("add", ".")
        self.git("commit", "-qm", "baseline")
        self.context = self.root / "context.json"
        self.context.write_text('{"dataset":"fixture","seed":42,"budget":"test"}')
        self.script = self.root / "benchmark.py"
        self.script.write_text(
            'import json, os, sys\nfrom pathlib import Path\n'
            'p = Path(os.environ["AGENT_RUN_DIR"])\n'
            '(p / "metrics.json").write_text(json.dumps({"score":float(sys.argv[1])}))\n'
            'print("done")\n')

    def git(self, *args):
        subprocess.run(["git", "-C", str(self.project), *args], check=True, capture_output=True)

    def cli(self, *args, ok=0, script=CLI):
        p = subprocess.run([sys.executable, str(script), *map(str, args)], cwd=self.project,
                           text=True, capture_output=True, timeout=25)
        self.assertEqual(p.returncode, ok, p.stdout + p.stderr)
        return p

    def run_fixture(self, name, score="1", extra=(), ok=0):
        out = self.root / name
        self.cli("run", "--out", out, "--context", self.context, "--timeout", "5",
                 *extra, "--", sys.executable, self.script, score, ok=ok)
        return out

    def test_install_idempotent_preserves_custom_rules(self):
        original = b"# Project\nLocal custom policy.\n"
        path = self.project / "AGENTS.md"
        path.write_bytes(original)
        args = ("install", "--target", self.project, "--profile", "research")
        self.cli(*args, "--check", ok=1)
        self.assertEqual(path.read_bytes(), original)
        self.cli(*args)
        self.assertTrue(path.read_bytes().startswith(original))
        self.assertIn(b"Research profile active", path.read_bytes())
        self.assertTrue((self.project / ".agents/skills/experiment/SKILL.md").exists())
        self.assertEqual(json.loads(self.cli(*args, "--check").stdout)["changed"], [])
        self.cli("doctor", script=self.project / ".agent-rules/agent.py")
        self.cli("task", "new", "probe", "--objective", "test",
                 script=self.project / ".agent-rules/agent.py")
        self.assertIn("Objective: test", (self.project / ".agent-work/tasks/probe/TASK.md").read_text())
        self.cli("task", "new", "../escape", "--objective", "test", ok=2)

    def test_install_conflict_is_non_destructive(self):
        skill = self.project / ".agents/skills/experiment/SKILL.md"
        skill.parent.mkdir(parents=True)
        skill.write_text("custom\n")
        self.cli("install", "--target", self.project, ok=2)
        self.assertEqual(skill.read_text(), "custom\n")
        self.assertFalse((self.project / "AGENTS.md").exists())

    def test_install_modified_managed_file_refused(self):
        args = ("install", "--target", self.project)
        self.cli(*args)
        file = self.project / ".agent-rules/research.md"
        file.write_text("local edit\n")
        self.cli(*args, ok=2)
        self.assertEqual(file.read_text(), "local edit\n")

    @unittest.skipUnless(os.name == "posix", "symlink permissions platform dependent")
    def test_install_symlink_refused(self):
        external = self.root / "external"
        external.mkdir()
        (self.project / ".agents").symlink_to(external, target_is_directory=True)
        self.cli("install", "--target", self.project, ok=2)
        self.assertEqual(list(external.iterdir()), [])

    def test_run_compare_and_gates(self):
        a = self.run_fixture("a", "1")
        b = self.run_fixture("b", "2")
        self.cli("verify", b, "--require-metrics")
        self.assertIn("done", self.cli("logs", b).stdout)
        gates = self.root / "gates.json"
        gates.write_text('{"score":{"min":2,"min_delta":1}}')
        result = json.loads(self.cli("compare", a, b, "--gates", gates).stdout)
        self.assertEqual(result["metrics"]["score"]["delta"], 1)
        self.assertEqual(result["status"], "pass")
        gates.write_text('{"score":{"min":3}}')
        self.cli("compare", a, b, "--gates", gates, ok=1)
        (b / "metrics.json").write_text('{"score":999}')
        self.cli("verify", b, "--require-metrics", ok=2)

    def test_mismatched_context(self):
        a = self.run_fixture("a")
        self.context.write_text('{"dataset":"other"}')
        b = self.run_fixture("b")
        self.cli("compare", a, b, ok=2)

    def test_dirty_and_collision(self):
        (self.project / "dirty").write_text("x")
        self.run_fixture("dirty", ok=2)
        a = self.run_fixture("a", extra=("--allow-dirty",))
        b = self.run_fixture("b", extra=("--allow-dirty",))
        self.cli("compare", a, b, ok=2)
        self.run_fixture("a", extra=("--allow-dirty",), ok=2)
        self.cli("run", "--out", self.project / "unignored", "--context", self.context,
                 "--timeout", "1", "--allow-dirty", "--", sys.executable, "-c", "pass", ok=2)

    def test_failure_and_timeout(self):
        for name, command, expected in (("failure", "raise SystemExit(7)", "failed"),
                                        ("timeout", "import time; time.sleep(10)", "timeout")):
            out = self.root / name
            self.cli("run", "--out", out, "--context", self.context, "--timeout", "0.5",
                     "--", sys.executable, "-c", command, ok=1)
            receipt = json.loads((out / "receipt.json").read_text())
            self.assertEqual(receipt["status"], expected)
            self.cli("verify", out, ok=2)

    def test_detached(self):
        out = self.run_fixture("detached", extra=("--detach",))
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            receipt = json.loads((out / "receipt.json").read_text())
            if receipt["status"] not in {"pending", "running"}:
                break
            time.sleep(0.05)
        self.cli("verify", out, "--require-metrics")

    def test_learn_append(self):
        path = self.root / "inbox.jsonl"
        for i in range(2):
            self.cli("learn", "--inbox", path, "--scope", "gpu", "--finding", f"finding {i}",
                     "--evidence", "commit/run")
        entries = [json.loads(line) for line in path.read_text().splitlines()]
        self.assertEqual([e["finding"] for e in entries], ["finding 0", "finding 1"])

    def test_nonfinite_and_boolean_metrics(self):
        for name, payload in (("nan", '{"score":NaN}'), ("bool", '{"score":true}')):
            out = self.root / name
            self.cli("run", "--out", out, "--context", self.context, "--timeout", "2", "--",
                     sys.executable, "-c",
                     "import os;from pathlib import Path;Path(os.environ['AGENT_RUN_DIR'],'metrics.json').write_text(" + repr(payload) + ")")
            self.cli("verify", out, "--require-metrics", ok=2)


if __name__ == "__main__":
    unittest.main()
