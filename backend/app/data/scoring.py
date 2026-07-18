"""
Pure scoring functions — argument-only, no DB knowledge, no rounding
(rounding happens only at report-assembly time, in the service layer).
"""

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


def compute_hhi_from_win_counts(win_counts: pd.DataFrame, group_col: str) -> dict:
    """
    win_counts: DataFrame with columns [group_col, 'vendor_id', 'win_count'].
    Returns dict: group_value -> {'hhi': float, 'count': int}
    """
    stats_by_group = {}
    for group_value, group_df in win_counts.groupby(group_col):
        total_wins = int(group_df["win_count"].sum())
        if total_wins == 0:
            continue
        shares_pct = (group_df["win_count"] / total_wins) * 100
        stats_by_group[group_value] = {
            "hhi": float((shares_pct ** 2).sum()),
            "count": total_wins
        }
    return stats_by_group


def hhi_classification(hhi: float, tender_count: int) -> str:
    """DOJ-style thresholds with minimum-count gate for statistical validity."""
    if tender_count < 10:
        return "INSUFFICIENT_DATA"
    if hhi < 1500:
        return "low concentration"
    elif hhi <= 2500:
        return "moderate concentration"
    else:
        return "HIGH concentration"


_model = None

def get_embeddings(texts: list[str]) -> np.ndarray:
    """
    PLUGGABLE embedding function — swapped to sentence-transformers/SBERT.
    Uses all-MiniLM-L6-v2.
    """
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model.encode(texts)


def compute_eligibility_scores(eligibility_df: pd.DataFrame) -> pd.DataFrame:
    """
    eligibility_df: columns [tender_id, category, eligibility_text].
    Returns eligibility_df with an added 'eligibility_deviation_score' column,
    full precision, None where deviation is undefined (category has only 1 tender).
    """
    embeddings = get_embeddings(eligibility_df["eligibility_text"].tolist())
    eligibility_df = eligibility_df.reset_index(drop=True)

    deviation_scores = []
    for idx, row in eligibility_df.iterrows():
        same_category_idx = eligibility_df.index[eligibility_df["category"] == row["category"]].tolist()

        if len(same_category_idx) <= 1:
            deviation_scores.append(None)
            continue

        this_vec = embeddings[idx].reshape(1, -1)
        category_baseline = embeddings[same_category_idx].mean(axis=0).reshape(1, -1)
        sim = cosine_similarity(this_vec, category_baseline)[0][0]
        deviation_scores.append(float(1 - sim))

    eligibility_df["eligibility_deviation_score"] = deviation_scores
    return eligibility_df


def compute_single_bidder_map(tender_ids: set, all_tender_ids: list) -> dict:
    return {tid: (tid in tender_ids) for tid in all_tender_ids}
