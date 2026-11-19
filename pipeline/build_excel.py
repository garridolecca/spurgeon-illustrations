"""Write the Illustration Bank workbooks (Drive) from data/items_tagged.jsonl: English ("Illustration Bank.xlsx")
and Spanish ("Banco de Ilustraciones.xlsx", same folder).

Sheets: Illustrations (one row each, with the original passage and a Turabian citation), Topics, About.
The Spanish workbook has the Spanish title / summary / point, the machine-translated passage next to the English
original, Spanish topics, Scripture references and citation connectors (sermon and book titles stay as published).
The PDF links point to the owner's Drive copies, so they stay in these private workbooks only (not on the site).
"""
import collections, json, os, re, sqlite3, sys, time
from openpyxl import Workbook
from openpyxl.cell import WriteOnlyCell
from openpyxl.styles import Alignment, Font, PatternFill

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import taxonomy_es as TES

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LR = os.path.join(os.path.dirname(ROOT), "logos-research")
SITE = "https://garridolecca.github.io/spurgeon-illustrations/"
XLSX = os.environ.get("ILLUS_XLSX", r"G:\My Drive\01. DIOS\01. Preaching\05. Illustration\Illustration Bank.xlsx")
XLSX_ES = os.path.join(os.path.dirname(XLSX), "Banco de Ilustraciones.xlsx")

BIBLE = json.load(open(os.path.join(ROOT, "web", "src", "bible-books.json"), encoding="utf8"))
BOOK_ES = dict(zip(BIBLE["books"], BIBLE["books_es"]))
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
          "November", "December"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre",
         "noviembre", "diciembre"]

L = {
    "en": dict(
        sheet="Illustrations", topics_sheet="Topics", about_sheet="About",
        head=["Title", "Kind", "Illustration", "Original passage", "Point illustrated", "Topics", "Category",
              "Scripture", "Author", "Sermon / section", "Sermon no.", "Delivered", "Sermon text", "Book", "Page",
              "Citation (Turabian)", "Search app", "Open PDF", "Open in Logos"],
        widths=[32, 10, 60, 80, 45, 34, 26, 22, 20, 36, 9, 14, 16, 40, 7, 70, 10, 8, 9],
        topics_head=["Topic", "Category", "Illustrations", "Browse in app", "Related raw themes"],
        open="Open", title="Illustration Bank", built="Built {d} from {n:,} illustrations in {b} books.",
        searchable="Searchable by meaning at",
        note="Each illustration was found and summarized by a local AI model reading public-domain sermon volumes; "
             "the 'Original passage' column quotes the source text. Check the original before preaching.",
        top="Top authors", q=""),
    "es": dict(
        sheet="Ilustraciones", topics_sheet="Temas", about_sheet="Acerca de",
        head=["Título", "Tipo", "Ilustración", "Pasaje (traducción automática)", "Pasaje original (inglés)",
              "Lo que ilustra", "Temas", "Categoría", "Escritura", "Autor", "Sermón / sección", "Sermón n.º",
              "Predicado", "Texto del sermón", "Libro", "Página", "Cita (Turabian)", "Abrir en la app",
              "Abrir PDF", "Abrir en Logos"],
        widths=[32, 10, 60, 80, 80, 45, 34, 26, 22, 20, 36, 9, 18, 16, 40, 7, 70, 10, 8, 9],
        topics_head=["Tema", "Categoría", "Ilustraciones", "Ver en la app", "Temas automáticos relacionados"],
        open="Abrir", title="Banco de Ilustraciones",
        built="Generado el {d} con {n:,} ilustraciones de {b} libros.",
        searchable="Búsqueda por significado en",
        note="Cada ilustración fue hallada y resumida por un modelo de IA local que leyó sermones y obras de dominio "
             "público; los textos en español son traducciones automáticas. La columna 'Pasaje original (inglés)' cita "
             "el texto de la fuente. Verifique el original antes de predicarlo.",
        top="Autores principales", q="&lang=es"),
}


def date_es(d):
    m = re.match(r"^([A-Z][a-z]+) (\d{1,2}), (\d{4})$", (d or "").strip())
    return f"{m.group(2)} de {MESES[MONTHS.index(m.group(1))]} de {m.group(3)}" if m and m.group(1) in MONTHS else d


def ref_es(s):
    m = re.match(r"^(.+?) (\d.*)$", s)
    if not m or m.group(1) not in BOOK_ES:
        return BOOK_ES.get(s, s)
    name = "Salmo" if m.group(1) == "Psalms" else BOOK_ES[m.group(1)]
    return f"{name} {m.group(2)}"


def cite_es(c):
    c = re.sub(r"sermon no\. ", "sermón n.º ", c)
    c = re.sub(r"delivered ([A-Z][a-z]+ \d{1,2}, \d{4})", lambda m: "predicado el " + date_es(m.group(1)), c)
    return re.sub(r"(\)|”)(,?) in ", lambda m: m.group(1) + m.group(2) + " en ", c, count=1)


def build(items, topics, lang, out, pdf):
    T = L[lang]
    es = lang == "es"
    wb = Workbook(write_only=True)
    ws = wb.create_sheet(T["sheet"])
    for i, w in enumerate(T["widths"]):
        ws.column_dimensions[chr(65 + i) if i < 26 else "A" + chr(65 + i - 26)].width = w
    ws.freeze_panes = "B2"
    hf, fill = Font(bold=True, color="FFFFFF"), PatternFill("solid", fgColor="7A2E1F")
    row = []
    for h in T["head"]:
        c = WriteOnlyCell(ws, h)
        c.font, c.fill = hf, fill
        row.append(c)
    ws.append(row)
    link, wrap = Font(color="1155CC", underline="single"), Alignment(wrap_text=True, vertical="top")

    def lc(text, url):
        c = WriteOnlyCell(ws, text)
        c.hyperlink, c.font = url, link
        return c

    def wc(v):
        c = WriteOnlyCell(ws, v)
        c.alignment = wrap
        return c
    for r in items:
        e = r.get("es") or {}
        tail = [
            lc(T["open"], f"{SITE}?id={r['id']}{T['q']}"),
            lc("PDF", f"https://drive.google.com/file/d/{pdf[r['book_id']]}/view") if pdf.get(r["book_id"]) else "",
            lc("Logos", "https://app.logos.com/books/" + r["rid"].replace(":", "%3A")) if r.get("rid") else "",
        ]
        if es:
            ws.append([
                wc(e.get("title") or r["title"]), TES.KINDS_ES.get(r["kind"], r["kind"]),
                wc(e.get("summary") or r["summary"]), wc(e.get("passage") or ""), wc(r["passage"]),
                wc(e.get("point") or r["point"]),
                "; ".join(TES.topic_es(t) for t in r["topics"]),
                "; ".join(TES.CATEGORIES_ES.get(c, c) for c in r["categories"]),
                "; ".join(ref_es(s) for s in r["scripture"]),
                r["author_display"], r.get("sermon") or "", r.get("sermon_no") or None,
                date_es(r.get("delivered") or ""), ref_es(r.get("sermon_text") or "") if r.get("sermon_text") else "",
                r["book"], r["page"], wc(cite_es(r["citation"])), *tail,
            ])
        else:
            ws.append([
                wc(r["title"]), r["kind"], wc(r["summary"]), wc(r["passage"]), wc(r["point"]),
                "; ".join(r["topics"]), "; ".join(r["categories"]), "; ".join(r["scripture"]),
                r["author_display"], r.get("sermon") or "", r.get("sermon_no") or None, r.get("delivered") or "",
                r.get("sermon_text") or "", r["book"], r["page"], wc(r["citation"]), *tail,
            ])
    last = chr(64 + len(T["head"])) if len(T["head"]) <= 26 else "A" + chr(64 + len(T["head"]) - 26)
    ws.auto_filter.ref = f"A1:{last}{len(items) + 1}"

    ts = wb.create_sheet(T["topics_sheet"])
    ts.column_dimensions["A"].width, ts.column_dimensions["B"].width = 34, 30
    ts.append(T["topics_head"])
    for t in sorted(range(len(topics)), key=lambda k: (topics[k]["category"], -topics[k]["items"])):
        tp = topics[t]
        c = WriteOnlyCell(ts, T["open"])
        c.hyperlink, c.font = f"{SITE}?topic={t}{T['q']}", link
        ts.append([TES.topic_es(tp["label"]) if es else tp["label"],
                   TES.CATEGORIES_ES.get(tp["category"], tp["category"]) if es else tp["category"],
                   tp["items"], c, ", ".join(tp["members"][:12])])

    ab = wb.create_sheet(T["about_sheet"])
    authors = collections.Counter(r["author_display"] for r in items)
    for line in [
        [T["title"]], [T["built"].format(d=time.strftime("%Y-%m-%d %H:%M"), n=len(items),
                                         b=len({r["book_id"] for r in items}))],
        [T["searchable"], SITE + ("?lang=es" if es else "")], [], [T["note"]],
        [], [T["top"]], *[[a, n] for a, n in authors.most_common(25)],
    ]:
        ab.append(line)
    tmp = out + ".tmp.xlsx"
    wb.save(tmp)
    os.replace(tmp, out)
    print(f"{len(items)} illustrations -> {out}", flush=True)


def main(out=XLSX, out_es=XLSX_ES):
    items = [json.loads(l) for l in open(os.path.join(ROOT, "data", "items_tagged.jsonl"), encoding="utf8")]
    topics = json.load(open(os.path.join(ROOT, "data", "topics.json"), encoding="utf8"))
    db = sqlite3.connect(f"file:{os.path.join(LR, 'library.db')}?mode=ro", uri=True)
    pdf = dict(db.execute("select id, pdf_id from books"))
    items.sort(key=lambda r: ((r["categories"] or ["~"])[0], (r["topics"] or ["~"])[0].lower(), r["title"]))
    build(items, topics, "en", out, pdf)
    if any((r.get("es") or {}).get("title") for r in items):
        build(items, topics, "es", out_es, pdf)


if __name__ == "__main__":
    main(*sys.argv[1:])
