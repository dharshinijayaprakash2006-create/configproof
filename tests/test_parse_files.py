from reportlab.pdfgen import canvas

from app.ingest import parse


def make_pdf(path):
    """3-page PDF: repeated header, heading, body lines and a page-number footer."""
    c = canvas.Canvas(str(path), pagesize=(595, 842))
    headings = ["1. Account opening", "2. Fees and charges", "3. Refunds"]
    for n, heading in enumerate(headings, start=1):
        c.setFont("Helvetica", 8)
        c.drawString(50, 820, "Demo Bank - Customer Policy 2026")
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, 760, heading)
        c.setFont("Helvetica", 11)
        for i in range(3):
            c.drawString(50, 730 - 20 * i, f"{['Alpha', 'Bravo', 'Charlie'][i]} body line of section {n}")
        c.setFont("Helvetica", 8)
        c.drawString(50, 30, f"Page {n} of 3")
        c.showPage()
    c.save()


def make_html(path):
    path.write_text(
        "<html><head><meta charset='utf-8'><script>var x = 1;</script></head><body>"
        "<nav>Home | About | Contact</nav>"
        "<main><h1>Fees page</h1><p>Fees are reviewed every year.</p>"
        "<table><tr><th>Service</th><th>Fee</th></tr>"
        "<tr><td>Cheque book</td><td>150</td></tr></table></main>"
        "<footer>Copyright footer</footer></body></html>",
        encoding="utf-8",
    )


def test_pdf_one_record_per_page_with_page_numbers(tmp_path):
    pdf = tmp_path / "demo-bank_2026_policy.pdf"
    make_pdf(pdf)
    records = parse.parse_file(pdf)
    assert [r["page"] for r in records] == [1, 2, 3]
    assert {r["doc_id"] for r in records} == {"demo-bank_2026_policy"}
    assert all(r["method"] == "text" for r in records)


def test_pdf_headings_found_by_font_size(tmp_path):
    pdf = tmp_path / "policy.pdf"
    make_pdf(pdf)
    records = parse.parse_file(pdf)
    assert records[0]["headings"] == ["1. Account opening"]
    assert records[1]["headings"] == ["2. Fees and charges"]


def test_pdf_header_and_page_numbers_removed(tmp_path):
    pdf = tmp_path / "policy.pdf"
    make_pdf(pdf)
    text = parse.parse_file(pdf)[0]["text"]
    assert "Customer Policy 2026" not in text
    assert "Page 1 of 3" not in text
    assert "Alpha body line" in text


def test_html_keeps_content_drops_menus(tmp_path):
    page = tmp_path / "fees.html"
    make_html(page)
    r = parse.parse_file(page)[0]
    assert r["method"] == "html" and r["page"] == 1
    assert r["headings"] == ["Fees page"]
    assert "Fees are reviewed every year." in r["text"]
    assert "Home | About" not in r["text"] and "Copyright footer" not in r["text"]
    assert r["tables"] == [[["Service", "Fee"], ["Cheque book", "150"]]]
