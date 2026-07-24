"""只从独立项目根解析版本与构建路径。"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
VERSION = "26.715.72359"
VERSION_ROOT = PROJECT_ROOT / "versions" / VERSION


@dataclass(frozen=True)
class AppSpec:
    version: str
    build_number: str
    package_name: str
    brand: str
    electron_version: str
    bundle_root: str
    prototype_name: str
    active_plugins: tuple[str, ...]
    excluded_plugins: tuple[str, ...]

    @property
    def resources_prefix(self) -> str:
        return f"{self.bundle_root}/Contents/Resources"


def load_spec() -> AppSpec:
    with (VERSION_ROOT / "version.toml").open("rb") as stream:
        value = tomllib.load(stream)
    app = value["app"]
    plugins = value["plugins"]
    return AppSpec(
        **app,
        active_plugins=tuple(plugins["active"]),
        excluded_plugins=tuple(plugins["excluded"]),
    )


APP = load_spec()
DMG = PROJECT_ROOT / f"inputs/chatgpt/{APP.version}/ChatGPT.dmg"
RUNTIME = PROJECT_ROOT / f"runtime/electron/{APP.electron_version}/extracted"
NATIVE_ROOT = PROJECT_ROOT / f"native/electron-{APP.electron_version}"
NATIVE_MODULES = NATIVE_ROOT / "node_modules"
ASAR_CLI = NATIVE_MODULES / ".bin/asar"
BUILD_ROOT = PROJECT_ROOT / "build"
DIST_ROOT = PROJECT_ROOT / "dist"
TECTONIC = PROJECT_ROOT / "runtime/tectonic/0.16.9/extracted/tectonic"
PACKAGE_NAME = f"chatgpt-linux-{APP.version}-x64.tar.zst"
CODEX_ICON_SOURCE_NAME = "icon-codex-dark-color.png"
CODEX_ICON_NAME = "codex-gui.png"
WINDOW_CLASS = "Codex-26-715-72359"


@dataclass(frozen=True)
class NativeArtifact:
    name: str
    source: str
    destination: str


DEVICE_ROOT = (
    "@worklouder/device-kit-oai/node_modules/@worklouder/wl-device-kit/"
    "node_modules"
)
NATIVE_ARTIFACTS = (
    NativeArtifact(
        "better-sqlite3",
        "better-sqlite3/build/Release/better_sqlite3.node",
        "better-sqlite3/build/Release/better_sqlite3.node",
    ),
    NativeArtifact(
        "node-pty",
        "node-pty/build/Release/pty.node",
        "node-pty/build/Release/pty.node",
    ),
    NativeArtifact(
        "serialport",
        "@serialport/bindings-cpp/build/Release/bindings.node",
        f"{DEVICE_ROOT}/serialport/node_modules/@serialport/bindings-cpp/"
        "build/Release/bindings.node",
    ),
    NativeArtifact(
        "node-hid",
        "node-hid/build/Release/HID.node",
        f"{DEVICE_ROOT}/node-hid/build/Release/HID.node",
    ),
    NativeArtifact(
        "node-hid-hidraw",
        "node-hid/build/Release/HID_hidraw.node",
        f"{DEVICE_ROOT}/node-hid/build/Release/HID_hidraw.node",
    ),
)
