import hashlib
from sqlalchemy.orm import Session
from rag.scope.models import Document

def calculate_file_hash(file_path: str) -> str:
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def is_file_already_indexed(db: Session, source_path: str, file_hash: str) -> bool:
    existing = db.query(Document).filter(Document.source_path == source_path).first()
    if not existing:
        return False
    return existing.file_hash == file_hash

def update_file_hash(db: Session, document_id: str, file_hash: str):
    doc = db.query(Document).filter(Document.document_id == document_id).first()
    if doc:
        doc.file_hash = file_hash
        db.commit()
