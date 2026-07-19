import pytest
import os
import pandas as pd
from app.data.postgres_source import PostgresTenderDataSource
from app.services.parsing_service import process_upload
from app.services.scoring_service import build_report

SAMPLE_DOCS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "sample_documents")

# To run this test, you need a seeded database and the DATABASE_URL environment variable set.
@pytest.fixture
def db_source():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        pytest.skip("DATABASE_URL not set; skipping integration tests.")
    return PostgresTenderDataSource(db_url)

def test_integration_upload_new_department(db_source):
    # Uploading doc_streetlighting_new_department.pdf
    pdf_path = os.path.join(SAMPLE_DOCS_DIR, "doc_streetlighting_new_department.pdf")
    
    tender_id = process_upload(pdf_path, db_source)
    assert tender_id is not None
    
    # Check HHI for the new group (should be INSUFFICIENT_DATA because n=1)
    report = build_report(db_source)
    tender_row = report[report["tender_id"] == tender_id].iloc[0]
    
    assert tender_row["department"] == "Municipal Corporation Zone 7"
    assert tender_row["category"] == "Street Lighting"
    
    # Assert minimum-count gate, accounting for repeated test runs on a persistent DB
    dept_win_counts = db_source.get_department_win_counts()
    dept_count = dept_win_counts[dept_win_counts["department"] == "Municipal Corporation Zone 7"]["win_count"].sum()
    
    if dept_count < 10:
        assert tender_row["dept_hhi_label"] == "INSUFFICIENT_DATA"
        assert tender_row["category_hhi_label"] == "INSUFFICIENT_DATA"
    else:
        assert tender_row["dept_hhi_label"] == "HIGH concentration"
        assert tender_row["category_hhi_label"] == "HIGH concentration"

def test_integration_upload_rigged(db_source):
    # Get baseline HHI for PWD Zone 4 / Road Construction
    baseline_report = build_report(db_source)
    baseline_rows = baseline_report[
        (baseline_report["department"] == "PWD Zone 4") &
        (baseline_report["category"] == "Road Construction")
    ]
    if baseline_rows.empty:
        pytest.skip("Baseline data not seeded. Run seed script first.")
        
    pre_dept_hhi = baseline_rows.iloc[0]["dept_hhi"]
    pre_cat_hhi = baseline_rows.iloc[0]["category_hhi"]
    
    # Upload doc_road_construction_rigged.pdf
    pdf_path = os.path.join(SAMPLE_DOCS_DIR, "doc_road_construction_rigged.pdf")
    tender_id = process_upload(pdf_path, db_source)
    
    # Get new HHI
    post_report = build_report(db_source)
    post_rows = post_report[
        (post_report["department"] == "PWD Zone 4") &
        (post_report["category"] == "Road Construction")
    ]
    
    post_dept_hhi = post_rows.iloc[0]["dept_hhi"]
    post_cat_hhi = post_rows.iloc[0]["category_hhi"]
    
    # Assert the post-upload HHI is STRICTLY greater than pre-upload HHI
    assert post_dept_hhi > pre_dept_hhi
    assert post_cat_hhi > pre_cat_hhi
