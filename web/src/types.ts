/** One illustration row as stored in data/items.json (columnar to keep the file small). */
export type ItemRow = [
  id: string, title: string, kind: string, summary: string, point: string,
  topics: number[], scripture: string[], author: number, book: number,
  sermon: string, sermonPart: string, sermonNo: number, delivered: string, sermonText: string, page: string,
];

export interface Book { title: string; rid: string | null; year: string | null; cite: string }

export interface Meta {
  version: string; count: number; dims: number; model: string; query_prefix: string; passage_chunk: number;
  categories: string[];
  topics: [label: string, category: number, items: number][];
  authors: string[]; books: Book[]; kinds: string[];
}

export interface Filters { category?: number; topic?: number; author?: number; kind?: string; book?: number }

export interface SearchResult {
  ids: number[];            // item indexes, best first
  mode: "semantic" | "scripture" | "browse" | "similar";
  ref?: string;             // the Scripture reference understood from the query
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
  | { type: "result"; seq: number; result: SearchResult }
  | { type: "error"; message: string };
