from qdrant_client.http.models import Distance, VectorParams
from qdrant_client.http.models import PayloadSchemaType
from rag.qdrant.client import qdrant

COLLECTION_NAME = "company_knowledge"
VECTOR_SIZE = 1536 # OpenAI text-embedding-3-small dimension

def create_collection():
    if not qdrant.collection_exists(COLLECTION_NAME):
        qdrant.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )
        
        # Create Payload Indexes as requested
        payload_fields = [
            "tenant_id", "client_id", "team_id", 
            "benefit_id", "process_id", "document_id", "active"
        ]
        
        for field in payload_fields:
            if field == "active":
                qdrant.create_payload_index(
                    collection_name=COLLECTION_NAME,
                    field_name=field,
                    field_schema=PayloadSchemaType.BOOL,
                )
            else:
                qdrant.create_payload_index(
                    collection_name=COLLECTION_NAME,
                    field_name=field,
                    field_schema=PayloadSchemaType.INTEGER,
                )
