"""Clean text that came out of a PDF, an HTML page or OCR."""

import re
import unicodedata
from collections import Counter

# soft hyphen, zero-width space, BOM. ZWJ/ZWNJ stay: Indic scripts need them.
INVISIBLE = dict.fromkeys(map(ord, "\u00ad\u200b\ufeff"), None)
PAGE_NUMBER = re.compile(r"^(page\s*)?[-\u2013]?\s*\d+\s*([-\u2013]|of\s+\d+)?$", re.IGNORECASE)


def clean_text(text: str, page_numbers: bool = True) -> str:
    text = unicodedata.normalize("NFKC", text).translate(INVISIBLE)
    text = re.sub(r"([a-z])-\n([a-z])", r"\1\2", text)  # "regu-\nlation" -> "regulation"
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
    if page_numbers:  # drop "7", "Page 7 of 40", "- 7 -" (never inside table cells)
        lines = [line for line in lines if not PAGE_NUMBER.match(line)]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def shape(line: str) -> str:
    """The line without numbers, so "Page 3" and "4 Page" look the same."""
    return re.sub(r"[\d\s]+", " ", line).strip()


def repeated_lines(pages: list[str], share: float = 0.5) -> set[str]:
    """Headers and footers: lines at the top or bottom of at least half the pages."""
    if len(pages) < 3:
        return set()
    seen = Counter()
    for text in pages:
        lines = [line for line in text.splitlines() if line.strip()]
        seen.update({shape(line) for line in lines[:2] + lines[-2:]})
    return {line for line, count in seen.items() if line and count >= share * len(pages)}


def drop_lines(text: str, unwanted: set[str]) -> str:
    return "\n".join(line for line in text.splitlines() if shape(line) not in unwanted)
