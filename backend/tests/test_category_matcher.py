from app.data.parser.category_matcher import match_category

def test_category_matcher():
    canonical = [
        "IT Hardware", 
        "Road Construction", 
        "Medical Supplies",
        "Pipeline Maintenance", 
        "School Furniture",
    ]
    
    # 1. Exact string match
    res1 = match_category("Road Construction", canonical)
    assert res1["is_new_category"] is False
    assert res1["similarity_score"] == 1.0
    assert res1["matched_category"] == "Road Construction"
    
    # 2. Match with substring / variations (e.g., Rural Road Construction)
    res2 = match_category("Rural Road Construction", canonical)
    assert res2["is_new_category"] is False
    assert res2["matched_category"] == "Road Construction"
    
    # 3. Genuinely new category
    res3 = match_category("Street Lighting", canonical)
    assert res3["is_new_category"] is True
    assert res3["matched_category"] == "Street Lighting"
    
    # 4. Post-SBERT swap fix check
    res4 = match_category("Highway & Roadworks", canonical)
    assert res4["is_new_category"] is False
    assert res4["matched_category"] == "Road Construction"
