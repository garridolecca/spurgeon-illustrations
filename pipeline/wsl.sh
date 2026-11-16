#!/bin/bash
# Run a pipeline script inside the WSL Ubuntu (Windows blocks torch / PyMuPDF native code via Smart App Control).
# usage: bash pipeline/wsl.sh <script.py> [args]
mkdir -p /mnt/g; mountpoint -q /mnt/g || mount -t drvfs G: /mnt/g
export HF_HOME=/mnt/c/Users/rdpuser/.cache/huggingface HF_HUB_OFFLINE=1 PYTHONUNBUFFERED=1 \
       ILLUS_PDF_DIR="/mnt/g/My Drive/Logos Books - Merged PDFs"
cd /mnt/c/Users/rdpuser/ClaudeProject/spurgeon-illustrations
exec /opt/illus/bin/python "$@"
