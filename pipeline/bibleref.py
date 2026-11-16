"""Find and parse Bible references ("Rom 8:28–30", "1 Cor. 13:13; 15:3", "Ps 23") in English text."""
import re

BOOKS = [  # canonical name, then aliases (abbreviations without the trailing period)
    ("Genesis", "Gen Ge Gn"), ("Exodus", "Exod Exo Ex"), ("Leviticus", "Lev Le Lv"),
    ("Numbers", "Num Nu Nm Nb"), ("Deuteronomy", "Deut Dt De"), ("Joshua", "Josh Jos Jsh"),
    ("Judges", "Judg Jdg Jg Jdgs"), ("Ruth", "Ru Rth"), ("1 Samuel", "1 Sam 1 Sa 1Sm"),
    ("2 Samuel", "2 Sam 2 Sa 2Sm"), ("1 Kings", "1 Kgs 1 Ki 1 Kin"), ("2 Kings", "2 Kgs 2 Ki 2 Kin"),
    ("1 Chronicles", "1 Chr 1 Chron 1 Ch"), ("2 Chronicles", "2 Chr 2 Chron 2 Ch"), ("Ezra", "Ezr"),
    ("Nehemiah", "Neh Ne"), ("Esther", "Esth Est Es"), ("Job", "Jb"), ("Psalms", "Ps Psa Pss Pslm"),
    ("Proverbs", "Prov Pro Prv Pr"), ("Ecclesiastes", "Eccl Eccles Ecc Qoh"),
    ("Song of Songs", "Song of Solomon Song Cant SS Sos"), ("Isaiah", "Isa Is"), ("Jeremiah", "Jer Je Jr"),
    ("Lamentations", "Lam La"), ("Ezekiel", "Ezek Eze Ezk"), ("Daniel", "Dan Da Dn"), ("Hosea", "Hos Ho"),
    ("Joel", "Joe Jl"), ("Amos", "Am"), ("Obadiah", "Obad Ob"), ("Jonah", "Jon Jnh"), ("Micah", "Mic Mi"),
    ("Nahum", "Nah Na"), ("Habakkuk", "Hab Hb"), ("Zephaniah", "Zeph Zep Zp"), ("Haggai", "Hag Hg"),
    ("Zechariah", "Zech Zec Zc"), ("Malachi", "Mal Ml"), ("Matthew", "Matt Mt"), ("Mark", "Mk Mrk"),
    ("Luke", "Lk Luk"), ("John", "Jn Jhn"), ("Acts", "Ac Act"), ("Romans", "Rom Ro Rm"),
    ("1 Corinthians", "1 Cor 1 Co"), ("2 Corinthians", "2 Cor 2 Co"), ("Galatians", "Gal Ga"),
    ("Ephesians", "Eph Ephes"), ("Philippians", "Phil Php Pp"), ("Colossians", "Col Co"),
    ("1 Thessalonians", "1 Thess 1 Th 1 Thes"), ("2 Thessalonians", "2 Thess 2 Th 2 Thes"),
    ("1 Timothy", "1 Tim 1 Ti"), ("2 Timothy", "2 Tim 2 Ti"), ("Titus", "Tit Ti"),
    ("Philemon", "Phlm Philem Phm"), ("Hebrews", "Heb He"), ("James", "Jas Jm"),
    ("1 Peter", "1 Pet 1 Pe 1 Pt"), ("2 Peter", "2 Pet 2 Pe 2 Pt"), ("1 John", "1 Jn 1 Jo 1 Jhn"),
    ("2 John", "2 Jn 2 Jo"), ("3 John", "3 Jn 3 Jo"), ("Jude", "Jud Jd"), ("Revelation", "Rev Re Rv Apoc"),
]
ROMAN = {"1": ["1", "I", "1st", "First"], "2": ["2", "II", "2nd", "Second"], "3": ["3", "III", "3rd", "Third"]}

NAME = {}  # lowercased alias (single spaces) -> (book number, is_full_name)
for num, (full, aliases) in enumerate(BOOKS, 1):
    names = [(full, True)] + ([("Psalm", True)] if full == "Psalms" else [])
    rest = aliases.split()
    i = 0
    while i < len(rest):  # re-join "1 Sam" style aliases split by the space
        if rest[i] in ("1", "2", "3") and i + 1 < len(rest):
            names.append((rest[i] + " " + rest[i + 1], False)); i += 2
        elif full.startswith("Song") and rest[i] == "Song" and rest[i + 1:i + 3] == ["of", "Solomon"]:
            names.append(("Song of Solomon", True)); i += 3
        else:
            names.append((rest[i], False)); i += 1
    for name, is_full in names:
        m = re.match(r"([123]) ?(.+)", name)
        variants = [p + " " + m.group(2) for p in ROMAN[m.group(1)]] + [m.group(1) + m.group(2)] if m else [name]
        for v in variants:
            NAME.setdefault(v.lower(), (num, is_full))

_alts = sorted(NAME, key=len, reverse=True)
_book_re = "|".join(re.escape(a).replace(r"\ ", r"\s+") for a in _alts)
# book, optional ".", chapter, optional :verse[-verse], then continuation list ("; 9:1", ", 30")
REF = re.compile(rf"\b({_book_re})\.?\s+(\d{{1,3}})(?:[:.](\d{{1,3}})(?:\s*[-–—]\s*(\d{{1,3}}))?)?"
                 rf"((?:\s*[,;]\s*\d{{1,3}}(?:[:.]\d{{1,3}})?(?:\s*[-–—]\s*\d{{1,3}})?(?!\s*(?:Sam|Sa|Sm|Samuel|Kgs|Ki|Kin|Kings|Chr|Chron|Ch|Chronicles|Cor|Co|Corinthians|Thess|Th|Thes|Thessalonians|Tim|Ti|Timothy|Pet|Pe|Pt|Peter|Jn|Jo|Jhn|John)\b))*)", re.I)
CONT = re.compile(r"([,;])\s*(\d{1,3})(?:[:.](\d{1,3}))?(?:\s*[-–—]\s*(\d{1,3}))?")


def _book(name):
    return NAME.get(re.sub(r"\s+", " ", name.lower()))


def find_refs(text):
    """[(book, chapter, verse_from, verse_to)] for references in text; verse 0 = whole chapter.
    Abbreviations need chapter:verse (so "Am 3" or "Is 5" in prose isn't taken as a reference)."""
    out = []
    for m in REF.finditer(text):
        b = _book(m.group(1))
        if not b:
            continue
        num, full = b
        ch, v1, v2 = int(m.group(2)), m.group(3), m.group(4)
        if v1 is None and not full:
            continue
        v1 = int(v1) if v1 else 0
        out.append((num, ch, v1, int(v2) if v2 else v1))
        for c in CONT.finditer(m.group(5) or ""):
            sep, a, b2, c2 = c.groups()
            if b2:  # "; 9:1"
                ch = int(a); out.append((num, ch, int(b2), int(c2) if c2 else int(b2)))
            elif v1:  # ", 30" = another verse in the same chapter
                out.append((num, ch, int(a), int(c2) if c2 else int(a)))
            else:  # ", 9" after a chapter-only ref = another chapter
                ch = int(a); out.append((num, ch, 0, 0))
    return out


def parse_query(q):
    """'Romans 8:28-30' -> (book, chapter, v1, v2) or None; v1 = 0 for a whole chapter."""
    m = re.match(rf"\s*({_book_re})\.?\s+(\d{{1,3}})(?:[:.](\d{{1,3}})(?:\s*[-–—]\s*(\d{{1,3}}))?)?\s*$", q, re.I)
    if not m or not _book(m.group(1)):
        return None
    v1 = int(m.group(3)) if m.group(3) else 0
    return _book(m.group(1))[0], int(m.group(2)), v1, int(m.group(4)) if m.group(4) else v1


def book_name(num):
    return BOOKS[num - 1][0]


if __name__ == "__main__":
    s = ("See Rom. 8:28–30; 9:1, 5 and 1 Cor 13:13. Cf. Ps 23 and Psalm 23; I Cor. 15:3; Is 5 is prose; "
         "Isa 53:5; Am 3; Amos 3:7; Gen 1:1-2; John 3:16; 2 Tim. 2:8–13")
    for r in find_refs(s):
        print(book_name(r[0]), r[1:], end=" | ")
    print("\n", parse_query("Romans 8:28-30"), parse_query("1 Cor 13"), parse_query("Ps 23"))
