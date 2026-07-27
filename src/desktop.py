"""Desktop launcher for the packaged EasyPass app."""

from __future__ import annotations

import os
import socket
import threading
import time
import traceback
import webbrowser
from contextlib import suppress
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
LIBS_DIR = ROOT_DIR / "libs"

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

if LIBS_DIR.exists() and str(LIBS_DIR) not in sys.path:
    sys.path.insert(0, str(LIBS_DIR))

from werkzeug.serving import make_server

if __package__ in {None, ""}:
    from src.app import app
    from src.config import DATA_DIR
else:
    from .app import app
    from .config import DATA_DIR

HOST = "127.0.0.1"
DEFAULT_PORT = int(os.environ.get("EASYPASS_PORT", "5000"))
PORT_TRIES = int(os.environ.get("EASYPASS_PORT_TRIES", "20"))
STARTUP_TIMEOUT = float(os.environ.get("EASYPASS_STARTUP_TIMEOUT", "10"))
LOG_FILE = DATA_DIR / "launcher.log"


def _log(message: str) -> None:
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as fh:
        fh.write(f"[{timestamp}] {message}\n")


def _port_available(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((HOST, port))
        except OSError:
            return False
    return True


def _pick_port() -> int:
    for port in range(DEFAULT_PORT, DEFAULT_PORT + PORT_TRIES):
        if _port_available(port):
            return port
    raise RuntimeError(f"No free port found in range {DEFAULT_PORT}-{DEFAULT_PORT + PORT_TRIES - 1}")


def _wait_until_ready(port: int, timeout: float) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.3)
            try:
                sock.connect((HOST, port))
                return True
            except OSError:
                time.sleep(0.1)
    return False


def run() -> None:
    port = _pick_port()
    server = make_server(HOST, port, app, threaded=True)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()

    if not _wait_until_ready(port, STARTUP_TIMEOUT):
        _log(f"Server did not respond within {STARTUP_TIMEOUT} seconds, opening browser anyway.")

    url = f"http://{HOST}:{port}"
    try:
        webbrowser.open_new(url)
    except Exception:
        _log("Failed to open browser.")
        _log(traceback.format_exc())

    try:
        worker.join()
    except KeyboardInterrupt:
        pass
    finally:
        with suppress(Exception):
            server.shutdown()
        with suppress(Exception):
            server.server_close()


if __name__ == "__main__":
    try:
        run()
    except Exception:
        _log("Desktop launcher failed.")
        _log(traceback.format_exc())
        raise
