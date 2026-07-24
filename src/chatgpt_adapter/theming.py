"""把版本化 Dream Skin 主题编译进 Codex webview。"""

from __future__ import annotations

import base64
import hashlib
import json
import re
import tomllib
from pathlib import Path
from typing import Any

from .common import ensure_file
from .config import PROJECT_ROOT, VERSION_ROOT


THEME_ROOT = PROJECT_ROOT / "themes/dream-skin"
SCRIPT_TAG = '    <script src="./dream-skin/theme.js"></script>\n'
SELECTOR_TOKEN = re.compile(r"__DREAM_SELECTOR_([A-Z0-9_]+)__")


def _read_json(path: Path) -> dict[str, Any]:
    ensure_file(path, "缺少主题 JSON")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"主题 JSON 根节点不是对象: {path}")
    return value


def _replace_once(source: str, token: str, value: str) -> str:
    count = source.count(token)
    if count != 1:
        raise RuntimeError(f"主题模板 token 数量异常: {token}={count}")
    return source.replace(token, value, 1)


def _load_selector_contract() -> tuple[dict[str, Any], dict[str, str]]:
    contract = _read_json(THEME_ROOT / "selectors.json")
    if contract.get("schema") != "codex-dream-skin-selectors/1":
        raise RuntimeError("Dream Skin selector schema 不受支持")
    entries = contract.get("selectors")
    if not isinstance(entries, list):
        raise RuntimeError("Dream Skin selectors 不是数组")
    selectors: dict[str, str] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            raise RuntimeError("Dream Skin selector 条目不是对象")
        key = entry.get("key")
        selector = entry.get("selector")
        if not isinstance(key, str) or not isinstance(selector, str) or key in selectors:
            raise RuntimeError(f"Dream Skin selector 条目异常: {entry!r}")
        selectors[key] = selector
    return contract, selectors


def _compile_css(source: str, selectors: dict[str, str]) -> str:
    def replace(match: re.Match[str]) -> str:
        key = match.group(1).lower().replace("_", "-")
        try:
            return selectors[key]
        except KeyError as error:
            raise RuntimeError(f"CSS 引用了未知 selector token: {match.group(0)}") from error

    compiled = SELECTOR_TOKEN.sub(replace, source)
    unresolved = SELECTOR_TOKEN.search(compiled)
    if unresolved:
        raise RuntimeError(f"CSS 残留 selector token: {unresolved.group(0)}")
    if ":has(" in compiled and re.search(r":has\([^()]*:has\(", compiled):
        raise RuntimeError("主题 CSS 包含嵌套 :has()")
    return compiled


def _runtime_contract(contract: dict[str, Any]) -> dict[str, Any]:
    selectors = []
    for entry in contract["selectors"]:
        selectors.append(
            {
                "key": entry["key"],
                "selector": entry["selector"],
                "tier": entry["tier"],
                "scope": entry["scope"],
                "required": bool(entry.get("required")),
            }
        )
    stable = contract.get("stableTestids")
    return {
        "schema": contract["schema"],
        "selectors": selectors,
        "stableTestids": stable if isinstance(stable, list) else [],
    }


def _data_url(image: Path) -> str:
    ensure_file(image, "主题背景图不存在")
    mime = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}.get(
        image.suffix.lower()
    )
    if mime is None:
        raise RuntimeError(f"不支持的主题背景格式: {image.suffix}")
    data = image.read_bytes()
    if not data or len(data) > 16 * 1024 * 1024:
        raise RuntimeError(f"主题背景大小异常: {len(data)}")
    return f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}"


def _compile_payload(preset_name: str) -> tuple[str, dict[str, Any]]:
    contract, selectors = _load_selector_contract()
    css_path = THEME_ROOT / "runtime/dream-skin.css"
    runtime_path = THEME_ROOT / "runtime/renderer-inject.js"
    preset_root = THEME_ROOT / "presets" / preset_name
    theme_path = preset_root / "theme.json"
    for path in (css_path, runtime_path, theme_path):
        ensure_file(path, "缺少 Dream Skin 源文件")
    theme = _read_json(theme_path)
    image_name = theme.get("image")
    if not isinstance(image_name, str) or Path(image_name).name != image_name:
        raise RuntimeError("主题 image 必须是 preset 根目录内的单文件名")

    css = _compile_css(css_path.read_text(encoding="utf-8"), selectors)
    runtime = runtime_path.read_text(encoding="utf-8")
    css_revision = hashlib.sha256(css.encode()).hexdigest()[:16]
    art = _data_url(preset_root / image_name)
    payload_revision = hashlib.sha256(
        css.encode() + json.dumps(theme, sort_keys=True).encode() + art.encode()
    ).hexdigest()[:16]
    values = {
        "__DREAM_SKIN_SELECTORS_JSON__": json.dumps(
            _runtime_contract(contract), ensure_ascii=False, separators=(",", ":")
        ),
        "__DREAM_SKIN_CSS_JSON__": json.dumps(css, ensure_ascii=False),
        "__DREAM_SKIN_ART_JSON__": json.dumps(art),
        "__DREAM_SKIN_THEME_JSON__": json.dumps(
            theme, ensure_ascii=False, separators=(",", ":")
        ),
        "__DREAM_SKIN_VERSION_JSON__": json.dumps("1.3.3-linux-adapter"),
        "__DREAM_SKIN_STYLE_REVISION_JSON__": json.dumps(css_revision),
        "__DREAM_SKIN_PAYLOAD_REVISION_JSON__": json.dumps(payload_revision),
    }
    for token, value in values.items():
        runtime = _replace_once(runtime, token, value)
    if "__DREAM_" in runtime:
        raise RuntimeError("主题 payload 残留未编译 token")
    return runtime, {
        "preset": preset_name,
        "payloadRevision": payload_revision,
        "styleRevision": css_revision,
    }


def apply_theme(extracted: Path, version_root: Path = VERSION_ROOT) -> dict[str, Any] | None:
    """根据版本配置生成同源主题脚本，并精确注册到 webview。"""
    config_path = version_root / "theme.toml"
    if not config_path.is_file():
        return None
    with config_path.open("rb") as stream:
        config = tomllib.load(stream).get("theme", {})
    if not config.get("enabled", False):
        return None
    preset = config.get("preset")
    if not isinstance(preset, str) or not preset:
        raise RuntimeError("theme.toml 缺少有效 preset")

    payload, metadata = _compile_payload(preset)
    webview = extracted / "webview"
    index = webview / "index.html"
    ensure_file(index, "webview 缺少 index.html")
    source = index.read_text(encoding="utf-8")
    if SCRIPT_TAG.strip() in source:
        raise RuntimeError("Dream Skin script 已存在，拒绝重复注入")
    if source.count("</head>") != 1:
        raise RuntimeError("webview index.html 的 </head> 锚点异常")
    source = source.replace("</head>", f"{SCRIPT_TAG}</head>", 1)

    output = webview / "dream-skin"
    output.mkdir(parents=True, exist_ok=True)
    (output / "theme.js").write_text(payload, encoding="utf-8")
    index.write_text(source, encoding="utf-8")
    if source.count(SCRIPT_TAG.strip()) != 1:
        raise RuntimeError("Dream Skin script 注入次数异常")
    return metadata
