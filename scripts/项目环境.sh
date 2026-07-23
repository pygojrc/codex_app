#!/usr/bin/env bash
# 把下载、依赖和临时缓存固定在项目目录内。
set -euo pipefail

if [ -n "${BASH_VERSION:-}" ]; then
  script_path="${BASH_SOURCE[0]}"
elif [ -n "${ZSH_VERSION:-}" ]; then
  script_path="${(%):-%x}"
else
  script_path="$0"
fi
project_root="$(cd "$(dirname "$script_path")/.." && pwd)"

export CHATGPT_ADAPTER_ROOT="$project_root"
export UV_CACHE_DIR="$project_root/.cache/uv"
export PNPM_STORE_PATH="$project_root/.cache/pnpm-store"
export npm_config_cache="$project_root/.cache/npm"
export ELECTRON_CACHE="$project_root/.cache/electron"
export TMPDIR="$project_root/tmp"

mkdir -p \
  "$UV_CACHE_DIR" \
  "$PNPM_STORE_PATH" \
  "$npm_config_cache" \
  "$ELECTRON_CACHE" \
  "$TMPDIR"
