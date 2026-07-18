import pytest
import pandas as pd
import math
from app.data.scoring import (
    compute_hhi_from_win_counts,
    hhi_classification,
    compute_eligibility_scores,
    compute_single_bidder_map,
    classify_pattern
)

def test_compute_hhi_from_win_counts_even_split():
    # 4 vendors, 1 win each (even split). HHI should be 10000 / 4 = 2500
    df = pd.DataFrame({
        "group": ["cat1", "cat1", "cat1", "cat1"],
        "vendor_id": [1, 2, 3, 4],
        "win_count": [1, 1, 1, 1]
    })
    res = compute_hhi_from_win_counts(df, "group")
    
    assert "cat1" in res
    assert math.isclose(res["cat1"]["hhi"], 2500.0, rel_tol=1e-5)
    assert res["cat1"]["count"] == 4
    
    # Check full precision (no rounding to integer or 2 decimals inside the function itself)
    # E.g. 3 vendors, 1 win each -> 10000/3 = 3333.3333...
    df3 = pd.DataFrame({
        "group": ["cat2", "cat2", "cat2"],
        "vendor_id": [1, 2, 3],
        "win_count": [1, 1, 1]
    })
    res3 = compute_hhi_from_win_counts(df3, "group")
    assert math.isclose(res3["cat2"]["hhi"], 3333.333333, rel_tol=1e-5)
    
def test_compute_hhi_from_win_counts_monopoly():
    # 1 vendor monopoly
    df = pd.DataFrame({
        "group": ["cat1"],
        "vendor_id": [1],
        "win_count": [50]
    })
    res = compute_hhi_from_win_counts(df, "group")
    assert math.isclose(res["cat1"]["hhi"], 10000.0, rel_tol=1e-5)

def test_hhi_classification():
    # Min count gate
    assert hhi_classification(10000.0, 9) == "INSUFFICIENT_DATA"
    
    # Low
    assert hhi_classification(1499.0, 10) == "low concentration"
    
    # Moderate
    assert hhi_classification(1500.0, 10) == "moderate concentration"
    assert hhi_classification(2500.0, 10) == "moderate concentration"
    
    # High
    assert hhi_classification(2500.1, 10) == "HIGH concentration"

def test_compute_eligibility_scores():
    # Category with 1 tender
    df1 = pd.DataFrame({
        "tender_id": [1],
        "category": ["cat1"],
        "eligibility_text": ["Some text"]
    })
    res1 = compute_eligibility_scores(df1)
    assert pd.isna(res1.iloc[0]["eligibility_deviation_score"]) or res1.iloc[0]["eligibility_deviation_score"] is None
    
    # Identical vs different text
    df2 = pd.DataFrame({
        "tender_id": [1, 2, 3],
        "category": ["cat2", "cat2", "cat2"],
        "eligibility_text": [
            "Vendor must supply generic office chairs.",
            "Vendor must supply generic office chairs.",
            "Vendor must supply specifically Herman Miller Aeron size B chairs."
        ]
    })
    res2 = compute_eligibility_scores(df2)
    dev_1 = res2.iloc[0]["eligibility_deviation_score"]
    dev_2 = res2.iloc[1]["eligibility_deviation_score"]
    dev_3 = res2.iloc[2]["eligibility_deviation_score"]
    
    # Identical texts should have lower deviation than the different one
    assert dev_1 < dev_3
    assert dev_2 < dev_3

def test_compute_single_bidder_map():
    all_tenders = [1, 2, 3, 4]
    single_bidders = {2, 4}
    res = compute_single_bidder_map(single_bidders, all_tenders)
    
    assert res[1] is False
    assert res[2] is True
    assert res[3] is False
    assert res[4] is True

def test_classify_pattern():
    # Insufficient data
    assert classify_pattern("INSUFFICIENT_DATA", "HIGH concentration", 0.5) == "Insufficient Data"
    assert classify_pattern("low concentration", "INSUFFICIENT_DATA", 0.1) == "Insufficient Data"
    
    # Concentrated Pattern (High, High, High Deviation)
    assert classify_pattern("HIGH concentration", "HIGH concentration", 0.5, deviation_threshold=0.4) == "Concentrated Pattern"
    
    # Usual Pattern (Low, Low, Low Deviation)
    assert classify_pattern("low concentration", "low concentration", 0.2, deviation_threshold=0.4) == "Usual Pattern"
    
    # Mixed Signal
    # High HHI but low deviation
    assert classify_pattern("HIGH concentration", "HIGH concentration", 0.1, deviation_threshold=0.4) == "Mixed Signal"
    # Low HHI but high deviation
    assert classify_pattern("low concentration", "low concentration", 0.8, deviation_threshold=0.4) == "Mixed Signal"
    # Moderate HHI
    assert classify_pattern("moderate concentration", "low concentration", 0.2, deviation_threshold=0.4) == "Mixed Signal"
    # Null deviation (e.g., category with 1 tender) but high HHIs
    assert classify_pattern("HIGH concentration", "HIGH concentration", None) == "Mixed Signal"
