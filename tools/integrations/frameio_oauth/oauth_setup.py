"""One-shot OAuth flow for Frame.io V4 via Adobe IMS.

Usage:
    .venv/bin/python tools/integrations/frameio_oauth/oauth_setup.py

What it does:
    1. Spins up a local HTTPS server on port 8765 (self-signed cert).
    2. Opens the Adobe IMS authorize URL in the user's default browser.
    3. User logs in to Adobe (already logged in for this session) and clicks Allow.
    4. Adobe redirects to https://localhost:8765/oauth/callback?code=...
    5. We capture the code, exchange it for access_token + refresh_token.
    6. Persist refresh_token to .env (FRAMEIO_REFRESH_TOKEN=...).

After this runs once, the regular tools use the refresh token to mint new
access tokens without user interaction.

References:
- https://developer.adobe.com/developer-console/docs/guides/authentication/UserAuthentication/
- https://developer.adobe.com/frameio/guides/getting-started/
"""

from __future__ import annotations

import http.server
import json
import os
import socketserver
import ssl
import sys
import threading
import urllib.parse
import webbrowser
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
CERT_DIR = Path(__file__).resolve().parent
ENV_PATH = REPO_ROOT / ".env"

# Adobe IMS endpoints (V2 used by V4 API per docs)
IMS_AUTHORIZE = "https://ims-na1.adobelogin.com/ims/authorize/v2"
IMS_TOKEN = "https://ims-na1.adobelogin.com/ims/token/v3"

# Scopes required for Frame.io V4 user-auth flow
SCOPES = ["openid", "AdobeID", "offline_access", "additional_info.roles", "email", "profile"]


def load_credentials() -> tuple[str, str, str]:
    """Pull FRAMEIO_CLIENT_ID, FRAMEIO_CLIENT_SECRET, FRAMEIO_REDIRECT_URI from .env."""
    sys.path.insert(0, str(REPO_ROOT))
    from tools.base_tool import _load_dotenv  # noqa: E402
    _load_dotenv()
    cid = os.environ.get("FRAMEIO_CLIENT_ID", "")
    secret = os.environ.get("FRAMEIO_CLIENT_SECRET", "")
    redirect = os.environ.get("FRAMEIO_REDIRECT_URI", "https://localhost:8765/oauth/callback")
    if not cid or not secret:
        raise RuntimeError("FRAMEIO_CLIENT_ID and FRAMEIO_CLIENT_SECRET must be in .env")
    return cid, secret, redirect


# ─────────────────────────────────────────────────────────────────────────
# Local HTTPS callback server
# ─────────────────────────────────────────────────────────────────────────

received_code: dict[str, str | None] = {"code": None, "error": None, "state": None}


class CallbackHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format: str, *args) -> None:  # silence default logging
        pass

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path != "/oauth/callback":
            self.send_response(404)
            self.end_headers()
            return
        params = urllib.parse.parse_qs(parsed.query)
        if "code" in params:
            received_code["code"] = params["code"][0]
            received_code["state"] = (params.get("state") or [None])[0]
            body = (
                b"<html><body style='font-family:system-ui;padding:40px;background:#0d0d1a;color:#f0e6d2;'>"
                b"<h1 style='color:#c9a84c;'>Frame.io OAuth complete</h1>"
                b"<p>You can close this tab. The terminal is finishing the setup.</p>"
                b"</body></html>"
            )
        else:
            received_code["error"] = (params.get("error") or ["unknown"])[0]
            body = (
                b"<html><body style='font-family:system-ui;padding:40px;background:#1c0a0a;color:#f0e6d2;'>"
                b"<h1 style='color:#b41e1e;'>OAuth failed</h1>"
                b"<p>" + received_code["error"].encode() + b"</p></body></html>"
            )
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def start_callback_server() -> socketserver.TCPServer:
    httpd = socketserver.TCPServer(("localhost", 8765), CallbackHandler)
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(certfile=str(CERT_DIR / "cert.pem"), keyfile=str(CERT_DIR / "key.pem"))
    httpd.socket = ctx.wrap_socket(httpd.socket, server_side=True)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    return httpd


def update_env_refresh_token(refresh_token: str) -> None:
    """Set FRAMEIO_REFRESH_TOKEN=<value> in .env, replacing any existing line."""
    lines = ENV_PATH.read_text().splitlines()
    out: list[str] = []
    found = False
    for line in lines:
        if line.startswith("FRAMEIO_REFRESH_TOKEN="):
            out.append(f"FRAMEIO_REFRESH_TOKEN={refresh_token}")
            found = True
        else:
            out.append(line)
    if not found:
        out.append(f"FRAMEIO_REFRESH_TOKEN={refresh_token}")
    ENV_PATH.write_text("\n".join(out) + "\n")


def main() -> int:
    cid, secret, redirect_uri = load_credentials()

    print("Starting local HTTPS callback server on https://localhost:8765 ...")
    server = start_callback_server()

    try:
        scope_str = " ".join(SCOPES)
        authorize_url = (
            f"{IMS_AUTHORIZE}?"
            + urllib.parse.urlencode(
                {
                    "client_id": cid,
                    "redirect_uri": redirect_uri,
                    "response_type": "code",
                    "scope": scope_str,
                }
            )
        )

        print()
        print("Opening Adobe authorization page in your browser...")
        print("If the page doesn't open automatically, visit:")
        print(f"  {authorize_url}")
        print()
        print("NOTE: Your browser will warn about a self-signed certificate at the")
        print("redirect step. That's expected — click 'Advanced' then 'Proceed to")
        print("localhost (unsafe)'. The server is local; the cert is self-issued.")
        print()
        webbrowser.open(authorize_url)

        print("Waiting for the OAuth callback (timeout 5 minutes)...")
        import time
        deadline = time.time() + 300
        while received_code["code"] is None and received_code["error"] is None:
            if time.time() > deadline:
                print("Timed out waiting for OAuth callback.")
                return 2
            time.sleep(0.5)

        if received_code["error"]:
            print(f"OAuth error: {received_code['error']}")
            return 3

        code = received_code["code"]
        print(f"Got authorization code: {code[:8]}... (truncated)")

        print("Exchanging code for tokens...")
        token_resp = requests.post(
            IMS_TOKEN,
            data={
                "grant_type": "authorization_code",
                "client_id": cid,
                "client_secret": secret,
                "code": code,
                "redirect_uri": redirect_uri,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30,
        )
        if token_resp.status_code != 200:
            print(f"Token exchange failed ({token_resp.status_code}):")
            print(token_resp.text[:500])
            return 4

        tokens = token_resp.json()
        refresh = tokens.get("refresh_token")
        if not refresh:
            print("No refresh_token in response. Response keys:", list(tokens.keys()))
            print("Make sure 'offline_access' was in the requested scopes.")
            return 5

        update_env_refresh_token(refresh)
        print("✓ Saved FRAMEIO_REFRESH_TOKEN to .env")
        print(f"  access_token expires in: {tokens.get('expires_in')}s")
        print(f"  scopes granted: {tokens.get('scope') or '(unknown)'}")
        return 0

    finally:
        server.shutdown()


if __name__ == "__main__":
    sys.exit(main())
