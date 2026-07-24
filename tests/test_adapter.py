"""独立适配项目的离线回归测试。"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from chatgpt_adapter.config import (
    APP,
    CODEX_ICON_NAME,
    PROJECT_ROOT,
    VERSION_ROOT,
    WINDOW_CLASS,
)
from chatgpt_adapter.installing import write_command_entry, write_desktop_files
from chatgpt_adapter.patching import _load_version_module, apply_patches
from chatgpt_adapter.theming import SCRIPT_TAG, apply_theme


class AdapterTests(unittest.TestCase):
    def test_fixed_versions(self) -> None:
        self.assertEqual(APP.version, "26.715.72359")
        self.assertEqual(APP.build_number, "5718")
        self.assertEqual(APP.electron_version, "42.3.0")

    def test_runtime_manifests(self) -> None:
        electron = json.loads(
            (PROJECT_ROOT / "runtime/electron/42.3.0/manifest.json").read_text()
        )
        tectonic = json.loads(
            (PROJECT_ROOT / "runtime/tectonic/0.16.9/manifest.json").read_text()
        )
        native = json.loads(
            (PROJECT_ROOT / "native/electron-42.3.0/manifest.json").read_text()
        )
        self.assertEqual(electron["sha256"], "487a667ca6a734b958c16cff1df74d9d44d2c18a6cccdb4dd51f6301a356c420")
        self.assertEqual(tectonic["sha256"], "60b13a0826ae7ad9ce34b4a2df06bff2cfcfa6dda8a915477c0cbb84e1a4a902")
        self.assertEqual(len(native["artifacts"]), 5)

    def test_resource_decisions_are_explicit(self) -> None:
        decisions = json.loads((VERSION_ROOT / "resources.json").read_text())
        for name in (
            "codex",
            "codex-code-mode-host",
            "codex_chronicle",
            "rg",
            "cua_node",
            "native",
            "default_app",
            "latex/bin/tectonic",
        ):
            self.assertIn(decisions[name]["action"], {"exclude", "replace"})

    def test_install_entries_use_codex_icon(self) -> None:
        with tempfile.TemporaryDirectory(dir=PROJECT_ROOT / "tmp") as temp:
            root = Path(temp)
            app = root / "app"
            icon = app / "resources" / CODEX_ICON_NAME
            icon.parent.mkdir(parents=True)
            icon.touch()
            system_codex = root / "bin" / "codex"
            system_codex.parent.mkdir()
            system_codex.touch(mode=0o755)
            entry = root / "commands" / "chatgpt"
            write_command_entry(entry, app, system_codex)
            menu = root / "home/.local/share/applications/chatgpt-gui-26-715-72359.desktop"
            menu.parent.mkdir(parents=True)
            menu.write_text(
                "[Desktop Entry]\n"
                f"Exec=env CODEX_APP_SERVER_PORT=18767 {entry}\n"
                "StartupWMClass=ChatGPT\n"
                "X-KDE-SubstituteUID=false\n",
                encoding="utf-8",
            )
            desktops = write_desktop_files(app, entry, root / "home")

            launcher = entry.read_text(encoding="utf-8")
            self.assertIn(f'export CODEX_CLI_PATH="{system_codex}"', launcher)
            self.assertIn(str(app / "run-chatgpt-linux.sh"), launcher)
            self.assertEqual(len(desktops), 2)
            for desktop in desktops:
                source = desktop.read_text(encoding="utf-8")
                self.assertIn(f"Icon={icon}", source)
                self.assertIn(str(entry), source)
                self.assertIn(f"StartupWMClass={WINDOW_CLASS}", source)
            menu_source = menu.read_text(encoding="utf-8")
            self.assertIn("CODEX_APP_SERVER_PORT=18767", menu_source)
            self.assertIn("X-KDE-SubstituteUID=false", menu_source)

    def test_dream_skin_compiles_once(self) -> None:
        with tempfile.TemporaryDirectory(dir=PROJECT_ROOT / "tmp") as temp:
            root = Path(temp)
            extracted = root / "app"
            webview = extracted / "webview"
            webview.mkdir(parents=True)
            (webview / "index.html").write_text(
                "<!doctype html><html><head></head><body></body></html>",
                encoding="utf-8",
            )
            version = root / "version"
            version.mkdir()
            (version / "theme.toml").write_text(
                '[theme]\nenabled = true\npreset = "gothic-void-crusade"\n',
                encoding="utf-8",
            )

            metadata = apply_theme(extracted, version)
            self.assertEqual(metadata["preset"], "gothic-void-crusade")
            index = (webview / "index.html").read_text(encoding="utf-8")
            payload = (webview / "dream-skin/theme.js").read_text(encoding="utf-8")
            self.assertEqual(index.count(SCRIPT_TAG.strip()), 1)
            self.assertIn('__CODEX_DREAM_SKIN_STATE__', payload)
            self.assertNotIn("__DREAM_", payload)
            self.assertIn("main.main-surface", payload)
            self.assertIn("data:image/jpeg;base64,", payload)

    def test_all_patch_anchors_apply_once(self) -> None:
        module = _load_version_module()
        self.assertEqual(len(module.PATCHES), 19)
        with tempfile.TemporaryDirectory(dir=PROJECT_ROOT / "tmp") as temp:
            root = Path(temp)
            (root / ".vite/build").mkdir(parents=True)
            (root / "webview/assets").mkdir(parents=True)
            grouped = {"main": [], "worker": [], "webview": []}
            for patch in module.PATCHES:
                grouped[patch.area].append(patch.old)
            (root / ".vite/build/main-test.js").write_text(
                "\n".join(grouped["main"]), encoding="utf-8"
            )
            (root / ".vite/build/worker.js").write_text(
                "\n".join(grouped["worker"]), encoding="utf-8"
            )
            (root / "webview/assets/test.js").write_text(
                "\n".join(grouped["webview"]), encoding="utf-8"
            )
            self.assertEqual(len(apply_patches(root)), 19)
            main = (root / ".vite/build/main-test.js").read_text(encoding="utf-8")
            worker = (root / ".vite/build/worker.js").read_text(encoding="utf-8")
            for source in (main, worker):
                self.assertIn("`.local`,`share`,`JetBrains`,`Toolbox`,`apps`", source)
                self.assertIn("r===`intellij`?`intellij-idea`:r", source)
                self.assertNotIn("detect:()=>Ds(l)??l", source)
                self.assertNotIn("detect:()=>U7(l)??l", source)
            self.assertIn(
                "icon:process.platform===`linux`?(0,f.join)"
                "(process.resourcesPath,`codex-gui.png`)",
                main,
            )


if __name__ == "__main__":
    unittest.main()
