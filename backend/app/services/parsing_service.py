from ..data.base import TenderDataSource
from ..data.parser.pdf_extractor import parse_tender_document
from ..data.parser.category_matcher import match_category
from ..data.in_memory import InMemoryTenderDataSource
from datetime import datetime

def process_upload(pdf_path: str, source: TenderDataSource) -> int:
    """
    Orchestrates the extraction of a tender PDF and inserts it into the database.
    Returns the newly created tender_id.
    """
    # 1. Extract raw data from PDF
    extracted = parse_tender_document(pdf_path)
    
    # 2. Match category against canonical ones
    canonical_cats = source.get_canonical_categories()
    match_result = match_category(extracted["category"], canonical_cats)
    final_category = match_result["matched_category"]
    
    # 3. Create or get Department
    dept_id = source.get_or_create_department(extracted["department"], extracted["region"])
    
    # 4. Parse dates correctly
    pub_date = datetime.strptime(extracted["published_date"], "%Y-%m-%d").date()
    award_date = datetime.strptime(extracted["award_date"], "%Y-%m-%d").date()

    # 5. Insert Tender
    tender_id = source.insert_tender(
        department_id=dept_id,
        category=final_category,
        region=extracted["region"],
        eligibility_text=extracted["eligibility_text"],
        estimated_value=extracted["estimated_value"],
        award_value=extracted["award_value"],
        published_date=pub_date,
        award_date=award_date
    )
    
    # 6. Get/create Vendors and map to their bid info
    bids_to_insert = []
    for bidder in extracted["bidders"]:
        vendor_id = source.get_or_create_vendor(bidder["vendor_name"])
        bids_to_insert.append({
            "vendor_id": vendor_id,
            "bid_amount": bidder["bid_amount"],
            "is_winner": bidder["is_winner"]
        })
        
    # 7. Insert Bids
    source.insert_bids(tender_id, bids_to_insert)
    
    return tender_id

def process_batch_upload(parsed_documents: list[dict]) -> InMemoryTenderDataSource:
    """
    Orchestrates business logic for batch processing: determines batch-local
    canonical categories, matches them, and constructs an isolated in-memory data source.
    """
    canonical_categories = list(set(doc["category"] for doc in parsed_documents))
    
    tenders_data = []
    bids_data = []
    
    for doc in parsed_documents:
        match_result = match_category(doc["category"], canonical_categories)
        final_category = match_result["matched_category"]
        
        tenders_data.append({
            "tender_id": doc["tender_id"],
            "department": doc["department"],
            "category": final_category,
            "region": doc["region"],
            "eligibility_text": doc["eligibility_text"],
            "estimated_value": doc["estimated_value"],
            "award_value": doc["award_value"],
            "published_date": doc["published_date"],
            "award_date": doc["award_date"],
            "_filename": doc.get("_filename")
        })
        
        for bidder in doc["bidders"]:
            bids_data.append({
                "tender_id": doc["tender_id"],
                "vendor_name": bidder["vendor_name"],
                "bid_amount": bidder["bid_amount"],
                "is_winner": bidder["is_winner"]
            })
            
    return InMemoryTenderDataSource(tenders=tenders_data, bids=bids_data)
