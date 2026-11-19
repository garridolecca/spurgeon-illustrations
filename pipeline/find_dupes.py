"""Find near-duplicate illustrations (the same story / image quoted in several sermons, volumes or editions) and write
web/public/data/dupes.json = {"<duplicate id>": "<canonical id>"}. Nothing is deleted: the app uses the map to fold
duplicates under one card. Reads data/item_emb.npy (search vectors) and web/public/data/{items.json,passages/}.

A pair counts as a duplicate when its meaning vectors are very close AND the quoted passages really overlap:
  - cosine >= COS_HI and passage containment >= CONT_HI           (a shorter window lying inside a longer one)
    (two illustrations from the SAME book page need cosine >= COS_SAME_PAGE: they are often different items of one passage)
  - or cosine >= COS_LO and passage containment >= CONT_LO         (a retelling with mostly the same words)
where containment = shared 5-word shingles / the smaller passage's shingles. Pairs are merged transitively.
Canonical = best cited: a dated Spurgeon sermon first, then any sermon, then the longest passage, then the lowest index.
Usage: python pipeline/find_dupes.py [--calibrate]"""
import collections, json, os, re, sys, time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
WEB = os.path.join(ROOT, "web", "public", "data")
COS_CAND = 0.93      # candidate pairs
COS_HI, CONT_HI = 0.94, 0.60      # different page or book
COS_LO, CONT_LO = 0.985, 0.35
COS_SAME_PAGE = 0.97               # two illustrations from the same page are often DIFFERENT items of one passage
K = 6                # neighbours kept per item
SH = 5               # shingle length (words)


def main():
    t0 = time.time()
    items = json.load(open(os.path.join(WEB, "items.json"), encoding="utf8"))
    meta = json.load(open(os.path.join(WEB, "meta.json"), encoding="utf8"))
    n, ch = len(items), meta["passage_chunk"]
    E = np.load(os.path.join(DATA, "item_emb.npy")).astype(np.float32)
    E /= np.maximum(np.linalg.norm(E, axis=1, keepdims=True), 1e-9)
    # candidate pairs from blocked top-K cosine search
    cand = {}
    B = 1500
    for s in range(0, n, B):
        S = E[s:s + B] @ E.T
        idx = np.arange(s, min(s + B, n))
        S[np.arange(len(idx)), idx] = -1
        top = np.argpartition(-S, K, axis=1)[:, :K]
        for r in range(len(idx)):
            for j in top[r]:
                c = S[r, j]
                if c >= COS_CAND:
                    a, b = int(idx[r]), int(j)
                    cand[(min(a, b), max(a, b))] = float(c)
        if (s // B) % 10 == 0:
            print(f"  search {s}/{n}  pairs={len(cand)}  {time.time() - t0:.0f}s", flush=True)
    print(f"candidate pairs >= {COS_CAND}: {len(cand)}", flush=True)

    # passages (English) -> shingle sets, only for items that occur in a candidate pair
    need = sorted({i for p in cand for i in p})
    words = {}
    chunks = collections.defaultdict(list)
    for i in need:
        chunks[i // ch].append(i)
    for k, lst in chunks.items():
        rows = json.load(open(os.path.join(WEB, "passages", f"{k}.json"), encoding="utf8"))
        for i in lst:
            words[i] = re.findall(r"[a-z0-9']+", rows[i % ch][0].lower())
    sh = {i: {tuple(w[x:x + SH]) for x in range(max(0, len(w) - SH + 1))} for i, w in words.items()}

    def contain(a, b):
        A, Bs = sh[a], sh[b]
        if not A or not Bs:
            return 0.0
        return len(A & Bs) / min(len(A), len(Bs))

    pairs = []
    for (a, b), c in cand.items():
        ct = contain(a, b)
        same_page = items[a][8] == items[b][8] and items[a][14] == items[b][14]
        if same_page and c < COS_SAME_PAGE:
            continue
        if (c >= COS_HI and ct >= CONT_HI) or (c >= COS_LO and ct >= CONT_LO):
            pairs.append((a, b, c, ct))
    print(f"duplicate pairs: {len(pairs)}  ({time.time() - t0:.0f}s)", flush=True)
    if "--calibrate" in sys.argv:
        rng = np.random.default_rng(0)
        for lo, hi in ((0.93, 0.95), (0.95, 0.97), (0.97, 0.985), (0.985, 1.01)):
            sel = [(a, b, c) for (a, b), c in cand.items() if lo <= c < hi]
            cs = [contain(a, b) for a, b, _ in sel]
            print(f"  cos {lo}-{hi}: {len(sel)} pairs, containment mean {np.mean(cs):.2f}, >=0.6: {sum(x >= .6 for x in cs)}, >=0.35: {sum(x >= .35 for x in cs)}")

    # union-find
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for a, b, _, _ in pairs:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)
    groups = collections.defaultdict(list)
    for a, b, _, _ in pairs:
        for x in (a, b):
            groups[find(x)].append(x)
    plen = np.fromfile(os.path.join(WEB, "len.u16"), dtype="<u2") if os.path.exists(os.path.join(WEB, "len.u16")) else np.zeros(n)

    def rank(i):   # higher = better cited
        it = items[i]
        return (1 if (it[9] and it[12]) else 0, 1 if it[9] else 0, int(plen[i]), -i)
    dupes = {}
    for g in groups.values():
        g = sorted(set(g))
        best = max(g, key=rank)
        for x in g:
            if x != best:
                dupes[items[x][0]] = items[best][0]
    json.dump(dupes, open(os.path.join(WEB, "dupes.json"), "w", encoding="utf8"), separators=(",", ":"))
    sizes = collections.Counter(len(set(g)) for g in groups.values())
    print(f"dupes.json: {len(dupes)} duplicates folded under {len(groups)} canonical illustrations "
          f"({100 * len(dupes) / n:.1f}% of {n}); group sizes {dict(sorted(sizes.items())[:8])}  ({time.time() - t0:.0f}s)")
    # samples for review
    rng = np.random.default_rng(1)
    for a, b, c, ct in [pairs[i] for i in rng.choice(len(pairs), min(20, len(pairs)), replace=False)]:
        print(f"- cos {c:.3f} contain {ct:.2f}\n    A: {items[a][1]} | {items[a][9] or meta['books'][items[a][8]]['title']} p.{items[a][14]}\n    B: {items[b][1]} | {items[b][9] or meta['books'][items[b][8]]['title']} p.{items[b][14]}")


if __name__ == "__main__":
    main()
