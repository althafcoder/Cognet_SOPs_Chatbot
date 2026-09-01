import json
import openai
from typing import List, Dict, Any
from rag.core.config import settings
from rag.chat.prompt_builder import build_prompt

openai.api_key = settings.OPENAI_API_KEY

def extract_suggestions(query: str, answer: str, retrieved_chunks: List[Dict[str, Any]]) -> List[str]:
    context_texts = []
    for chunk in retrieved_chunks:
        context_texts.append(f"[{chunk.get('document_name', '?')}] [Page {chunk.get('page_number', '?')}]: {chunk.get('content', '')}")

    context_block = "\n\n".join(context_texts)

    prompt = f"""You are a helpful assistant for an enterprise document knowledge base.

Below is the ONLY content available in the knowledge base, taken from the retrieved documents. Generate a small number of short follow-up questions the user could ask next.

STRICT RULES:
- Only suggest a question if its answer can be found directly and explicitly in the retrieved context below.
- Do NOT invent, infer, or speculate beyond what is written in the context.
- Do NOT ask about general company facts, people's backgrounds, business strategy, initiatives, or anything not covered by the documents.
- If the context only supports 0, 1, or 2 questions, return only that many (return an empty array if none are supported).
- Return ONLY a JSON array of strings, nothing else. No markdown, no commentary.
Example: ["Question 1?", "Question 2?"]

User question:
{query}

Assistant answer:
{answer}

Retrieved context (the ONLY knowledge available):
{context_block}
"""
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=200
        )
        content = response.choices[0].message.content.strip()
        # Extract JSON array robustly
        start = content.find('[')
        end = content.rfind(']')
        if start != -1 and end != -1 and end > start:
            content = content[start:end+1]
        suggestions = json.loads(content)
        if isinstance(suggestions, list):
            return [str(s).strip() for s in suggestions if str(s).strip()][:3]
    except Exception as e:
        print(f"Error generating suggestions: {e}")
    return []


def generate_response(query: str, retrieved_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not retrieved_chunks:
        return {
            "answer": "I could not find sufficient information about this topic in the currently selected company documents.",
            "sources": [],
            "suggestions": ["/stats", "Show me the document file counts", "What processes are available?"]
        }
        
    prompt = build_prompt(query, retrieved_chunks)
    
    response = openai.chat.completions.create(
        model="gpt-4o", # using gpt-4o as default
        messages=[
            {"role": "system", "content": prompt}
        ],
        temperature=0.0
    )
    
    answer = response.choices[0].message.content

    suggestions = extract_suggestions(query, answer, retrieved_chunks)

    # Simple citation extraction based on chunks used
    sources = []
    for chunk in retrieved_chunks:
        sources.append({
            "client": chunk.get("client_name"),
            "benefit": chunk.get("benefit_name"),
            "document": chunk.get("document_name"),
            "page": chunk.get("page_number")
        })
        
    return {
        "answer": answer,
        "sources": sources,
        "suggestions": suggestions
    }
