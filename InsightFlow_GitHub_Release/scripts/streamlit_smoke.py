"""Launch the real Streamlit server and verify its local health endpoint."""
from __future__ import annotations

import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PORT = 8765
URL = f"http://127.0.0.1:{PORT}/_stcore/health"


def main() -> int:
    command = [
        sys.executable, "-m", "streamlit", "run", str(ROOT / "app.py"),
        "--server.address", "127.0.0.1", "--server.port", str(PORT),
        "--server.headless", "true", "--browser.gatherUsageStats", "false",
    ]
    process = subprocess.Popen(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    try:
        deadline = time.monotonic() + 35
        last_error: Exception | None = None
        while time.monotonic() < deadline:
            if process.poll() is not None:
                output = process.stdout.read() if process.stdout else ""
                print(output[-8000:])
                print(f"Streamlit exited before serving HTTP (code {process.returncode}).")
                return 1
            try:
                with urllib.request.urlopen(URL, timeout=2) as response:
                    body = response.read(256).decode("utf-8", errors="replace").lower()
                    if response.status == 200 and "ok" in body:
                        print(f"Streamlit health endpoint passed: {URL}")
                        return 0
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                last_error = exc
            time.sleep(0.5)
        output = process.stdout.read(8000) if process.stdout else ""
        print(output)
        print(f"Streamlit health endpoint did not become ready. Last error: {last_error}")
        return 1
    finally:
        process.terminate()
        try:
            process.wait(timeout=8)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


if __name__ == "__main__":
    raise SystemExit(main())
