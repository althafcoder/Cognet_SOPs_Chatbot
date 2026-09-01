from typing import List, Dict, Any
import re

def chunk_text(pages: List[Dict[str, Any]], target_tokens: int = 500, overlap: int = 50) -> List[Dict[str, Any]]:
    # A simple word-based chunker for now. For tokens, we'd use tiktoken.
    # In production, we'd use tiktoken to accurately count tokens.
    
    chunks = []
    chunk_number = 1
    
    for page in pages:
        words = page["content"].split()
        page_num = page["page_number"]
        
        start = 0
        while start < len(words):
            end = min(start + target_tokens, len(words))
            chunk_words = words[start:end]
            chunk_text = " ".join(chunk_words)
            
            chunks.append({
                "page_number": page_num,
                "chunk_number": chunk_number,
                "content": chunk_text
            })
            
            chunk_number += 1
            if end == len(words):
                break
                
            # Overlap
            start = end - overlap
            
    return chunks
