import { useEffect, useMemo, useRef, useState } from "preact/hooks";
import type { Filters, ItemRow, Meta, SearchResult, WorkerOut } from "./types";

const BASE = import.meta.env.BASE_URL;
const PAGE = 25;
const EXAMPLES = ["the love of God", "compassion for sinners", "God's faithfulness in trials", "the danger of delay", "Romans 8:28", "Psalm 23", "pride before a fall", "assurance of salvation"];

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
const passageChunks = new Map<number, Promise<[string, string][]>>();
function passage(meta: Meta, index: number) {
  const c = Math.floor(index / meta.passage_chunk);
  if (!passageChunks.has(c)) passageChunks.set(c, fetch(`${BASE}data/passages/${c}.json?v=${encodeURIComponent(meta.version)}`).then((r) => r.json()));
  return passageChunks.get(c)!.then((rows) => rows[index % meta.passage_chunk]);
}

// ---------- url state ----------
interface UrlState { q: string; f: Filters; id?: string; like?: string }
function readUrl(): UrlState {
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
  const url = `${location.pathname}${p.toString() ? "?" + p : ""}`;
  if (url !== location.pathname + location.search) history.replaceState(null, "", url);
}

// ---------- citation ----------
export function citation(meta: Meta, it: ItemRow): string {
  const au = meta.authors[it[7]];
  const bk = meta.books[it[8]];
  if (it[9]) {
    const extra = [it[11] ? `sermon no. ${it[11]}` : "", it[12] ? `delivered ${it[12]}` : ""].filter(Boolean).join(", ");
    return extra ? `${au}, “${it[9]}” (${extra}), in ${bk.cite}, ${it[14]}.` : `${au}, “${it[9]},” in ${bk.cite}, ${it[14]}.`;
  }
  return `${au}, ${bk.cite}, ${it[14]}.`;
}

function useToast(): [string, (s: string) => void] {
  const [t, setT] = useState("");
  const timer = useRef<number>();
  return [t, (s: string) => { setT(s); clearTimeout(timer.current); timer.current = window.setTimeout(() => setT(""), 1800); }];
}

// ---------- components ----------
export function App() {
  const init = useMemo(readUrl, []);
  const [meta, setMeta] = useState<Meta | null>(null);
  const [items, setItems] = useState<ItemRow[]>([]);
  const [progress, setProgress] = useState<{ stage: string; pct: number }>({ stage: "Starting", pct: 0 });
  const [modelState, setModelState] = useState<"loading" | "ready" | "failed">("loading");
  const [q, setQ] = useState(init.q);
  const [f, setF] = useState<Filters>(init.f);
  const [like, setLike] = useState<string | undefined>(init.like);
  const [focusId] = useState<string | undefined>(init.id);
  const [res, setRes] = useState<SearchResult | null>(null);
  const [shown, setShown] = useState(PAGE);
  const [busy, setBusy] = useState(false);
  const [toast, showToast] = useToast();
  const idIndex = useMemo(() => new Map(items.map((it, i) => [it[0], i])), [items]);

  useEffect(() => {
    const l = (m: WorkerOut) => {
      if (m.type === "progress") setProgress({ stage: m.stage, pct: m.pct });
      else if (m.type === "ready") { setMeta(m.meta); setItems(m.items); }
      else if (m.type === "model") setModelState(m.ready ? "ready" : "failed");
    };
    listeners.add(l);
    return () => listeners.delete(l);
  }, []);

  // run the search (debounced on typing)
  useEffect(() => {
    if (!meta) return;
    writeUrl({ q, f, like, id: focusId });
    let live = true;
    const t = setTimeout(async () => {
      setBusy(true);
      const likeIdx = like ? idIndex.get(like) : undefined;
      const r = likeIdx != null ? await ask({ type: "similar", index: likeIdx, filters: f }) : await ask({ type: "search", q, filters: f });
      if (live) { setRes(r); setShown(PAGE); setBusy(false); }
    }, q ? 280 : 0);
    return () => { live = false; clearTimeout(t); };
  }, [meta, q, f, like, modelState]);

  if (!meta) return <Loading progress={progress} />;

  const set = (patch: Partial<Filters>) => { setLike(undefined); setF({ ...f, ...patch }); };
  const browsing = !q && f.topic == null && f.category == null && f.author == null && f.book == null && !f.kind && !like;
  const focus = focusId != null ? idIndex.get(focusId) : undefined;
  const ids = res?.ids ?? [];

  return (
    <div class="page">
      <header class="masthead">
        <a class="brand" href={BASE}>Spurgeon Illustrations</a>
        <p class="tagline">Search {meta.count.toLocaleString()} sermon illustrations from C. H. Spurgeon and the Puritans by <em>meaning</em>, with each one quoted and cited to its sermon, book and page.</p>
      </header>

      <div class="searchbar" role="search">
        <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7" /><path d="m20 20-4-4" /></svg>
        <input
          value={q} autoFocus aria-label="Search illustrations"
          placeholder="Search by meaning: “the love of God”, “compassion”, Romans 8:28 …"
          onInput={(e) => { setLike(undefined); setQ((e.target as HTMLInputElement).value); }}
        />
        {q && <button class="clear" aria-label="Clear" onClick={() => setQ("")}>×</button>}
      </div>
      <div class="status">
        {modelState === "loading" && <span>Preparing meaning search… (word search works meanwhile)</span>}
        {modelState === "failed" && <span>Meaning search could not load on this device; using word search.</span>}
      </div>

      <FilterBar meta={meta} f={f} set={set} />

      {browsing ? (
        <Browse meta={meta} pick={(t) => set({ topic: t, category: undefined })} example={(s) => setQ(s)} />
      ) : (
        <section class="results" aria-busy={busy}>
          <div class="summary-line">
            {like != null && <span>Illustrations similar to <b>{items[idIndex.get(like)!]?.[1]}</b> · <a href="#" onClick={(e) => { e.preventDefault(); setLike(undefined); }}>back</a></span>}
            {res?.mode === "scripture" && <span>Illustrations tied to <b>{res.ref}</b> (their Scripture or the sermon's text)</span>}
            {res && <span class="count">{ids.length >= 500 ? "500+" : ids.length.toLocaleString()} {res.mode === "semantic" ? "best matches" : "illustrations"}</span>}
          </div>
          {res && res.related.length > 0 && (
            <div class="related">
              <span>Related topics:</span>
              {res.related.map(([t]) => <button class="chip" onClick={() => set({ topic: t })}>{meta.topics[t][0]}</button>)}
            </div>
          )}
          {focus != null && <Card meta={meta} it={items[focus]} index={focus} setTopic={(t) => set({ topic: t })} onLike={(id) => setLike(id)} toast={showToast} open />}
          {ids.slice(0, shown).filter((i) => i !== focus).map((i) => (
            <Card key={items[i][0]} meta={meta} it={items[i]} index={i} setTopic={(t) => set({ topic: t })} onLike={(id) => { setLike(id); setQ(""); window.scrollTo({ top: 0 }); }} toast={showToast} />
          ))}
          {res && ids.length === 0 && <p class="empty">No illustrations matched. Try different words, or clear a filter.</p>}
          {shown < ids.length && <button class="more" onClick={() => setShown(shown + PAGE)}>Show more</button>}
        </section>
      )}

      <footer>
        <p>Illustrations were found and summarized by an AI model reading public-domain sermon volumes and works; always check the original passage before preaching it. Data version {meta.version}. <a href="https://github.com/garridolecca/spurgeon-illustrations">Source &amp; data on GitHub</a>.</p>
      </footer>
      {toast && <div class="toast" role="status">{toast}</div>}
    </div>
  );
}

function Loading({ progress }: { progress: { stage: string; pct: number } }) {
  return (
    <div class="page loading">
      <header class="masthead"><span class="brand">Spurgeon Illustrations</span></header>
      <p>{progress.stage}…</p>
      <div class="bar"><div style={{ width: `${Math.max(3, progress.pct)}%` }} /></div>
      <p class="hint">The first visit downloads the library (about 30–60 MB); later visits load from your browser's cache.</p>
    </div>
  );
}

function FilterBar({ meta, f, set }: { meta: Meta; f: Filters; set: (p: Partial<Filters>) => void }) {
  const topicsInCat = useMemo(
    () => meta.topics.map((t, i) => [i, t] as const).filter(([, t]) => f.category == null || t[1] === f.category).sort((a, b) => a[1][0].localeCompare(b[1][0])),
    [meta, f.category],
  );
  const authors = useMemo(() => meta.authors.map((a, i) => [i, a] as const).sort((a, b) => a[1].localeCompare(b[1])), [meta]);
  const any = f.topic != null || f.category != null || f.author != null || f.book != null || f.kind;
  return (
    <div class="filters">
      <label>Category
        <select value={f.category ?? ""} onChange={(e) => { const v = (e.target as HTMLSelectElement).value; set({ category: v === "" ? undefined : +v, topic: undefined }); }}>
          <option value="">All</option>
          {meta.categories.map((c, i) => <option value={i}>{c}</option>)}
        </select>
      </label>
      <label>Topic
        <select value={f.topic ?? ""} onChange={(e) => { const v = (e.target as HTMLSelectElement).value; set({ topic: v === "" ? undefined : +v }); }}>
          <option value="">All</option>
          {topicsInCat.map(([i, t]) => <option value={i}>{t[0]} ({t[2]})</option>)}
        </select>
      </label>
      <label>Author
        <select value={f.author ?? ""} onChange={(e) => { const v = (e.target as HTMLSelectElement).value; set({ author: v === "" ? undefined : +v }); }}>
          <option value="">All</option>
          {authors.map(([i, a]) => <option value={i}>{a}</option>)}
        </select>
      </label>
      <div class="kinds" role="group" aria-label="Kind">
        {meta.kinds.map((k) => <button class={`chip ${f.kind === k ? "on" : ""}`} aria-pressed={f.kind === k} onClick={() => set({ kind: f.kind === k ? undefined : k })}>{k}</button>)}
      </div>
      {f.book != null && <span class="chip on" onClick={() => set({ book: undefined })}>{meta.books[f.book].title} ×</span>}
      {any && <button class="link" onClick={() => set({ topic: undefined, category: undefined, author: undefined, book: undefined, kind: undefined })}>Clear filters</button>}
    </div>
  );
}

function Browse({ meta, pick, example }: { meta: Meta; pick: (t: number) => void; example: (s: string) => void }) {
  const byCat = useMemo(() => {
    const m = meta.categories.map(() => [] as number[]);
    meta.topics.forEach((t, i) => m[t[1]].push(i));
    m.forEach((l) => l.sort((a, b) => meta.topics[b][2] - meta.topics[a][2]));
    return m;
  }, [meta]);
  const [open, setOpen] = useState<number | null>(null);
  return (
    <section class="browse">
      <div class="examples"><span>Try:</span>{EXAMPLES.map((s) => <button class="chip" onClick={() => example(s)}>{s}</button>)}</div>
      <h2>Browse by topic</h2>
      <div class="cats">
        {meta.categories.map((c, ci) => {
          const list = byCat[ci];
          if (!list.length) return null;
          const total = list.reduce((s, t) => s + meta.topics[t][2], 0);
          const show = open === ci ? list : list.slice(0, 9);
          return (
            <div class="cat">
              <h3>{c} <small>{total.toLocaleString()}</small></h3>
              <div class="chips">
                {show.map((t) => <button class="chip" onClick={() => pick(t)}>{meta.topics[t][0]} <small>{meta.topics[t][2]}</small></button>)}
                {list.length > 9 && <button class="link" onClick={() => setOpen(open === ci ? null : ci)}>{open === ci ? "fewer" : `+${list.length - 9} more`}</button>}
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}

function Card({ meta, it, index, setTopic, onLike, toast, open: startOpen = false }: {
  meta: Meta; it: ItemRow; index: number; setTopic: (t: number) => void; onLike: (id: string) => void; toast: (s: string) => void; open?: boolean;
}) {
  const [open, setOpen] = useState(startOpen);
  const [text, setText] = useState<[string, string] | null>(null);
  useEffect(() => { if (open && !text) passage(meta, index).then(setText); }, [open]);
  const bk = meta.books[it[8]];
  const cite = citation(meta, it);
  const copy = async (s: string, what: string) => { await navigator.clipboard.writeText(s); toast(`${what} copied`); };
  const full = async () => {
    const p = text ?? (await passage(meta, index));
    copy(`${it[1]}\n\n${p[0] ? `“${p[0]}”\n\n` : `${it[3]}\n\n`}${cite}`, "Illustration and citation");
  };
  const permalink = `${location.origin}${BASE}?id=${it[0]}`;
  return (
    <article class="card">
      <div class="card-head">
        <h3>{it[1]}</h3>
        <span class={`kind k-${it[2].toLowerCase()}`}>{it[2]}</span>
      </div>
      <p class="sum">{it[3]}</p>
      {it[4] && <p class="point"><span>Illustrates</span> {it[4]}</p>}
      <div class="chips">
        {it[5].map((t) => <button class="chip small" onClick={() => setTopic(t)}>{meta.topics[t][0]}</button>)}
        {it[6].map((s) => <span class="chip small scripture">{s}</span>)}
      </div>
      <p class="source">
        <b>{meta.authors[it[7]]}</b>
        {it[9] && <> · “{it[9]}”{it[11] ? ` (No. ${it[11]})` : ""}</>}
        {it[10] && <> · {it[10]}</>}
        {it[12] && <> · {it[12]}</>}
        {it[13] && <> · text: {it[13]}</>}
        <br /><i>{bk.title}</i>, p. {it[14]}
      </p>
      {open && (
        <blockquote class="passage">
          {text ? (text[0] ? <>“{text[0]}”{text[1] === "a" && <small> (nearest matching passage on the page)</small>}</> : <small>The original passage could not be located; see the book at the page cited.</small>) : <small>Loading…</small>}
        </blockquote>
      )}
      <div class="actions">
        <button onClick={() => setOpen(!open)}>{open ? "Hide original" : "Read original"}</button>
        <button onClick={() => copy(cite, "Citation")}>Copy citation</button>
        <button onClick={full}>Copy for sermon</button>
        <button onClick={() => onLike(it[0])}>More like this</button>
        <button onClick={() => copy(permalink, "Link")}>Link</button>
        {bk.rid && <a href={`https://app.logos.com/books/${encodeURIComponent(bk.rid)}`} target="_blank" rel="noopener">Open in Logos</a>}
      </div>
    </article>
  );
}
