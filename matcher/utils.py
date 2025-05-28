import pdfplumber
import docx
import logging

logger = logging.getLogger(__name__)

def extract_text_from_file(file):
    name = file.name.lower()
    if name.endswith('.pdf'):
        return extract_pdf_text(file)
    elif name.endswith('.docx'):
        return extract_docx_text(file)
    else:
        raise ValueError("Unsupported file type")

def extract_pdf_text(file):
    try:
        text = ""
        with pdfplumber.open(file) as pdf:
            total_pages = len(pdf.pages)
            logger.info(f"Processing PDF with {total_pages} pages")
            
            for i, page in enumerate(pdf.pages, 1):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                        logger.info(f"Successfully extracted text from page {i}/{total_pages}")
                    else:
                        logger.warning(f"No text extracted from page {i}/{total_pages}")
                except Exception as e:
                    logger.error(f"Error extracting text from page {i}: {str(e)}")
                    continue
                    
        if not text.strip():
            logger.warning("No text was extracted from the PDF")
            return ""
            
        return text.strip()
    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}")
        raise ValueError(f"Failed to extract text from PDF: {str(e)}")

def extract_docx_text(file):
    try:
        doc = docx.Document(file)
        text = "\n".join([para.text for para in doc.paragraphs])
        if not text.strip():
            logger.warning("No text was extracted from the DOCX")
        return text.strip()
    except Exception as e:
        logger.error(f"Error processing DOCX: {str(e)}")
        raise ValueError(f"Failed to extract text from DOCX: {str(e)}")