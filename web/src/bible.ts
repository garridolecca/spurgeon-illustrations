import data from "./bible-books.json";

export interface Ref { book: number; ch: number; v1: number; v2: number } // v1 = 0: whole chapter; ch = 0: whole book

const ALIAS = data.alias as Record<string, number>;
const NAMES = Object.keys(ALIAS).sort((a, b) => b.length - a.length);
const esc = (s: string) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&").replace(/ /g, "\\s+");
const QUERY_RE = new RegExp(
  `^\\s*(${NAMES.map(esc).join("|")})\\.?(?:\\s+(\\d{1,3})(?:[:.](\\d{1,3})(?:\\s*[-–—]\\s*(\\d{1,3}))?)?)?\\s*$`, "i");
const CANON_RE = /^(.+?) (\d+)(?::(\d+)(?:–(\d+))?)?$/;

export const bookName = (n: number) => data.books[n - 1];

/** "Rom 8:28-30" / "Psalm 23" / "Hebrews" -> Ref, when the whole query is a Bible reference. */
export function parseQuery(q: string): Ref | null {
  const m = QUERY_RE.exec(q);
  if (!m) return null;
  const book = ALIAS[m[1].toLowerCase().replace(/\s+/g, " ")];
  if (!book) return null;
  const ch = m[2] ? +m[2] : 0;
  const v1 = m[3] ? +m[3] : 0;
  return { book, ch, v1, v2: m[4] ? +m[4] : v1 };
}

/** Canonical strings written by the pipeline ("Romans 8:28–30", "Psalms 23") -> Ref. */
export function parseCanon(s: string): Ref | null {
  const m = CANON_RE.exec(s);
  if (!m) return null;
  const book = ALIAS[m[1].toLowerCase()];
  if (!book) return null;
  const v1 = m[3] ? +m[3] : 0;
  return { book, ch: +m[2], v1, v2: m[4] ? +m[4] : v1 };
}

export function formatRef(r: Ref): string {
  return `${r.book === 19 && r.ch ? "Psalm" : bookName(r.book)}${r.ch ? " " + r.ch : ""}${r.v1 ? ":" + r.v1 + (r.v2 !== r.v1 ? "–" + r.v2 : "") : ""}`;
}

/** 3 = verses overlap, 2 = same chapter (or whole chapter asked), 1 = same book, 0 = no match. */
export function refMatch(q: Ref, r: Ref): number {
  if (q.book !== r.book) return 0;
  if (!q.ch) return 2;
  if (q.ch !== r.ch) return 1;
  if (!q.v1 || !r.v1) return 2;
  return r.v1 <= q.v2 && q.v1 <= r.v2 ? 3 : 2;
}
