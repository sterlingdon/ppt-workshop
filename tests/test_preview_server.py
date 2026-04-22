from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.preview_server import is_port_open, managed_preview_server


class DummyProcess:
    def __init__(self):
        self.pid = 12345
        self._polled = None
        self.terminated = False
        self.waited = False

    def poll(self):
        return self._polled

    def terminate(self):
        self.terminated = True

    def wait(self, timeout=None):
        self.waited = True
        return 0

    def kill(self):
        self.terminated = True


def test_is_port_open_detects_open_socket():
    class FakeSocket:
        def __init__(self):
            self.timeout = None

        def settimeout(self, timeout):
            self.timeout = timeout

        def connect_ex(self, address):
            assert address == ("127.0.0.1", 5173)
            return 0

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    class FakeSocketModule:
        AF_INET = object()
        SOCK_STREAM = object()

        def socket(self, family, kind):
            return FakeSocket()

    original_socket_module = __import__("tools.preview_server", fromlist=["socket"]).socket
    import tools.preview_server as preview_server

    preview_server.socket = FakeSocketModule()
    try:
        assert is_port_open(5173)
    finally:
        preview_server.socket = original_socket_module


def test_managed_preview_server_reuses_open_port(monkeypatch, tmp_path):
    monkeypatch.setattr("tools.preview_server.is_port_open", lambda port, host='127.0.0.1': True)
    spawned = []
    monkeypatch.setattr("tools.preview_server.subprocess.Popen", lambda *args, **kwargs: spawned.append((args, kwargs)))

    with managed_preview_server(tmp_path, port=5173) as server:
        assert server.owns_process is False
        assert server.process is None

    assert spawned == []


def test_managed_preview_server_terminates_spawned_process(monkeypatch, tmp_path):
    dummy = DummyProcess()
    monkeypatch.setattr("tools.preview_server.is_port_open", lambda port, host='127.0.0.1': False)
    monkeypatch.setattr("tools.preview_server.subprocess.Popen", lambda *args, **kwargs: dummy)
    monkeypatch.setattr("tools.preview_server.wait_for_http", lambda url, timeout_s=30.0: None)
    monkeypatch.setattr("tools.preview_server.os.getpgid", lambda pid: pid)
    killed = []
    monkeypatch.setattr("tools.preview_server.os.killpg", lambda pgid, sig: killed.append((pgid, sig)))

    with managed_preview_server(tmp_path, port=5173) as server:
        assert server.owns_process is True
        assert server.process is dummy

    assert dummy.waited is True
    assert killed
