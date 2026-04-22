from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import os
import signal
import socket
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path


@dataclass(frozen=True)
class PreviewServerHandle:
    port: int
    url: str
    process: subprocess.Popen[str] | None
    owns_process: bool


def is_port_open(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.2)
        return sock.connect_ex((host, port)) == 0


def wait_for_http(url: str, timeout_s: float = 30.0) -> None:
    deadline = time.monotonic() + timeout_s
    last_error: Exception | None = None

    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1.0) as response:
                if 200 <= getattr(response, "status", 200) < 500:
                    return
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as exc:
            last_error = exc
            time.sleep(0.25)

    raise TimeoutError(f"preview server did not become ready at {url}") from last_error


@contextmanager
def managed_preview_server(web_dir: str | Path, port: int = 5173):
    """Reuse an existing preview server if possible; otherwise start and stop one."""
    url = f"http://127.0.0.1:{port}"
    if is_port_open(port):
        yield PreviewServerHandle(port=port, url=url, process=None, owns_process=False)
        return

    process = subprocess.Popen(
        ["npm", "run", "dev", "--", "--host", "127.0.0.1", "--port", str(port), "--strictPort"],
        cwd=str(web_dir),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
        text=True,
    )

    try:
        wait_for_http(url, timeout_s=30.0)
        yield PreviewServerHandle(port=port, url=url, process=process, owns_process=True)
    finally:
        if process.poll() is None:
            try:
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            except Exception:
                process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                except Exception:
                    process.kill()
                process.wait(timeout=5)
