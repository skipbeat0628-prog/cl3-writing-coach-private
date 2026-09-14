import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from server import ROOT, run_codex


class CodexEnvironmentTests(unittest.TestCase):
    def test_cli_receives_explicit_codex_home(self):
        def fake_run(command, **kwargs):
            self.assertEqual(kwargs["env"]["CODEX_HOME"], str(Path("C:/Users/teacher") / ".codex"))
            Path(command[command.index("--output-last-message") + 1]).write_text(
                json.dumps({"ok": True}), encoding="utf-8"
            )
            return subprocess.CompletedProcess(command, 0, "", "")

        with patch("server.shutil.which", return_value="codex.exe"), \
             patch("server.os.environ.copy", return_value={"USERPROFILE": "C:/Users/teacher"}), \
             patch("server.subprocess.run", side_effect=fake_run):
            result = run_codex({}, lambda _: "test", ROOT / "ai_schema.json")
        self.assertEqual(result, {"ok": True})


if __name__ == "__main__":
    unittest.main()
