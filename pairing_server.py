import base64
import json
import os
import threading
import urllib.error
import urllib.parse
import urllib.request
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import keyring
from plugins.plugin_storage import plugin_data_dir

_SERVER = None
_MAX_UPLOAD_BYTES = 25 * 1024 * 1024
_ALLOWED_UPLOAD_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".webp", ".gif", ".heic",
    ".wav", ".mp3", ".m4a", ".ogg", ".flac", ".webm",
    ".pdf", ".txt", ".md", ".csv", ".json", ".docx", ".xlsx", ".pptx",
}


def _expected_url():
    return os.environ["ORBIT_DASHBOARD_URL"].rstrip("/")


def _expected_origin():
    return os.environ["ORBIT_DASHBOARD_ORIGIN"].rstrip("/")


def _installation_id():
    state_file = plugin_data_dir("orbit-dashboard") / "installation-id"
    if state_file.exists():
        return state_file.read_text(encoding="utf-8").strip()
    value = "orbit-" + uuid.uuid4().hex
    state_file.write_text(value, encoding="utf-8")
    return value


class PairHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", _expected_origin())
        self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Private-Network", "true")

    def _json(self, status, value):
        content = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self._cors()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_OPTIONS(self):
        if self.headers.get("Origin") != _expected_origin():
            self.send_response(403)
            self.end_headers()
            return
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        if self.path != "/v1/orbit/status" or self.headers.get("Origin") != _expected_origin():
            self._json(403, {"error": "origin not allowed"})
            return
        service = "orbit-dashboard:" + _expected_url()
        installation_id = keyring.get_password(service, "installation-id")
        token = keyring.get_password(service, installation_id) if installation_id else None
        if not token:
            self._json(200, {"paired": False})
            return
        try:
            request = urllib.request.Request(
                _expected_url() + "/api/hermes/capabilities",
                method="GET",
                headers={"Authorization": "Bearer " + token},
            )
            with urllib.request.urlopen(request, timeout=10) as response:
                capabilities = json.loads(response.read())
            self._json(200, {"paired": True, "user_id": capabilities["user_id"]})
        except (KeyError, json.JSONDecodeError, urllib.error.URLError):
            self._json(200, {"paired": False, "reason": "credential rejected or dashboard unavailable"})

    def do_POST(self):
        if self.headers.get("Origin") != _expected_origin():
            self._json(403, {"error": "origin not allowed"})
            return
        if self.path == "/v1/orbit/upload":
            self._upload()
            return
        if self.path != "/v1/orbit/pair":
            self._json(404, {"error": "not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 4096:
                raise ValueError("invalid body")
            body = json.loads(self.rfile.read(length))
            dashboard_url = str(body.get("dashboard_url", "")).rstrip("/")
            pairing_token = body.get("pairing_token")
            if dashboard_url != _expected_url() or not isinstance(pairing_token, str):
                raise ValueError("dashboard or pairing token mismatch")
            installation_id = _installation_id()
            request = urllib.request.Request(
                dashboard_url + "/api/hermes/enroll",
                data=json.dumps({"pairing_token": pairing_token, "installation_id": installation_id, "label": os.environ.get("COMPUTERNAME") or os.environ.get("HOSTNAME") or "Hermes Agent"}).encode("utf-8"),
                method="POST",
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(request, timeout=15) as response:
                enrolled = json.loads(response.read())
            service = "orbit-dashboard:" + dashboard_url
            keyring.set_password(service, installation_id, enrolled["dashboard_token"])
            keyring.set_password(service, "installation-id", installation_id)
            self._json(200, {"ok": True, "user_id": enrolled["user_id"]})
        except (ValueError, KeyError, json.JSONDecodeError, urllib.error.URLError, RuntimeError) as error:
            self._json(400, {"error": str(error)})

    def _upload(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > (_MAX_UPLOAD_BYTES * 4 // 3) + 65536:
                raise ValueError("file is empty or exceeds 25 MB")
            body = json.loads(self.rfile.read(length))
            filename = Path(str(body.get("filename") or "")).name
            extension = Path(filename).suffix.lower()
            data_url = body.get("data_url")
            if not filename or extension not in _ALLOWED_UPLOAD_EXTENSIONS:
                raise ValueError("file type is not allowed")
            if not isinstance(data_url, str) or not data_url.startswith("data:") or "," not in data_url:
                raise ValueError("invalid file payload")
            encoded = data_url.split(",", 1)[1]
            content = base64.b64decode(encoded, validate=True)
            if not content or len(content) > _MAX_UPLOAD_BYTES:
                raise ValueError("file is empty or exceeds 25 MB")
            upload_dir = plugin_data_dir("orbit-dashboard") / "uploads"
            upload_dir.mkdir(parents=True, exist_ok=True)
            target = upload_dir / f"{uuid.uuid4().hex}-{filename}"
            target.write_bytes(content)
            self._json(201, {"ok": True, "path": str(target), "filename": filename, "size_bytes": len(content)})
        except (ValueError, json.JSONDecodeError, OSError) as error:
            self._json(400, {"error": str(error)})


def start_pairing_server(port=8765):
    global _SERVER
    if _SERVER is None:
        try:
            _SERVER = ThreadingHTTPServer(("127.0.0.1", int(port)), PairHandler)
        except OSError:
            # Hermes Desktop can supervise a second gateway process. The first
            # plugin instance owns the one localhost pairing listener.
            return None
        threading.Thread(target=_SERVER.serve_forever, name="orbit-pairing", daemon=True).start()
    return _SERVER
