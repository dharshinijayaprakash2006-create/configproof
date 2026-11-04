from app.rag.chunking import MAX_CHARS, chunk_pages, content_hash

PARA = "Students must attend 75 percent of classes. " * 6  # about 260 characters


def page(n, text, headings=(), tables=(), doc="regs"):
    return {
        "doc_id": doc,
        "source_file": f"{doc}.pdf",
        "page": n,
        "headings": list(headings),
        "text": text,
        "tables": list(tables),
    }


def test_heading_starts_a_section_and_carries_to_next_page():
    pages = [
        page(1, f"Attendance\n{PARA}\nFees\n{PARA}", ["Attendance", "Fees"]),
        page(2, PARA),
    ]  # page 2 has no heading: still under "Fees"
    chunks = chunk_pages(pages)
    assert [(c.page, c.section) for c in chunks] == [(1, "Attendance"), (1, "Fees"), (2, "Fees")]
    assert all(c.doc_id == "regs" and c.source_file == "regs.pdf" for c in chunks)


def test_chunks_stay_under_the_limit_and_overlap():
    chunks = chunk_pages([page(1, "\n\n".join([PARA] * 12))])
    assert len(chunks) > 1
    assert all(len(c.text) <= MAX_CHARS for c in chunks)
    first, second = chunks[0].text, chunks[1].text
    assert second[:40] in first  # the second chunk starts with the end of the first


def test_one_huge_paragraph_is_cut_at_sentence_ends():
    chunks = chunk_pages([page(1, PARA * 10)])
    assert all(len(c.text) <= MAX_CHARS for c in chunks)
    assert chunks[0].text.endswith(".")


def test_table_is_its_own_chunk_with_header_repeated():
    rows = [["Course", "Credits"]] + [[f"Subject {i}", "4"] for i in range(120)]
    chunks = [c for c in chunk_pages([page(3, "", tables=[rows])]) if c.kind == "table"]
    assert len(chunks) > 1
    assert all(c.text.startswith("Course | Credits") for c in chunks)


def test_hash_ignores_spacing_but_not_words():
    assert content_hash("Fees  are\nRs 500.") == content_hash("Fees are Rs 500.")
    assert content_hash("Fees are Rs 500.") != content_hash("Fees are Rs 600.")


def test_scraps_and_empty_pages_make_no_chunks():
    assert chunk_pages([page(1, "Page 3 of 40"), page(2, "")]) == []


def test_page_footer_lines_are_dropped():
    chunks = chunk_pages([page(1, f"{PARA}\nPage 1 of 40")])
    assert "Page 1 of 40" not in chunks[0].text


def test_table_text_appended_by_genai8_is_not_chunked_twice():
    rows = [["Service", "Fee (Rs)"], ["Cheque book", "150"]]
    text = f"Fees\n{PARA}\n\nTable 1:\nService | Fee (Rs)\nCheque book | 150"
    chunks = chunk_pages([page(1, text, ["Fees"], tables=[rows])])
    assert [c.kind for c in chunks] == ["text", "table"]
    assert "Cheque book" not in chunks[0].text and "Cheque book" in chunks[1].text
