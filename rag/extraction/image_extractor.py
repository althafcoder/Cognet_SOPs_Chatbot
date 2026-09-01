import base64
import openai
from rag.core.config import settings

openai.api_key = settings.OPENAI_API_KEY

def extract_text_from_image(image_bytes: bytes, mime_type: str = "image/png") -> str:
    """Extracts text from an image using OpenAI's Vision model."""
    if not settings.OPENAI_API_KEY:
        return ""
        
    try:
        import time
        time.sleep(1) # Prevent rate limiting on bulk image syncs
        base64_image = base64.b64encode(image_bytes).decode("utf-8")
        
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Extract all visible text, labels, and procedural steps from this image as plain text only. Do not use any markdown formatting like ### or ** or bullet points. If it is a flowchart or diagram, list the steps in order as numbered plain text sentences. Only return the extracted content, no commentary."},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{base64_image}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1000,
            temperature=0.0
        )
        result = response.choices[0].message.content.strip()
        if "unable to extract text" in result.lower() or "sorry" in result.lower():
            return ""
        # Strip any remaining markdown formatting
        import re
        result = re.sub(r'#{1,6}\s*', '', result)  # Remove ### headers
        result = re.sub(r'\*\*([^*]+)\*\*', r'\1', result)  # Remove **bold**
        result = re.sub(r'\*([^*]+)\*', r'\1', result)  # Remove *italic*
        result = re.sub(r'^\s*[-•]\s+', '', result, flags=re.MULTILINE)  # Remove bullet points
        result = re.sub(r'\n{3,}', '\n\n', result)  # Collapse excessive newlines
        return result.strip()
    except Exception as e:
        error_msg = f"Error extracting text from image: {e}"
        print(error_msg)
        with open("ocr_errors.log", "a") as f:
            f.write(error_msg + "\n")
        return ""
