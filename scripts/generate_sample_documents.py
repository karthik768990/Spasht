"""
Generates simulated "Tender Award Summary" PDF documents — the kind of
document a user would upload for the app to parse and score.

These are formatted like real Indian government e-procurement result
notices (fictional entities only — no real departments/vendors), and are
deliberately varied to exercise different cases your Parser will need to
handle correctly:

  1. doc_it_hardware_normal.pdf
       - Existing department/category (General Admin / IT Hardware)
       - NEW vendor not yet in the seeded DB ("Nova Systems Pvt Ltd")
       - Tests: does the Parser/insert logic correctly create a new
         vendor row rather than failing or silently mismatching?

  2. doc_road_construction_rigged.pdf
       - Existing department/category (PWD Zone 4 / Road Construction)
       - Winner = the already-dominant seeded vendor (Suvidha Constructions)
       - Narrow eligibility text (matches the planted-anomaly pattern)
       - Tests: does inserting this correctly PUSH UP an already-high
         dept/category HHI even further, and does eligibility deviation
         correctly flag the narrow text?

  3. doc_medical_single_bidder.pdf
       - Existing department/category (Health Dept / Medical Supplies)
       - Only ONE bidder listed
       - Tests: single-bidder detection on a freshly uploaded document

  4. doc_school_furniture_grayzone.pdf
       - Existing department/category (Education Dept / School Furniture)
       - Winner = the moderately-dominant vendor (Vidya Furnishings)
       - Tests: does one more data point measurably move a gray-zone HHI?

  5. doc_streetlighting_new_department.pdf
       - ENTIRELY NEW department AND category, not in the seeded DB at all
       - 3 bidders, competitive spread
       - Tests: does the Parser/insert path correctly handle a brand-new
         department + category (insert new department row, new category
         value) without breaking, and does HHI correctly treat it as a
         fresh, low-sample group?

A ground_truth.md file is generated alongside listing the exact fields
each PDF encodes, so you can verify your Parser's extraction output
field-by-field rather than eyeballing it.

USAGE
-----
    python generate_sample_documents.py
    # outputs into ./sample_documents/
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)

OUTPUT_DIR = "sample_documents"
os.makedirs(OUTPUT_DIR, exist_ok=True)

styles = getSampleStyleSheet()
title_style = ParagraphStyle("TitleStyle", parent=styles["Title"], fontSize=14)
heading_style = ParagraphStyle("HeadingStyle", parent=styles["Heading2"], fontSize=11,
                                spaceBefore=10, spaceAfter=4)
normal_style = styles["Normal"]
label_style = ParagraphStyle("LabelStyle", parent=styles["Normal"], fontName="Helvetica-Bold")


def build_document(filename, tender_ref, department, region, category,
                    eligibility_text, estimated_value, award_value,
                    published_date, award_date, bidders):
    """
    bidders: list of (vendor_name, bid_amount, is_winner) tuples
    """
    path = os.path.join(OUTPUT_DIR, filename)
    doc = SimpleDocTemplate(path, pagesize=A4,
                             topMargin=2*cm, bottomMargin=2*cm,
                             leftMargin=2*cm, rightMargin=2*cm)
    story = []

    story.append(Paragraph("TENDER AWARD SUMMARY", title_style))
    story.append(Paragraph("(Public Procurement Result Notice)", normal_style))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", color=colors.grey))
    story.append(Spacer(1, 10))

    meta_rows = [
        ["Tender Reference No.:", tender_ref],
        ["Issuing Department:", department],
        ["Region:", region],
        ["Category of Work/Supply:", category],
        ["Estimated Tender Value (INR):", f"{estimated_value:,.2f}"],
        ["Final Award Value (INR):", f"{award_value:,.2f}"],
        ["Date of Publication:", published_date],
        ["Date of Award:", award_date],
    ]
    meta_table = Table(meta_rows, colWidths=[6.5*cm, 9*cm])
    meta_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 14))

    story.append(Paragraph("Eligibility Criteria", heading_style))
    story.append(Paragraph(eligibility_text, normal_style))
    story.append(Spacer(1, 14))

    story.append(Paragraph("Bid Summary", heading_style))
    bid_rows = [["S.No.", "Bidder Name", "Bid Amount (INR)", "Status"]]
    for i, (name, amount, is_winner) in enumerate(bidders, start=1):
        status = "AWARDED" if is_winner else "NOT SELECTED"
        bid_rows.append([str(i), name, f"{amount:,.2f}", status])

    bid_table = Table(bid_rows, colWidths=[1.5*cm, 7*cm, 4*cm, 3*cm])
    bid_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e0e0e0")),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(bid_table)
    story.append(Spacer(1, 16))

    story.append(HRFlowable(width="100%", color=colors.grey))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "This is a system-generated summary published for transparency purposes "
        "in accordance with public procurement disclosure norms.",
        ParagraphStyle("Footer", parent=normal_style, fontSize=8, textColor=colors.grey)
    ))

    doc.build(story)
    print(f"[created] {path}")


# ---------------------------------------------------------------------------
# Document 1 — IT Hardware, competitive, NEW vendor
# ---------------------------------------------------------------------------
build_document(
    filename="doc_it_hardware_normal.pdf",
    tender_ref="GA/ZNA/ITH/2026/0142",
    department="General Admin",
    region="Zone A",
    category="IT Hardware",
    eligibility_text=(
        "Bidder must have at least 3 years experience supplying desktop "
        "computers and printers to government offices, and must hold a "
        "valid GST registration."
    ),
    estimated_value=545000,
    award_value=522000,
    published_date="12-01-2026",
    award_date="28-01-2026",
    bidders=[
        ("Nova Systems Pvt Ltd", 522000, True),
        ("Beta Computech", 538000, False),
        ("Gamma IT Solutions", 551000, False),
    ],
)

# ---------------------------------------------------------------------------
# Document 2 — Road Construction, rigged pattern, dominant seeded vendor
# ---------------------------------------------------------------------------
build_document(
    filename="doc_road_construction_rigged.pdf",
    tender_ref="PWD/ZN4/RC/2026/0091",
    department="PWD Zone 4",
    region="Zone D",
    category="Road Construction",
    eligibility_text=(
        "Contractor must hold Class-A road construction license, have "
        "completed at least 5 km of rural road work, and must own a "
        "proprietary asphalt-mixing unit model AX-500."
    ),
    estimated_value=9350000,
    award_value=9210000,
    published_date="03-02-2026",
    award_date="22-02-2026",
    bidders=[
        ("Suvidha Constructions Pvt Ltd", 9210000, True),
        ("Nirman Infra Works", 9480000, False),
    ],
)

# ---------------------------------------------------------------------------
# Document 3 — Medical Supplies, single bidder
# ---------------------------------------------------------------------------
build_document(
    filename="doc_medical_single_bidder.pdf",
    tender_ref="HD/ZNC/MS/2026/0217",
    department="Health Dept",
    region="Zone C",
    category="Medical Supplies",
    eligibility_text=(
        "Vendor must be a licensed pharmaceutical distributor registered "
        "with the state drug controller."
    ),
    estimated_value=312000,
    award_value=305000,
    published_date="15-01-2026",
    award_date="30-01-2026",
    bidders=[
        ("MedSure Distributors", 305000, True),
    ],
)

# ---------------------------------------------------------------------------
# Document 4 — School Furniture, gray-zone dominant vendor
# ---------------------------------------------------------------------------
build_document(
    filename="doc_school_furniture_grayzone.pdf",
    tender_ref="ED/ZNE/SF/2026/0064",
    department="Education Dept",
    region="Zone E",
    category="School Furniture",
    eligibility_text=(
        "Bidder must supply ISI-certified school furniture and have prior "
        "experience with government educational institution contracts."
    ),
    estimated_value=210000,
    award_value=198500,
    published_date="20-01-2026",
    award_date="05-02-2026",
    bidders=[
        ("Vidya Furnishings", 198500, True),
        ("Study Interiors Pvt Ltd", 205000, False),
    ],
)

# ---------------------------------------------------------------------------
# Document 5 — Street Lighting, ENTIRELY NEW department + category
# ---------------------------------------------------------------------------
build_document(
    filename="doc_streetlighting_new_department.pdf",
    tender_ref="MC/ZN7/SL/2026/0033",
    department="Municipal Corporation Zone 7",
    region="Zone G",
    category="Street Lighting",
    eligibility_text=(
        "Bidder must have at least 2 years experience installing or "
        "maintaining public LED street lighting systems for a municipal body."
    ),
    estimated_value=780000,
    award_value=745000,
    published_date="18-02-2026",
    award_date="10-03-2026",
    bidders=[
        ("Brightway Electricals", 745000, True),
        ("Luminous Public Works", 762000, False),
        ("CityGlow Contractors", 770000, False),
    ],
)


# ---------------------------------------------------------------------------
# Ground truth file — exact fields each document encodes
# ---------------------------------------------------------------------------
ground_truth = """\
# Sample Document Ground Truth

Use this to verify your Parser's extraction output field-by-field against
what each PDF actually encodes. Don't eyeball the PDF and guess — check
your Parser's output against this file directly.

## doc_it_hardware_normal.pdf
- tender_ref: GA/ZNA/ITH/2026/0142
- department: General Admin (EXISTING in seeded DB)
- category: IT Hardware (EXISTING)
- region: Zone A
- estimated_value: 545000.00
- award_value: 522000.00
- published_date: 2026-01-12
- award_date: 2026-01-28
- bidders: Nova Systems Pvt Ltd (522000, WINNER, NEW vendor not in seeded DB),
           Beta Computech (538000, not selected, existing vendor),
           Gamma IT Solutions (551000, not selected, existing vendor)
- Test focus: new-vendor creation on insert

## doc_road_construction_rigged.pdf
- tender_ref: PWD/ZN4/RC/2026/0091
- department: PWD Zone 4 (EXISTING)
- category: Road Construction (EXISTING)
- region: Zone D
- estimated_value: 9350000.00
- award_value: 9210000.00
- published_date: 2026-02-03
- award_date: 2026-02-22
- bidders: Suvidha Constructions Pvt Ltd (9210000, WINNER, existing dominant vendor),
           Nirman Infra Works (9480000, not selected)
- Test focus: inserting this should push dept_hhi and category_hhi for
  PWD Zone 4 / Road Construction even higher than the seeded baseline;
  eligibility_deviation_score should flag the narrow "AX-500" text

## doc_medical_single_bidder.pdf
- tender_ref: HD/ZNC/MS/2026/0217
- department: Health Dept (EXISTING)
- category: Medical Supplies (EXISTING)
- region: Zone C
- estimated_value: 312000.00
- award_value: 305000.00
- published_date: 2026-01-15
- award_date: 2026-01-30
- bidders: MedSure Distributors (305000, WINNER) — ONLY bidder
- Test focus: single_bidder_flag should be True for this tender

## doc_school_furniture_grayzone.pdf
- tender_ref: ED/ZNE/SF/2026/0064
- department: Education Dept (EXISTING)
- category: School Furniture (EXISTING)
- region: Zone E
- estimated_value: 210000.00
- award_value: 198500.00
- published_date: 2026-01-20
- award_date: 2026-02-05
- bidders: Vidya Furnishings (198500, WINNER, existing dominant vendor),
           Study Interiors Pvt Ltd (205000, not selected)
- Test focus: one more win for the already-dominant vendor should nudge
  the gray-zone HHI further toward "high" — good for testing threshold
  sensitivity

## doc_streetlighting_new_department.pdf
- tender_ref: MC/ZN7/SL/2026/0033
- department: Municipal Corporation Zone 7 (BRAND NEW, not in seeded DB)
- category: Street Lighting (BRAND NEW, not in seeded DB)
- region: Zone G
- estimated_value: 780000.00
- award_value: 745000.00
- published_date: 2026-02-18
- award_date: 2026-03-10
- bidders: Brightway Electricals (745000, WINNER),
           Luminous Public Works (762000, not selected),
           CityGlow Contractors (770000, not selected)
- Test focus: Parser/insert logic must create a NEW department row; HHI
  for this group will be based on a sample of 1 tender — a good live
  check of your earlier decision on how to handle small-sample HHI
  (insufficient-data threshold vs relative baseline)
"""

with open(os.path.join(OUTPUT_DIR, "ground_truth.md"), "w") as f:
    f.write(ground_truth)
print(f"[created] {os.path.join(OUTPUT_DIR, 'ground_truth.md')}")
