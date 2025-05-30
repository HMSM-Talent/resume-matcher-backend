import PyPDF2
import io
import logging
from django.core.cache import cache
from django.conf import settings
import re
from typing import Tuple, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
from matcher.llm import get_similarity_score_from_llm

logger = logging.getLogger(__name__)

# Initialize the model
model = SentenceTransformer('all-MiniLM-L6-v2')

def normalize_text(text: str) -> str:
    """Normalize text by removing extra whitespace, converting to lowercase, and removing punctuation."""
    if not text:
        return ""
    # Convert to lowercase
    text = text.lower()
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove punctuation except for periods in abbreviations
    text = re.sub(r'[^\w\s.]', '', text)
    return text.strip()

def extract_text_from_file(file) -> str:
    """Extract text from PDF file with error handling."""
    try:
        if not file:
            raise ValueError("No file provided")

        # Read the file content
        content = file.read()
        if not content:
            raise ValueError("Empty file")

        # Create a PDF reader object
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
        
        # Extract text from all pages
        text = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

        if not text.strip():
            raise ValueError("No text content found in PDF")

        return normalize_text(text)

    except PyPDF2.PdfReadError as e:
        logger.error(f"PDF reading error: {str(e)}")
        raise ValueError("Invalid PDF file format")
    except Exception as e:
        logger.error(f"Error extracting text from file: {str(e)}")
        raise ValueError(f"Error processing file: {str(e)}")

def get_cached_embedding(text: str, cache_key: str) -> Optional[np.ndarray]:
    """Get cached embedding or compute and cache new one."""
    # Try to get from cache
    cached_embedding = cache.get(cache_key)
    if cached_embedding is not None:
        return np.array(cached_embedding)
    
    # Compute new embedding
    try:
        embedding = model.encode([text])[0]
        # Cache for 24 hours
        cache.set(cache_key, embedding.tolist(), 60 * 60 * 24)
        return embedding
    except Exception as e:
        logger.error(f"Error computing embedding: {str(e)}")
        raise ValueError(f"Error computing text embedding: {str(e)}")

from matcher.llm import get_similarity_score_from_llm

def calculate_similarity(resume_text: str, jd_text: str) -> Tuple[float, dict]:
    """
    Calculate similarity score between resume and job description using LLM (Phi-2).
    Returns a tuple of score and analysis dictionary.
    """
    try:
        if not resume_text or not jd_text:
            raise ValueError("Empty resume or job description text")

        score = get_similarity_score_from_llm(resume_text, jd_text)

        analysis = {
            "resume_length": len(resume_text.split()),
            "jd_length": len(jd_text.split()),
            "llm_score": score
        }

        return score, analysis

    except Exception as e:
        logger.error(f"LLM-based similarity scoring failed: {str(e)}")
        raise ValueError(f"Error calculating LLM similarity: {str(e)}")
    
def get_match_category(score: float) -> str:
    """Get match category based on similarity score."""
    if score >= 0.8:
        return "Excellent Match"
    elif score >= 0.6:
        return "Good Match"
    elif score >= 0.4:
        return "Moderate Match"
    else:
        return "Poor Match"