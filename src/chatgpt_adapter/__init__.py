"""ChatGPT macOS DMG 到 Linux 桌面版本的适配工具。"""

__version__ = "0.1.0"

from .builder import build_prototype
from .verify import verify_prototype

__all__ = ["build_prototype", "verify_prototype"]
