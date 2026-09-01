from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ScopeSession(BaseModel):
    session_id: str
    client_id: Optional[int] = None
    team_id: Optional[int] = None
    benefit_id: Optional[int] = None
    process_id: Optional[int] = None

class ClientBase(BaseModel):
    client_name: str
    source_path: str
    active: bool = True

class ClientCreate(ClientBase):
    pass

class Client(ClientBase):
    client_id: int
    tenant_id: int

    class Config:
        from_attributes = True

class DocumentBase(BaseModel):
    file_name: str
    source_path: str
    file_hash: str
    index_status: str
    active: bool = True

class DocumentCreate(DocumentBase):
    document_id: str
    process_id: Optional[int] = None

class Document(DocumentBase):
    document_id: str
    process_id: Optional[int] = None
    modified_at: datetime

    class Config:
        from_attributes = True
