/** One illustration row as stored in data/items.json (columnar to keep the file small). */
export type ItemRow = [
  id: string, title: string, kind: string, summary: string, point: string,
  topics: number[], scripture: string[], author: number, book: number,
  sermon: string, sermonPart: string, sermonNo: number, delivered: string, sermonText: string, page: string,
  titleEs: string, summaryEs: string, pointEs: string,
];

/** One row of data/passages/{k}.json: original passage, match quality ("e"xact / "a"pprox / "n"one), Spanish. */
export type PassageRow = [text: string, quality: string, textEs: string];

export type Lang = "en" | "es";

export interface Book { title: string; rid: string | null; year: string | null; cite: string }

export interface Meta {
  version: string; count: number; dims: number; model: string; query_prefix: string; passage_chunk: number;
  pooling?: "mean" | "cls"; model_parts?: string[];
  categories: string[]; categories_es?: string[]; topics_es?: string[]; kinds_es?: Record<string, string>;
  topics: [label: string, category: number, items: number][];
  authors: string[]; books: Book[]; kinds: string[];
}

export interface Filters { category?: number; topic?: number; author?: number; kind?: string; book?: number; dupes?: boolean }

export interface SearchResult {
  ids: number[];            // item indexes, best first
  mode: "semantic" | "scripture" | "browse" | "similar";
  ref?: string;             // the Scripture reference understood from the query
  refObj?: { book: number; ch: number; v1: number; v2: number };
  related: [topic: number, count: number][];
  ms: number;
}

export type WorkerIn =
  | { type: "init"; base: string }
  | { type: "search"; seq: number; q: string; filters: Filters }
  | { type: "similar"; seq: number; index: number; filters: Filters };

export type WorkerOut =
  | { type: "progress"; stage: string; pct: number }
  | { type: "ready"; meta: Meta; items: ItemRow[] }
  | { type: "model"; ready: boolean; error?: string }
  | { type: "vectors" }
  | { type: "result"; seq: number; result: SearchResult }
  | { type: "error"; message: string };
