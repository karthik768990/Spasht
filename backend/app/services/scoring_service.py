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
    for _, t in merged.iterrows():
        dept_stat = dept_hhi.get(t["department"], {"hhi": 0.0, "count": 0})
        cat_stat = cat_hhi.get(t["category"], {"hhi": 0.0, "count": 0})
        
        dh = dept_stat["hhi"]
        dc = dept_stat["count"]
        ch = cat_stat["hhi"]
        cc = cat_stat["count"]
        
        dh_label = hhi_classification(dh, dc)
        ch_label = hhi_classification(ch, cc)
        elig_score = (
            round(t["eligibility_deviation_score"], 4)
            if pd.notna(t["eligibility_deviation_score"]) else None
        )
        
        rows.append(dict(
            tender_id=t["tender_id"],
            department=t["department"],
            category=t["category"],
            winning_vendor=t["winning_vendor"],
            dept_hhi=round(dh, 2) if dc > 0 else 0.0,
            dept_hhi_label=dh_label,
            category_hhi=round(ch, 2) if cc > 0 else 0.0,
            category_hhi_label=ch_label,
            single_bidder_flag=single_bidder_map.get(t["tender_id"], False),
            eligibility_deviation_score=elig_score,
            pattern_classification=classify_pattern(dh_label, ch_label, elig_score)
        ))
    return pd.DataFrame(rows)
