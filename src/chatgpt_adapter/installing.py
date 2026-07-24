"""把已验收的发行包版本化安装到 Linux 桌面环境。"""

from __future__ import annotations

import argparse
import shutil
import textwrap
from datetime import datetime
from pathlib import Path

from .common import ensure_dir, ensure_file, make_executable, run, sha256_file
from .config import APP, CODEX_ICON_NAME, DIST_ROOT, PACKAGE_NAME, WINDOW_CLASS
from .packaging import verify_package
from .verify import resolve_system_codex, verify_prototype


DEFAULT_PACKAGE = DIST_ROOT / PACKAGE_NAME
DEFAULT_PKG_DIR = Path("/data/pkg")
DEFAULT_OPT_DIR = Path("/data/opt")
DEFAULT_BIN = Path("/data/bin/chatgpt_gui_26_715_72359")
DEFAULT_CODEX_ALIAS = Path("/data/bin/codex_gui_26_715_72359")
APP_DIR_NAME = f"chatgpt-gui-{APP.version}"
DESKTOP_FILE_NAME = "chatgpt-gui-26-715-72359.desktop"


def _write_atomic(path: Path, content: str, mode: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.parent / f".{path.name}.tmp"
    temporary.write_text(content, encoding="utf-8")
    temporary.chmod(mode)
    temporary.replace(path)


def copy_package(package: Path, pkg_dir: Path) -> Path:
    """原子复制包到本地包仓库，并核对 SHA256。"""
    pkg_dir.mkdir(parents=True, exist_ok=True)
    target = pkg_dir / package.name
    if package.resolve() == target.resolve():
        return target
    temporary = pkg_dir / f".{package.name}.tmp"
    shutil.copy2(package, temporary)
    temporary.replace(target)
    if sha256_file(package) != sha256_file(target):
        raise RuntimeError("复制到 /data/pkg 后 SHA256 不一致")
    return target


def extract_package(package: Path, opt_dir: Path) -> Path:
    """解压到同文件系统暂存目录，供后续原子安装。"""
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    staging = opt_dir / f".{APP_DIR_NAME}.install-{stamp}"
    if staging.exists():
        raise RuntimeError(f"安装暂存目录已存在: {staging}")
    staging.mkdir(parents=True)
    run(["tar", "--zstd", "-xf", str(package), "-C", str(staging)])
    ensure_dir(staging / APP.prototype_name, "压缩包内缺少应用目录")
    return staging


def install_app(staging: Path, opt_dir: Path) -> tuple[Path, Path | None]:
    """替换版本化安装目录；异常时恢复已有安装。"""
    source = staging / APP.prototype_name
    target = opt_dir / APP_DIR_NAME
    backup: Path | None = None
    if target.exists():
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup = opt_dir / f".{APP_DIR_NAME}.backup-{stamp}"
        target.rename(backup)
    try:
        source.rename(target)
        staging.rmdir()
    except Exception:
        if target.exists():
            shutil.rmtree(target)
        if backup is not None and backup.exists():
            backup.rename(target)
        raise
    return target, backup


def write_command_entry(path: Path, app_dir: Path, system_codex: Path) -> None:
    """写入不依赖当前工作目录的命令入口。"""
    launcher = textwrap.dedent(
        f"""\
        #!/usr/bin/env bash
        # 使用系统 native Codex 启动版本化桌面应用。
        set -euo pipefail
        export CODEX_CLI_PATH="{system_codex}"
        export PATH="{system_codex.parent}:$PATH"
        exec "{app_dir / 'run-chatgpt-linux.sh'}" "$@"
        """
    )
    _write_atomic(path, launcher, 0o755)


def desktop_targets(home: Path) -> tuple[Path, Path]:
    return (
        home / ".local/share/applications" / DESKTOP_FILE_NAME,
        home / "Desktop" / DESKTOP_FILE_NAME,
    )


def _merge_desktop(existing: str, values: dict[str, str], bin_path: Path) -> str:
    """更新受管字段，同时保留用户添加的 Exec 参数和 KDE 字段。"""
    rows = existing.rstrip("\n").splitlines() if existing else ["[Desktop Entry]"]
    found: set[str] = set()
    for index, row in enumerate(rows):
        if "=" not in row:
            continue
        key, current = row.split("=", 1)
        if key not in values:
            continue
        found.add(key)
        if key == "Exec" and str(bin_path) in current:
            continue
        rows[index] = f"{key}={values[key]}"
    rows.extend(f"{key}={value}" for key, value in values.items() if key not in found)
    return "\n".join(rows) + "\n"


def write_desktop_files(app_dir: Path, bin_path: Path, home: Path) -> list[Path]:
    """创建应用菜单和桌面快捷方式，统一使用 Codex 官方图标。"""
    icon = app_dir / "resources" / CODEX_ICON_NAME
    values = {
        "Type": "Application",
        "Name": f"Codex {APP.version}",
        "Comment": f"启动 Codex {APP.version} Linux GUI",
        "Exec": str(bin_path),
        "Icon": str(icon),
        "Terminal": "false",
        "Categories": "Development;Utility;",
        "StartupNotify": "true",
        "StartupWMClass": WINDOW_CLASS,
    }
    targets = list(desktop_targets(home))
    for target in targets:
        existing = target.read_text(encoding="utf-8") if target.is_file() else ""
        desktop = _merge_desktop(existing, values, bin_path)
        _write_atomic(target, desktop, 0o755)
    return targets


def refresh_desktop_database(home: Path) -> None:
    """让新写入的应用菜单入口立即被桌面环境发现。"""
    updater = shutil.which("update-desktop-database")
    if updater is not None:
        run([updater, str(home / ".local/share/applications")])


def verify_install(
    app_dir: Path,
    package: Path,
    bin_paths: tuple[Path, Path],
    desktop_paths: list[Path],
) -> None:
    """检查安装目录、命令入口和桌面入口。"""
    for path in (
        package,
        app_dir / "ChatGPT",
        app_dir / "Codex",
        app_dir / "run-chatgpt-linux.sh",
        app_dir / "resources" / CODEX_ICON_NAME,
        *bin_paths,
        *desktop_paths,
    ):
        ensure_file(path, "安装后缺少关键文件")
    for name in ("ChatGPT", "Codex", "electron", "run-chatgpt-linux.sh"):
        make_executable(app_dir / name)
    if (app_dir / "resources/codex").exists():
        raise RuntimeError("安装目录不应包含 resources/codex")
    for desktop in desktop_paths:
        source = desktop.read_text(encoding="utf-8")
        if f"Icon={app_dir / 'resources' / CODEX_ICON_NAME}" not in source:
            raise RuntimeError(f"桌面入口没有使用 Codex 图标: {desktop}")
        if f"StartupWMClass={WINDOW_CLASS}" not in source:
            raise RuntimeError(f"桌面入口窗口 class 异常: {desktop}")
    validator = shutil.which("desktop-file-validate")
    if validator is not None:
        for desktop in desktop_paths:
            run([validator, str(desktop)])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", default=str(DEFAULT_PACKAGE), help="待安装 tar.zst")
    parser.add_argument("--pkg-dir", default=str(DEFAULT_PKG_DIR), help="包仓库目录")
    parser.add_argument("--opt-dir", default=str(DEFAULT_OPT_DIR), help="安装根目录")
    parser.add_argument("--bin", default=str(DEFAULT_BIN), help="主命令入口")
    parser.add_argument("--codex-alias", default=str(DEFAULT_CODEX_ALIAS), help="Codex 兼容入口")
    parser.add_argument("--home", default=str(Path.home()), help="桌面入口所属用户主目录")
    args = parser.parse_args()

    package = Path(args.package).resolve()
    pkg_dir = Path(args.pkg_dir).resolve()
    opt_dir = Path(args.opt_dir).resolve()
    bin_path = Path(args.bin).resolve()
    codex_alias = Path(args.codex_alias).resolve()
    home = Path(args.home).resolve()

    ensure_file(package, "待安装包不存在")
    verify_package(package)
    opt_dir.mkdir(parents=True, exist_ok=True)
    package_copy = copy_package(package, pkg_dir)
    staging = extract_package(package_copy, opt_dir)
    extracted = staging / APP.prototype_name
    try:
        system_codex = verify_prototype(extracted)
        app_dir, backup = install_app(staging, opt_dir)
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        raise

    # 重新解析一次，确保入口引用的是安装目录之外的系统 Codex。
    system_codex = resolve_system_codex(app_dir)
    write_command_entry(bin_path, app_dir, system_codex)
    write_command_entry(codex_alias, app_dir, system_codex)
    desktops = write_desktop_files(app_dir, bin_path, home)
    verify_install(app_dir, package_copy, (bin_path, codex_alias), desktops)
    refresh_desktop_database(home)

    print(f"包副本: {package_copy}")
    print(f"安装目录: {app_dir}")
    print(f"主入口: {bin_path}")
    print(f"Codex 兼容入口: {codex_alias}")
    for desktop in desktops:
        print(f"桌面入口: {desktop}")
    if backup is not None:
        print(f"旧安装备份: {backup}")


if __name__ == "__main__":
    main()
