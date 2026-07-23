"""
upload.py — Handles single document ingestion to the persistent PostgreSQL database.
Validates the uploaded file, invokes the parsing service to extract and persist
tender/bid records, and returns the generated database tender_id.
"""

import os
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from ..deps import get_data_source
from ..services.parsing_service import process_upload
from ..data.parser.pdf_extractor import PdfExtractionError
from ..services.file_service import validate_pdf_header, save_upload_to_disk, cleanup_file

router = APIRouter()

@router.post("/")
async def upload_document(file: UploadFile = File(...), source = Depends(get_data_source)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")
        
    await validate_pdf_header(file)
    
    file_path = await save_upload_to_disk(file)
    
    try:
        tender_id = process_upload(file_path, source)
        
        # Safe to remove file ONLY on successful completion
        cleanup_file(file_path)
        
        return {"message": "Document uploaded successfully", "tender_id": tender_id}
        
    except PdfExtractionError as e:
        # We do not delete the file here so it can be debugged
        raise HTTPException(status_code=400, detail=f"Failed to extract document: {str(e)}")
    except Exception as e:
        print(f"Server Error during processing: {e}. Preserved failed document at: {file_path}")
        raise HTTPException(status_code=500, detail="An internal server error occurred while processing the document.")

@router.get("/samples")
def list_sample_documents():
    sample_dir = "/sample_documents"
    if not os.path.exists(sample_dir):
        return {"samples": []}
        
    samples = []
    for f in os.listdir(sample_dir):
        if f.endswith(".pdf"):
            samples.append(f)
    return {"samples": sorted(samples)}

@router.post("/samples/{filename}")
def process_sample_document(filename: str, source = Depends(get_data_source)):
    sample_dir = "/sample_documents"
    file_path = os.path.join(sample_dir, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Sample document not found.")
        
    try:
        tender_id = process_upload(file_path, source)
    except PdfExtractionError as e:
        raise HTTPException(status_code=400, detail=f"Failed to extract document: {str(e)}")
    except Exception as e:
        print(f"Server Error during processing sample: {e}")
        raise HTTPException(status_code=500, detail="An internal server error occurred while processing the document.")
        
    return {"message": "Sample document processed successfully", "tender_id": tender_id}
