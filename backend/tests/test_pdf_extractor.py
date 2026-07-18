import pytest
import os
from app.data.parser.pdf_extractor import parse_tender_document, PdfExtractionError

SAMPLE_DOCS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "sample_documents")

def test_extract_it_hardware():
    pdf_path = os.path.join(SAMPLE_DOCS_DIR, "doc_it_hardware_normal.pdf")
    res = parse_tender_document(pdf_path)
    
    assert res["tender_ref"] == "GA/ZNA/ITH/2026/0142"
    assert res["department"] == "General Admin"
    assert res["category"] == "IT Hardware"
    assert res["region"] == "Zone A"
    assert res["estimated_value"] == 545000.00
    assert res["award_value"] == 522000.00
    assert res["published_date"] == "2026-01-12"
    assert res["award_date"] == "2026-01-28"
    assert len(res["bidders"]) == 3
    
    winner = next(b for b in res["bidders"] if b["is_winner"])
    assert winner["vendor_name"] == "Nova Systems Pvt Ltd"
    assert winner["bid_amount"] == 522000.0

def test_extract_medical_single_bidder():
    pdf_path = os.path.join(SAMPLE_DOCS_DIR, "doc_medical_single_bidder.pdf")
    res = parse_tender_document(pdf_path)
    
    assert res["tender_ref"] == "HD/ZNC/MS/2026/0217"
    assert res["department"] == "Health Dept"
    assert res["category"] == "Medical Supplies"
    assert res["region"] == "Zone C"
    assert len(res["bidders"]) == 1
    
    winner = res["bidders"][0]
    assert winner["vendor_name"] == "MedSure Distributors"
    assert winner["is_winner"] is True
    assert winner["bid_amount"] == 305000.0

def test_pdf_extraction_error_missing_field(tmp_path):
    from reportlab.pdfgen import canvas
    
    pdf_path = tmp_path / "bad.pdf"
    c = canvas.Canvas(str(pdf_path))
    c.drawString(100, 750, "Tender Reference No.: BAD/123")
    c.drawString(100, 730, "Issuing Department: Bad Dept")
    # Missing other fields deliberately
    c.save()
    
    with pytest.raises(PdfExtractionError):
        parse_tender_document(str(pdf_path))
