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


# Stress-Test Documents — Ground Truth Addendum

## doc_large_bidder_pool.pdf
- tender_ref: GA/ZNA/ITH/2026/0198
- department: General Admin (EXISTING), category: IT Hardware (EXISTING)
- estimated_value: 610000.00, award_value: 589000.00
- published_date: 2026-03-05, award_date: 2026-03-21
- bidders: 9 total — winner is Alpha Systems Pvt Ltd (589000)
- Test focus: bid table with 9 rows — confirms parser/UI handles a large
  bidder list without truncation or layout breakage

## doc_tied_bids.pdf
- tender_ref: HD/ZNC/MS/2026/0289
- department: Health Dept (EXISTING), category: Medical Supplies (EXISTING)
- estimated_value: 340000.00, award_value: 318000.00
- published_date: 2026-03-10, award_date: 2026-03-26
- bidders: MedSure Distributors (318000, WINNER), CarePlus Pharma Supply
  (318000, NOT selected) — IDENTICAL bid amounts
- Test focus: confirms winner determination relies on the explicit
  AWARDED/NOT SELECTED status column, not on "lowest bid amount" inference
  (which would be ambiguous/wrong here since both amounts are equal)

## doc_long_eligibility_text.pdf
- tender_ref: PWD/ZN4/RC/2026/0305
- department: PWD Zone 4 (EXISTING), category: Road Construction (EXISTING)
- estimated_value: 9800000.00, award_value: 9450000.00
- published_date: 2026-03-12, award_date: 2026-04-02
- bidders: Nirman Infra Works (9450000, WINNER), Pathway Builders
  (9600000, not selected)
- Test focus: eligibility text is long enough to push the document onto a
  SECOND PAGE — confirms the extractor correctly concatenates text across
  multiple pdfplumber pages before running the eligibility-text regex,
  rather than only reading page 1


# Stress-Test Documents — Ground Truth Addendum

## doc_large_bidder_pool.pdf
- tender_ref: GA/ZNA/ITH/2026/0198
- department: General Admin (EXISTING), category: IT Hardware (EXISTING)
- estimated_value: 610000.00, award_value: 589000.00
- published_date: 2026-03-05, award_date: 2026-03-21
- bidders: 9 total — winner is Alpha Systems Pvt Ltd (589000)
- Test focus: bid table with 9 rows — confirms parser/UI handles a large
  bidder list without truncation or layout breakage

## doc_tied_bids.pdf
- tender_ref: HD/ZNC/MS/2026/0289
- department: Health Dept (EXISTING), category: Medical Supplies (EXISTING)
- estimated_value: 340000.00, award_value: 318000.00
- published_date: 2026-03-10, award_date: 2026-03-26
- bidders: MedSure Distributors (318000, WINNER), CarePlus Pharma Supply
  (318000, NOT selected) — IDENTICAL bid amounts
- Test focus: confirms winner determination relies on the explicit
  AWARDED/NOT SELECTED status column, not on "lowest bid amount" inference
  (which would be ambiguous/wrong here since both amounts are equal)

## doc_long_eligibility_text.pdf
- tender_ref: PWD/ZN4/RC/2026/0305
- department: PWD Zone 4 (EXISTING), category: Road Construction (EXISTING)
- estimated_value: 9800000.00, award_value: 9450000.00
- published_date: 2026-03-12, award_date: 2026-04-02
- bidders: Nirman Infra Works (9450000, WINNER), Pathway Builders
  (9600000, not selected)
- Test focus: eligibility text is long enough to push the document onto a
  SECOND PAGE — confirms the extractor correctly concatenates text across
  multiple pdfplumber pages before running the eligibility-text regex,
  rather than only reading page 1


# Stress-Test Documents — Ground Truth Addendum

## doc_large_bidder_pool.pdf
- tender_ref: GA/ZNA/ITH/2026/0198
- department: General Admin (EXISTING), category: IT Hardware (EXISTING)
- estimated_value: 610000.00, award_value: 589000.00
- published_date: 2026-03-05, award_date: 2026-03-21
- bidders: 9 total — winner is Alpha Systems Pvt Ltd (589000)
- Test focus: bid table with 9 rows — confirms parser/UI handles a large
  bidder list without truncation or layout breakage

## doc_tied_bids.pdf
- tender_ref: HD/ZNC/MS/2026/0289
- department: Health Dept (EXISTING), category: Medical Supplies (EXISTING)
- estimated_value: 340000.00, award_value: 318000.00
- published_date: 2026-03-10, award_date: 2026-03-26
- bidders: MedSure Distributors (318000, WINNER), CarePlus Pharma Supply
  (318000, NOT selected) — IDENTICAL bid amounts
- Test focus: confirms winner determination relies on the explicit
  AWARDED/NOT SELECTED status column, not on "lowest bid amount" inference
  (which would be ambiguous/wrong here since both amounts are equal)

## doc_long_eligibility_text.pdf
- tender_ref: PWD/ZN4/RC/2026/0305
- department: PWD Zone 4 (EXISTING), category: Road Construction (EXISTING)
- estimated_value: 9800000.00, award_value: 9450000.00
- published_date: 2026-03-12, award_date: 2026-04-02
- bidders: Nirman Infra Works (9450000, WINNER), Pathway Builders
  (9600000, not selected)
- Test focus: eligibility text is long enough to push the document onto a
  SECOND PAGE — confirms the extractor correctly concatenates text across
  multiple pdfplumber pages before running the eligibility-text regex,
  rather than only reading page 1
