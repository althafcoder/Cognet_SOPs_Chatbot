from typing import List, Dict, Any

def build_prompt(query: str, retrieved_chunks: List[Dict[str, Any]]) -> str:
    context_texts = []
    
    for i, chunk in enumerate(retrieved_chunks):
        context_texts.append(f"Source {i+1} [{chunk.get('client_name', 'Unknown')}] [{chunk.get('benefit_name', 'Unknown')}] [{chunk.get('document_name', 'Unknown')}] [Page {chunk.get('page_number', '?')}]:\n{chunk.get('content', '')}")
        
    context_block = "\n\n".join(context_texts)
    
    prompt = f"""You are a helpful enterprise RAG assistant.
    
Answer the user's question using ONLY the retrieved company context below. 
Do not add information from general knowledge.
Do not guess missing information.
If the retrieved documents do not contain enough information, say: "I could not find sufficient information about this topic in the currently selected company documents."

Retrieved Context:
{context_block}

Question:
{query}
"""
    return prompt
