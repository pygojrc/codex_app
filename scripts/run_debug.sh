#!/usr/bin/bash

cd /data/projects/Local/codex_app/chatgpt_adapter/build/ChatGPT-linux-26.715.72359

chatgpt_tmp_profile="$(mktemp -d /tmp/chatgpt-linux.XXXXXX)"
trap 'rm -rf -- "$chatgpt_tmp_profile"' EXIT

CODEX_APP_SERVER_PORT=18767 \
CODEX_ELECTRON_USER_DATA_PATH="$chatgpt_tmp_profile" \
CODEX_CLI_PATH=/data/bin/codex \
./run-chatgpt-linux.sh
