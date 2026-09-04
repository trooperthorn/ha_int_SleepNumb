#!/usr/bin/env python
"""SleepNumber local bridge -- runs ON the rooted SleepIQ hub.

The stock SleepIQ hub (model 360SIQ01D) is outbound-only: it talks to Sleep
Number's cloud and exposes nothing on the LAN.  Once rooted over the J16 UART
(see docs/LOCAL_ROOT.md), this daemon turns the hub into a first-class local
device: a tiny HTTP/JSON server that answers the Home Assistant integration
directly, with no cloud in the path.

Design choice: this does NOT reimplement the pump's serial wire format.  The
hub already ships a vendor binary that speaks to the Firmness Control System
pump; we invoke that existing command interface (the 4-letter protocol -- PSNL,
PSNS, LBPL, ...) and return its result as JSON.  This is the same approach that
made local root useful in the first place, and it is robust to firmware quirks
because the vendor tool owns the framing/checksums.

Compatible with the hub's Python 2.7.18 (stdlib only).  Configure via env:

    SNB_CMD    command template invoked per key; {key} and {arg} are filled.
               Default: "/bam/scripts/bio {key} {arg}"
    SNB_PORT   listen port (default 8765)
    SNB_TOKEN  optional shared secret; if set, requests must send
               header  X-SNB-Token: <token>

Endpoints (all GET):
    /health                      -> {"ok": true, "ts": ...}
    /raw?key=PSNL&arg=           -> {"key": "...", "raw": "<tool stdout>"}
    /status                      -> merged snapshot (sleep number + presence/side)
"""

import json
import os
import subprocess
import time

try:                       # Python 2
    from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
    from urlparse import parse_qs, urlparse
except ImportError:        # Python 3 (for local testing on a workstation)
    from http.server import BaseHTTPRequestHandler, HTTPServer
    from urllib.parse import parse_qs, urlparse


CMD_TEMPLATE = os.environ.get("SNB_CMD", "/bam/scripts/bio {key} {arg}")
PORT = int(os.environ.get("SNB_PORT", "8765"))
TOKEN = os.environ.get("SNB_TOKEN", "")

# Read-only keys the /status snapshot gathers.  Left/right variants per the
# documented pump protocol (see docs/LOCAL_ROOT.md).
STATUS_KEYS = {
    "sleep_number_left": ("PSNL", ""),
    "sleep_number_right": ("PSNR", ""),
    "in_bed_left": ("LBPL", ""),
    "in_bed_right": ("LBPR", ""),
}


def run_key(key, arg=""):
    """Invoke the hub's command tool for one 4-letter key; return stdout text."""
    cmd = CMD_TEMPLATE.format(key=key, arg=arg).strip()
    proc = subprocess.Popen(
        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    out, _ = proc.communicate()
    if isinstance(out, bytes):
        out = out.decode("utf-8", "replace")
    return out.strip(), proc.returncode


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _send(self, code, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _authorized(self):
        if not TOKEN:
            return True
        return self.headers.get("X-SNB-Token", "") == TOKEN

    def log_message(self, *args):
        pass  # keep the hub's console quiet

    def do_GET(self):
        if not self._authorized():
            return self._send(401, {"error": "unauthorized"})
        parsed = urlparse(self.path)
        route = parsed.path
        query = parse_qs(parsed.query)

        if route == "/health":
            return self._send(200, {"ok": True, "ts": int(time.time())})

        if route == "/raw":
            key = (query.get("key") or [""])[0]
            arg = (query.get("arg") or [""])[0]
            if not key:
                return self._send(400, {"error": "missing key"})
            raw, rc = run_key(key, arg)
            return self._send(200, {"key": key, "arg": arg, "raw": raw, "rc": rc})

        if route == "/status":
            snap = {"ts": int(time.time())}
            for name, (key, arg) in STATUS_KEYS.items():
                raw, rc = run_key(key, arg)
                snap[name] = raw if rc == 0 else None
            return self._send(200, snap)

        return self._send(404, {"error": "not found", "path": route})


def main():
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    print("sleepnumber_bridge listening on 0.0.0.0:%d (cmd=%r)" % (PORT, CMD_TEMPLATE))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()


if __name__ == "__main__":
    main()
