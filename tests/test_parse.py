import json

from app.ingest import parse
from app.ingest.clean import clean_text, drop_lines, repeated_lines


def test_clean_text_rules():
    assert clean_text("\ufb01le") == "file"  # ligature -> fi
    assert clean_text("regu-\nlation") == "regulation"  # hyphen at line end joined
    assert clean_text("a\u00adb") == "ab"  # soft hyphen removed
    assert clean_text("hello\nPage 7 of 40\nworld") == "hello\nworld"  # page number dropped
    assert clean_text("a   b") == "a b"  # spaces collapsed


def test_page_numbers_kept_inside_table_cells():
    assert clean_text("150", page_numbers=False) == "150"


def test_repeated_header_removed():
    pages = ["Demo Bank\nbody a\nPage 1", "Demo Bank\nbody b\nPage 2", "Demo Bank\nbody c\nPage 3"]
    noise = repeated_lines(pages)
    assert "Demo Bank" in noise
    assert "Demo Bank" not in drop_lines(pages[0], noise)


def test_kconfig_parsed_as_code(tmp_path):
    f = tmp_path / "Kconfig"
    f.write_text('config SCHED_TICKLESS\n\tbool "Tickless"\n\tdefault n\n', encoding="utf-8")
    records = parse.parse_file(f)
    assert len(records) == 1
    r = records[0]
    assert r["method"] == "code" and r["page"] == 1
    assert r["headings"] == ["config SCHED_TICKLESS"]
    assert "\tbool" in r["text"]  # indentation kept


def test_c_file_keeps_indentation(tmp_path):
    f = tmp_path / "main.c"
    f.write_text("int main(void)\n{\n    return 0;\n}\n", encoding="utf-8")
    r = parse.parse_file(f)[0]
    assert "    return 0;" in r["text"]


def test_unknown_suffix_is_skipped(tmp_path):
    assert parse.parse_file(tmp_path / "photo.bin") == []


def test_duplicate_doc_ids_are_reported():
    records = [
        {"doc_id": "faq", "source_file": "a/faq.pdf"},
        {"doc_id": "faq", "source_file": "b/faq.pdf"},
    ]
    assert parse.duplicate_ids(records) == ["faq"]


def test_command_line_writes_jsonl_and_sample(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "Kconfig").write_text("config A\n\tbool\n", encoding="utf-8")
    out = tmp_path / "out" / "pages.jsonl"
    parse.main([str(raw), "--out", str(out)])
    lines = out.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    fields = {"doc_id", "source_file", "page", "headings", "text", "tables", "method"}
    assert set(json.loads(lines[0])) == fields
    assert (out.parent / "sample_pages.json").exists()
