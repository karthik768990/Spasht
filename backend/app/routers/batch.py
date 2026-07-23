"""
batch.py — Handles isolated batch analysis of multiple documents.
Parses documents in memory and computes relative scores purely within the
batch boundary, without touching the PostgreSQL dataset.
"""

import json
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException
from ..services.parsing_service import process_batch_upload
from ..data.parser.pdf_extractor import parse_tender_document, PdfExtractionError
from ..services.scoring_service import build_report
from ..services.file_service import validate_pdf_header, save_upload_to_disk, cleanup_file

router = APIRouter()

MAX_FILES = 25

@router.post("")
async def scan_batch(files: List[UploadFile] = File(...)):
    if not files or len(files) == 0:
        raise HTTPException(status_code=400, detail="At least one file must be provided.")
    if len(files) > MAX_FILES:
        raise HTTPException(status_code=400, detail=f"Maximum {MAX_FILES} files allowed per batch.")
        
    parsed_documents = []
    errors = []
    
    for file in files:
        if file.content_type != "application/pdf":
            errors.append({"filename": file.filename, "error": "Not a PDF file."})
            continue
            
        try:
            await validate_pdf_header(file)
        except HTTPException:
            errors.append({"filename": file.filename, "error": "Invalid PDF magic bytes."})
            continue
            
        try:
            file_path = await save_upload_to_disk(file, file_identifier=file.filename)
        except HTTPException as e:
            errors.append({"filename": file.filename, "error": e.detail})
            continue
        
        # Parse document
        try:
            extracted = parse_tender_document(file_path)
            extracted["_filename"] = file.filename
            extracted["tender_id"] = file.filename
            parsed_documents.append(extracted)
            
            # Safe to remove file ONLY on successful completion
            cleanup_file(file_path)
            
        except PdfExtractionError as e:
            errors.append({"filename": file.filename, "error": str(e)})
            print(f"Failed to extract {file.filename}. Preserved at: {file_path}")
        except Exception as e:
            print(f"Server Error during processing {file.filename}: {e}. Preserved at: {file_path}")
            errors.append({"filename": file.filename, "error": "Internal server error during parsing."})
                
    if not parsed_documents:
        raise HTTPException(
            status_code=400,
            detail={"message": "No documents were successfully parsed.", "errors": errors}
        )

    # Orchestrate business logic to build InMemoryTenderDataSource
    source = process_batch_upload(parsed_documents)
    
    # Run the report using the pure scoring logic
    report_df = build_report(source)
    
    # Return as JSON
    result = json.loads(report_df.to_json(orient="records"))
    
    return {"results": result, "errors": errors}
