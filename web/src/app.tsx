import { useEffect, useMemo, useRef, useState } from "preact/hooks";
import type { Filters, ItemRow, Lang, Meta, PassageRow, SearchResult, WorkerOut } from "./types";
import { categoryName, dateEs, initialLang, kindName, point, rememberLang, strings, summary, title, topicName, type Strings } from "./i18n";
import { formatRef, showRef, bookName } from "./bible";
import data from "./bible-books.json";

const BASE = import.meta.env.BASE_URL;
const PAGE = 25;

// ---------- worker plumbing ----------
const worker = new Worker(new URL("./worker.ts", import.meta.url), { type: "module" });
let seq = 0;
const pending = new Map<number, (r: SearchResult) => void>();
const listeners = new Set<(m: WorkerOut) => void>();
worker.onmessage = (e: MessageEvent<WorkerOut>) => {
  const m = e.data;
  if (m.type === "result") { pending.get(m.seq)?.(m.result); pending.delete(m.seq); }
  listeners.forEach((l) => l(m));
};
worker.postMessage({ type: "init", base: BASE });
const ask = (msg: { type: "search"; q: string; filters: Filters } | { type: "similar"; index: number; filters: Filters }) =>
  new Promise<SearchResult>((res) => { const s = ++seq; pending.set(s, res); worker.postMessage({ ...msg, seq: s }); });

// ---------- passages (lazy, chunked) ----------
const passageChunks = new Map<number, Promise<PassageRow[]>>();
function passage(meta: Meta, index: number) {
  const c = Math.floor(index / meta.passage_chunk);
  if (!passageChunks.has(c)) passageChunks.set(c, fetch(`${BASE}data/passages/${c}.json?v=${encodeURIComponent(meta.version)}`).then((r) => r.json()));
  return passageChunks.get(c)!.then((rows) => rows[index % meta.passage_chunk]);
}

// ---------- url state ----------
interface UrlState { q: string; f: Filters; id?: string; like?: string; lang: Lang }
function readUrl(): Omit<UrlState, "lang"> {
  const p = new URLSearchParams(location.search);
  const num = (k: string) => (p.has(k) ? +p.get(k)! : undefined);
  return { q: p.get("q") ?? "", f: { topic: num("topic"), category: num("cat"), author: num("author"), kind: p.get("kind") ?? undefined, book: num("book") }, id: p.get("id") ?? undefined, like: p.get("like") ?? undefined };
}
function writeUrl(s: UrlState) {
  const p = new URLSearchParams();
  if (s.q) p.set("q", s.q);
  if (s.f.topic != null) p.set("topic", String(s.f.topic));
  if (s.f.category != null) p.set("cat", String(s.f.category));
  if (s.f.author != null) p.set("author", String(s.f.author));
  if (s.f.book != null) p.set("book", String(s.f.book));
  if (s.f.kind) p.set("kind", s.f.kind);
  if (s.like) p.set("like", s.like);
  if (s.id) p.set("id", s.id);
  if (s.lang === "es") p.set("lang", "es");
  const url = `${location.pathname}${p.toString() ? "?" + p : ""}`;
  if (url !== location.pathname + location.search) history.replaceState(null, "", url);
}

// ---------- citation (Turabian; sermon and book titles stay as published) ----------
export function citation(meta: Meta, it: ItemRow, lang: Lang = "en"): string {
  const au = meta.authors[it[7]];
  const bk = meta.books[it[8]];
  const es = lang === "es";
  const inn = es ? "en" : "in";
  if (it[9]) {
    const extra = [
      it[11] ? (es ? `sermón n.º ${it[11]}` : `sermon no. ${it[11]}`) : "",
      it[12] ? (es ? `predicado el ${dateEs(it[12])}` : `delivered ${it[12]}`) : "",
    ].filter(Boolean).join(", ");
    return extra ? `${au}, “${it[9]}” (${extra}), ${inn} ${bk.cite}, ${it[14]}.` : `${au}, “${it[9]},” ${inn} ${bk.cite}, ${it[14]}.`;
  }
  return `${au}, ${bk.cite}, ${it[14]}.`;
}

function useToast(): [string, (s: string) => void] {
  const [t, setT] = useState("");
  const timer = useRef<number>();
  return [t, (s: string) => { setT(s); clearTimeout(timer.current); timer.current = window.setTimeout(() => setT(""), 1800); }];
}

// ---------- my list (saved in this browser) ----------
const LIST_KEY = "spurgeon-list";
function loadList(): string[] { try { return JSON.parse(localStorage.getItem(LIST_KEY) || "[]"); } catch { return []; } }
let listIds: string[] = loadList();
const listSubs = new Set<() => void>();
function setList(next: string[]) {
  listIds = next;
  try { localStorage.setItem(LIST_KEY, JSON.stringify(next)); } catch { /* storage unavailable */ }
  listSubs.forEach((l) => l());
}
function useList(): string[] {
  const [, bump] = useState(0);
  useEffect(() => { const l = () => bump((x) => x + 1); listSubs.add(l); return () => { listSubs.delete(l); }; }, []);
  return listIds;
}
const toggleList = (id: string) => setList(listIds.includes(id) ? listIds.filter((x) => x !== id) : [...listIds, id]);

const esc = (t: string) => t.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
async function listEntries(meta: Meta, items: ItemRow[], idIndex: Map<string, number>, lang: Lang, T: Strings) {
  const out: { title: string; body: string; cite: string }[] = [];
  for (const id of listIds) {
    const i = idIndex.get(id);
    if (i == null) continue;
    const it = items[i];
    const p = await passage(meta, i);
    const es = lang === "es" && !!p?.[2];
    const body = es ? `${p[2]} (${T.translationNote})` : p?.[0] || summary(it, lang);
    out.push({ title: title(it, lang), body, cite: citation(meta, it, lang) });
  }
  return out;
}
const listHtml = (rows: { title: string; body: string; cite: string }[], heading: string) =>
  `<html><head><meta charset="utf-8"><title>${esc(heading)}</title><style>body{font-family:Georgia,serif;max-width:42em;margin:2em auto;line-height:1.5}h1{font-size:1.5em}h2{font-size:1.1em;margin-bottom:.2em}blockquote{margin:.3em 0 .3em 1em}p.c{font-size:.9em;color:#444}</style></head><body><h1>${esc(heading)}</h1>${
    rows.map((r, n) => `<h2>${n + 1}. ${esc(r.title)}</h2><blockquote>“${esc(r.body)}”</blockquote><p class="c">${esc(r.cite)}</p>`).join("")}</body></html>`;

/** the illustration of the day: the same for everyone on a given date */
function dayIndex(n: number): number {
  const d = new Date();
  const day = Math.floor(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()) / 86400000);
  return (day * 2654435761) % n;
}
const CHAPTERS = [50,40,27,36,34,24,21,4,31,24,22,25,29,36,10,13,10,42,150,31,12,8,66,52,5,48,12,14,3,9,1,4,7,3,3,3,2,14,4,28,16,24,21,28,16,16,13,6,6,4,4,5,3,6,4,3,1,13,5,5,3,5,1,1,1,22];

// ---------- components ----------
export function App() {
  const init = useMemo(readUrl, []);
  const [lang, setLang] = useState<Lang>(initialLang);
  const [modal, setModal] = useState<"help" | "support" | "list" | null>(null);
  const saved = useList();
  const [vectors, setVectors] = useState(false);
  const T = strings(lang);
  const [meta, setMeta] = useState<Meta | null>(null);
  const [items, setItems] = useState<ItemRow[]>([]);
  const [progress, setProgress] = useState<{ stage: string; pct: number }>({ stage: "Starting", pct: 0 });
  const [modelState, setModelState] = useState<"loading" | "ready" | "failed">("loading");
  const [q, setQ] = useState(init.q);
  const [f, setF] = useState<Filters>(init.f);
  const [like, setLike] = useState<string | undefined>(init.like);
  const [focusId, setFocusId] = useState<string | undefined>(init.id);
  const [res, setRes] = useState<SearchResult | null>(null);
  const [shown, setShown] = useState(PAGE);
  const [busy, setBusy] = useState(false);
  const [toast, showToast] = useToast();
  const idIndex = useMemo(() => new Map(items.map((it, i) => [it[0], i])), [items]);

  useEffect(() => { rememberLang(lang); document.title = T.brand; }, [lang]);

  useEffect(() => {
    const l = (m: WorkerOut) => {
      if (m.type === "progress") setProgress({ stage: m.stage, pct: m.pct });
      else if (m.type === "ready") { setMeta(m.meta); setItems(m.items); }
      else if (m.type === "model") setModelState(m.ready ? "ready" : "failed");
      else if (m.type === "vectors") setVectors(true);
    };
    listeners.add(l);
    return () => listeners.delete(l);
  }, []);

  useEffect(() => { if (meta) writeUrl({ q, f, like, id: focusId, lang }); }, [lang]);

  // run the search (debounced on typing)
  useEffect(() => {
    if (!meta) return;
    writeUrl({ q, f, like, id: focusId, lang });
    let live = true;
    const t = setTimeout(async () => {
      setBusy(true);
      const likeIdx = like ? idIndex.get(like) : undefined;
      const r = likeIdx != null ? await ask({ type: "similar", index: likeIdx, filters: f }) : await ask({ type: "search", q, filters: f });
      if (live) { setRes(r); setShown(PAGE); setBusy(false); }
    }, q ? 280 : 0);
    return () => { live = false; clearTimeout(t); };
  }, [meta, q, f, like, modelState, vectors]);

  if (!meta) return <Loading progress={progress} T={T} lang={lang} setLang={setLang} />;

  const set = (patch: Partial<Filters>) => { setLike(undefined); setFocusId(undefined); setF({ ...f, ...patch }); };
  const focus = focusId != null ? idIndex.get(focusId) : undefined;
  const filtered = f.topic != null || f.category != null || f.author != null || f.book != null || !!f.kind;
  const solo = focus != null && !q && !filtered && !like;
  const browsing = !solo && !q && !filtered && !like;
  const openItem = (i: number) => { setLike(undefined); setQ(""); setF({}); setFocusId(items[i][0]); window.scrollTo({ top: 0 }); };
  const ids = res?.ids ?? [];
  const refShown = res?.refObj ? formatRef(res.refObj, lang) : res?.ref ?? "";

  return (
    <div class="page">
      <header class="masthead">
        <div class="brand-row">
          <a class="brand" href={`${BASE}${lang === "es" ? "?lang=es" : ""}`}>{T.brand}</a>
          <div class="top-actions">
            <button class="top-btn" onClick={() => setModal("list")}>★ {T.myList}{saved.length ? ` (${saved.length})` : ""}</button>
            <button class="top-btn" onClick={() => setModal("help")}>{T.howTo}</button>
            <button class="top-btn donate" onClick={() => setModal("support")}>♥ {T.support}</button>
            <LangSwitch lang={lang} setLang={setLang} />
          </div>
        </div>
        <p class="tagline">{T.tagline(meta.count.toLocaleString(lang))}</p>
      </header>

      <div class="searchbar" role="search">
        <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7" /><path d="m20 20-4-4" /></svg>
        <input
          value={q} autoFocus aria-label={T.searchLabel}
          placeholder={T.placeholder}
          onInput={(e) => { setLike(undefined); setFocusId(undefined); setQ((e.target as HTMLInputElement).value); }}
        />
        {q && <button class="clear" aria-label={T.clear} onClick={() => { setFocusId(undefined); setQ(""); }}>×</button>}
      </div>
      <div class="status">
        {modelState === "loading" && <span>{T.modelLoading}</span>}
        {modelState === "ready" && !vectors && <span>{T.vectorsLoading}</span>}
        {modelState === "failed" && <span>{T.modelFailed}</span>}
      </div>

      <FilterBar meta={meta} f={f} set={set} T={T} lang={lang} />

      {solo ? (
        <section class="results">
          <div class="summary-line"><a href="#" onClick={(e) => { e.preventDefault(); setFocusId(undefined); }}>← {T.backToBrowse}</a></div>
          <Card meta={meta} it={items[focus!]} index={focus!} T={T} lang={lang} setTopic={(t) => set({ topic: t })} onLike={(id) => { setFocusId(undefined); setLike(id); }} toast={showToast} open />
        </section>
      ) : browsing ? (
        <Browse meta={meta} items={items} T={T} lang={lang} pick={(t) => set({ topic: t, category: undefined })} example={(s) => setQ(s)} openItem={openItem} />
      ) : (
        <section class="results" aria-busy={busy}>
          <div class="summary-line">
            {like != null && <span>{T.similarTo} <b>{idIndex.has(like) ? title(items[idIndex.get(like)!], lang) : ""}</b> · <a href="#" onClick={(e) => { e.preventDefault(); setLike(undefined); }}>{T.back}</a></span>}
            {res?.mode === "scripture" && <span>{T.tiedTo(refShown)}</span>}
            {res && <span class="count">{ids.length >= 500 ? "500+" : ids.length.toLocaleString(lang)} {res.mode === "semantic" ? T.bestMatches : T.illustrations}</span>}
          </div>
          {res && res.related.length > 0 && (
            <div class="related">
              <span>{T.relatedTopics}</span>
              {res.related.map(([t]) => <button class="chip" onClick={() => set({ topic: t })}>{topicName(meta, t, lang)}</button>)}
            </div>
          )}
          {ids.slice(0, shown).map((i) => (
            <Card key={items[i][0]} meta={meta} it={items[i]} index={i} T={T} lang={lang} setTopic={(t) => set({ topic: t })} onLike={(id) => { setLike(id); setQ(""); window.scrollTo({ top: 0 }); }} toast={showToast} />
          ))}
          {res && ids.length === 0 && <p class="empty">{T.noMatch}</p>}
          {shown < ids.length && <button class="more" onClick={() => setShown(shown + PAGE)}>{T.showMore}</button>}
        </section>
      )}

      <footer>
        <p>{T.footer(meta.version)}</p>
      </footer>
      {toast && <div class="toast" role="status">{toast}</div>}
      {modal && modal !== "list" && <InfoModal kind={modal} T={T} close={() => setModal(null)} />}
      {modal === "list" && <ListModal meta={meta} items={items} idIndex={idIndex} T={T} lang={lang} close={() => setModal(null)} toast={showToast} />}
    </div>
  );
}

const VENMO = "https://venmo.com/u/garridolecca";
const PAYPAL = "https://paypal.me/cgarridolecca";
const EMAIL = "garridolecca.rivera@gmail.com";

function InfoModal({ kind, T, close }: { kind: "help" | "support"; T: Strings; close: () => void }) {
  useEffect(() => {
    const k = (e: KeyboardEvent) => { if (e.key === "Escape") close(); };
    window.addEventListener("keydown", k);
    return () => window.removeEventListener("keydown", k);
  }, []);
  const contact = <p class="help-contact">{T.donateEmailLabel} <a href={`mailto:${EMAIL}`}>{EMAIL}</a></p>;
  return (
    <div class="modal-overlay" onClick={(e) => { if (e.target === e.currentTarget) close(); }}>
      <div class="modal" role="dialog" aria-modal="true" aria-labelledby="modal-title">
        <div class="modal-head">
          <h2 id="modal-title">{kind === "help" ? T.helpTitle : T.donateTitle}</h2>
          <button class="modal-close" aria-label={T.close} onClick={close}>×</button>
        </div>
        {kind === "help" ? (
          <div class="modal-body">
            <ol class="help-list">{T.help.map(([h, d]) => <li><b>{h}.</b> {d}</li>)}</ol>
            <p class="help-check">{T.helpCheck}</p>
            {contact}
          </div>
        ) : (
          <div class="modal-body">
            <p>{T.donateText}</p>
            <div class="donate-buttons">
              <a class="donate-btn venmo" href={VENMO} target="_blank" rel="noopener">{T.donateButton} via Venmo</a>
              <a class="donate-btn paypal" href={PAYPAL} target="_blank" rel="noopener">{T.donateButton} via PayPal</a>
            </div>
            <p class="donate-qr-label">{T.donateQr}</p>
            <img class="donate-qr" width="150" height="150" alt="Venmo QR code"
              src={`https://api.qrserver.com/v1/create-qr-code/?size=180x180&data=${encodeURIComponent(VENMO)}`} />
            <hr />
            {contact}
          </div>
        )}
      </div>
    </div>
  );
}

function ListModal({ meta, items, idIndex, T, lang, close, toast }: {
  meta: Meta; items: ItemRow[]; idIndex: Map<string, number>; T: Strings; lang: Lang; close: () => void; toast: (s: string) => void;
}) {
  const ids = useList();
  useEffect(() => {
    const k = (e: KeyboardEvent) => { if (e.key === "Escape") close(); };
    window.addEventListener("keydown", k);
    return () => window.removeEventListener("keydown", k);
  }, []);
  const rows = ids.map((id) => idIndex.get(id)).filter((i): i is number => i != null);
  const copyAll = async () => {
    const e = await listEntries(meta, items, idIndex, lang, T);
    await navigator.clipboard.writeText(e.map((r, n) => `${n + 1}. ${r.title}\n\n“${r.body}”\n\n${r.cite}`).join("\n\n---\n\n"));
    toast(T.copied(T.wIllustration));
  };
  const print = async () => {
    const w = window.open("", "_blank");
    if (!w) return;
    w.document.write(listHtml(await listEntries(meta, items, idIndex, lang, T), T.listTitle));
    w.document.close(); w.focus(); w.print();
  };
  const word = async () => {
    const html = listHtml(await listEntries(meta, items, idIndex, lang, T), T.listTitle);
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob(["\ufeff", html], { type: "application/msword" }));
    a.download = "sermon-illustrations.doc";
    a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 2000);
  };
  return (
    <div class="modal-overlay" onClick={(e) => { if (e.target === e.currentTarget) close(); }}>
      <div class="modal" role="dialog" aria-modal="true" aria-labelledby="list-title">
        <div class="modal-head">
          <h2 id="list-title">{T.listTitle} ({rows.length})</h2>
          <button class="modal-close" aria-label={T.close} onClick={close}>×</button>
        </div>
        <div class="modal-body">
          {rows.length === 0 ? <p>{T.listEmpty}</p> : (
            <>
              <ol class="list-items">
                {rows.map((i) => (
                  <li><b>{title(items[i], lang)}</b><br /><small>{citation(meta, items[i], lang)}</small>
                    <button class="link" onClick={() => toggleList(items[i][0])}>{T.removeFromList}</button></li>
                ))}
              </ol>
              <div class="actions">
                <button onClick={copyAll}>{T.copyAll}</button>
                <button onClick={print}>{T.printList}</button>
                <button onClick={word}>{T.downloadWord}</button>
                <button onClick={() => setList([])}>{T.clearList}</button>
              </div>
            </>
          )}
          <p class="help-check">{T.listNote}</p>
        </div>
      </div>
    </div>
  );
}

function LangSwitch({ lang, setLang }: { lang: Lang; setLang: (l: Lang) => void }) {
  return (
    <div class="lang" role="group" aria-label="Language / Idioma">
      {(["en", "es"] as const).map((l) => (
        <button class={lang === l ? "on" : ""} aria-pressed={lang === l} lang={l} title={strings(l).langName} onClick={() => setLang(l)}>{l.toUpperCase()}</button>
      ))}
    </div>
  );
}

function Loading({ progress, T, lang, setLang }: { progress: { stage: string; pct: number }; T: Strings; lang: Lang; setLang: (l: Lang) => void }) {
  return (
    <div class="page loading">
      <header class="masthead"><div class="brand-row"><span class="brand">{T.brand}</span><LangSwitch lang={lang} setLang={setLang} /></div></header>
      <p>{T.stages[progress.stage] ?? progress.stage}…</p>
      <div class="bar"><div style={{ width: `${Math.max(3, progress.pct)}%` }} /></div>
      <p class="hint">{T.loadingHint}</p>
    </div>
  );
}

function FilterBar({ meta, f, set, T, lang }: { meta: Meta; f: Filters; set: (p: Partial<Filters>) => void; T: Strings; lang: Lang }) {
  const topicsInCat = useMemo(
    () => meta.topics.map((t, i) => [i, t] as const).filter(([, t]) => f.category == null || t[1] === f.category)
      .sort((a, b) => topicName(meta, a[0], lang).localeCompare(topicName(meta, b[0], lang), lang)),
    [meta, f.category, lang],
  );
  const authors = useMemo(() => meta.authors.map((a, i) => [i, a] as const).sort((a, b) => a[1].localeCompare(b[1])), [meta]);
  const any = f.topic != null || f.category != null || f.author != null || f.book != null || f.kind;
  return (
    <div class="filters">
      <label>{T.category}
        <select value={f.category ?? ""} onChange={(e) => { const v = (e.target as HTMLSelectElement).value; set({ category: v === "" ? undefined : +v, topic: undefined }); }}>
          <option value="">{T.all}</option>
          {meta.categories.map((_, i) => <option value={i}>{categoryName(meta, i, lang)}</option>)}
        </select>
      </label>
      <label>{T.topic}
        <select value={f.topic ?? ""} onChange={(e) => { const v = (e.target as HTMLSelectElement).value; set({ topic: v === "" ? undefined : +v }); }}>
          <option value="">{T.all}</option>
          {topicsInCat.map(([i, t]) => <option value={i}>{topicName(meta, i, lang)} ({t[2]})</option>)}
        </select>
      </label>
      <label>{T.author}
        <select value={f.author ?? ""} onChange={(e) => { const v = (e.target as HTMLSelectElement).value; set({ author: v === "" ? undefined : +v }); }}>
          <option value="">{T.all}</option>
          {authors.map(([i, a]) => <option value={i}>{a}</option>)}
        </select>
      </label>
      <div class="kinds" role="group" aria-label={T.kind}>
        {meta.kinds.map((k) => <button class={`chip ${f.kind === k ? "on" : ""}`} aria-pressed={f.kind === k} onClick={() => set({ kind: f.kind === k ? undefined : k })}>{kindName(meta, k, lang)}</button>)}
      </div>
      {f.book != null && <span class="chip on" onClick={() => set({ book: undefined })}>{meta.books[f.book].title} ×</span>}
      {any && <button class="link" onClick={() => set({ topic: undefined, category: undefined, author: undefined, book: undefined, kind: undefined })}>{T.clearFilters}</button>}
    </div>
  );
}

function Browse({ meta, items, T, lang, pick, example, openItem }: { meta: Meta; items: ItemRow[]; T: Strings; lang: Lang; pick: (t: number) => void; example: (s: string) => void; openItem: (i: number) => void }) {
  const byCat = useMemo(() => {
    const m = meta.categories.map(() => [] as number[]);
    meta.topics.forEach((t, i) => m[t[1]].push(i));
    m.forEach((l) => l.sort((a, b) => meta.topics[b][2] - meta.topics[a][2]));
    return m;
  }, [meta]);
  const [open, setOpen] = useState<number | null>(null);
  const [bk, setBk] = useState(0);
  const [ch, setCh] = useState(0);
  const day = items.length ? dayIndex(items.length) : -1;
  return (
    <section class="browse">
      {day >= 0 && (
        <div class="daily">
          <h2>{T.dayTitle}</h2>
          <p><b>{title(items[day], lang)}</b> — {summary(items[day], lang)}</p>
          <div class="actions">
            <button onClick={() => openItem(day)}>{T.openIt}</button>
            <button onClick={() => openItem(Math.floor(Math.random() * items.length))}>🎲 {T.random}</button>
          </div>
        </div>
      )}
      <div class="bible-browse">
        <h2>{T.byBible}</h2>
        <select aria-label={T.book} value={bk} onChange={(e) => { setBk(+(e.target as HTMLSelectElement).value); setCh(0); }}>
          <option value={0}>{T.book}…</option>
          {data.books.map((_, i) => <option value={i + 1}>{lang === "es" ? data.books_es[i] : bookName(i + 1)}</option>)}
        </select>
        {bk > 0 && (
          <select aria-label={T.chapter} value={ch} onChange={(e) => setCh(+(e.target as HTMLSelectElement).value)}>
            <option value={0}>{T.wholeBook}</option>
            {Array.from({ length: CHAPTERS[bk - 1] }, (_, i) => <option value={i + 1}>{T.chapter} {i + 1}</option>)}
          </select>
        )}
        {bk > 0 && <button class="chip on" onClick={() => example(`${lang === "es" ? (bk === 19 && ch ? "Salmo" : data.books_es[bk - 1]) : (bk === 19 && ch ? "Psalm" : bookName(bk))}${ch ? " " + ch : ""}`)}>{T.go}</button>}
      </div>
      <div class="examples"><span>{T.tryLabel}</span>{T.examples.map((s) => <button class="chip" onClick={() => example(s)}>{s}</button>)}</div>
      <h2>{T.browseTitle}</h2>
      <div class="cats">
        {meta.categories.map((_, ci) => {
          const list = byCat[ci];
          if (!list.length) return null;
          const total = list.reduce((s, t) => s + meta.topics[t][2], 0);
          const show = open === ci ? list : list.slice(0, 9);
          return (
            <div class="cat">
              <h3>{categoryName(meta, ci, lang)} <small>{total.toLocaleString(lang)}</small></h3>
              <div class="chips">
                {show.map((t) => <button class="chip" onClick={() => pick(t)}>{topicName(meta, t, lang)} <small>{meta.topics[t][2]}</small></button>)}
                {list.length > 9 && <button class="link" onClick={() => setOpen(open === ci ? null : ci)}>{open === ci ? T.fewer : T.more(list.length - 9)}</button>}
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}

function Card({ meta, it, index, T, lang, setTopic, onLike, toast, open: startOpen = false }: {
  meta: Meta; it: ItemRow; index: number; T: Strings; lang: Lang; setTopic: (t: number) => void; onLike: (id: string) => void; toast: (s: string) => void; open?: boolean;
}) {
  const saved = useList();
  const [open, setOpen] = useState(startOpen);
  const [text, setText] = useState<PassageRow | null>(null);
  const [english, setEnglish] = useState(false);   // Spanish readers can switch the passage to the English original
  useEffect(() => { if (open && !text) passage(meta, index).then(setText); }, [open]);
  const bk = meta.books[it[8]];
  const cite = citation(meta, it, lang);
  const copy = async (s: string, what: string) => { await navigator.clipboard.writeText(s); toast(T.copied(what)); };
  const translated = (p: PassageRow | null) => lang === "es" && !!p?.[2];
  const full = async () => {
    const p = text ?? (await passage(meta, index));
    const body = translated(p) && !english ? `“${p[2]}”\n(${T.translationNote})` : p[0] ? `“${p[0]}”` : summary(it, lang);
    copy(`${title(it, lang)}\n\n${body}\n\n${cite}`, T.wIllustration);
  };
  const permalink = `${location.origin}${BASE}?id=${it[0]}${lang === "es" ? "&lang=es" : ""}`;
  const showEs = translated(text) && !english;
  return (
    <article class="card">
      <div class="card-head">
        <h3>{title(it, lang)}</h3>
        <span class={`kind k-${it[2].toLowerCase()}`}>{kindName(meta, it[2], lang)}</span>
      </div>
      <p class="sum">{summary(it, lang)}</p>
      {point(it, lang) && <p class="point"><span>{T.illustrates}</span> {point(it, lang)}</p>}
      <div class="chips">
        {it[5].map((t) => <button class="chip small" onClick={() => setTopic(t)}>{topicName(meta, t, lang)}</button>)}
        {it[6].map((s) => <span class="chip small scripture">{showRef(s, lang)}</span>)}
      </div>
      <p class="source">
        <b>{meta.authors[it[7]]}</b>
        {it[9] && <> · “{it[9]}”{it[11] ? ` (${lang === "es" ? "n.º" : "No."} ${it[11]})` : ""}</>}
        {it[10] && <> · {it[10]}</>}
        {it[12] && <> · {lang === "es" ? dateEs(it[12]) : it[12]}</>}
        {it[13] && <> · {T.text}: {showRef(it[13], lang)}</>}
        <br /><i>{bk.title}</i>, {T.page} {it[14]}
      </p>
      {open && (
        <blockquote class="passage" lang={showEs ? "es" : "en"}>
          {text ? (text[0]
            ? <>
                “{showEs ? text[2] : text[0]}”
                {text[1] === "a" && <small>{T.nearest}</small>}
                {translated(text) && (
                  <small class="translation-note">
                    {showEs && <>{T.translationNote} </>}
                    <a href="#" onClick={(e) => { e.preventDefault(); setEnglish(!english); }}>{english ? T.showSpanish : T.showEnglish}</a>
                  </small>
                )}
              </>
            : <small>{T.noPassage}</small>) : <small>{T.loading}</small>}
        </blockquote>
      )}
      <div class="actions">
        <button onClick={() => setOpen(!open)}>{open ? T.hideOriginal : T.readOriginal}</button>
        <button onClick={() => copy(cite, T.wCitation)}>{T.copyCitation}</button>
        <button onClick={full}>{T.copyForSermon}</button>
        <button onClick={() => onLike(it[0])}>{T.moreLike}</button>
        <button class={saved.includes(it[0]) ? "starred" : ""} aria-pressed={saved.includes(it[0])} onClick={() => toggleList(it[0])}>{saved.includes(it[0]) ? "★ " + T.inList : "☆ " + T.addToList}</button>
        <button onClick={() => copy(permalink, T.wLink)}>{T.link}</button>
        {bk.rid && <a href={`https://app.logos.com/books/${encodeURIComponent(bk.rid)}`} target="_blank" rel="noopener">{T.openLogos}</a>}
      </div>
    </article>
  );
}
