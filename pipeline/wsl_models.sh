#!/bin/bash
grep -E "setup done|illus torch|vllm " /root/setup.log
export HF_HOME=/mnt/c/Users/rdpuser/.cache/huggingface
/opt/illus/bin/python - <<EOF
from huggingface_hub import snapshot_download as s
print(s("BAAI/bge-small-en-v1.5")); print(s("intfloat/multilingual-e5-small"))
EOF
