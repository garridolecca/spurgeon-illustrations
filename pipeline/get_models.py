"""Download the embedding models.
- BAAI/bge-small-en-v1.5 (backend: topics, categories, semantic tags).
- intfloat/multilingual-e5-small (backend search vectors, English + Spanish) and its ONNX build
  Xenova/multilingual-e5-small: a full copy in models/ (MCP server, local) and a copy for the site in
  web/public/models/ whose 118 MB weights file is split in two parts (GitHub Pages refuses files over 100 MB);
  the app's worker reassembles the parts into the browser cache.
"""
import os, shutil
from huggingface_hub import snapshot_download

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILES = ["config.json", "tokenizer.json", "tokenizer_config.json", "special_tokens_map.json",
         "onnx/model_quantized.onnx"]
if os.environ.get("SKIP_BACKEND") != "1":          # backend models: run this inside WSL (shared HF cache)
    print(snapshot_download("BAAI/bge-small-en-v1.5"))
    print(snapshot_download("intfloat/multilingual-e5-small"))
full = os.path.join(ROOT, "models", "Xenova", "multilingual-e5-small")
print(snapshot_download("Xenova/multilingual-e5-small", allow_patterns=FILES, local_dir=full))

web = os.path.join(ROOT, "web", "public", "models", "Xenova", "multilingual-e5-small")
os.makedirs(os.path.join(web, "onnx"), exist_ok=True)
for f in FILES[:-1]:
    shutil.copy(os.path.join(full, f), os.path.join(web, f))
src = os.path.join(full, "onnx", "model_quantized.onnx")
data = open(src, "rb").read()
half = len(data) // 2 + 1
for k, chunk in enumerate((data[:half], data[half:])):
    open(os.path.join(web, "onnx", f"model_quantized.onnx.part{k}"), "wb").write(chunk)
print("split", len(data), "bytes into 2 parts")
old = os.path.join(ROOT, "web", "public", "models", "Xenova", "bge-small-en-v1.5")
if os.path.isdir(old):
    shutil.rmtree(old)          # the site no longer uses the English-only model
