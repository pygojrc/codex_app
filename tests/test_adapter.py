"""独立适配项目的离线回归测试。"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from chatgpt_adapter.config import APP, PROJECT_ROOT, VERSION_ROOT
from chatgpt_adapter.patching import _load_version_module, apply_patches


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

    def test_all_patch_anchors_apply_once(self) -> None:
        module = _load_version_module()
        self.assertEqual(len(module.PATCHES), 18)
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
            self.assertEqual(len(apply_patches(root)), 18)


if __name__ == "__main__":
    unittest.main()
