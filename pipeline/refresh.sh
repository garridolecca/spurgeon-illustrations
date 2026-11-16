#!/bin/bash
# Full refresh: sections (WSL) -> export (Windows) -> topics + vectors (WSL) -> Excel on Drive -> publish site.
# Called by ../logos-research/illus_nonstop.py after every extraction round; can also be run by hand.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
W="wsl.exe -d Ubuntu-24.04 -u root -- bash /mnt/c/Users/rdpuser/ClaudeProject/spurgeon-illustrations/pipeline/wsl.sh"
export MSYS_NO_PATHCONV=1 PYTHONIOENCODING=utf8
echo "== sections";  $W pipeline/sections.py
echo "== export";    python pipeline/export.py
echo "== embed";     $W pipeline/embed.py
echo "== excel";     python pipeline/build_excel.py
echo "== publish";   bash pipeline/publish.sh
echo "== refresh done $(date '+%Y-%m-%d %H:%M')"
