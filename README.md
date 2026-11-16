# Spurgeon Illustrations

**Live search:** https://garridolecca.github.io/spurgeon-illustrations/

A searchable bank of sermon illustrations from **C. H. Spurgeon** and the **Puritans** (Brooks, Sibbes, Manton,
Watson, Bunyan, Baxter, Goodwin, Edwards and others): stories, historical incidents, analogies and images,
each **quoted from the original text and cited to its sermon, book and page**.

Search works by **meaning**, not exact words: *compassion* finds illustrations about pity, mercy and tender
care even when the word "compassion" never appears; *the love of God* finds the father running to the
prodigal. A Bible reference (`Romans 8:28`, `Psalm 23`, `Heb 11`) finds the illustrations tied to that text,
including every illustration from a sermon preached on it.

## Using it

- Type what you want to illustrate in plain English, or a Scripture reference.
- Narrow by **category** (≈26 headings from systematic theology and the Christian life), **topic** (canonical
  topics clustered from ~15,000 theme tags), **author** or **kind** (Story, Historical, Analogy, Image).
- **Read original** shows the passage itself; **Copy citation** gives a Turabian footnote, e.g.
  > C. H. Spurgeon, “How They Conquered the Dragon,” (sermon no. 1237, delivered May 30 1875) in The
  > Metropolitan Tabernacle Pulpit Sermons, vol. 21 (London: Passmore & Alabaster, 1875), 568.
- **Copy for sermon** copies the title, quoted passage and citation together; **More like this** finds
  illustrations with the same meaning; every result has a permanent link.

## How it was built

```
public-domain sermon volumes (PDF + text)
  └─ local LLM (Qwen3-4B) reads every page → illustrations: title, kind, summary, point, themes, Scripture
      └─ pipeline/sections.py   PDF bookmarks → which sermon/chapter each page belongs to
                                (title, sermon number, date delivered, place, sermon text)
      └─ pipeline/export.py     quoted original passage, normalized Scripture, Turabian citation, stable ids
      └─ pipeline/embed.py      bge-small-en-v1.5 vectors; theme tags clustered into canonical topics
                                and categories; each illustration tagged by its themes + nearest topics
      └─ pipeline/build_excel.py  the Illustration Bank workbook
      └─ pipeline/publish.sh    builds the site → `gh-pages` branch (GitHub Pages); dataset → `data` branch
```

The site is fully static. The browser downloads the illustrations and their int8-quantized vectors once
(cached afterwards), embeds the query with the **same** model (`Xenova/bge-small-en-v1.5`, ONNX, via
transformers.js in a Web Worker) and ranks by cosine similarity, fused (Reciprocal Rank Fusion) with BM25
keyword ranking (MiniSearch) so exact words help while meaning decides.

## Data

The `data` branch holds the generated dataset (replaced on every refresh):

- `dataset/illustrations.jsonl.gz` — every illustration with all fields, including the passage and citation.
- `dataset/topics.json` — topics, their category and member theme words.

The `gh-pages` branch is the built site (also replaced on every refresh).

## Caveats

Illustrations were found and summarized by an AI model; summaries can be imperfect. Always read the
original passage (shown with every result) before preaching it. Source texts are public domain.

## License

Code: MIT. Source texts: public domain. Summaries, tags and the dataset: CC0.
