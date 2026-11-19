#!/bin/bash
# Spanish translation under vLLM in the temporary Ubuntu. usage: bash pipeline/wsl_translate.sh [--limit N]
export HF_HOME=/mnt/c/Users/rdpuser/.cache/huggingface HF_HUB_OFFLINE=1 PYTHONUNBUFFERED=1 VLLM_ENABLE_V1_MULTIPROCESSING=0 ES_GPU_UTIL=0.92 ES_CHUNK=8192
cd /mnt/c/Users/rdpuser/ClaudeProject/spurgeon-illustrations
exec /opt/vllm/bin/python pipeline/translate.py "$@"
