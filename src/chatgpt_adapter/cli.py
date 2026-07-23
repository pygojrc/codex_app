"""ChatGPT Linux 适配构建入口。"""

from __future__ import annotations

import argparse

from .builder import build_prototype
from .config import BUILD_ROOT
from .packaging import package_prototype
from .verify import verify_prototype


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-package", action="store_true", help="只构建原型")
    args = parser.parse_args()
    prototype = build_prototype(BUILD_ROOT)
    verify_prototype(prototype)
    print(f"原型目录: {prototype}")
    if not args.no_package:
        print(f"发行包: {package_prototype(prototype)}")


if __name__ == "__main__":
    main()
