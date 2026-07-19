import os
import tempfile
import uuid
import json
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException
from ..data.parser.pdf_extractor import parse_tender_document, PdfExtractionError
from ..data.parser.category_matcher import match_category
from ..data.in_memory import InMemoryTenderDataSource
from ..services.scoring_service import build_report

router = APIRouter()

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_FILES = 25

@router.post("")
async def scan_batch(files: List[UploadFile] = File(...)):
    if not files or len(files) == 0:
        raise HTTPException(status_code=400, detail="At least one file must be provided.")
    if len(files) > MAX_FILES:
        raise HTTPException(status_code=400, detail=f"Maximum {MAX_FILES} files allowed per batch.")
        
    for f in files:
        if f.content_type != "application/pdf":
            raise HTTPException(status_code=400, detail=f"File {f.filename} is not a PDF. Only PDF files are allowed.")
            
    parsed_documents = []
    
    # We need to assign deterministic tender_ids for the session
    tender_id_counter = 1
    
    temp_dir = tempfile.gettempdir()
    
    for file in files:
        file_size = 0
        safe_filename = f"{uuid.uuid4()}.pdf"
        file_path = os.path.join(temp_dir, safe_filename)
        
        try:
            with open(file_path, "wb") as f_out:
                while chunk := await file.read(1024 * 1024):  # 1MB chunks
                    file_size += len(chunk)
                    if file_size > MAX_FILE_SIZE:
                        raise HTTPException(status_code=400, detail=f"File {file.filename} exceeds the 10MB limit.")
                    f_out.write(chunk)
            
            # Parse document
            try:
                extracted = parse_tender_document(file_path)
                extracted["_filename"] = file.filename
                extracted["tender_id"] = tender_id_counter
                tender_id_counter += 1
                parsed_documents.append(extracted)
            except PdfExtractionError as e:
                raise HTTPException(status_code=400, detail=f"Failed to extract document {file.filename}: {str(e)}")
            except Exception as e:
                print(f"Server Error during processing {file.filename}: {e}")
                raise HTTPException(status_code=500, detail=f"An internal server error occurred while processing {file.filename}.")
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)
                
    if not parsed_documents:
        raise HTTPException(status_code=400, detail="No documents were successfully parsed.")

    # Build canonical categories strictly from this batch
    canonical_categories = list(set(doc["category"] for doc in parsed_documents))
    
    tenders_data = []
    bids_data = []
    
    for doc in parsed_documents:
        # Match category within the batch context
        match_result = match_category(doc["category"], canonical_categories)
        final_category = match_result["matched_category"]
        
        # Build tender record
        tenders_data.append({
            "tender_id": doc["tender_id"],
            "department": doc["department"],
            "category": final_category,
            "region": doc["region"],
            "eligibility_text": doc["eligibility_text"],
            "estimated_value": doc["estimated_value"],
            "award_value": doc["award_value"],
            "published_date": doc["published_date"],
            "award_date": doc["award_date"]
        })
        
        # Build bids records
        for bidder in doc["bidders"]:
            bids_data.append({
                "tender_id": doc["tender_id"],
                "vendor_name": bidder["vendor_name"],
                "bid_amount": bidder["bid_amount"],
                "is_winner": bidder["is_winner"]
            })
            
    # Create InMemory Data Source
    source = InMemoryTenderDataSource(tenders=tenders_data, bids=bids_data)
    
    # Run the report using the pure scoring logic
    report_df = build_report(source)
    
    # Return as JSON
    result = json.loads(report_df.to_json(orient="records"))
    
    return {"results": result}
