"""Turn PDFs, HTML and text files into one clean JSON record per page.

Record: {doc_id, source_file, page, headings, text, tables, method}
Run:    python -m app.ingest.parse data/raw --out data/parsed/pages.jsonl
"""

import argparse
import json
import os
import re
import shutil
import statistics
from collections import Counter
from pathlib import Path

import pdfplumber
from bs4 import BeautifulSoup

from app.ingest.clean import clean_text, drop_lines, repeated_lines, shape

MIN_CHARS = 25  # a PDF page with an image and less text than this = scanned
HEADING_SIZE = 1.15  # a line 15% bigger than body text is a heading
# path to the Tesseract program; None means OCR is not installed
TESSERACT = os.getenv("TESSERACT_CMD") or shutil.which("tesseract")
NUMBERED = re.compile(r"^\d+(\.\d+)*\.?\s+[^\W\d]")  # "3. Refunds", "2.1 Fees"


def make_record(path, page, headings, text, tables, method):
    return {
        "doc_id": re.sub(r"[^a-z0-9_-]+", "-", path.stem.lower()).strip("-"),
        "source_file": path.as_posix(),
        "page": page,
        "headings": headings,
        "text": text,
        "tables": tables,
        "method": method,
    }


def with_tables(text, tables):
    """Add each table as "cell | cell" lines, so search still finds what is inside."""
    for i, rows in enumerate(tables, start=1):
        text += f"\n\nTable {i}:\n" + "\n".join(" | ".join(row) for row in rows)
    return text.strip()


def clean_rows(rows):
    def cell(c):
        return clean_text(c or "", page_numbers=False).replace("\n", " ")

    rows = [[cell(c) for c in row] for row in rows]
    return [row for row in rows if any(row)]


# ---------------------------------------------------------------- PDF
def outside(page, boxes):
    """The page without its table areas, so table text is not read twice."""

    def keep(obj):
        x, y = (obj["x0"] + obj["x1"]) / 2, (obj["top"] + obj["bottom"]) / 2
        return not any(x0 <= x <= x1 and y0 <= y <= y1 for x0, y0, x1, y1 in boxes)

    return page.filter(keep)


def line_styles(page):
    """(text, font size, bold?) for every line on the page."""
    styles = []
    for line in page.extract_text_lines(return_chars=True, use_text_flow=True):
        chars = [c for c in line["chars"] if c["text"].strip()]
        if chars:
            size = statistics.median(c["size"] for c in chars)
            bold = all("bold" in c["fontname"].lower() for c in chars)
            styles.append((line["text"].strip(), size, bold))
    return styles


def ocr(page, lang):
    if not TESSERACT:
        return "", "needs_ocr"
    import pytesseract  # optional: only scanned pages need it

    pytesseract.pytesseract.tesseract_cmd = TESSERACT
    image = page.to_image(resolution=300).original
    return pytesseract.image_to_string(image, lang=lang), "ocr"


def is_heading(text, size, bold, body_size, noise):
    looks_big = size >= body_size * HEADING_SIZE or bold
    short = 2 < len(text) <= 100 and text[-1] not in ".,;" and any(c.isalpha() for c in text)
    return looks_big and short and shape(text) not in noise


def parse_pdf(path: Path, lang: str = "eng") -> list[dict]:
    pages = []
    with pdfplumber.open(path) as pdf:
        for number, page in enumerate(pdf.pages, start=1):
            found = page.find_tables()
            tables = [clean_rows(t.extract()) for t in found]
            body = outside(page, [t.bbox for t in found])
            text = body.extract_text(use_text_flow=True) or ""  # columns in reading order
            styles, method = line_styles(body), "text"
            if len(text.strip()) < MIN_CHARS and page.images:  # a photo of paper
                text, method = ocr(page, lang)  # OCR has no font sizes, so numbered
                lines = [ln.strip() for ln in text.splitlines()]  # lines count as headings
                styles = [(ln, 0, True) for ln in lines if NUMBERED.match(ln)]
            pages.append(dict(page=number, text=text, styles=styles, tables=tables, method=method))
            page.close()  # free this page's memory: annual reports have 300+ pages

    sizes = Counter(round(size) for p in pages for _, size, _ in p["styles"])
    body_size = sizes.most_common(1)[0][0] if sizes else 10  # most lines are body text
    noise = repeated_lines([p["text"] for p in pages])
    records, current = [], []
    for p in pages:
        heads = [t for t, size, bold in p["styles"] if is_heading(t, size, bold, body_size, noise)]
        current = heads[-1:] or current  # a page with no heading inherits the last one
        text = with_tables(clean_text(drop_lines(p["text"], noise)), p["tables"])
        method = p["method"] if text or p["method"] == "needs_ocr" else "empty"
        records.append(make_record(path, p["page"], heads or current, text, p["tables"], method))
    return records


# ---------------------------------------------------------------- HTML, text, code
NOT_CONTENT = ["script", "style", "noscript", "nav", "header", "footer", "aside", "form"]
BLOCKS = ["p", "div", "li", "br", "tr", "h1", "h2", "h3", "h4", "h5", "h6"]


def parse_html(path: Path) -> list[dict]:
    soup = BeautifulSoup(path.read_bytes(), "html.parser")  # bytes: bs4 reads <meta charset>
    for tag in soup(NOT_CONTENT):
        tag.decompose()
    root = soup.find("main") or soup.find("article") or soup.body or soup
    tables = []
    for table in root.find_all("table"):
        rows = [[c.get_text(" ") for c in tr.find_all(["th", "td"])] for tr in table.find_all("tr")]
        tables.append(clean_rows(rows))
        table.decompose()
    headings = [clean_text(h.get_text(" ")) for h in root.find_all(["h1", "h2", "h3"])]
    for tag in root.find_all(BLOCKS):
        tag.append("\n")  # keep paragraphs on separate lines
    text = with_tables(clean_text(root.get_text()), tables)
    return [make_record(path, 1, headings, text, tables, "html")]


def parse_text(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8", errors="replace")
    heads = [ln.lstrip("#").strip() for ln in text.splitlines() if ln.startswith("#")]
    heads = heads if path.suffix == ".md" else []
    return [make_record(path, 1, heads, clean_text(text), [], "text")]


# NuttX: .h added to code; Kconfig files have no suffix, so they are matched by name
CODE = {".py", ".java", ".js", ".ts", ".go", ".c", ".h", ".cpp", ".cs", ".kt", ".rb", ".php"}
DEFINITION = re.compile(
    r"^\s*(class|def|func|function|interface|public|private|config|menuconfig|menu|choice)\b"
)


def parse_code(path: Path) -> list[dict]:
    """Code keeps its indentation: no cleaning. Headings = class, function and config lines."""
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    heads = [ln.strip()[:100] for ln in text.splitlines() if DEFINITION.match(ln)]
    return [make_record(path, 1, heads[:30], text, [], "code")]


PARSERS = {
    ".pdf": parse_pdf,
    ".html": parse_html,
    ".htm": parse_html,
    ".md": parse_text,
    ".rst": parse_text,
}


def parse_file(path: Path) -> list[dict]:
    suffix = path.suffix.lower()
    if suffix in CODE or "kconfig" in path.name.lower():
        return parse_code(path)
    if suffix == ".txt":
        return parse_text(path)
    parser = PARSERS.get(suffix)
    return parser(path) if parser else []


# ---------------------------------------------------------------- command line
def summary(records):
    methods = Counter(r["method"] for r in records)
    parts = [f"docs: {len({r['doc_id'] for r in records})}", f"pages: {len(records)}"]
    parts += [f"{m}: {n}" for m, n in sorted(methods.items())]
    parts.append(f"tables: {sum(len(r['tables']) for r in records)}")
    return " | ".join(parts)


def duplicate_ids(records):
    """doc_ids used by more than one file."""
    files = {}
    for r in records:
        files.setdefault(r["doc_id"], set()).add(r["source_file"])
    return sorted(doc for doc, paths in files.items() if len(paths) > 1)


def main(argv=None) -> list[dict]:
    ap = argparse.ArgumentParser(description="One clean JSON record per page.")
    ap.add_argument("folder", type=Path)
    ap.add_argument("--out", type=Path, default=Path("data/parsed/pages.jsonl"))
    ap.add_argument("--limit", type=int, default=0, help="stop after N pages (0 = all)")
    ap.add_argument("--sample", type=int, default=5, help="records in sample_pages.json")
    args = ap.parse_args(argv)

    records = []
    for path in sorted(p for p in args.folder.rglob("*") if p.is_file()):
        try:
            records += parse_file(path)
        except Exception as exc:  # one broken file must not stop the run
            print(f"BROKEN  {path}  {type(exc).__name__}: {exc}")
        if args.limit and len(records) >= args.limit:
            records = records[: args.limit]
            break

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as f:
        for r in records:  # ensure_ascii=False keeps Tamil and Hindi readable
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    sample = args.out.with_name("sample_pages.json")
    sample_json = json.dumps(records[: args.sample], ensure_ascii=False, indent=2)
    sample.write_text(sample_json, encoding="utf-8")
    print(summary(records))
    for doc in duplicate_ids(records):
        print(f"WARNING  two files share doc_id {doc}: rename one so citations stay clear")
    print(f"wrote {args.out} and {sample}")
    return records


if __name__ == "__main__":
    main()
