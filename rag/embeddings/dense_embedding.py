import openai
from typing import List
from rag.core.config import settings

openai.api_key = settings.OPENAI_API_KEY

def get_dense_embedding(text: str, model: str = "text-embedding-3-small") -> List[float]:
    if not text.strip():
        return []
    
    response = openai.embeddings.create(
        input=text,
        model=model
    )
    return response.data[0].embedding
