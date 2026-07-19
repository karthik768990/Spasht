"""
upload.py — Handles single document ingestion to the persistent PostgreSQL database.
Validates the uploaded file, invokes the parsing service to extract and persist
tender/bid records, and returns the generated database tender_id.
"""

import os
import tempfile
import uuid
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from ..deps import get_data_source
from ..services.parsing_service import process_upload
from ..data.parser.pdf_extractor import PdfExtractionError

router = APIRouter()

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

@router.post("/")
async def upload_document(file: UploadFile = File(...), source = Depends(get_data_source)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")
        
    header = await file.read(5)
    if header != b"%PDF-":
        raise HTTPException(status_code=400, detail="File is not a valid PDF document.")
    await file.seek(0)
        
    file_size = 0
    # Safe temporary location
    temp_dir = tempfile.gettempdir()
    safe_filename = f"{uuid.uuid4()}.pdf"
    file_path = os.path.join(temp_dir, safe_filename)
    
    try:
        with open(file_path, "wb") as f:
            while chunk := await file.read(1024 * 1024):  # 1MB chunks
                file_size += len(chunk)
                if file_size > MAX_FILE_SIZE:
                    raise HTTPException(status_code=400, detail="File size exceeds the 10MB limit.")
                f.write(chunk)
                
        # Parse and insert
        try:
            tender_id = process_upload(file_path, source)
        except PdfExtractionError as e:
            raise HTTPException(status_code=400, detail=f"Failed to extract document: {str(e)}")
        except Exception as e:
            # Mask raw database exceptions in API response
            print(f"Server Error during processing: {e}")
            raise HTTPException(status_code=500, detail="An internal server error occurred while processing the document.")
            
        return {"message": "Document uploaded successfully", "tender_id": tender_id}
        
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

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
