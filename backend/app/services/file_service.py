import os
import tempfile
import uuid
import time
from fastapi import UploadFile, HTTPException

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

async def validate_pdf_header(file: UploadFile) -> None:
    """Validates that the file has a PDF magic header."""
    header = await file.read(5)
    if header != b"%PDF-":
        raise HTTPException(status_code=400, detail="File is not a valid PDF document.")
    await file.seek(0)

async def save_upload_to_disk(file: UploadFile, file_identifier: str = "") -> str:
    """
    Saves the uploaded file to a safe temporary location.
    Reads in 1MB chunks to avoid loading the entire file into memory at once.
    Raises an HTTPException if the file size exceeds the limit.
    """
    temp_dir = tempfile.gettempdir()
    safe_filename = f"{uuid.uuid4()}.pdf"
    file_path = os.path.join(temp_dir, safe_filename)
    
    file_size = 0
    with open(file_path, "wb") as f_out:
        while True:
            chunk = await file.read(1024 * 1024)  # 1MB chunks
            if not chunk:
                break
            
            file_size += len(chunk)
            if file_size > MAX_FILE_SIZE:
                # Cleanup partial file before raising
                f_out.close()
                if os.path.exists(file_path):
                    os.remove(file_path)
                
                error_detail = "File size exceeds the 10MB limit."
                if file_identifier:
                    error_detail = f"File {file_identifier} exceeds the 10MB limit."
                raise HTTPException(status_code=400, detail=error_detail)
            
            f_out.write(chunk)
            
    return file_path

def cleanup_file(file_path: str) -> None:
    """Safely removes a file from disk."""
    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
        except OSError as e:
            print(f"Warning: Failed to cleanup file {file_path}: {e}")

def cleanup_old_pdfs(max_age_hours: float = 1.0) -> None:
    """
    Finds and deletes any .pdf files in the system's temporary directory that are
    older than a specified threshold.
    """
    temp_dir = tempfile.gettempdir()
    current_time = time.time()
    max_age_seconds = max_age_hours * 3600
    
    deleted_count = 0
    failed_count = 0

    print(f"Scanning {temp_dir} for PDF files older than {max_age_hours} hour(s)...")

    for filename in os.listdir(temp_dir):
        if not filename.lower().endswith('.pdf'):
            continue
            
        file_path = os.path.join(temp_dir, filename)
        
        try:
            # Check file modification time
            file_mtime = os.path.getmtime(file_path)
            age_seconds = current_time - file_mtime
            
            if age_seconds > max_age_seconds:
                os.remove(file_path)
                deleted_count += 1
                print(f"Deleted old PDF: {filename} (Age: {age_seconds/3600:.2f} hours)")
        except OSError as e:
            print(f"Warning: Failed to process or delete {filename}: {e}")
            failed_count += 1

    print(f"Cleanup complete. Deleted: {deleted_count}, Failed: {failed_count}.")

