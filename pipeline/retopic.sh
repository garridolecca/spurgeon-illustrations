#!/bin/bash
# Re-run only topics/vectors -> Excel -> publish (after editing taxonomy.py). Logs to refresh.log.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export MSYS_NO_PATHCONV=1 PYTHONIOENCODING=utf8
exec >> refresh.log 2>&1
echo "=== retopic $(date '+%Y-%m-%d %H:%M')"
wsl.exe -d Ubuntu-24.04 -u root -- bash /mnt/c/Users/rdpuser/ClaudeProject/spurgeon-illustrations/pipeline/wsl.sh pipeline/embed.py
python pipeline/build_excel.py
bash pipeline/publish.sh
echo "== refresh done $(date '+%Y-%m-%d %H:%M') (retopic)"
