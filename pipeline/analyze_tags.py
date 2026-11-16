"""Calibrate the semantic-tag threshold: similarity of each illustration to the topics its own themes map to
(true tags) versus to random other topics."""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import embed

items = [json.loads(l) for l in open(os.path.join(embed.DATA, "items_tagged.jsonl"), encoding="utf8")]
topics = json.load(open(os.path.join(embed.DATA, "topics.json"), encoding="utf8"))
E = np.load(os.path.join(embed.DATA, "item_emb.npy")).astype(np.float32)
m = embed.load_model()
C = np.stack([embed.enc(m, t["members"][:25]).mean(0) for t in topics])
C /= np.linalg.norm(C, axis=1, keepdims=True)
lab = {t["label"]: i for i, t in enumerate(topics)}
rng = np.random.default_rng(0)
own, other, top1 = [], [], []
idx = rng.choice(len(items), 4000, replace=False)
S = E[idx] @ C.T
for k, i in enumerate(idx):
    mine = {lab[t] for t in items[i]["themes"] if t in lab}
    for t in mine:
        own.append(S[k, t])
    for t in rng.choice(len(topics), 5):
        if t not in mine:
            other.append(S[k, t])
    top1.append(S[k].max())
for name, a in (("own-theme topics", own), ("random topics", other), ("best topic", top1)):
    a = np.array(a)
    print(f"{name:18s} n={len(a):6d}  p10={np.percentile(a,10):.3f} p50={np.percentile(a,50):.3f} p90={np.percentile(a,90):.3f} p99={np.percentile(a,99):.3f}")
