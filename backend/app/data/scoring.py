"""
Pure scoring functions — argument-only, no DB knowledge, no rounding
(rounding happens only at report-assembly time, in the service layer).
"""

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def compute_hhi_from_win_counts(win_counts: pd.DataFrame, group_col: str) -> dict:
    """
    win_counts: DataFrame with columns [group_col, 'vendor_id', 'win_count'].
    Returns full-precision HHI per group value (0-10000 scale).
    """
    hhi_by_group = {}
    for group_value, group_df in win_counts.groupby(group_col):
        total_wins = group_df["win_count"].sum()
        shares_pct = (group_df["win_count"] / total_wins) * 100
        hhi_by_group[group_value] = float((shares_pct ** 2).sum())
    return hhi_by_group


def hhi_classification(hhi: float) -> str:
    """DOJ-style thresholds: <1500 low, 1500-2500 moderate, >2500 high."""
    if hhi < 1500:
        return "low concentration"
    elif hhi <= 2500:
        return "moderate concentration"
    else:
        return "HIGH concentration"


def get_embeddings(texts: list[str]) -> np.ndarray:
    """
    PLUGGABLE embedding function — TF-IDF placeholder for now.
    Swap the body for sentence-transformers/SBERT once decided; nothing
    downstream (compute_eligibility_scores, category_matcher) needs to change,
    since both only call this function and do cosine similarity on the result.
    """
    vectorizer = TfidfVectorizer(stop_words="english")
    return vectorizer.fit_transform(texts).toarray()


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
