"""Tiny HTTP server for the local review tool.

Serves review.html + the master MP4 from this directory, and accepts POST
/submit with the comment bundle. Writes each submission to submissions/ as a
timestamped JSON, plus decodes the embedded frame snapshots to individual JPGs
(submissions/<ts>_frames/) so Claude can read them as images.

Usage:
    python serve_review.py
    # opens on http://localhost:3010

Stop with Ctrl+C.
"""
from __future__ import annotations

import base64
import http.server
import json
import os
import socketserver
import sys
from datetime import datetime
from pathlib import Path

PORT = int(os.environ.get("REVIEW_PORT", "3010"))
ROOT = Path(__file__).resolve().parent
SUB_DIR = ROOT / "submissions"
SUB_DIR.mkdir(exist_ok=True)


class ReviewHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, fmt, *args):
        # Quieter logging — only show POSTs and errors
        if "POST" in fmt or "error" in fmt.lower() or args and "POST" in (args[0] if args else ""):
            sys.stderr.write(f"[review] {self.address_string()} - {fmt % args}\n")

    def do_GET(self):
        # Default index → review.html
        if self.path in ("/", ""):
            self.path = "/review.html"
        # Serve the master MP4 from ../renders/
        if self.path == "/master_draft.mp4":
            mp4 = ROOT.parent / "renders" / "master_draft.mp4"
            if mp4.exists():
                self.send_response(200)
                self.send_header("Content-Type", "video/mp4")
                self.send_header("Content-Length", str(mp4.stat().st_size))
                self.send_header("Accept-Ranges", "bytes")
                self.end_headers()
                with open(mp4, "rb") as f:
                    self.wfile.write(f.read())
                return
            else:
                self.send_error(404, "master_draft.mp4 not found yet — render still running?")
                return
        return super().do_GET()

    def do_POST(self):
        if self.path != "/submit":
            self.send_error(404, "Not Found")
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length)
            payload = json.loads(body)
        except Exception as e:
            self._json(400, {"ok": False, "error": f"Bad JSON: {e}"})
            return

        comments = payload.get("comments", [])
        if not comments:
            self._json(400, {"ok": False, "error": "No comments in payload"})
            return

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        frames_dir = SUB_DIR / f"{ts}_frames"
        frames_dir.mkdir(exist_ok=True)

        # Strip embedded full-frame data from JSON, write frames as JPGs
        clean_comments = []
        for i, c in enumerate(comments):
            full_b64 = c.pop("full", None)
            if full_b64 and full_b64.startswith("data:image/"):
                # Strip data URL prefix
                header, _, b64 = full_b64.partition(",")
                ext = "jpg" if "jpeg" in header else "png"
                frame_name = f"frame_{i:03d}_t{c['time']:07.2f}_shot{c['shot_id']}.{ext}"
                (frames_dir / frame_name).write_bytes(base64.b64decode(b64))
                c["frame_file"] = f"{frames_dir.name}/{frame_name}"
            # also drop the thumb (small base64) to keep the JSON readable
            c.pop("thumb", None)
            clean_comments.append(c)

        payload["comments"] = clean_comments
        payload["frames_dir"] = frames_dir.name

        bundle_path = SUB_DIR / f"{ts}_review.json"
        bundle_path.write_text(json.dumps(payload, indent=2))

        rel_path = str(bundle_path.relative_to(ROOT.parent.parent.parent.parent))
        print(f"[review] WROTE {bundle_path}  ({len(comments)} notes + {len(list(frames_dir.iterdir()))} frames)")
        self._json(200, {"ok": True, "path": rel_path, "frame_count": len(list(frames_dir.iterdir()))})

    def _json(self, code: int, body: dict):
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def main():
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", PORT), ReviewHandler) as httpd:
        print(f"[review] Studio running at  http://localhost:{PORT}")
        print(f"[review] Submissions land in  {SUB_DIR}")
        print(f"[review] Ctrl+C to stop.\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[review] stopped.")


if __name__ == "__main__":
    main()
