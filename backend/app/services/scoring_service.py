"""
scoring_service.py — Orchestrates the assembly of the final analysis report.
Fetches pre-aggregated data from the provided TenderDataSource, applies pure
scoring functions from data/scoring.py, and merges the results into a final Pandas DataFrame.
"""

from ..data.base import TenderDataSource
import pandas as pd
from ..data.scoring import (
    compute_hhi_from_win_counts,
    compute_eligibility_scores,
    compute_single_bidder_map,
    hhi_classification,
    classify_pattern,
)



def build_report(source: TenderDataSource) -> pd.DataFrame:
    dept_win_counts = source.get_department_win_counts()
    cat_win_counts = source.get_category_win_counts()
    single_bidder_ids = source.get_single_bidder_tender_ids()
    eligibility_df = source.get_eligibility_texts()
    summary = source.get_tender_summary()

    dept_hhi = compute_hhi_from_win_counts(dept_win_counts, "department")
    cat_hhi = compute_hhi_from_win_counts(cat_win_counts, "category")
    eligibility_scored = compute_eligibility_scores(eligibility_df)
    single_bidder_map = compute_single_bidder_map(single_bidder_ids, summary["tender_id"].tolist())

    merged = summary.merge(
        eligibility_scored[["tender_id", "eligibility_deviation_score"]],
        on="tender_id", how="left"
    )

    rows = []
    for _, tender_row in merged.iterrows():
        dept_stat = dept_hhi.get(tender_row["department"], {"hhi": 0.0, "count": 0})
        cat_stat = cat_hhi.get(tender_row["category"], {"hhi": 0.0, "count": 0})
        
        dept_hhi_val = dept_stat["hhi"]
        dept_count = dept_stat["count"]
        cat_hhi_val = cat_stat["hhi"]
        cat_count = cat_stat["count"]
        
        dept_hhi_label = hhi_classification(dept_hhi_val, dept_count)
        cat_hhi_label = hhi_classification(cat_hhi_val, cat_count)
        elig_score = (
            round(tender_row["eligibility_deviation_score"], 4)
            if pd.notna(tender_row["eligibility_deviation_score"]) else None
        )
        
        rows.append(dict(
            tender_id=tender_row["tender_id"],
            department=tender_row["department"],
            category=tender_row["category"],
            winning_vendor=tender_row["winning_vendor"],
            dept_hhi=round(dept_hhi_val, 2) if dept_count > 0 else 0.0,
            dept_hhi_label=dept_hhi_label,
            category_hhi=round(cat_hhi_val, 2) if cat_count > 0 else 0.0,
            category_hhi_label=cat_hhi_label,
            single_bidder_flag=single_bidder_map.get(tender_row["tender_id"], False),
            eligibility_deviation_score=elig_score,
            pattern_classification=classify_pattern(dept_hhi_label, cat_hhi_label, elig_score)
        ))
    return pd.DataFrame(rows)
