import os

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".xlsx", ".txt"}
MAX_FILE_SIZE = 50 * 1024 * 1024 # 50 MB

def validate_file(file_path: str) -> bool:
    if not os.path.exists(file_path):
        return False
        
    _, ext = os.path.splitext(file_path)
    if ext.lower() not in ALLOWED_EXTENSIONS:
        return False
        
    file_size = os.path.getsize(file_path)
    if file_size > MAX_FILE_SIZE or file_size == 0:
        return False
        
    return True
