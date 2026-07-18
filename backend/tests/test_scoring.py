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
    # Insufficient data (Check A verified - this only hits if total wins < 10)
    assert classify_pattern("INSUFFICIENT_DATA", "HIGH concentration", 0.5) == "Insufficient Data"
    assert classify_pattern("low concentration", "INSUFFICIENT_DATA", 0.1) == "Insufficient Data"
    
    # 1. General Admin / IT Hardware: competitive, low HHI -> Usual Pattern
    assert classify_pattern("low concentration", "low concentration", 0.1) == "Usual Pattern"
    
    # 2. PWD Zone 4 / Road Construction: ~85% one vendor (High HHI), some narrow eligibility text (High Deviation)
    assert classify_pattern("HIGH concentration", "HIGH concentration", 0.6) == "Concentrated Pattern — Strong Signal"
    
    # 3. PWD Zone 4 / Road Construction (alternative case): High HHI, but normal text -> Partial Signal
    assert classify_pattern("HIGH concentration", "HIGH concentration", 0.1) == "Concentrated Pattern — Partial Signal"
    
    # 4. Health Dept / Medical Supplies: 50/30/20 split -> likely Moderate Pattern (assuming HHI between 1500 and 2500)
    # HHI = 50^2 + 30^2 + 20^2 = 2500 + 900 + 400 = 3800 (Wait, 3800 is High, let's use 40/40/20 = 1600+1600+400=3600...
    # If the label returns moderate (say HHI 2000), it should be Moderate Pattern
    assert classify_pattern("moderate concentration", "moderate concentration", 0.2) == "Moderate Pattern"
    
    # 5. Education Dept / School Furniture: ~65/35 gray-zone -> HHI = 4225 + 1225 = 5450 (High)
    # Wait, 5450 is HIGH concentration. If it's High concentration but low deviation -> Partial Signal.
    # If it was moderate concentration and low deviation -> Moderate Pattern.
    assert classify_pattern("HIGH concentration", "moderate concentration", 0.2) == "Concentrated Pattern — Partial Signal"
    
    # Test High Eligibility Deviation alone -> Partial Signal
    assert classify_pattern("low concentration", "low concentration", 0.8) == "Concentrated Pattern — Partial Signal"
