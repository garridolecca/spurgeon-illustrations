"""Semantic layer: canonical topics + categories, per-illustration topic tags, and search vectors.

1. Embed every raw theme the model wrote (≈15k strings) with BAAI/bge-small-en-v1.5.
2. Cluster the frequent ones (agglomerative, cosine) into canonical topics; a topic is labelled by its most
   frequent member ("love of god", "affliction", ...). Rare themes join their nearest topic if close enough.
   Optional hand corrections: pipeline/topic_overrides.json {"rename": {old: new}, "merge": {topic: into}}.
3. Each topic goes under one of ~26 broad categories (systematic-theology headings, CATEGORIES below) by
   embedding similarity to the category description.
4. Each illustration's topics = its own themes mapped to topics + the topics nearest its meaning (semantic tags).
5. Illustration vectors (title + summary + point + topics), int8-quantized, for the browser search.

Writes data/items_tagged.jsonl and the site's data under web/public/data/.
Run inside WSL (Windows torch is blocked by Smart App Control): /opt/illus/bin/python pipeline/embed.py
"""
import collections, json, math, os, re, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
WEB = os.path.join(ROOT, "web", "public", "data")
MODEL = "BAAI/bge-small-en-v1.5"
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "

CATEGORIES = {
    "God and His Attributes": "the being and character of God: holiness, sovereignty, power, wisdom, faithfulness, love, mercy, justice, omniscience, the Trinity",
    "Providence": "God's providence and sovereign control of events, His care for His people, guidance, God working all things for good",
    "Christ: Person and Work": "Jesus Christ, His deity and humanity, incarnation, life, the cross, atonement, blood, resurrection, intercession, Christ as Savior, Shepherd, King",
    "The Holy Spirit": "the Holy Spirit, His work, indwelling, comfort, power, regeneration, illumination, fruit of the Spirit",
    "Scripture": "the Bible, the Word of God, reading and studying Scripture, the promises of God, truth",
    "Sin and the Human Heart": "sin, depravity, the deceitful heart, guilt, pride, unbelief, hypocrisy, self-righteousness, backsliding, idolatry",
    "Grace and Salvation": "salvation by grace, justification, redemption, forgiveness, election, regeneration, new birth, adoption, the gospel",
    "Faith and Repentance": "saving faith, trusting Christ, coming to Christ, repentance, conversion, turning from sin",
    "Assurance and Perseverance": "assurance of salvation, doubts and fears, perseverance of the saints, security in Christ, eternal life",
    "Prayer": "prayer, supplication, intercession, communion with God, answered prayer, waiting on God",
    "Holiness and Sanctification": "holiness, sanctification, obedience, mortifying sin, growth in grace, self-denial, spiritual discipline",
    "Christian Virtues": "love for others, humility, patience, meekness, kindness, gratitude, contentment, generosity, compassion, zeal",
    "Suffering and Affliction": "affliction, trials, suffering, sorrow, grief, chastening, persecution, the furnace, sickness, adversity",
    "Comfort and Hope": "comfort, consolation, hope, peace, joy in God, encouragement for the downcast, God's presence",
    "Temptation and Spiritual Warfare": "temptation, Satan, the devil, spiritual warfare, resisting evil, the world, the flesh",
    "Worldliness and Riches": "worldliness, riches, money, covetousness, earthly pleasures, vanity of the world, materialism",
    "Death and Eternity": "death, dying, the brevity of life, mortality, eternity, the grave, preparing to die",
    "Heaven and Glory": "heaven, glory, the eternal home, rewards, the saints in glory, the beatific vision",
    "Judgment and Hell": "the judgment day, God's wrath, hell, eternal punishment, warning the wicked, accountability",
    "Last Things": "the second coming of Christ, resurrection of the body, the end of the world, the kingdom of God",
    "The Church and Fellowship": "the church, the body of Christ, fellowship, unity, baptism, the Lord's Supper, church members",
    "Preaching and Ministry": "preaching, ministers, pastors, soul-winning, Christian service, laboring for Christ, the pulpit",
    "Evangelism and the Gospel Call": "the gospel invitation, calling sinners to Christ, missions, witness, evangelism, urgency of salvation",
    "Worship and Praise": "worship, praise, thanksgiving, singing, glorifying God, the Sabbath, devotion",
    "Family and Daily Life": "family, marriage, children, parents, home, work, daily duties, friendship, old age, youth",
    "Wisdom and Character": "wisdom, foolishness, conscience, honesty, integrity, diligence, time, habits, the tongue",
}

KIND_HINT = {"Story": "story anecdote", "Historical": "history", "Analogy": "analogy", "Image": "image metaphor"}


def load_model():
    import torch
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(MODEL, device="cuda" if torch.cuda.is_available() else "cpu")


def enc(m, texts, bs=256):
    return m.encode(texts, batch_size=bs, normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False).astype(np.float32)


def topic_label(s):
    small = {"a", "an", "and", "as", "at", "by", "for", "in", "of", "on", "or", "the", "to", "with", "from"}
    w = s.split()
    return " ".join(x if (i and x in small) else (x[:1].upper() + x[1:]) for i, x in enumerate(w))


def main():
    from sklearn.cluster import AgglomerativeClustering
    items = [json.loads(l) for l in open(os.path.join(DATA, "items.jsonl"), encoding="utf8")]
    print(len(items), "illustrations", flush=True)
    m = load_model()

    # ---- 1-2. canonical topics from the raw themes
    cnt = collections.Counter(t for it in items for t in set(it["themes"]))
    vocab = sorted(cnt, key=lambda t: -cnt[t])
    V = enc(m, vocab)
    vi = {t: i for i, t in enumerate(vocab)}
    freq = [t for t in vocab if cnt[t] >= 4]
    F = V[[vi[t] for t in freq]]
    cl = AgglomerativeClustering(n_clusters=None, metric="cosine", linkage="average",
                                 distance_threshold=float(os.environ.get("TOPIC_DIST", 0.2))).fit(F).labels_
    groups = collections.defaultdict(list)
    for t, c in zip(freq, cl):
        groups[c].append(t)
    import taxonomy                        # curated: merges synonyms, names topics, fixes categories
    ov = taxonomy.overrides()
    # overrides are keyed by the automatic label (the cluster's most frequent theme):
    #   drop: [labels]   merge: {label: into_label}   rename: {label: new}   category: {final_label: category}
    drop, merge, rename = set(ov.get("drop", [])), ov.get("merge", {}), ov.get("rename", {})
    topics = []           # [{label, members, count}]
    for c, mem in groups.items():
        mem.sort(key=lambda t: -cnt[t])
        n = sum(cnt[t] for t in mem)
        # clusters reshuffle as data grows, so match the curated taxonomy on any member (most frequent first)
        mapped = next((merge[t] for t in mem if t in merge), None)
        if n < int(os.environ.get("TOPIC_MIN", 60)) or (not mapped and mem[0] in drop):  # too small / vague
            continue
        label = mapped or rename.get(mem[0]) or mem[0]
        topics.append(dict(label=label, members=mem, count=n))
    by_label = {}
    for tp in topics:
        tgt = tp["label"]
        if tgt in by_label:
            by_label[tgt]["members"] += tp["members"]
            by_label[tgt]["count"] += tp["count"]
        else:
            by_label[tgt] = dict(tp, label=tgt)
    # clusters the taxonomy doesn't know yet (new data reshuffles clustering): fold each into the curated topic
    # whose name or listed cluster labels it is closest to, when that is clear (cos >= TOPIC_AUTO); else keep it
    finals = sorted(set(merge.values()))
    alias = [(f, f) for f in finals] + [(a, f) for a, f in merge.items()]
    A = enc(m, [a for a, _ in alias])
    auto_th = float(os.environ.get("TOPIC_AUTO", 0.83))
    for lab in [l for l in by_label if l not in ov["category"]]:
        tp = by_label[lab]
        u = V[[vi[t] for t in tp["members"]]].mean(0)
        s = A @ (u / np.linalg.norm(u))
        j = int(s.argmax())
        if s[j] >= auto_th:
            tgt = alias[j][1]
            print(f"AUTO {lab} -> {tgt} ({s[j]:.2f}, via '{alias[j][0]}')", flush=True)
            if tgt in by_label:
                by_label[tgt]["members"] += tp["members"]
                by_label[tgt]["count"] += tp["count"]
            else:
                by_label[tgt] = dict(tp, label=tgt)
            del by_label[lab]
        elif os.environ.get("KEEP_UNLISTED") != "1":
            # not a browse topic of its own: its illustrations keep their semantic topic tags and stay searchable
            print(f"UNMAPPED {lab} ({tp['count']})", flush=True)
            del by_label[lab]
    topics = sorted(by_label.values(), key=lambda t: -t["count"])
    C = np.stack([V[[vi[t] for t in tp["members"]]].mean(0) for tp in topics])
    C /= np.linalg.norm(C, axis=1, keepdims=True)
    # every raw theme -> nearest topic if close enough
    sims = V @ C.T
    theme2topic = {t: int(sims[i].argmax()) for i, t in enumerate(vocab) if sims[i].max() >= 0.80}
    print(len(topics), "topics;", f"{len(theme2topic)}/{len(vocab)} raw themes mapped", flush=True)
    unlisted = [t["label"] for t in topics if t["label"] not in ov["category"]]
    if unlisted:
        print("NOTE unlisted clusters (add to taxonomy.py):", ", ".join(unlisted), flush=True)

    # ---- 3. categories
    cats = list(CATEGORIES)
    K = enc(m, [f"{k}: {v}" for k, v in CATEGORIES.items()])
    T = enc(m, [tp["label"] for tp in topics])
    tc = (0.5 * (T @ K.T) + 0.5 * (C @ K.T)).argmax(1)
    fixed = ov.get("category", {})
    for tp, k in zip(topics, tc):
        tp["category"] = fixed.get(tp["label"], cats[int(k)])
        assert tp["category"] in CATEGORIES, tp

    # ---- 4-5. illustration vectors and topic tags
    def text_of(it):
        return f"{it['title']}. {it['summary']} {it['point']} Themes: {', '.join(it['themes'])}."
    E = enc(m, [text_of(it) for it in items], bs=512)
    S = E @ C.T
    for i, it in enumerate(items):
        own = []
        for t in it["themes"]:
            k = theme2topic.get(t)
            if k is not None and k not in own:
                own.append(k)
        # calibrated (pipeline/analyze_tags.py): unrelated topics score p50 0.57 / p99 0.70, an illustration's
        # own-theme topics p50 0.66, its best topic p50 0.73 -> take at most 2 extra, >= 0.70, near the best
        best = S[i].max()
        sem = [int(k) for k in np.argsort(-S[i])[:4]
               if S[i, k] >= 0.70 and S[i, k] >= best - 0.04 and int(k) not in own][:2]
        it["topics"] = [topics[k]["label"] for k in (own + sem)[:7]]
        it["categories"] = list(dict.fromkeys(topics[k]["category"] for k in (own + sem)[:4]))
    tcount = collections.Counter(t for it in items for t in it["topics"])
    for tp in topics:
        tp["items"] = tcount.get(tp["label"], 0)

    with open(os.path.join(DATA, "items_tagged.jsonl"), "w", encoding="utf8") as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")
    json.dump([dict(label=t["label"], category=t["category"], items=t["items"], members=t["members"][:25])
               for t in topics], open(os.path.join(DATA, "topics.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
    np.save(os.path.join(DATA, "item_emb.npy"), E.astype(np.float16))

    # ---- web data
    write_web(items, topics, E)


def write_web(items, topics, E):
    os.makedirs(os.path.join(WEB, "passages"), exist_ok=True)
    # books table (citation base computed once per book)
    books, bidx = [], {}
    authors, aidx = [], {}
    for it in items:
        if it["book_id"] not in bidx:
            bidx[it["book_id"]] = len(books)
            books.append(dict(title=it["book"], rid=it.get("rid"), year=it.get("year"), cite=it["book_cite"]))
        if it["author_display"] not in aidx:
            aidx[it["author_display"]] = len(authors)
            authors.append(it["author_display"])
    tix = {t["label"]: i for i, t in enumerate(topics)}
    cats = list(CATEGORIES)
    rows = []
    for it in items:
        rows.append([it["id"], it["title"], it["kind"], it["summary"], it["point"],
                     [tix[t] for t in it["topics"]], it["scripture"], aidx[it["author_display"]], bidx[it["book_id"]],
                     it.get("sermon") or "", it.get("sermon_part") or "", it.get("sermon_no") or 0,
                     it.get("delivered") or "", it.get("sermon_text") or "", it["page"]])
    json.dump(rows, open(os.path.join(WEB, "items.json"), "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
    CH = 2000
    for k in range(0, len(items), CH):
        json.dump([[it["passage"], it["passage_quality"][0]] for it in items[k:k + CH]],
                  open(os.path.join(WEB, "passages", f"{k // CH}.json"), "w", encoding="utf8"),
                  ensure_ascii=False, separators=(",", ":"))
    # int8 vectors with a per-vector scale
    sc = np.abs(E).max(1) / 127.0
    q = np.clip(np.round(E / sc[:, None]), -127, 127).astype(np.int8)
    q.tofile(os.path.join(WEB, "emb.i8"))
    sc.astype(np.float32).tofile(os.path.join(WEB, "emb.scale.f32"))
    meta = dict(
        version=__import__("time").strftime("%Y-%m-%d %H:%M"), count=len(items), dims=int(E.shape[1]),
        model="Xenova/bge-small-en-v1.5", query_prefix=QUERY_PREFIX, passage_chunk=CH,
        categories=cats, topics=[[t["label"], cats.index(t["category"]), t["items"]] for t in topics],
        authors=authors, books=books,
        kinds=sorted({it["kind"] for it in items}),
    )
    json.dump(meta, open(os.path.join(WEB, "meta.json"), "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
    print("web data:", len(items), "items,", len(topics), "topics,", len(books), "books", flush=True)


if __name__ == "__main__":
    main()
