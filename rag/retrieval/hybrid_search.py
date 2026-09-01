from typing import List, Dict, Any, Optional
from qdrant_client.http import models
from rag.qdrant.client import qdrant
from rag.qdrant.collection_service import COLLECTION_NAME
from rag.embeddings.dense_embedding import get_dense_embedding
from rag.scope.schemas import ScopeSession

def build_qdrant_filter(session: ScopeSession, allowed_client_ids: List[int]) -> models.Filter:
    must_conditions = [
        models.FieldCondition(
            key="active",
            match=models.MatchValue(value=True)
        )
    ]
    
    # 1. Authorization constraint: Must be within allowed client IDs
    if allowed_client_ids:
        must_conditions.append(
            models.FieldCondition(
                key="client_id",
                match=models.MatchAny(any=allowed_client_ids)
            )
        )
        
    # 2. Scope constraint
    if session.client_id:
        # If user selected a client, enforce it (assuming it's allowed, validation should happen before this)
        must_conditions.append(
            models.FieldCondition(
                key="client_id",
                match=models.MatchValue(value=session.client_id)
            )
        )
    if session.team_id:
        must_conditions.append(
            models.FieldCondition(
                key="team_id",
                match=models.MatchValue(value=session.team_id)
            )
        )
    if session.benefit_id:
        must_conditions.append(
            models.FieldCondition(
                key="benefit_id",
                match=models.MatchValue(value=session.benefit_id)
            )
        )
    if session.process_id:
        must_conditions.append(
            models.FieldCondition(
                key="process_id",
                match=models.MatchValue(value=session.process_id)
            )
        )
        
    return models.Filter(must=must_conditions)

def search(query: str, session: ScopeSession, allowed_client_ids: List[int], top_k: int = 5) -> List[Dict[str, Any]]:
    query_vector = get_dense_embedding(query)
    qdrant_filter = build_qdrant_filter(session, allowed_client_ids)
    
    search_result = qdrant.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        query_filter=qdrant_filter,
        limit=top_k
    )
    
    return [hit.payload for hit in search_result.points]
