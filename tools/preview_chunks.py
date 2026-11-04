"""Print a few random chunks so you can check them by eye. Needs no database and no model.

python -m tools.preview_chunks data/parsed --n 5
"""

import argparse
import random

from app.rag.chunking import chunk_pages
from tools.ingest import NO_TEXT, load_pages

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("folder", nargs="?", default="data/parsed")
    ap.add_argument("--n", type=int, default=5)
    ap.add_argument("--seed", type=int, default=9)
    args = ap.parse_args()
    pages = load_pages(args.folder)
    usable = [p for p in pages if p.get("method") not in NO_TEXT]
    chunks = chunk_pages(usable)
    sizes = sorted(len(c.text) for c in chunks)
    print(
        f"{len(usable)} pages with text -> {len(chunks)} chunks; size min {sizes[0]}, "
        f"median {sizes[len(sizes) // 2]}, max {sizes[-1]} characters\n"
    )
    for c in random.Random(args.seed).sample(chunks, min(args.n, len(chunks))):
        print(f"--- {c.doc_id} | page {c.page} | {c.section or '(no heading)'} | #{c.chunk_index} | {c.kind}")
        print(c.text, "\n")
