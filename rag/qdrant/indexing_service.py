import uuid
from typing import List, Dict, Any
from qdrant_client.http.models import PointStruct, Filter, FieldCondition, MatchValue
from rag.qdrant.client import qdrant
from rag.qdrant.collection_service import COLLECTION_NAME

def upsert_chunks(chunks: List[Dict[str, Any]]):
    points = []
    
    for chunk in chunks:
        # Generate a stable or random chunk ID
        chunk_id = str(uuid.uuid4())
        
        payload = {
            "tenant_id": chunk.get("tenant_id", 1),
            "client_id": chunk.get("client_id"),
            "team_id": chunk.get("team_id"),
            "benefit_id": chunk.get("benefit_id"),
            "process_id": chunk.get("process_id"),
            "document_id": chunk.get("document_id"),
            "client_name": chunk.get("client_name"),
            "team_name": chunk.get("team_name"),
            "benefit_name": chunk.get("benefit_name"),
            "process_name": chunk.get("process_name"),
            "document_name": chunk.get("document_name"),
            "page_number": chunk.get("page_number"),
            "chunk_number": chunk.get("chunk_number"),
            "content": chunk.get("content"),
            "active": chunk.get("active", True)
        }
        
        points.append(
            PointStruct(
                id=chunk_id,
                vector=chunk["embedding"],
                payload=payload
            )
        )
        
    if points:
        qdrant.upsert(
            collection_name=COLLECTION_NAME,
            points=points
        )

def delete_chunks_by_document_id(document_id: str):
    qdrant.delete(
        collection_name=COLLECTION_NAME,
        points_selector=Filter(
            must=[
                FieldCondition(
                    key="document_id",
                    match=MatchValue(value=document_id)
                )
            ]
        )
    )
