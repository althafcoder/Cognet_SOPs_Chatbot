import fitz  # PyMuPDF
from typing import List, Dict, Any

def extract_pdf_content(file_path: str) -> List[Dict[str, Any]]:
    pages = []
    doc = None
    try:
        doc = fitz.open(file_path)
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text("text")

            pages.append({
                "page_number": page_num + 1,
                "content": text.strip()
            })
    except Exception as e:
        print(f"Error extracting PDF {file_path}: {e}")
    finally:
        if doc is not None:
            doc.close()
        import gc
        gc.collect()

    return pages
