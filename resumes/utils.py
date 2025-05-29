import io
from PyPDF2 import PdfReader

def extract_text_from_file(file):
    try:
        # Read binary content
        pdf_file = file.read()
        file.seek(0)  # Reset file pointer for further use

        # Use PdfReader to extract text
        reader = PdfReader(io.BytesIO(pdf_file))
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text.strip()
    except Exception as e:
        raise ValueError(f"Failed to extract text from PDF: {str(e)}")