"""Chunk, embed and store parsed pages.

python -m tools.ingest data/parsed --max-pages 50 --report INGESTION.md
"""

import argparse
import json
import time
from datetime import date
from pathlib import Path

from app.config import get_settings
from app.rag.chunking import MAX_CHARS, OVERLAP, chunk_pages
from app.rag.embeddings import get_embedder
from app.rag.store import connect, count_chunks, existing_hashes, insert_chunks

LOCAL_DB = "postgresql://app:app@localhost:5432/rag"  # Compose's db, seen from your laptop


def load_pages(folder: str) -> list[dict]:
    """Read GenAI 8 output: *.jsonl, one page per line. sample_pages.json is a preview copy: not read."""
    pages = []
    for path in sorted(Path(folder).glob("*.jsonl")):
        lines = path.read_text(encoding="utf-8").splitlines()
        pages += [json.loads(line) for line in lines if line.strip()]
    return pages


NO_TEXT = {"needs_ocr", "empty"}  # GenAI 8 methods for pages with nothing to embed


def ingest(folder: str, db_url: str, max_pages: int | None = None, batch: int = 64) -> dict:
    settings = get_settings()
    t0 = time.perf_counter()
    pages = load_pages(folder)[:max_pages]
    usable = [p for p in pages if p.get("method") not in NO_TEXT]
    chunks = chunk_pages(usable)
    seen, unique = set(), []
    for c in chunks:  # the same text twice in this run (a copied PDF, a repeated notice): keep one
        if c.content_hash not in seen:
            seen.add(c.content_hash)
            unique.append(c)

    embedder = get_embedder(settings)
    conn = connect(db_url, settings.embedding_dim)
    known = existing_hashes(conn, [c.content_hash for c in unique])
    new = [c for c in unique if c.content_hash not in known]  # only these cost embedding time
    stored = 0
    for i in range(0, len(new), batch):
        part = new[i : i + batch]
        vectors = embedder.embed([f"{c.section}\n{c.text}" for c in part])
        stored += insert_chunks(conn, part, vectors, embedder.model)
    stats = {
        "pages": len(pages),
        "pages_no_text": len(pages) - len(usable),
        "chunks": len(chunks),
        "duplicates": len(chunks) - len(unique),
        "already_stored": len(known),
        "stored": stored,
        "rows_in_table": count_chunks(conn),
        "seconds": round(time.perf_counter() - t0, 1),
        "model": embedder.model,
        "dim": embedder.dim,
    }
    conn.close()
    return stats


def report_row(s: dict) -> str:
    return (
        f"| {date.today()} | {s['pages']} | {s['pages_no_text']} | {s['chunks']} "
        f"| {s['duplicates'] + s['already_stored']} "
        f"| {s['stored']} | {s['rows_in_table']} | {s['seconds']} | {s['model']} ({s['dim']}) "
        f"| {MAX_CHARS}/{OVERLAP} |"
    )


HEADER = (
    "| Date | Pages | No-text pages | Chunks made | Skipped (duplicate) | New stored | Rows in table "
    "| Seconds | Model (dim) | Chunk/overlap chars |\n|---|---|---|---|---|---|---|---|---|---|\n"
)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("folder", nargs="?", default="data/parsed")
    ap.add_argument("--db", default=LOCAL_DB)
    ap.add_argument("--max-pages", type=int)
    ap.add_argument("--report", help="append one table row to this file, e.g. INGESTION.md")
    args = ap.parse_args()
    stats = ingest(args.folder, args.db, args.max_pages)
    print(json.dumps(stats, indent=2))
    if args.report:
        path = Path(args.report)
        if not path.exists():
            path.write_text("# Ingestion log\n\n" + HEADER, encoding="utf-8")
        with path.open("a", encoding="utf-8") as f:
            f.write(report_row(stats) + "\n")
