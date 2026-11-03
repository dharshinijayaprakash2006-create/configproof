# Dataset

| File | Source URL | Pages | Licence / terms | Downloaded on |
|---|---|---|---|---|
| | | | | |

Full data lives in `data/raw/` (not committed). A 2–3 file sample is in `data/sample/`.





## Parsing

Parser: `python -m app.ingest.parse data/raw --limit 50`

Summary from the run on 50 files from the Apache NuttX repository:

`docs: 50 | pages: 50 | code: 50 | tables: 0`

| method | count |
|---|---|
| code | 50 |
| ocr | 0 |
| needs_ocr | 0 |
| empty | 0 |

Files parsed: 25 Kconfig files and 25 C/H files from `sched/`. Each source file is one record with page 1. Indentation is kept, and `config`, `menuconfig`, `menu` and `choice` lines are stored as headings.

Problem found and fixed: Kconfig files have no suffix, so the parser skipped them. I added a rule that matches any file with "kconfig" in its name, and added `.h` to the code suffixes.

No tables or scanned pages: NuttX is source code, so tables is 0 and no OCR is needed.
