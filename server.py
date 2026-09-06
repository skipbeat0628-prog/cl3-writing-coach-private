"""Local-only server for the CL3 writing coach.

Serves the static site and uses the signed-in Codex CLI for essay analysis.
No API key is stored in the project.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import threading
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from prompts import build_discovery_prompt, build_enrichment_prompt


ROOT = Path(__file__).resolve().parent
DISCOVERY_SCHEMA = ROOT / "ai_schema.json"
ENRICHMENT_SCHEMA = ROOT / "comment_schema.json"
HOST = "127.0.0.1"
PORT = 8765
MAX_BODY_BYTES = 100_000
CODEX_TIMEOUT_SECONDS = 240
CODEX_LOCK = threading.Lock()


def run_codex(data: dict, prompt_builder, schema: Path) -> dict:
    codex = shutil.which("codex")
    if not codex:
        raise RuntimeError("找不到 Codex CLI，請先安裝或從 Codex App 啟動")

    prompt = prompt_builder(data)
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as output_file:
        output_path = Path(output_file.name)

    command = [
        codex,
        "exec",
        "--ephemeral",
        "--ignore-rules",
        "--skip-git-repo-check",
        "--sandbox",
        "read-only",
        "--output-schema",
        str(schema),
        "--output-last-message",
        str(output_path),
        "-",
    ]
    environment = os.environ.copy()
    environment["NO_COLOR"] = "1"
    creation_flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0

    try:
        with CODEX_LOCK:
            completed = subprocess.run(
                command,
                input=prompt,
                text=True,
                encoding="utf-8",
                errors="replace",
                cwd=ROOT,
                env=environment,
                capture_output=True,
                timeout=CODEX_TIMEOUT_SECONDS,
                creationflags=creation_flags,
                check=False,
            )
        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout or "Codex 執行失敗").strip()
            raise RuntimeError(detail[-1200:])
        raw = output_path.read_text(encoding="utf-8").strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        return json.loads(raw)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("AI 分析超過四分鐘，請再試一次") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError("AI 回傳格式無法解析，請再試一次") from exc
    finally:
        output_path.unlink(missing_ok=True)


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_GET(self) -> None:
        if self.path == "/api/health":
            self.send_json({"ok": True, "codexAvailable": bool(shutil.which("codex"))})
            return
        if self.path == "/":
            self.path = "/index.html"
        super().do_GET()

    def do_POST(self) -> None:
        routes = {
            "/api/analyze": (build_discovery_prompt, DISCOVERY_SCHEMA, "analysis"),
            "/api/enrich": (build_enrichment_prompt, ENRICHMENT_SCHEMA, "enrichment"),
        }
        if self.path not in routes:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > MAX_BODY_BYTES:
                raise ValueError("請求內容大小不正確")
            data = json.loads(self.rfile.read(length).decode("utf-8"))
            prompt_builder, schema, response_key = routes[self.path]
            result = run_codex(data, prompt_builder, schema)
            self.send_json({"ok": True, response_key: result})
        except (ValueError, json.JSONDecodeError) as error:
            self.send_json({"ok": False, "error": str(error)}, HTTPStatus.BAD_REQUEST)
        except Exception as error:
            self.send_json({"ok": False, "error": str(error)}, HTTPStatus.INTERNAL_SERVER_ERROR)

    def send_json(self, data: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args) -> None:
        print(f"[{self.log_date_time_string()}] {format % args}")


if __name__ == "__main__":
    print(f"CL3 作文批改教練：http://{HOST}:{PORT}")
    print("請保持這個視窗開啟；按 Ctrl+C 停止伺服器。")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
