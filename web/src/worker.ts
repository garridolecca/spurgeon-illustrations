/// <reference lib="webworker" />
/**
 * Search engine (runs off the main thread).
 *  - semantic: the query is embedded in the browser with multilingual-e5-small (the same model that embedded the
 *    illustrations' English + Spanish text), so English and Spanish queries both work; int8 vectors
 *    (dot product x per-vector scale);
 *  - keyword: MiniSearch BM25 over title / summary / point / topics / sermon in English and Spanish, accent-
 *    insensitive, with prefix + light fuzziness;
 *  - the two rankings are fused with Reciprocal Rank Fusion, so exact words help but meaning decides;
 *  - a query that is a Bible reference ("Rom 8:28", "Psalm 23") searches the illustrations' Scripture and the
 *    sermon texts instead.
 */
import MiniSearch from "minisearch";
import type { Filters, ItemRow, Meta, SearchResult, WorkerIn, WorkerOut } from "./types";
import { parseCanon, parseQuery, formatRef, refMatch, type Ref } from "./bible";

const post = (m: WorkerOut) => (self as unknown as Worker).postMessage(m);

let meta: Meta;
let items: ItemRow[];
let E: Int8Array;
let S: Float32Array;
let dims = 384;
let refs: Ref[][] = [];
let mini: MiniSearch;
let indexPromise: Promise<void> | null = null;
let vectorsPromise: Promise<void> | null = null;
let hidden: Uint8Array | null = null;   // 1 = near-duplicate of another illustration (hidden unless asked for)
let extractor: ((t: string, o: object) => Promise<{ data: Float32Array }>) | null = null;
let modelPromise: Promise<void> | null = null;
let base = "/";

async function fetchWithProgress(url: string, stage: string, from: number, to: number): Promise<ArrayBuffer> {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`${url}: ${res.status}`);
  const total = +(res.headers.get("content-length") ?? 0);
  if (!res.body || !total) return res.arrayBuffer();
  const reader = res.body.getReader();
  const chunks: Uint8Array[] = [];
  let got = 0;
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    chunks.push(value);
    got += value.length;
    post({ type: "progress", stage, pct: from + ((to - from) * Math.min(got, total)) / total });
  }
  const out = new Uint8Array(got);
  let o = 0;
  for (const c of chunks) { out.set(c, o); o += c.length; }
  return out.buffer;
}

async function init(b: string) {
  base = b;
  const d = `${base}data/`;
  post({ type: "progress", stage: "Loading illustrations", pct: 2 });
  meta = await (await fetch(`${d}meta.json`, { cache: "no-cache" })).json();
  const v = encodeURIComponent(meta.version);
  dims = meta.dims;
  modelPromise = loadModel(); // in parallel with the data
  const itemsBuf = await fetchWithProgress(`${d}items.json?v=${v}`, "Loading illustrations", 5, 85);
  items = JSON.parse(new TextDecoder().decode(itemsBuf));
  post({ type: "progress", stage: "Indexing", pct: 88 });
  refs = items.map((it) => {
    const out: Ref[] = [];
    for (const s of it[6]) { const r = parseCanon(s); if (r) out.push(r); }
    if (it[13]) { const r = parseCanon(it[13]); if (r) out.push(r); }
    return out;
  });
  indexPromise = Promise.resolve().then(buildIndex);
  loadExtras(d, v);
  post({ type: "ready", meta, items });
  // the meaning vectors (the larger download) arrive in the background; word search works meanwhile
  vectorsPromise = loadVectors(d, v);
}


function buildIndex() {
  const fold = (t: string) => t.normalize("NFD").replace(/\p{M}/gu, "").toLowerCase();
  mini = new MiniSearch({
    fields: ["title", "summary", "point", "topics", "sermon", "titleEs", "summaryEs", "pointEs", "topicsEs"],
    storeFields: [],
    processTerm: fold,
    searchOptions: {
      boost: { title: 2.5, titleEs: 2.5, topics: 1.8, topicsEs: 1.8, point: 1.3, pointEs: 1.3 },
      prefix: (t) => t.length > 3, fuzzy: (t) => (t.length > 5 ? 0.15 : false), processTerm: fold,
    },
  });
  mini.addAll(items.map((it, i) => ({
    id: i, title: it[1], summary: it[3], point: it[4], sermon: it[9],
    topics: it[5].map((t) => meta.topics[t][0]).join(" "),
    titleEs: it[15] ?? "", summaryEs: it[16] ?? "", pointEs: it[17] ?? "",
    topicsEs: meta.topics_es ? it[5].map((t) => meta.topics_es![t]).join(" ") : "",
  })));
}

async function loadVectors(d: string, v: string) {
  const [embBuf, scaleBuf] = await Promise.all([
    fetchWithProgress(`${d}emb.i8?v=${v}`, "Loading meaning vectors", 0, 100),
    fetch(`${d}emb.scale.f32?v=${v}`).then((r) => r.arrayBuffer()),
  ]);
  E = new Int8Array(embBuf);
  S = new Float32Array(scaleBuf);
  post({ type: "vectors" });
}

/** Optional files written by pipeline/: near-duplicate map. Missing files are fine. */
async function loadExtras(d: string, v: string) {
  try {
    const r = await fetch(`${d}dupes.json?v=${v}`);
    if (r.ok) {
      const map = (await r.json()) as Record<string, string>;
      const idx = new Map(items.map((it, i) => [it[0], i]));
      hidden = new Uint8Array(items.length);
      for (const k of Object.keys(map)) { const i = idx.get(k); if (i != null) hidden[i] = 1; }
    }
  } catch { /* optional */ }
}

async function loadModel() {
  try {
    const tf = await import("@huggingface/transformers");
    tf.env.allowLocalModels = true;
    tf.env.localModelPath = new URL(`${base}models/`, self.location.origin).href;
    // the weights are served in parts (GitHub Pages refuses files over 100 MB): put them back together in the
    // cache where transformers.js looks first, so the model loads from the site and stays cached
    tf.env.allowRemoteModels = !(await assembleModel(tf.env.localModelPath));
    const pipe = await tf.pipeline("feature-extraction", meta.model, {
      dtype: "q8",
      progress_callback: (p: { status: string; progress?: number }) => {
        if (p.status === "progress" && p.progress != null) post({ type: "progress", stage: "Loading meaning model", pct: 85 + p.progress * 0.15 });
      },
    });
    extractor = pipe as unknown as typeof extractor;
    post({ type: "model", ready: true });
  } catch (e) {
    post({ type: "model", ready: false, error: String(e) });
  }
}

async function assembleModel(root: string): Promise<boolean> {
  if (!meta.model_parts?.length || typeof caches === "undefined") return true;
  try {
    const key = `${root.replace(/\/$/, "")}/${meta.model}/onnx/model_quantized.onnx`;
    const cache = await caches.open("transformers-cache");
    if (await cache.match(key)) return true;
    const parts: ArrayBuffer[] = [];
    for (let k = 0; k < meta.model_parts.length; k++) {
      const n = meta.model_parts.length;
      parts.push(await fetchWithProgress(`${root.replace(/\/$/, "")}/${meta.model}/${meta.model_parts[k]}`,
        "Loading meaning model", 85 + (15 * k) / n, 85 + (15 * (k + 1)) / n));
    }
    const blob = new Blob(parts, { type: "application/octet-stream" });
    await cache.put(key, new Response(blob, { headers: { "content-type": "application/octet-stream", "content-length": String(blob.size) } }));
    return true;
  } catch {
    return false; // e.g. storage blocked: let transformers.js fetch the model from Hugging Face instead
  }
}

async function embed(text: string): Promise<Float32Array | null> {
  if (modelPromise) await modelPromise;
  if (!extractor) return null;
  const out = await extractor(meta.query_prefix + text, { pooling: meta.pooling ?? "cls", normalize: true });
  return out.data;
}

function passes(i: number, f: Filters): boolean {
  const it = items[i];
  if (hidden && hidden[i] && !f.dupes) return false;
  if (f.author != null && it[7] !== f.author) return false;
  if (f.book != null && it[8] !== f.book) return false;
  if (f.kind && it[2] !== f.kind) return false;
  if (f.topic != null && !it[5].includes(f.topic)) return false;
  if (f.category != null && !it[5].some((t) => meta.topics[t][1] === f.category)) return false;
  return true;
}

function semanticRank(q: Float32Array, cand: number[], limit: number, exclude = -1): [number, number][] {
  if (!E) return [];
  const out: [number, number][] = [];
  for (const i of cand) {
    if (i === exclude) continue;
    let s = 0;
    const o = i * dims;
    for (let d = 0; d < dims; d++) s += q[d] * E[o + d];
    out.push([i, s * S[i]]);
  }
  out.sort((a, b) => b[1] - a[1]);
  return out.slice(0, limit);
}

function related(ids: number[], f: Filters): [number, number][] {
  const c = new Map<number, number>();
  for (const i of ids.slice(0, 120)) for (const t of items[i][5]) if (t !== f.topic) c.set(t, (c.get(t) ?? 0) + 1);
  return [...c.entries()].filter(([, n]) => n >= 3).sort((a, b) => b[1] - a[1]).slice(0, 14);
}

async function search(q: string, f: Filters): Promise<SearchResult> {
  const t0 = performance.now();
  q = q.trim();
  const cand: number[] = [];
  for (let i = 0; i < items.length; i++) if (passes(i, f)) cand.push(i);

  // 1. Scripture reference
  const ref = q ? parseQuery(q) : null;
  if (ref) {
    const scored: [number, number][] = [];
    for (const i of cand) {
      let best = 0;
      for (const r of refs[i]) best = Math.max(best, refMatch(ref, r));
      if (best >= (ref.ch ? 2 : 1)) scored.push([i, best]);
    }
    // best match first; among equals, illustrations tied to few passages (i.e. specifically to this one) first
    scored.sort((a, b) => b[1] - a[1] || refs[a[0]].length - refs[b[0]].length);
    const ids = scored.map((s) => s[0]);
    return { ids, mode: "scripture", ref: formatRef(ref), refObj: ref, related: related(ids, f), ms: performance.now() - t0 };
  }

  // 2. browse: no query -> order a topic / filter by closeness to the topic itself
  if (!q) {
    let ids = cand;
    if (f.topic != null || f.category != null) {
      const label = f.topic != null ? meta.topics[f.topic][0] : meta.categories[f.category!];
      const v = E ? await embed(label) : null;
      if (v) ids = semanticRank(v, cand, cand.length).map((x) => x[0]);
    }
    return { ids, mode: "browse", related: related(ids, f), ms: performance.now() - t0 };
  }

  // 3. meaning + words, fused
  if (indexPromise) await indexPromise;
  const v = E ? await embed(q) : null;
  const sem = v ? semanticRank(v, cand, 600) : [];
  const allowed = new Set(cand);
  const kw = mini.search(q, { combineWith: "OR" }).filter((r) => allowed.has(r.id as number)).slice(0, 600);
  const K = 60;
  const score = new Map<number, number>();
  sem.forEach(([i], r) => score.set(i, (score.get(i) ?? 0) + 1 / (K + r)));
  kw.forEach((h, r) => score.set(h.id as number, (score.get(h.id as number) ?? 0) + 0.65 / (K + r)));
  // a strong semantic match should not be outranked by a weak keyword-only hit
  const topSem = sem[0]?.[1] ?? 0;
  sem.forEach(([i, s]) => { if (s > topSem - 0.04) score.set(i, (score.get(i) ?? 0) + 0.004); });
  const ids = [...score.entries()].sort((a, b) => b[1] - a[1]).map((x) => x[0]).slice(0, 500);
  return { ids, mode: "semantic", related: related(ids, f), ms: performance.now() - t0 };
}

async function similar(index: number, f: Filters): Promise<SearchResult> {
  if (vectorsPromise) await vectorsPromise;
  const t0 = performance.now();
  const q = new Float32Array(dims);
  const o = index * dims;
  for (let d = 0; d < dims; d++) q[d] = E[o + d] * S[index];
  const cand: number[] = [];
  for (let i = 0; i < items.length; i++) if (passes(i, f)) cand.push(i);
  const ids = semanticRank(q, cand, 300, index).map((x) => x[0]);
  return { ids, mode: "similar", related: related(ids, f), ms: performance.now() - t0 };
}

self.onmessage = async (e: MessageEvent<WorkerIn>) => {
  const m = e.data;
  try {
    if (m.type === "init") await init(m.base);
    else if (m.type === "search") post({ type: "result", seq: m.seq, result: await search(m.q, m.filters) });
    else if (m.type === "similar") post({ type: "result", seq: m.seq, result: await similar(m.index, m.filters) });
  } catch (err) {
    post({ type: "error", message: String(err) });
  }
};
