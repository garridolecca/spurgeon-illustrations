"""Download the embedding model: BAAI/bge-small-en-v1.5 (backend, sentence-transformers) and its ONNX build
Xenova/bge-small-en-v1.5 (served with the site so the browser embeds queries with the same model)."""
import os
from huggingface_hub import snapshot_download

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
print(snapshot_download("BAAI/bge-small-en-v1.5"))
print(snapshot_download("Xenova/bge-small-en-v1.5",
                        allow_patterns=["config.json", "tokenizer.json", "tokenizer_config.json",
                                        "special_tokens_map.json", "onnx/model_quantized.onnx"],
                        local_dir=os.path.join(ROOT, "web", "public", "models", "Xenova", "bge-small-en-v1.5")))
