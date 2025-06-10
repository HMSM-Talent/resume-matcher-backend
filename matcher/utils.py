import PyPDF2
import io
import logging
import re
import hashlib
import numpy as np
from typing import Tuple, Optional

from django.core.cache import cache
from sentence_transformers import SentenceTransformer
from resumes.utils import extract_text_from_file, normalize_text

from matcher.llm import get_llm_similarity_score, get_cosine_similarity

logger = logging.getLogger(__name__)
model = SentenceTransformer('all-MiniLM-L6-v2')

def normalize_text(text: str) -> str:
    """Clean up text for processing."""
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s.]', '', text)
    return text.strip()

def hash_text_for_cache(text: str) -> str:
    """Create a unique cache key using SHA256 hashing."""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def get_cached_embedding(text: str) -> Optional[np.ndarray]:
    """Get or compute and cache the sentence embedding."""
    key = f"embedding_{hash_text_for_cache(text)}"
    cached = cache.get(key)
    if cached is not None:
        return np.array(cached)

    try:
        embedding = model.encode([text])[0]
        cache.set(key, embedding.tolist(), 60 * 60 * 24)
        return embedding
    except Exception as e:
        logger.error(f"Embedding error: {str(e)}")
        raise ValueError("Error generating embedding")

def calculate_similarity(resume_text: str, jd_text: str) -> Tuple[float, dict]:
    """Calculate similarity score using sentence transformer embeddings."""
    try:
        if not resume_text or not jd_text:
            raise ValueError("Empty resume or job description text")

        # Get cosine similarity using MiniLM
        cosine_score = get_cosine_similarity(resume_text, jd_text)
        logger.info(f"Cosine similarity score: {cosine_score}")

        # Get semantic similarity using LLM
        llm_score = get_llm_similarity_score(resume_text, jd_text)
        logger.info(f"LLM semantic score: {llm_score}")

        # Calculate final hybrid score with adjusted weights
        final_score = round((0.3 * cosine_score + 0.7 * llm_score), 2)

        analysis = {
            "resume_length": len(resume_text.split()),
            "jd_length": len(jd_text.split()),
            "cosine_score": cosine_score,
            "llm_score": llm_score,
            "hybrid_score": final_score
        }

        logger.info(f"Final hybrid similarity score: {final_score}")
        return final_score, analysis

    except Exception as e:
        logger.error(f"Similarity scoring failed: {str(e)}", exc_info=True)
        raise ValueError(f"Similarity scoring failed: {str(e)}")

def get_match_category(score: float) -> str:
    if score >= 0.8:
        return "Excellent Match"
    elif score >= 0.6:
        return "Good Match"
    elif score >= 0.4:
        return "Moderate Match"
    else:
        return "Poor Match"