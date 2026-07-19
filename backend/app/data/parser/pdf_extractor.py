"""
pdf_extractor.py — Job A: extract labeled fields + the bid table out of a
"Tender Award Summary" PDF using pdfplumber for text/table access and
regex for label -> value extraction.

This module does ONE job: turn a PDF into a plain dict of extracted values.
It does NOT decide whether a category is new or known (that's Job B, in
category_matcher.py), and it does NOT touch the database — insertion is
a separate concern in the service layer, so this stays a pure, testable
function: pdf path in, dict out.
"""

import re
from datetime import datetime

import pdfplumber


# Label -> regex pattern. Each pattern captures everything after the label
# on the same line, which matches how build_document() in
# generate_sample_documents.py lays the metadata table out.
FIELD_PATTERNS = {
    "tender_ref": r"Tender Reference No\.?:\s*(.+)",
    "department": r"Issuing Department:\s*(.+)",
    "region": r"Region:\s*(.+)",
    "category": r"Category of Work/Supply:\s*(.+)",
    "estimated_value": r"Estimated Tender Value \(INR\):\s*([\d,]+\.\d{2})",
    "award_value": r"Final Award Value \(INR\):\s*([\d,]+\.\d{2})",
    "published_date": r"Date of Publication:\s*(\d{2}-\d{2}-\d{4})",
    "award_date": r"Date of Award:\s*(\d{2}-\d{2}-\d{4})",
}


class PdfExtractionError(Exception):
    """Raised when a required field can't be found in the document."""
    pass


def _parse_money(raw: str) -> float:
    return float(raw.replace(",", "").strip())


def _parse_date(raw: str) -> str:
    """Document dates are DD-MM-YYYY; normalize to ISO (YYYY-MM-DD)."""
    return datetime.strptime(raw.strip(), "%d-%m-%Y").strftime("%Y-%m-%d")


def _extract_labeled_fields(full_text: str) -> dict:
    fields = {}
    missing = []
    for field_name, pattern in FIELD_PATTERNS.items():
        match = re.search(pattern, full_text)
        if not match:
            missing.append(field_name)
            continue
        fields[field_name] = match.group(1).strip()

    if missing:
        raise PdfExtractionError(
            f"Could not find required field(s) in document: {', '.join(missing)}"
        )

    fields["estimated_value"] = _parse_money(fields["estimated_value"])
    fields["award_value"] = _parse_money(fields["award_value"])
    fields["published_date"] = _parse_date(fields["published_date"])
    fields["award_date"] = _parse_date(fields["award_date"])
    return fields


def _extract_eligibility_text(full_text: str) -> str:
    """
    Eligibility text spans multiple lines between the "Eligibility Criteria"
    heading and the "Bid Summary" heading — doesn't fit the single-line
    label pattern above, so it gets its own extraction with DOTALL.
    """
    match = re.search(
        r"Eligibility Criteria\s*(.+?)\s*Bid Summary",
        full_text,
        re.DOTALL,
    )
    if not match:
        raise PdfExtractionError("Could not find Eligibility Criteria section.")
    # Collapse internal newlines from PDF line-wrapping into single spaces.
    text = match.group(1).strip()
    return re.sub(r"\s+", " ", text)


def _extract_bidders(tables: list) -> list[dict]:
    """
    Expects a table with header ["S.No.", "Bidder Name", "Bid Amount (INR)",
    "Status"], matching the layout generate_sample_documents.py produces.
    Returns a list of {vendor_name, bid_amount, is_winner} dicts.
    """
    for table in tables:
        if not table or len(table) < 2:
            continue
        header = [c.strip() if c else "" for c in table[0]]
        if header[:2] != ["S.No.", "Bidder Name"]:
            continue  # not the bid table — could be some other table on the page

        bidders = []
        for row in table[1:]:
            if not row or len(row) < 4:
                continue
            _, name, amount_str, status = row[:4]
            bidders.append({
                "vendor_name": name.strip(),
                "bid_amount": _parse_money(amount_str),
                "is_winner": status.strip().upper() == "AWARDED",
            })
        return bidders

    raise PdfExtractionError("Could not find a bid summary table in document.")


def parse_tender_document(pdf_path: str) -> dict:
    """
    Main entry point for Job A. Returns a dict:
        {
            "tender_ref": str,
            "department": str,
            "region": str,
            "category": str,
            "eligibility_text": str,
            "estimated_value": float,
            "award_value": float,
            "published_date": "YYYY-MM-DD",
            "award_date": "YYYY-MM-DD",
            "bidders": [{"vendor_name": str, "bid_amount": float, "is_winner": bool}, ...],
        }

    Raises PdfExtractionError if required fields or the bid table can't be found —
    deliberately loud rather than silently returning partial/wrong data, since
    this feeds a governance tool where silent mis-extraction is worse than a
    visible failure.
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            if len(pdf.pages) > 50:
                raise PdfExtractionError("Document exceeds maximum allowed length of 50 pages.")
                
            full_text = ""
            all_tables = []
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    full_text += page_text + "\n"
                all_tables.extend(page.extract_tables())
                
                # Defend against text-bomb PDFs
                if len(full_text) > 1_000_000:
                    raise PdfExtractionError("Document exceeds maximum allowed text length.")
    except Exception as e:
        if isinstance(e, PdfExtractionError):
            raise
        raise PdfExtractionError(f"File could not be parsed as a valid PDF document. Underlying error: {str(e)}")

    fields = _extract_labeled_fields(full_text)
    fields["eligibility_text"] = _extract_eligibility_text(full_text)
    fields["bidders"] = _extract_bidders(all_tables)

    return fields


if __name__ == "__main__":
    # Quick manual check against the sample documents — not a formal test
    # suite, just a way to eyeball extraction output against ground_truth.md.
    import sys
    import json

    if len(sys.argv) < 2:
        print("Usage: python pdf_extractor.py <path_to_pdf>")
        sys.exit(1)

    result = parse_tender_document(sys.argv[1])
    print(json.dumps(result, indent=2))
