"""
batch.py — Handles isolated batch analysis of multiple documents.
Parses documents in memory and computes relative scores purely within the
batch boundary, without touching the PostgreSQL dataset.
"""

import os
import tempfile
import uuid
import json
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException
from ..services.parsing_service import process_batch_upload
from ..data.parser.pdf_extractor import parse_tender_document, PdfExtractionError
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
        
    parsed_documents = []
    errors = []
    
    temp_dir = tempfile.gettempdir()
    
    for file in files:
        if file.content_type != "application/pdf":
            errors.append({"filename": file.filename, "error": "Not a PDF file."})
            continue
            
        header = await file.read(5)
        if header != b"%PDF-":
            errors.append({"filename": file.filename, "error": "Invalid PDF magic bytes."})
            continue
        await file.seek(0)
            
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
                extracted["tender_id"] = file.filename
                parsed_documents.append(extracted)
            except PdfExtractionError as e:
                errors.append({"filename": file.filename, "error": str(e)})
            except Exception as e:
                print(f"Server Error during processing {file.filename}: {e}")
                errors.append({"filename": file.filename, "error": "Internal server error during parsing."})
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)
                
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
