from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from pydantic import BaseModel

from rag.database import get_db
from rag.scope.schemas import ScopeSession
from rag.scope.command_parser import parse_scope_command
from rag.retrieval.hybrid_search import search
from rag.chat.chat_service import generate_response
from rag.chat.stats_service import (
    get_client_stats, format_stats_text, lookup_file_count_for_client, COUNT_QUERY_PATTERNS
)

router = APIRouter()

# In-memory session store for simplicity (in prod, use Redis or DB)
sessions: Dict[str, ScopeSession] = {}

class ChatRequest(BaseModel):
    session_id: str
    message: str

class ChatResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    current_scope: Dict[str, Any]
    suggestions: List[str] = []

def handle_stats_command(db: Session) -> ChatResponse:
    stats = get_client_stats(db)
    return ChatResponse(
        answer=format_stats_text(stats),
        sources=[],
        current_scope={}
    )

def handle_count_query(db: Session, session: ScopeSession, message: str) -> ChatResponse:
    # Check if scoped to a current client
    if session.client_id:
        from rag.scope.models import Client
        client = db.query(Client).filter(Client.client_id == session.client_id).first()
        if client:
            data = lookup_file_count_for_client(db, client.client_name)
            if data["found"]:
                lines = [f"{data['client_name']} has {data['file_count']} source file(s) indexed in the knowledge base."]
                for p in data["processes"]:
                    if p["count"] > 0:
                        lines.append(f"- {p['process']}: {p['count']} file(s)")
                return ChatResponse(
                    answer="\n".join(lines),
                    sources=[],
                    current_scope=session.dict()
                )

    # Try to find a client name in the message
    import re
    from rag.scope.models import Client
    for client in db.query(Client).filter(Client.active == True).all():
        if client.client_name.lower() in message.lower():
            data = lookup_file_count_for_client(db, client.client_name)
            if data["found"]:
                lines = [f"{data['client_name']} has {data['file_count']} source file(s) indexed in the knowledge base."]
                for p in data["processes"]:
                    if p["count"] > 0:
                        lines.append(f"- {p['process']}: {p['count']} file(s)")
                return ChatResponse(
                    answer="\n".join(lines),
                    sources=[],
                    current_scope=session.dict()
                )

    # No client found, show full stats
    stats = get_client_stats(db, session)
    return ChatResponse(
        answer=format_stats_text(stats),
        sources=[],
        current_scope=session.dict()
    )

@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    session_id = request.session_id
    message = request.message.strip()
    
    # Get or create session
    if session_id not in sessions:
        sessions[session_id] = ScopeSession(session_id=session_id)
    session = sessions[session_id]
    
    # Parse scope commands if message starts with '/'
    if message.startswith("/"):
        if message.lower().startswith("/stats"):
            result = handle_stats_command(db)
            result.current_scope = session.dict()
            return result

        session = parse_scope_command(db, session, message)
        sessions[session_id] = session
        
        # Build scope text
        scope_parts = []
        if session.client_id: scope_parts.append(f"Client={session.client_id}")
        if session.team_id: scope_parts.append(f"Team={session.team_id}")
        if session.benefit_id: scope_parts.append(f"Benefit={session.benefit_id}")
        if session.process_id: scope_parts.append(f"Process={session.process_id}")
        
        scope_str = " > ".join(scope_parts) if scope_parts else "All Authorized Company Knowledge"
        
        return ChatResponse(
            answer=f"Scope updated. Current Scope: {scope_str}",
            sources=[],
            current_scope=session.dict()
        )
        
    # Detect count/stats natural language queries
    msg_lower = message.lower()
    if any(pattern in msg_lower for pattern in COUNT_QUERY_PATTERNS):
        result = handle_count_query(db, session, message)
        sessions[session_id] = session
        return result
        
    # If regular query, perform RAG
    # Assuming user has permission to view everything for now.
    # In production, pass authorized client IDs based on user identity.
    allowed_client_ids = [] 
    
    # 1. Retrieve chunks
    if message.startswith("DEBUG_CHUNKS"):
        doc_name = message.replace("DEBUG_CHUNKS", "").strip()
        from qdrant_client.http import models
        from rag.qdrant.client import qdrant
        from rag.qdrant.collection_service import COLLECTION_NAME
        res = qdrant.scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter=models.Filter(must=[models.FieldCondition(key="document_name", match=models.MatchValue(value=doc_name))]),
            limit=1000
        )
        chunks_res = res[0]
        texts = []
        for c in chunks_res:
            score = 0 # Not a similarity search
            content = c.payload.get("content", "")
            texts.append(f"[Chunk] {content[:200]}...")
        
        return ChatResponse(
            answer="DEBUG CHUNKS:\n\n" + "\n".join(texts),
            sources=[],
            current_scope=session.dict()
        )
        
    chunks = search(message, session, allowed_client_ids)
    
    # 2. Generate response
    response_data = generate_response(message, chunks)
    
    return ChatResponse(
        answer=response_data["answer"],
        sources=response_data["sources"],
        current_scope=session.dict(),
        suggestions=response_data.get("suggestions", [])
    )
