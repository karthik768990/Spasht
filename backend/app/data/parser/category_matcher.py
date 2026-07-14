"""
category_matcher.py — Job B: decide whether a category string extracted
from an uploaded document (Job A's output) matches an existing canonical
category in the system, or represents a genuinely new one.

Deliberately reuses get_embeddings() from data/scoring.py rather than
building a second, parallel similarity pipeline — same embedding function
that scores eligibility-text deviation is used here, satisfying the
"reuse modules, don't recreate them" rule. If you swap TF-IDF for
sentence-transformers/SBERT later, both this module and eligibility
scoring upgrade together automatically.

IMPORTANT LIMITATION (be aware of this, don't just trust it blindly):
TF-IDF is a bag-of-words method with no shared vocabulary awareness across
short phrases. Two category names sharing zero words ("Road Construction"
vs "Highway & Roadworks") will score LOW similarity even though a human
reader would consider them the same category — TF-IDF has no notion that
"Road" and "Highway" are related concepts. This is a much bigger practical
problem for Job B (matching short 2-4 word category names) than it is for
eligibility-text deviation (matching full sentences, where more shared
vocabulary naturally exists). Test this yourself against realistic
category-name variants before trusting it — if it's too unreliable at this
scale, that's a real reason to prioritize the SBERT swap for THIS module
specifically, even before upgrading eligibility scoring.
"""

from ..scoring import get_embeddings
from sklearn.metrics.pairwise import cosine_similarity


def match_category(
    extracted_category: str,
    canonical_categories: list[str],
    threshold: float = 0.6,
) -> dict:
    """
    Returns:
        {
            "matched_category": str,   # canonical name to use, or the
                                        # extracted text itself if judged new
            "similarity_score": float, # 0-1, best match found
            "is_new_category": bool,   # True if below threshold
        }

    No side effects, no DB access — pure function, same principle as the
    scoring functions: takes exactly the arguments it needs and nothing else.
    """
    if not canonical_categories:
        # No existing categories to compare against — necessarily new.
        return {
            "matched_category": extracted_category,
            "similarity_score": 1.0,
            "is_new_category": True,
        }

    # Exact match short-circuit — cheap, and avoids TF-IDF noise entirely
    # for the common case where the document uses your exact wording.
    for canonical in canonical_categories:
        if extracted_category.strip().lower() == canonical.strip().lower():
            return {
                "matched_category": canonical,
                "similarity_score": 1.0,
                "is_new_category": False,
            }

    texts = canonical_categories + [extracted_category]
    embeddings = get_embeddings(texts)
    canonical_vecs = embeddings[:-1]
    query_vec = embeddings[-1].reshape(1, -1)

    similarities = cosine_similarity(query_vec, canonical_vecs)[0]
    best_idx = int(similarities.argmax())
    best_score = float(similarities[best_idx])

    is_new = best_score < threshold

    return {
        "matched_category": canonical_categories[best_idx] if not is_new else extracted_category,
        "similarity_score": best_score,
        "is_new_category": is_new,
    }


if __name__ == "__main__":
    # Manual check — deliberately includes both an exact match AND a
    # phrasing variant, so you can see the TF-IDF limitation described
    # above for yourself rather than take the warning on faith.
    canonical = [
        "IT Hardware", "Road Construction", "Medical Supplies",
        "Pipeline Maintenance", "School Furniture",
    ]

    test_cases = [
        "Road Construction",           # exact match
        "Highway & Roadworks",         # phrasing variant of Road Construction
        "Rural Road Construction",     # shares "Road Construction" as substring
        "Street Lighting",             # genuinely new category
    ]

    for case in test_cases:
        result = match_category(case, canonical)
        print(f"{case!r:35} -> {result}")
