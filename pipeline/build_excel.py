"""Write the Illustration Bank workbook (Drive) from data/items_tagged.jsonl.

Sheets: Illustrations (one row each, with the original passage and a Turabian citation), Topics, About.
The PDF links point to the owner's Drive copies, so they stay in this private workbook only (not on the site).
"""
import collections, json, os, sqlite3, sys, time
from openpyxl import Workbook
from openpyxl.cell import WriteOnlyCell
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.table import Table, TableStyleInfo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LR = os.path.join(os.path.dirname(ROOT), "logos-research")
SITE = "https://garridolecca.github.io/spurgeon-illustrations/"
XLSX = os.environ.get("ILLUS_XLSX", r"G:\My Drive\01. DIOS\01. Preaching\05. Illustration\Illustration Bank.xlsx")


def main(out=XLSX):
    items = [json.loads(l) for l in open(os.path.join(ROOT, "data", "items_tagged.jsonl"), encoding="utf8")]
    topics = json.load(open(os.path.join(ROOT, "data", "topics.json"), encoding="utf8"))
    db = sqlite3.connect(f"file:{os.path.join(LR, 'library.db')}?mode=ro", uri=True)
    pdf = dict(db.execute("select id, pdf_id from books"))
    items.sort(key=lambda r: ((r["categories"] or ["~"])[0], (r["topics"] or ["~"])[0].lower(), r["title"]))

    wb = Workbook(write_only=True)
    ws = wb.create_sheet("Illustrations")
    head = ["Title", "Kind", "Illustration", "Original passage", "Point illustrated", "Topics", "Category",
            "Scripture", "Author", "Sermon / section", "Sermon no.", "Delivered", "Sermon text", "Book", "Page",
            "Citation (Turabian)", "Search app", "Open PDF", "Open in Logos"]
    widths = [32, 10, 60, 80, 45, 34, 26, 22, 20, 36, 9, 14, 16, 40, 7, 70, 10, 8, 9]
    for i, w in enumerate(widths):
        ws.column_dimensions[chr(65 + i) if i < 26 else "A" + chr(65 + i - 26)].width = w
    ws.freeze_panes = "B2"
    hf, fill = Font(bold=True, color="FFFFFF"), PatternFill("solid", fgColor="7A2E1F")
    row = []
    for h in head:
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
        ws.append([
            wc(r["title"]), r["kind"], wc(r["summary"]), wc(r["passage"]), wc(r["point"]),
            "; ".join(r["topics"]), "; ".join(r["categories"]), "; ".join(r["scripture"]),
            r["author_display"], r.get("sermon") or "", r.get("sermon_no") or None, r.get("delivered") or "",
            r.get("sermon_text") or "", r["book"], r["page"], wc(r["citation"]),
            lc("Open", f"{SITE}?id={r['id']}"),
            lc("PDF", f"https://drive.google.com/file/d/{pdf[r['book_id']]}/view") if pdf.get(r["book_id"]) else "",
            lc("Logos", "https://app.logos.com/books/" + r["rid"].replace(":", "%3A")) if r.get("rid") else "",
        ])
    n = len(items) + 1
    tab = Table(displayName="Illustrations", ref=f"A1:S{n}")
    tab.tableStyleInfo = TableStyleInfo(name="TableStyleLight9", showRowStripes=True)
    ws.add_table(tab)

    ts = wb.create_sheet("Topics")
    ts.column_dimensions["A"].width, ts.column_dimensions["B"].width = 34, 30
    ts.append(["Topic", "Category", "Illustrations", "Browse in app", "Related raw themes"])
    for i, t in enumerate(sorted(range(len(topics)), key=lambda k: (topics[k]["category"], -topics[k]["items"]))):
        tp = topics[t]
        c = WriteOnlyCell(ts, "Open")
        c.hyperlink, c.font = f"{SITE}?topic={t}", link
        ts.append([tp["label"], tp["category"], tp["items"], c, ", ".join(tp["members"][:12])])

    ab = wb.create_sheet("About")
    authors = collections.Counter(r["author_display"] for r in items)
    for line in [
        ["Illustration Bank"], [f"Built {time.strftime('%Y-%m-%d %H:%M')} from {len(items):,} illustrations in "
                                f"{len({r['book_id'] for r in items})} books."],
        ["Searchable by meaning at", SITE], [],
        ["Each illustration was found and summarized by a local AI model reading public-domain sermon volumes; "
         "the 'Original passage' column quotes the source text. Check the original before preaching."],
        [], ["Top authors"], *[[a, n] for a, n in authors.most_common(25)],
    ]:
        ab.append(line)
    tmp = out + ".tmp.xlsx"
    wb.save(tmp)
    os.replace(tmp, out)
    print(f"{len(items)} illustrations -> {out}")


if __name__ == "__main__":
    main(*sys.argv[1:])
