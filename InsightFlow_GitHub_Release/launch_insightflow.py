"""Launch InsightFlow on a free local port and keep the server in this console."""
from __future__ import annotations

import socket
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
APP = ROOT / "app.py"


def find_available_port(start: int = 8501, end: int = 8999) -> int:
    """Return a currently bindable localhost port. Try the usual Streamlit range first."""
    for port in range(start, end + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    # Let the OS choose an ephemeral port if the normal range is occupied.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def main() -> int:
    if not APP.is_file():
        print(f"ERROR: app.py was not found in the project folder: {ROOT}")
        return 2
    port = find_available_port()
    url = f"http://localhost:{port}"
    print("=" * 58)
    print("  INSIGHTFLOW | BUSINESS INTELLIGENCE WORKSPACE")
    print("=" * 58)
    print(f"Project folder: {ROOT}")
    print(f"Opening application at: {url}")
    print("Keep this Command Prompt window open while using InsightFlow.")
    print("To stop the application, press Ctrl+C in this window.")
    command = [
        sys.executable, "-m", "streamlit", "run", str(APP),
        "--server.address", "127.0.0.1",
        "--server.port", str(port),
        "--server.headless", "false",
        "--browser.gatherUsageStats", "false",
    ]
    try:
        return int(subprocess.run(command, cwd=ROOT, check=False).returncode)
    except KeyboardInterrupt:
        print("\nInsightFlow stopped.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
