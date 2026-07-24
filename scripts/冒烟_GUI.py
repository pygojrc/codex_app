#!/usr/bin/env python3
"""以独立 profile 启动 Linux 原型并采集短时 GUI 冒烟日志。"""

from __future__ import annotations

import argparse
import os
import shutil
import signal
import socket
import subprocess
import threading
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROTOTYPE = ROOT / "build/ChatGPT-linux-26.715.72359"
PROFILE = ROOT / "tmp/smoke-profile"
LOG = ROOT / "tmp/gui-smoke.log"


class TcpProbeServer:
    """提供可接受 TCP 连接的最小 app-server 探针。"""

    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port
        self._stop = threading.Event()
        self._socket: socket.socket | None = None
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self.host, self.port))
        server.listen()
        server.settimeout(0.2)
        self._socket = server

        def serve() -> None:
            while not self._stop.is_set():
                try:
                    connection, _ = server.accept()
                except TimeoutError:
                    continue
                except OSError:
                    break
                with connection:
                    connection.settimeout(0.2)
                    try:
                        connection.recv(4096)
                    except (TimeoutError, OSError):
                        pass

        self._thread = threading.Thread(target=serve, daemon=True)
        self._thread.start()

    def close(self) -> None:
        self._stop.set()
        if self._socket is not None:
            self._socket.close()
        if self._thread is not None:
            self._thread.join(timeout=1)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seconds", type=int, default=15)
    parser.add_argument("--keep-profile", action="store_true")
    parser.add_argument("--xvfb", action="store_true", help="通过 xvfb-run 启动")
    parser.add_argument("--mock-app-server", action="store_true")
    parser.add_argument("--port", type=int, default=18767)
    args = parser.parse_args()

    launcher = PROTOTYPE / "run-chatgpt-linux.sh"
    if not launcher.is_file():
        raise RuntimeError(f"原型 launcher 不存在: {launcher}")
    source = launcher.read_text(encoding="utf-8")
    expected = f'CODEX_APP_SERVER_PORT:-{args.port}'
    if expected not in source:
        raise RuntimeError(f"launcher 默认端口不是 {args.port}")

    if not args.keep_profile and PROFILE.exists():
        shutil.rmtree(PROFILE)
    PROFILE.mkdir(parents=True, exist_ok=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env["CODEX_ELECTRON_USER_DATA_PATH"] = str(PROFILE)
    env["CODEX_APP_SERVER_HOST"] = "127.0.0.1"
    env["CODEX_APP_SERVER_PORT"] = str(args.port)
    env.pop("CODEX_CLI_PATH", None)

    command = [str(launcher), "--headless"]
    if args.xvfb:
        xvfb = shutil.which("xvfb-run")
        if xvfb is None:
            raise RuntimeError("找不到 xvfb-run")
        command = [xvfb, "-a", *command]

    probe = TcpProbeServer("127.0.0.1", args.port) if args.mock_app_server else None
    if probe is not None:
        probe.start()

    started = time.monotonic()
    try:
        with LOG.open("w", encoding="utf-8") as output:
            process = subprocess.Popen(
                command,
                cwd=PROTOTYPE,
                env=env,
                stdout=output,
                stderr=subprocess.STDOUT,
                start_new_session=True,
                text=True,
            )
            time.sleep(args.seconds)
            alive = process.poll() is None
            if alive:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
    finally:
        if probe is not None:
            probe.close()

    elapsed = time.monotonic() - started
    log = LOG.read_text(encoding="utf-8", errors="replace")
    print(log[-8000:])
    if not alive:
        raise RuntimeError(f"GUI 在 {elapsed:.1f}s 内提前退出，exit={process.returncode}")

    fatal_markers = (
        "MODULE_NOT_FOUND",
        "ERR_DLOPEN_FAILED",
        "SyntaxError:",
        "FATAL:",
        "promise rejected",
        "error while loading shared libraries",
    )
    found = [marker for marker in fatal_markers if marker in log]
    if found:
        raise RuntimeError(f"GUI 日志出现 fatal 标记: {found}")
    if args.mock_app_server and f"ws://127.0.0.1:{args.port}" not in log:
        raise RuntimeError("launcher 未选择默认 app-server WebSocket 地址")
    print(f"GUI 冒烟存活 {args.seconds}s，日志: {LOG}")


if __name__ == "__main__":
    main()
