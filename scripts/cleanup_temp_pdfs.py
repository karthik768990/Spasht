#!/usr/bin/env python3
"""
cleanup_temp_pdfs.py - Cron script to clean up abandoned temporary PDF files.
Finds and deletes any .pdf files in the system's temporary directory that are
older than a specified threshold (e.g., 1 hour).
"""

import os
import tempfile
import time

def cleanup_old_pdfs(max_age_hours=1):
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

if __name__ == "__main__":
    cleanup_old_pdfs(max_age_hours=1)
