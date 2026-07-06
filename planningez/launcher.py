"""Desktop launcher for the packaged PlanningEz executable.

Starts the FastAPI server on a local port and opens the default web browser at
the app URL. This is the entry point used by the PyInstaller build so a
double-click behaves like a native application: no terminal, no Python, no
Node required.
"""

from __future__ import annotations

import os
import socket
import threading
import time
import webbrowser


def _find_free_port(preferred: int = 8000) -> int:
    """Return the preferred port if free, otherwise an OS-assigned one."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind(("127.0.0.1", preferred))
            return preferred
        except OSError:
            sock.bind(("127.0.0.1", 0))
            return sock.getsockname()[1]


def _open_browser_when_ready(url: str, host: str, port: int) -> None:
    """Open the browser once the server accepts connections."""
    deadline = time.time() + 15
    while time.time() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.5)
            if sock.connect_ex((host, port)) == 0:
                break
        time.sleep(0.2)
    webbrowser.open(url)


def main() -> int:
    """Launch the PlanningEz server and open the browser."""
    import uvicorn

    # Import the app object directly (rather than by import string) so static
    # bundlers like PyInstaller trace every dependency.
    from planningez.api.app import app

    host = os.environ.get("PLANNINGEZ_HOST", "127.0.0.1")
    port = int(os.environ.get("PLANNINGEZ_PORT", str(_find_free_port(8000))))
    url = f"http://{host}:{port}"

    print(f"PlanningEz démarre sur {url} …")
    if os.environ.get("PLANNINGEZ_NO_BROWSER") != "1":
        threading.Thread(
            target=_open_browser_when_ready, args=(url, host, port), daemon=True
        ).start()

    uvicorn.run(app, host=host, port=port, log_level="info")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
