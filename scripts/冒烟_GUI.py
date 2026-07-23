#!/usr/bin/env python3
"""以独立 profile 启动 Linux 原型并采集短时 GUI 冒烟日志。"""

from __future__ import annotations

import argparse
import os
import shutil
import signal
import subprocess
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROTOTYPE = ROOT / "build/ChatGPT-linux-26.715.72359"
PROFILE = ROOT / "tmp/smoke-profile"
LOG = ROOT / "tmp/gui-smoke.log"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seconds", type=int, default=15)
    parser.add_argument("--keep-profile", action="store_true")
    args = parser.parse_args()
    launcher = PROTOTYPE / "run-chatgpt-linux.sh"
    if not launcher.is_file():
        raise RuntimeError(f"原型 launcher 不存在: {launcher}")
    if not args.keep_profile and PROFILE.exists():
        shutil.rmtree(PROFILE)
    PROFILE.mkdir(parents=True, exist_ok=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["CODEX_ELECTRON_USER_DATA_PATH"] = str(PROFILE)
    env.setdefault("CODEX_CLI_PATH", "/data/bin/codex")
    command = [
        str(launcher),
        "--headless",
    ]
    started = time.monotonic()
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
    elapsed = time.monotonic() - started
    log = LOG.read_text(encoding="utf-8", errors="replace")
    print(log[-8000:])
    if not alive:
        raise RuntimeError(
            f"GUI 在 {elapsed:.1f}s 内提前退出，exit={process.returncode}"
        )
    fatal_markers = (
        "MODULE_NOT_FOUND",
        "ERR_DLOPEN_FAILED",
        "SyntaxError:",
        "FATAL:",
        "promise rejected",
    )
    found = [marker for marker in fatal_markers if marker in log]
    if found:
        raise RuntimeError(f"GUI 日志出现 fatal 标记: {found}")
    print(f"GUI 冒烟存活 {args.seconds}s，日志: {LOG}")


if __name__ == "__main__":
    main()
