"""Find the sermon / chapter (and its details) each illustration page belongs to.

Primary source: the bookmarks (outline) of the book's public-domain PDF in Drive, e.g.
    "Love's Climax (No. 2,394)" > "Exposition by C. H. Spurgeon (1 John 4)"
library.db rows are aligned to PDF pages by their printed page labels. From the first page of the sermon the
date delivered and the sermon's text (Scripture) are read. Fallback when a PDF has no usable outline:
ALL-CAPS title + "A Sermon" detection on the page text.

Writes data/sections.json: {rowid: {path: [...], section, sermon_no?, delivered?, text_ref?, place?, how}}
"""
import json, os, re, sqlite3, sys, unicodedata
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LR = os.path.join(os.path.dirname(ROOT), "logos-research")
DB = os.path.join(LR, "library.db")
PDF_DIR = os.environ.get("ILLUS_PDF_DIR", r"G:\My Drive\Logos Books - Merged PDFs")

MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December"
NO_RE = re.compile(r"\(No\.?\s*([\d,]{1,6})\)|\bNo\.\s*([\d,]{1,6})\b", re.I)
DATE_RE = re.compile(rf"((?:{MONTHS})\s+\d{{1,2}}(?:st|nd|rd|th)?,?\s+1[6-9]\d\d)", re.I)
DELIV_RE = re.compile(rf"(?:Lord[’'`]?s[-\s]?day|Sabbath|Sunday|Thursday|Monday|Tuesday|Wednesday|Friday|Saturday|New Year[’']?s Day)"
                      rf"[^.]{{0,40}}?((?:{MONTHS})\s+\d{{1,2}}(?:st|nd|rd|th)?,?\s+1[6-9]\d\d)", re.I)
PLACE_RE = re.compile(r"\bAT\s+((?:THE\s+)?[A-Z][A-Z’'\-]+(?:[ ,]+[A-Z][A-Z’'\-]+){0,5})")
REF_RE = re.compile(r"”\s*[—–-]+\s*((?:[1-3]\s?)?[A-Z][a-z]+\.?(?:\sof\s[A-Z][a-z]+)?\s\d{1,3}(?::\s?\d{1,3}(?:\s?[-–]\s?\d{1,3})?(?:,\s?\d{1,3})*)?)")
SERMON_MARK = re.compile(r"\b(a sermon|sermon no\.?|delivered (on|by|at)|preached (at|by|on)|intended for reading|published on)\b", re.I)
CONTAINER = re.compile(r"^(title page|contents|cover|copyright|index.*|preface|volume [ivxlc\d]+|sermons?|works|part [ivxlc\d]+)$", re.I)


def clean_title(t):
    t = re.sub(r"\s+", " ", t).strip()
    return t


def norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "", s)


def outline(path):
    """[(depth, title, text_from_bookmark_page)] for every bookmark, or None. The PDF's pagination differs from
    library.db's, so entries are located later by text, not page number. Cached per PDF."""
    cache = os.path.join(ROOT, "data", "outline_cache", norm(os.path.basename(path))[:120] + ".json")
    if os.path.exists(cache):
        return json.load(open(cache, encoding="utf8"))
    import fitz  # PyMuPDF (fast); run in WSL, where Smart App Control does not block its native code
    try:
        doc = fitz.open(path)
        flat = [(p - 1, lvl - 1, clean_title(t)) for lvl, t, p in doc.get_toc(simple=True) if p >= 1]
        texts = {}
        out = []
        for p, d, t in flat:
            if CONTAINER.match(t):
                continue
            if p not in texts:
                try:
                    texts[p] = doc[p].get_text()
                    if p + 1 < doc.page_count:     # a section may start near the bottom of its page
                        texts[p] += "\n" + doc[p + 1].get_text()
                except Exception:
                    texts[p] = ""
            out.append((d, t, texts[p]))
    except Exception as e:
        print("  outline failed:", os.path.basename(path), e, flush=True)
        out = None
    os.makedirs(os.path.dirname(cache), exist_ok=True)
    json.dump(out, open(cache, "w", encoding="utf8"), ensure_ascii=False)
    return out


def from_title(page_text, title):
    """The bookmark page's text starting at the section title (falls back to the whole page)."""
    words = [w for w in re.findall(r"[A-Za-z]{3,}", re.sub(r"\(No\..*?\)", "", title))][:4]
    if words:
        m = re.search(r"\W+".join(map(re.escape, words)), page_text, re.I)
        if m:
            return page_text[m.start():]
    # drop the running citation header Logos puts on every page
    return re.sub(r"^.{0,200}?\(\w[^)]{0,80}\d{4}\)\.\s*", "", page_text, count=1, flags=re.S)


def locate(entries, rows):
    """Row index where each entry begins: find a snippet of the text just after the title in the book's text."""
    joined, starts = [], []
    pos = 0
    for _, _, text in rows:
        n = norm(text)
        starts.append(pos)
        joined.append(n)
        pos += len(n)
    book = "".join(joined)
    import bisect
    out, last = [], 0
    for d, t, page_text in entries:
        seg = norm(from_title(page_text, t))
        hit = -1
        for off in (len(norm(t)) + 120, len(norm(t)) + 260, len(norm(t)) + 420, 40, 600, 900):
            snip = seg[off:off + 45]
            if len(snip) < 30:
                continue
            hit = book.find(snip, last)
            if hit < 0:
                hit = book.find(snip)
            if hit >= 0:
                hit = max(0, hit - off)   # back up to (about) where the section itself starts
                break
        out.append(None if hit < 0 else bisect.bisect_right(starts, hit) - 1)
        if hit >= 0:
            last = hit
    return out


def details(text):
    head = text[:1500]
    info = {}
    m = DELIV_RE.search(head) or DATE_RE.search(head)
    if m:
        d = re.sub(r"(\d)(st|nd|rd|th)", r"\1", re.sub(r"\s+", " ", m.group(1))).replace(",", "").title()
        info["delivered"] = re.sub(r"(\d{1,2}) (\d{4})$", r"\1, \2", d)          # "May 30, 1875"
    m = REF_RE.search(head)
    if m:
        info["text_ref"] = re.sub(r"\s+", " ", m.group(1))
    m = PLACE_RE.search(head)
    if m and "SPURGEON" not in m.group(1):
        info["place"] = m.group(1).title().strip(" ,")
    return info


def caps_title(text):
    out = []
    for ln in text.split("\n")[:6]:
        t = ln.strip().lstrip("#").strip()
        if not t:
            if out:
                break
            continue
        letters = [c for c in t if c.isalpha()]
        if len(letters) >= 4 and sum(c.isupper() for c in letters) / len(letters) > 0.85 and len(t) < 90 \
                and not re.match(r"^(C\.?\s*H\.?\s*SPURGEON|A SERMON|SERMON|INTENDED|PUBLISHED|DELIVERED|\d)", t, re.I):
            out.append(t.rstrip(","))
        elif out or len(t) > 25:
            break
    if not out:
        return None
    small = {"a", "an", "and", "as", "at", "but", "by", "for", "in", "of", "on", "or", "the", "to", "with", "from", "unto"}
    w = " ".join(out).lower().split()
    return " ".join(x if (i and x in small) else x[:1].upper() + x[1:] for i, x in enumerate(w))


def book_sections(bid, rid, md_path, rows, want):
    """rows: [(rowid, page_label, text)] in order. Returns {rowid: info} for rowids in want."""
    res = {}
    pdf = os.path.join(PDF_DIR, os.path.splitext(md_path or "")[0] + ".pdf") if md_path else None
    entries = outline(pdf) if pdf and os.path.exists(pdf) else None
    if entries:
        at = locate(entries, rows)
        found = sum(a is not None for a in at)
        # (row index, order, depth, title, details) for the entries we could place
        marks = sorted((a, i, d, t, details(from_title(pt, t))) for i, ((d, t, pt), a) in enumerate(zip(entries, at))
                       if a is not None)
        stack, e = [], 0
        for i, (rowid, label, text) in enumerate(rows):
            while e < len(marks) and marks[e][0] <= i:
                _, _, d, t, det = marks[e]
                stack = [s for s in stack if s[0] < d] + [(d, t, det)]
                e += 1
            if rowid in want and stack:
                top = stack[0]
                info = dict(path=[s[1] for s in stack], section=re.sub(r"\s*\(Nos?\.?\s*[\d,]+(?:\s*[–-]\s*[\d,]+)?\)\s*$", "", top[1]),
                            how="outline", **top[2])
                m = NO_RE.search(top[1])
                if m:
                    info["sermon_no"] = int((m.group(1) or m.group(2)).replace(",", ""))
                res[rowid] = info
        return res, f"outline {found}/{len(entries)}"
    # fallback: text heuristics
    cur = None
    for rowid, label, text in rows:
        if SERMON_MARK.search(text[:900]):
            t = caps_title(text)
            if t:
                cur = dict(path=[t], section=t, how="text", **details(text))
        if rowid in want and cur:
            res[rowid] = cur
    return res, "text"


def run(rowids):
    db = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    want = set(rowids)
    books = {int(b) for (b,) in db.execute(f"select book_id from pages where rowid in ({','.join(map(str, rowids))})")}
    pages_of = {b: [] for b in books}
    for rowid, bid, page, text in db.execute("select rowid, book_id, page, text from pages"):
        if int(bid) in books:
            pages_of[int(bid)].append((rowid, page, text))
    meta = {b: db.execute("select rid, md_path from books where id = ?", (b,)).fetchone() for b in books}
    result, how = {}, {}

    def one(b):
        return b, book_sections(b, meta[b][0], meta[b][1], sorted(pages_of[b]), want)

    with ThreadPoolExecutor(8) as ex:
        for b, (res, h) in ex.map(one, books):
            result.update(res)
            if h.startswith("outline"):
                f, n = map(int, h.split()[1].split("/"))
                how["outline_books"] = how.get("outline_books", 0) + 1
                how["bookmarks_placed"] = how.get("bookmarks_placed", 0) + f
                how["bookmarks"] = how.get("bookmarks", 0) + n
            else:
                how[h] = how.get(h, 0) + 1
    return result, how


if __name__ == "__main__":
    items = [json.loads(l) for l in open(os.path.join(LR, "illustrations.jsonl"), encoding="utf8")]
    rowids = sorted({r["rowid"] for r in items if r.get("items")})
    res, how = run(rowids)
    os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)
    json.dump({str(k): v for k, v in res.items()}, open(os.path.join(ROOT, "data", "sections.json"), "w", encoding="utf8"),
              ensure_ascii=False)
    print(f"{len(rowids)} pages, {len(res)} with a section; books by method {how}")
