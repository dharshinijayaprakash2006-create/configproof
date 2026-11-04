"""Split parsed pages (GenAI 8 output) into chunks that carry their metadata."""

import hashlib
import re
from dataclasses import dataclass

MAX_CHARS = 1000  # about 250 tokens: fits all-MiniLM-L6-v2, which cuts input at 256 tokens
OVERLAP = 150  # about 15%: a sentence on a boundary appears whole in at least one chunk
MIN_CHARS = 25  # drop scraps shorter than this
FOOTER = re.compile(r"^\s*page \d+( of \d+)?\s*$", re.IGNORECASE)  # "Page 3 of 40" lines


@dataclass
class Chunk:
    doc_id: str
    source_file: str
    page: int
    section: str  # the heading this text sits under
    chunk_index: int  # position on its page: 0, 1, 2 ...
    kind: str  # "text" or "table"
    text: str
    content_hash: str


def normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def content_hash(text: str) -> str:
    """Same words = same hash, even if spacing or line breaks differ."""
    return hashlib.sha256(normalise(text).encode("utf-8")).hexdigest()


def strip_table_text(text: str, tables: list) -> str:
    """GenAI 8 also appends each table to text as "Table N:" rows.
    Tables already become their own chunks, so drop that second copy here."""
    if not tables:
        return text
    if text.startswith("Table 1:\n"):
        return ""
    i = text.rfind("\n\nTable 1:\n")
    return text[:i] if i >= 0 else text


def split_by_heading(text: str, headings: list[str], section: str):
    """Yield (section, body). A line that equals one of the page's headings starts a new section."""
    wanted = {h.strip() for h in headings if h and h.strip()}
    lines: list[str] = []
    for line in text.splitlines():
        if FOOTER.match(line):
            continue  # found by inspecting chunks by hand: footers were glued onto text
        if line.strip() in wanted:
            if "".join(lines).strip():
                yield section, "\n".join(lines)
            section, lines = line.strip(), [line.strip()]
        else:
            lines.append(line)
    if "".join(lines).strip():
        yield section, "\n".join(lines)


def _cut(para: str, limit: int) -> list[str]:
    """Cut a long paragraph at the last sentence end (else the last space) before the limit."""
    parts = []
    while len(para) > limit:
        cut = para.rfind(". ", 0, limit) + 1 or para.rfind(" ", 0, limit)
        cut = cut if cut > 0 else limit
        parts.append(para[:cut].strip())
        para = para[cut:].strip()
    return parts + [para] if para else parts


def pack(body: str, max_chars: int = MAX_CHARS, overlap: int = OVERLAP) -> list[str]:
    """Fill chunks paragraph by paragraph; each new chunk starts with the tail of the last one."""
    pieces = []
    for para in re.split(r"\n\s*\n", body):
        pieces += _cut(normalise(para), max_chars - overlap)
    chunks, cur = [], ""
    for p in pieces:
        if cur and len(cur) + 1 + len(p) > max_chars:
            chunks.append(cur)
            tail = cur[-(overlap - 1) :]
            cur = tail[tail.find(" ") + 1 :] + " " + p  # start the tail on a whole word
        else:
            cur = f"{cur} {p}".strip()
    return chunks + [cur] if cur else chunks


def table_texts(table, max_chars: int = MAX_CHARS) -> list[str]:
    """A table becomes its own chunk(s): one row per line, header repeated in every chunk."""
    if isinstance(table, str):
        return pack(table, max_chars)
    rows = [" | ".join(str(c or "").strip() for c in row) for row in table if row]
    if not rows:
        return []
    header, out, cur = rows[0], [], rows[0]
    for row in rows[1:]:
        if cur != header and len(cur) + 1 + len(row) > max_chars:
            out.append(cur)
            cur = header
        cur += "\n" + row
    return out + [cur]


def chunk_pages(pages: list[dict], max_chars: int = MAX_CHARS, overlap: int = OVERLAP) -> list[Chunk]:
    """pages: GenAI 8 records {doc_id, source_file, page, headings, text, tables}."""
    chunks: list[Chunk] = []
    section, last_doc = "", None
    for p in sorted(pages, key=lambda r: (r["doc_id"], r["page"])):
        if p["doc_id"] != last_doc:  # new document: forget the old heading
            section, last_doc = "", p["doc_id"]
        pieces = []
        text = strip_table_text(p.get("text", ""), p.get("tables") or [])
        for sec, body in split_by_heading(text, p.get("headings") or [], section):
            pieces += [(sec, "text", t) for t in pack(body, max_chars, overlap)]
            section = sec  # the next page starts under the last heading seen
        for table in p.get("tables") or []:
            pieces += [(section, "table", t) for t in table_texts(table, max_chars)]
        meta = (p["doc_id"], p.get("source_file", ""), int(p["page"]))
        for i, (sec, kind, text) in enumerate(t for t in pieces if len(t[2]) >= MIN_CHARS):
            chunks.append(Chunk(*meta, sec, i, kind, text, content_hash(text)))
    return chunks
