#!/bin/bash
# One-time setup of the temporary Ubuntu used for GPU steps (Smart App Control blocks torch on Windows).
set -e
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq && apt-get install -y -qq python3-venv python3-pip > /dev/null
# /opt/illus: sentence-transformers, clustering, PDF outlines
python3 -m venv /opt/illus
/opt/illus/bin/pip install -q --upgrade pip
/opt/illus/bin/pip install -q torch --index-url https://download.pytorch.org/whl/cu128
/opt/illus/bin/pip install -q "transformers==5.22.2" "sentence-transformers==6.2.0" accelerate openpyxl "scikit-learn==1.7.2" "pymupdf==1.26.5" numpy
# /opt/vllm: fast generation (translation)
python3 -m venv /opt/vllm
/opt/vllm/bin/pip install -q --upgrade pip
/opt/vllm/bin/pip install -q "vllm==0.34.0"
mkdir -p /opt/models
cp -r /mnt/c/Users/rdpuser/ClaudeProject/llm/models/Qwen3-4B-Instruct-2507 /opt/models/
echo "setup done"
/opt/illus/bin/python -c "import torch, sentence_transformers; print('illus torch', torch.__version__, torch.cuda.is_available())"
/opt/vllm/bin/python -c "import vllm; print('vllm', vllm.__version__)"
