import docx
from typing import List, Dict, Any

def extract_docx_content(file_path: str) -> List[Dict[str, Any]]:
    pages = []
    doc = None
    try:
        doc = docx.Document(file_path)

        text_elements = []

        for node in doc.element.body.iter():
            if node.tag.endswith('}p'):
                texts = [t.text for t in node.iter() if t.tag.endswith('}t') and t.text]
                if texts:
                    p_text = "".join(texts).strip()
                    if p_text:
                        text_elements.append(p_text)

        text = "\n".join(text_elements)

        pages.append({
            "page_number": 1,
            "content": text.strip()
        })
    except Exception as e:
        print(f"Error extracting DOCX {file_path}: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if doc is not None:
            try:
                doc.part.package._rels
            except Exception:
                pass
            doc = None
        import gc
        gc.collect()

    return pages
