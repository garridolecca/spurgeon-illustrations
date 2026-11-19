"""Spanish translation of every illustration (WSL, vLLM, local Qwen3-4B-Instruct): title, summary, point and the
original passage. Resumable: appends to data/items_es.jsonl ({id, title, summary, point, passage}), skipping ids done.

  /opt/vllm/bin/python pipeline/translate.py [--limit N]
"""
import json, os, re, sys, time

os.environ.setdefault("VLLM_ENABLE_V1_MULTIPROCESSING", "0")     # in-process engine (no spawn under WSL)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
SRC, OUT = os.path.join(DATA, "items.jsonl"), os.path.join(DATA, "items_es.jsonl")
MODEL = os.environ.get("ES_MODEL", "/opt/models/Qwen3-4B-Instruct-2507")
CHUNK = int(os.environ.get("ES_CHUNK", 4096))

META = """Translate this sermon illustration's title, summary and point from English into natural, clear Spanish \
for Spanish-speaking pastors (neutral Latin American Spanish, evangelical vocabulary: "gracia", "pecador", \
"Evangelio", "Señor"...). Keep names; translate meaning, not word for word. Return only JSON:
{{"title": "...", "summary": "...", "point": "..."}}

title: {title}
summary: {summary}
point: {point}"""

PASSAGE = """Translate this passage from a 19th-century English sermon or Puritan book into faithful, natural \
Spanish. Keep the author's meaning, imagery, tone and paragraphing; keep quotation marks and dialogue. Quote Bible \
verses in Reina-Valera 1960 wording. Do not add notes, titles or explanations: output only the Spanish translation.

{passage}"""


def parse(text):
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    try:
        return json.loads(text)
    except Exception:
        m = re.search(r"\{.*\}", text, flags=re.S)
        try:
            return json.loads(m.group(0)) if m else None
        except Exception:
            return None


def main():
    from vllm import LLM, SamplingParams
    from transformers import AutoTokenizer
    limit = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else None
    items = [json.loads(l) for l in open(SRC, encoding="utf8")]
    done = set()
    if os.path.exists(OUT):
        done = {json.loads(l)["id"] for l in open(OUT, encoding="utf8")}
    todo = [it for it in items if it["id"] not in done][:limit]
    print(f"{len(todo)} to translate ({len(done)} done)", flush=True)
    if not todo:
        return
    tok = AutoTokenizer.from_pretrained(MODEL)
    fp8 = os.environ.get("ES_FP8", "1") == "1"      # FP8 weights (Ada GPU): frees ~4 GB for KV cache = more sequences at once
    llm = LLM(model=MODEL, dtype="bfloat16", max_model_len=4096, enable_prefix_caching=True, seed=0,
              gpu_memory_utilization=float(os.environ.get("ES_GPU_UTIL", 0.9)),
              **(dict(quantization="fp8", max_num_seqs=512) if fp8 else {}))
    chat = lambda p: tok.apply_chat_template([{"role": "user", "content": p}], tokenize=False, add_generation_prompt=True)
    t0, n = time.time(), 0
    with open(OUT, "a", encoding="utf8") as f:
        for i in range(0, len(todo), CHUNK):
            part = todo[i:i + CHUNK]
            prompts, params = [], []
            for it in part:
                prompts.append(chat(META.format(title=it["title"], summary=it["summary"], point=it.get("point", ""))))
                params.append(SamplingParams(temperature=0, max_tokens=500, repetition_penalty=1.03))
                psg = (it.get("passage") or "").strip()
                if psg:
                    ntok = len(tok(psg).input_ids)
                    prompts.append(chat(PASSAGE.format(passage=psg)))
                    params.append(SamplingParams(temperature=0, max_tokens=min(2400, int(ntok * 2) + 64),
                                                 repetition_penalty=1.03))
            outs = iter(llm.generate(prompts, params, use_tqdm=False))
            for it in part:
                meta = parse(next(outs).outputs[0].text) or {}
                rec = {"id": it["id"], "title": str(meta.get("title") or ""), "summary": str(meta.get("summary") or ""),
                       "point": str(meta.get("point") or "")}
                if (it.get("passage") or "").strip():
                    o = next(outs).outputs[0]
                    es = o.text.strip()
                    # a cut-off or runaway translation is worse than none: the app then shows the English original
                    ratio = len(es) / max(1, len(it["passage"]))
                    rec["passage"] = es if (o.finish_reason == "stop" and 0.6 <= ratio <= 2.2) else ""
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            f.flush()
            n += len(part)
            el = time.time() - t0
            print(f"{n}/{len(todo)} items, {el:.0f}s, eta {(len(todo) - n) * el / n / 3600:.1f}h", flush=True)


if __name__ == "__main__":
    main()
