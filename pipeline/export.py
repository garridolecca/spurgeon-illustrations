"""Assemble the illustration records: book + sermon/chapter + quoted passage + normalized Scripture + citation.

Inputs : ../logos-research/illustrations.jsonl (model output per page), library.db, data/sections.json
Output : data/items.jsonl  (one record per illustration, stable ids)
"""
import hashlib, json, os, re, sqlite3, sys, unicodedata
from urllib.parse import unquote

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bibleref

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LR = os.path.join(os.path.dirname(ROOT), "logos-research")
DB = os.path.join(LR, "library.db")
GENERIC = re.compile(r"^(the\s+\w+\s+)?(sermon|chapter|chap\.?|lecture|discourse|homily|section|letter|part|book)"
                     r"(\s+[ivxlc\d]+\.?)?$|^the\s+\w+\s+(sermon|chapter|lecture|discourse)$", re.I)
KINDS = {"analogy": "Analogy", "image": "Image", "story": "Story", "historical": "Historical"}


# ---------- text helpers ----------
def fold(s):
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()


def clean_page(t):
    t = re.sub(r"^.{0,200}?\(\w[^)]{0,80}\d{4}\)\.\s*", "", t, count=1, flags=re.S)  # Logos running citation
    t = re.sub(r">\s*\*\*Notes:\*\*.*", "", t, flags=re.S)                           # footnote block
    t = re.sub(r"^#+\s*", "", t, flags=re.M)
    t = re.sub(r"(\w)-\s+(\w)", r"\1\2", t)                                            # hyphenation at line ends
    return re.sub(r"\s+", " ", t).strip()


def fold_map(text):
    """fold(text) plus, for each folded character, its offset in the original text."""
    out, idx = [], []
    for i, ch in enumerate(text):
        f = fold(ch)
        out.append(f)
        idx.extend([i] * len(f))
    return "".join(out), idx


def find_start(text, opening):
    """Character offset (in the original text) of the illustration's opening words, or -1."""
    if not opening:
        return -1
    ft, idx = fold_map(text)
    words = re.findall(r"[a-z0-9]+", fold(opening))
    for n in (8, 6, 4):
        if len(words) < min(n, 3):
            continue
        pat = r"\b" + r"\W+".join(map(re.escape, words[:n]))
        m = re.search(pat, ft)
        if m:
            return idx[m.start()]
    return -1


def best_window(text, summary):
    """Fallback: the ~700-char window sharing most words with the summary."""
    sw = {w for w in re.findall(r"[a-z]{4,}", fold(summary))}
    sents = re.split(r"(?<=[.!?”])\s+", text)
    best, bi = 0, 0
    for i in range(len(sents)):
        win = " ".join(sents[i:i + 5])
        sc = len(sw & set(re.findall(r"[a-z]{4,}", fold(win))))
        if sc > best:
            best, bi = sc, i
    return " ".join(sents[bi:bi + 5]) if best >= 3 else ""


def excerpt(text, start, lo=350, hi=1100):
    s = text[start:]
    if len(s) <= hi:
        return s
    cut = [m.end() for m in re.finditer(r"[.!?][”’\"]?(\s|$)", s) if lo <= m.end() <= hi]
    return s[:cut[-1]].strip() if cut else s[:hi].rsplit(" ", 1)[0] + " …"


# ---------- citation helpers ----------
def cit_fields(c):
    out = {}
    for part in (c or "").split("|"):
        if "=" in part:
            k, v = part.split("=", 1)
            out[k] = unquote(v)
    return out


def person(name):
    """'Spurgeon, C. H.' -> 'C. H. Spurgeon'."""
    name = name.strip()
    if "," in name:
        last, first = [x.strip() for x in name.split(",", 1)]
        return f"{first} {last}".strip()
    return name


def roman_vol(title):
    m = re.search(r"Vol(?:ume)?\.?\s+([IVXLC]+|\d+)\b", title)
    if not m:
        return None
    v = m.group(1)
    if v.isdigit():
        return int(v)
    vals = dict(I=1, V=5, X=10, L=50, C=100)
    n = 0
    for a, b in zip(v, v[1:] + " "):
        n += -vals[a] if b != " " and vals.get(b, 0) > vals[a] else vals[a]
    return n


def section_title(sec):
    path = [re.sub(r"\s*\(Nos?\.?\s*[\d,]+(?:\s*[–-]\s*[\d,]+)?\)\s*$", "", p).strip() for p in (sec or {}).get("path", [])]
    if not path:
        return None, None
    top = path[0]
    sub = path[1] if len(path) > 1 else None
    if GENERIC.match(top) and sub:
        top, sub = f"{top}: {sub}", (path[2] if len(path) > 2 else None)
    return top, sub


def book_cite(it):
    """'The Metropolitan Tabernacle Pulpit Sermons, vol. 21 (London: Passmore & Alabaster, 1875)'."""
    book = it["book"]
    vol = roman_vol(book)
    if vol and re.search(r"Metropolitan Tabernacle Pulpit|New Park Street Pulpit", book):
        book = f"{re.sub(r',?\s*Vol(ume)?\.?\s+[IVXLC0-9]+$', '', book)}, vol. {vol}"
    pub = ", ".join(x for x in [": ".join(x for x in [it.get("place"), it.get("publisher")] if x), it.get("year")] if x)
    ed = f", ed. {it['editor']}" if it.get("editor") else ""
    return f"{book}{ed} ({pub})" if pub else f"{book}{ed}"


def citation(it):
    """Turabian (Chicago notes) style footnote for the illustration."""
    au = it["author_display"]
    page = it.get("page") or ""
    sec = it.get("sermon")
    if sec:
        extra = [f"sermon no. {it['sermon_no']}"] if it.get("sermon_no") else []
        if it.get("delivered"):
            extra.append(f"delivered {it['delivered']}")
        if extra:
            return f"{au}, “{sec}” ({', '.join(extra)}), in {it['book_cite']}, {page}."
        return f"{au}, “{sec},” in {it['book_cite']}, {page}."
    return f"{au}, {it['book_cite']}, {page}."


def fmt_date(d):
    """'May 30 1875' -> 'May 30, 1875'."""
    return re.sub(r"(\d{1,2}),? (\d{4})$", lambda m: f"{m.group(1)}, {m.group(2)}", d) if d else None


def norm_scripture(lst):
    if lst and all(isinstance(x, str) and len(x) <= 1 for x in lst):      # model sometimes split a string
        lst = ["".join(lst)]
    refs = []
    for s in lst or []:
        for b, c, v1, v2 in bibleref.find_refs(str(s)):
            r = f"{bibleref.book_name(b)} {c}" + (f":{v1}" + (f"–{v2}" if v2 and v2 != v1 else "") if v1 else "")
            if r not in refs:
                refs.append(r)
    return refs[:8]


def main():
    db = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    sections = json.load(open(os.path.join(ROOT, "data", "sections.json"), encoding="utf8"))
    pages = [json.loads(l) for l in open(os.path.join(LR, "illustrations.jsonl"), encoding="utf8")]
    pages = [p for p in pages if p.get("items")]
    rowids = sorted({p["rowid"] for p in pages})
    want = set(rowids) | {r + 1 for r in rowids}
    text = {}
    ids = sorted(want)
    for i in range(0, len(ids), 900):
        chunk = ids[i:i + 900]
        for r, bid, pg, t in db.execute(f"select rowid, book_id, page, text from pages where rowid in ({','.join(map(str, chunk))})"):
            text[r] = (int(bid), pg, t)
    books = {}
    for bid, title, authors, year, cit, rid in db.execute("select id, title, authors, year, citation, rid from books"):
        books[bid] = (title, authors, year, cit_fields(cit), rid)

    out, seen, stats = [], set(), dict(exact=0, approx=0, none=0)
    for p in pages:
        r = p["rowid"]
        if r not in text:
            continue
        bid, pg, t = text[r]
        nxt = text.get(r + 1)
        page_txt = clean_page(t)
        both = page_txt + (" " + clean_page(nxt[2]) if nxt and nxt[0] == bid else "")
        title, authors, year, cf, rid = books[bid]
        sec = sections.get(str(r)) or {}
        stitle, ssub = section_title(sec)
        for it in p["items"]:
            if len(it.get("summary", "")) < 20:
                continue
            key = (bid, re.sub(r"\W+", "", it["title"].lower())[:30])
            if key in seen:
                continue
            seen.add(key)
            st = find_start(both, it.get("opening", ""))
            if st >= 0:
                passage, q = excerpt(both, st), "exact"
            else:
                passage = best_window(page_txt, it["summary"] + " " + it.get("point", ""))
                q = "approx" if passage else "none"
            stats[q] += 1
            auth_raw = cf.get("au") or (authors or "").split(";")[0]
            rec = dict(
                id=hashlib.sha1(f"{r}:{it['title']}".encode()).hexdigest()[:10],
                title=it["title"].strip(), kind=KINDS.get(it.get("kind"), "Image"),
                summary=it["summary"].strip(), point=it.get("point", "").strip(),
                themes=[x.strip().lower() for x in it.get("themes", []) if x and len(x) < 60][:6],
                scripture=norm_scripture(it.get("scripture")),
                passage=passage, passage_quality=q,
                author=(authors or "").split(";")[0].strip(), author_display=person(auth_raw.split(";")[0]),
                book=title, book_id=bid, rid=rid, page=str(pg),
                year=cf.get("yr") or year, place=(cf.get("pl") or "").split(";")[0].strip() or None,
                publisher=(cf.get("pr") or "").split(";")[0].strip() or None,
                editor=person(cf["ed"].split(";")[0]) if cf.get("ed") else None,
                sermon=stitle, sermon_part=ssub, sermon_no=sec.get("sermon_no"), delivered=fmt_date(sec.get("delivered")),
                sermon_text=(norm_scripture([sec["text_ref"]]) or [None])[0] if sec.get("text_ref") else None,
                place_preached=sec.get("place"), rowid=r,
            )
            rec["book_cite"] = book_cite(rec)
            rec["citation"] = citation(rec)
            out.append(rec)
    with open(os.path.join(ROOT, "data", "items.jsonl"), "w", encoding="utf8") as f:
        for rec in out:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"{len(out)} illustrations; passages {stats}; with sermon/section {sum(1 for r in out if r['sermon'])}")


if __name__ == "__main__":
    main()
