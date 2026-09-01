from qdrant_client import QdrantClient
from rag.core.config import settings

def get_qdrant_client() -> QdrantClient:
    # Use local disk storage if QDRANT_URL is not set or local
    if settings.QDRANT_URL == "memory":
        return QdrantClient(path="qdrant_db")
    else:
        return QdrantClient(url=settings.QDRANT_URL)

qdrant = get_qdrant_client()
