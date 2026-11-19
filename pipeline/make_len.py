"""Write web/public/data/len.u16: one little-endian uint16 per illustration (items.json order) = word count of the
English passage (capped at 65535). The app uses it for the short / medium / long filter.
Run after embed.py (which writes web/public/data/passages); called from publish.sh. Prints the quartiles."""
import json, os, re, sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(ROOT, "web", "public", "data")


def main():
    meta = json.load(open(os.path.join(WEB, "meta.json"), encoding="utf8"))
    n, ch = meta["count"], meta["passage_chunk"]
    out = np.zeros(n, dtype="<u2")
    for k in range((n + ch - 1) // ch):
        rows = json.load(open(os.path.join(WEB, "passages", f"{k}.json"), encoding="utf8"))
        for j, r in enumerate(rows):
            out[k * ch + j] = min(65535, len(r[0].split()))
    out.tofile(os.path.join(WEB, "len.u16"))
    nz = out[out > 0]
    q = np.percentile(nz, [10, 25, 50, 75, 90])
    print(f"len.u16: {n} items, {int((out == 0).sum())} without a passage; words p10/p25/p50/p75/p90 = "
          + " / ".join(str(int(x)) for x in q) + f"; max {int(out.max())}")


if __name__ == "__main__":
    main()
