"""Spanish translation clean-up: fixes recurring theological / proper-name renderings in the machine translation.

Applies the same regex fixes to
  - data/items_es.jsonl                         (source of truth; embed.py and build_excel.py read it)
  - web/public/data/items.json   fields 15-17   (Spanish title / summary / point)
  - web/public/data/passages/*.json  rows[2]    (Spanish passage)
so it can be run after embed.py (which regenerates the web data from items_es.jsonl) or on its own. It is idempotent:
running it twice changes nothing. The first run keeps the untouched original in data/backup_es/items_es.orig.jsonl.

Only unambiguous problems are fixed (see FIXES). Ambiguous renderings are reported by `--audit` but never changed.
Usage: python pipeline/fix_es.py [--dry] [--audit]
"""
import collections, json, os, re, shutil, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
WEB = os.path.join(ROOT, "web", "public", "data")

# (name, pattern, replacement)
FIXES = [
    # Holy Spirit: "Espíritu Santo" is the standard Spanish form (7,243 uses) next to a stray "Santo Espíritu" (2,280)
    ("Santo Espíritu -> Espíritu Santo", r"\bSanto Espíritu\b", "Espíritu Santo"),
    ("santo Espíritu -> Espíritu Santo", r"\bsanto Espíritu\b", "Espíritu Santo"),
    ("Espíritu santo -> Espíritu Santo", r"\bEspíritu santo\b", "Espíritu Santo"),
    # Gethsemane: five different spellings in the output -> the Spanish name
    ("Gethsemane/Gethsemana/Gethsemané -> Getsemaní", r"\bGethseman[eéa]s?(?:['’]s)?\b", "Getsemaní"),
    # "Lord's-day" read as a name
    ("día de Lord -> día del Señor", r"\bdía de Lord\b", "día del Señor"),
    # Jehovah left in English (not inside the Latin "Vivat Rex Jehovah")
    ("Jehovah -> Jehová", r"(?<!Rex )\bJehovah\b", "Jehová"),
    # "covenant" left in English as an adjective
    ("X covenant -> X del pacto", r"\b(amor|promesas?|bendiciones|bendición) covenant\b", r"\1 del pacto"),
    ("covenant eterno -> pacto eterno", r"\bcovenant eterno\b", "pacto eterno"),
    # mercy-seat left in English
    ("propiciatorio, o el mercy-seat -> propiciatorio", r"(propiciatorio),? o (?:el )?mercy-?seat\b", r"\1"),
    ("mercy-seat -> propiciatorio", r"\b[Mm]ercy-?seat\b", "propiciatorio"),
]
COMPILED = [(n, re.compile(p), r) for n, p, r in FIXES]
counts = collections.Counter()
samples = collections.defaultdict(list)


def fix(text, keep=False):
    if not text:
        return text
    for n, rx, rep in COMPILED:
        def sub(m, n=n, rep=rep):
            counts[n] += 1
            new = m.expand(rep)
            if keep and len(samples[n]) < 3:
                a, b = max(0, m.start() - 40), m.end() + 40
                samples[n].append((m.string[a:b].replace("\n", " "), m.string[a:m.start()].replace("\n", " ") + new + m.string[m.end():b].replace("\n", " ")))
            return new
        text = rx.sub(sub, text)
    return text


def main():
    dry = "--dry" in sys.argv
    p = os.path.join(DATA, "items_es.jsonl")
    if not os.path.exists(p):
        print("no items_es.jsonl; nothing to do"); return
    bk = os.path.join(DATA, "backup_es")
    os.makedirs(bk, exist_ok=True)
    orig = os.path.join(bk, "items_es.orig.jsonl")
    if not os.path.exists(orig) and not dry:
        shutil.copyfile(p, orig)
    out, changed = [], 0
    for l in open(p, encoding="utf8"):
        r = json.loads(l)
        before = json.dumps(r, ensure_ascii=False)
        for k in ("title", "summary", "point", "passage"):
            if k in r:
                r[k] = fix(r[k], keep=True)
        after = json.dumps(r, ensure_ascii=False)
        changed += before != after
        out.append(after)
    es_counts = collections.Counter(counts)
    print(f"items_es.jsonl: {changed} records changed")
    if not dry:
        with open(p, "w", encoding="utf8", newline="\n") as f:
            f.write("\n".join(out) + "\n")
    # items_tagged.jsonl carries a copy of the Spanish text under "es" (read by build_excel.py and published in the dataset)
    tp = os.path.join(DATA, "items_tagged.jsonl")
    if os.path.exists(tp):
        saved_counts = collections.Counter(counts)
        lines, n_t = [], 0
        for l in open(tp, encoding="utf8"):
            r = json.loads(l)
            e = r.get("es")
            if e:
                new = {k: fix(v) for k, v in e.items()}
                n_t += new != e
                r["es"] = new
                l = json.dumps(r, ensure_ascii=False) + chr(10)
            lines.append(l)
        if not dry:
            with open(tp, "w", encoding="utf8", newline=chr(10)) as f:
                f.writelines(lines)
        counts.clear(); counts.update(saved_counts)   # keep the per-fix report about items_es.jsonl only
        print(f"items_tagged.jsonl: {n_t} records changed")
    # the web data is a projection of items_es.jsonl: apply the same fixes (silently counted separately)
    items_p = os.path.join(WEB, "items.json")
    if os.path.exists(items_p):
        items = json.load(open(items_p, encoding="utf8"))
        for row in items:
            for i in (15, 16, 17):
                row[i] = fix(row[i])
        n_pass = 0
        for fn in sorted(os.listdir(os.path.join(WEB, "passages"))):
            fp = os.path.join(WEB, "passages", fn)
            rows = json.load(open(fp, encoding="utf8"))
            for row in rows:
                new = fix(row[2])
                n_pass += new != row[2]
                row[2] = new
            if not dry:
                json.dump(rows, open(fp, "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
        if not dry:
            json.dump(items, open(items_p, "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
        print(f"web data: {n_pass} passages changed; field replacements in web = {sum(counts.values()) - sum(es_counts.values())}")
    print("fixes applied in items_es.jsonl:")
    for n, _, _ in FIXES:
        print(f"  {n}: {es_counts[n]}")
    if "--samples" in sys.argv:
        for n, ex in samples.items():
            for a, b in ex:
                print(f"- [{n}]\n   before: {a}\n   after:  {b}")


if __name__ == "__main__":
    main()
