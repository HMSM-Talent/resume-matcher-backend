import io
import logging
import re
from PyPDF2 import PdfReader

logger = logging.getLogger(__name__)

def normalize_text(text: str) -> str:
    """Clean up text for processing."""
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s.]', '', text)
    return text.strip()

def extract_text_from_file(file) -> str:
    """Extract normalized text from a PDF file."""
    try:
        if not file:
            raise ValueError("No file provided")

        content = file.read()
        file.seek(0)  # Reset file pointer for further use
        
        if not content:
            raise ValueError("Empty file")

        reader = PdfReader(io.BytesIO(content))
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

        if not text.strip():
            raise ValueError("No text content found in PDF")

        return normalize_text(text)

    except Exception as e:
        logger.error(f"PDF processing error: {str(e)}")
        raise ValueError(f"Error processing PDF file: {str(e)}")