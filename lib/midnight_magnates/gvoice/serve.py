#!/usr/bin/env python3
"""G-voice review server (stdlib only).

Serves the review UI + the project's voice_report.json + the VO audio (with HTTP
Range so the browser can seek), and accepts POST /submit which writes
artifacts/approvals/voice.json — the artifact runner.run_stage() requires to pass
the voice stage.

    python -m lib.midnight_magnates.gvoice.serve --project <dir> [--port 3011]
"""

from __future__ import annotations

import argparse
import json
import mimetypes
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Optional

GVOICE_DIR = Path(__file__).resolve().parent

_AUDIO_CANDIDATES = ["vo_full.wav", "vo_full.mp3", "voice/vo_full.wav", "voice/vo_full.mp3", "vo.wav", "vo.mp3"]


def find_vo_audio(artifacts: Path) -> Optional[Path]:
    for name in _AUDIO_CANDIDATES:
        p = artifacts / name
        if p.is_file():
            return p
    for d in (artifacts, artifacts / "voice"):
        if d.is_dir():
            for ext in ("*.wav", "*.mp3", "*.m4a", "*.aiff", "*.flac"):
                hits = sorted(d.glob(ext))
                if hits:
                    return hits[0]
    return None


class Handler(BaseHTTPRequestHandler):
    project = "."  # set on the class before serving

    def log_message(self, *a):  # quiet
        return

    def _send(self, code, ctype, body, extra=None):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if body:
            self.wfile.write(body)

    def do_GET(self):
        art = Path(self.project) / "artifacts"
        path = self.path.split("?")[0]
        if path in ("/", "/index.html", "/review.html"):
            self._send(200, "text/html; charset=utf-8", (GVOICE_DIR / "review.html").read_bytes())
            return
        if path == "/voice_report.json":
            f = art / "voice_report.json"
            if f.is_file():
                self._send(200, "application/json", f.read_bytes())
            else:
                self._send(404, "application/json", b'{"error":"no voice_report.json yet"}')
            return
        if path == "/audio":
            a = find_vo_audio(art)
            if not a:
                self._send(404, "text/plain", b"no VO audio found in artifacts/")
                return
            data = a.read_bytes()
            ctype = mimetypes.guess_type(str(a))[0] or "audio/wav"
            rng = self.headers.get("Range")
            if rng and rng.startswith("bytes="):
                s, _, e = rng[6:].partition("-")
                start = int(s) if s else 0
                end = int(e) if e else len(data) - 1
                end = min(end, len(data) - 1)
                chunk = data[start:end + 1]
                self._send(206, ctype, chunk, {
                    "Content-Range": "bytes {0}-{1}/{2}".format(start, end, len(data)),
                    "Accept-Ranges": "bytes",
                })
                return
            self._send(200, ctype, data, {"Accept-Ranges": "bytes"})
            return
        self._send(404, "text/plain", b"not found")

    def do_POST(self):
        if self.path.split("?")[0] != "/submit":
            self._send(404, "text/plain", b"not found")
            return
        n = int(self.headers.get("Content-Length", "0") or "0")
        try:
            payload = json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            self._send(400, "application/json", b'{"error":"bad json"}')
            return
        appr = Path(self.project) / "artifacts" / "approvals"
        appr.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().isoformat()
        record = {
            "stage": "voice",
            "approved": bool(payload.get("approved")),
            "reviewer": payload.get("reviewer", "human"),
            "ts": ts,
            "segments": payload.get("segments", []),  # [{id, action: keep|regenerate|approve, note, fix_hint}]
        }
        (appr / "voice.json").write_text(json.dumps(record, indent=2))
        subs = appr / "submissions"
        subs.mkdir(exist_ok=True)
        (subs / (ts.replace(":", "-") + "_voice.json")).write_text(json.dumps(record, indent=2))
        self._send(200, "application/json", json.dumps(
            {"ok": True, "approved": record["approved"], "written": str(appr / "voice.json")}).encode())


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="gvoice.serve")
    ap.add_argument("--project", required=True)
    ap.add_argument("--port", type=int, default=3011)
    args = ap.parse_args(argv)
    Handler.project = str(Path(args.project).resolve())
    srv = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print("G-voice review: http://127.0.0.1:{0}   project: {1}".format(args.port, Handler.project))
    print("Approve segments or flag them 'regenerate'; Submit writes artifacts/approvals/voice.json.")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
