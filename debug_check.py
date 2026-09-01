import docx

doc = docx.Document('test.docx')

# Simulate EXACTLY what docx_extractor does
text_elements = []
last_heading = "Document Content"
image_count = 0
image_ocr_count = 0
skipped_count = 0

for node in doc.element.body.iter():
    if node.tag.endswith('}p'):
        texts = [t.text for t in node.iter() if t.tag.endswith('}t') and t.text]
        if texts:
            p_text = "".join(texts).strip()
            if p_text:
                text_elements.append(p_text)
                if len(p_text) < 100 and not p_text.startswith("Figure "):
                    last_heading = p_text
    elif node.tag.endswith('}blip') or node.tag.endswith('}imagedata'):
        rId = node.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed') or node.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
        if rId and rId in doc.part.rels:
            rel = doc.part.rels[rId]
            if "image" in rel.reltype:
                image_count += 1
                img_bytes = rel.target_part.blob
                mime_type = getattr(rel.target_part, 'content_type', 'image/png')
                if rId == 'rId11':
                    print(f"*** rId11 REACHED in loop at image_count={image_count} ***")
                    print(f"    heading='{last_heading}', size={len(img_bytes)}")
        else:
            if rId:
                skipped_count += 1

print(f"\nTotal images found by iterator: {image_count}")
print(f"Skipped (rId not in rels): {skipped_count}")
print(f"Text elements: {len(text_elements)}")
print(f"'5. Procedure Map' in text_elements: {any('5. Procedure Map' in t for t in text_elements)}")
