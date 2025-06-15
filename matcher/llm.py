import json
import requests
import logging
import re
import time
from sentence_transformers import SentenceTransformer, util
import os

logger = logging.getLogger(__name__)

# Initialize the embedding model
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

# Local LLM server URL, configurable via environment variable
LLM_SERVER_URL = os.getenv("LLM_SERVER_URL", "http://127.0.0.1:1234")

def get_cosine_similarity(resume_text: str, jd_text: str) -> float:
    """
    Calculate cosine similarity between resume and job description using MiniLM.
    Returns a float between 0.0 and 1.0.
    """
    try:
        # Encode texts to embeddings
        resume_embedding = embedding_model.encode(resume_text, convert_to_tensor=True)
        jd_embedding = embedding_model.encode(jd_text, convert_to_tensor=True)

        # Calculate cosine similarity
        similarity = util.cos_sim(resume_embedding, jd_embedding).item()
        similarity = round(max(0.0, min(similarity, 1.0)), 4)  # Clamp within range

        logger.info(f"MiniLM cosine similarity: {similarity}")
        return similarity
    except Exception as e:
        logger.error(f"Error calculating cosine similarity: {e}", exc_info=True)
        return 0.0

def post_with_retries(payload, retries=3, delay=2):
    """Retry LLM request if it fails due to timeout or network errors."""
    for attempt in range(retries):
        try:
            # Use the correct chat completions endpoint
            response = requests.post(f"{LLM_SERVER_URL}/v1/chat/completions", json=payload, timeout=10)
            response.raise_for_status()
            return response
        except Exception as e:
            logger.warning(f"[Retry {attempt + 1}] LLM request failed: {e}")
            time.sleep(delay)
    raise RuntimeError("LLM request failed after all retries.")

def get_llm_similarity_score(resume_text: str, jd_text: str) -> float:
    """
    Uses local Phi-2 server to calculate semantic similarity between a resume and a job description.
    Returns a float between 0.0 and 1.0.
    """
    logger.info("Starting LLM similarity score calculation...")
    logger.debug(f"Resume text length: {len(resume_text)}, JD text length: {len(jd_text)}")

    prompt = f"""
You are a strict scoring assistant.

Instructions:
- Evaluate how well the resume matches the job description.
- Consider:
  * Required skills match
  * Experience level match
  * Job responsibilities alignment
  * Industry/domain relevance
- Respond with only a decimal number between 0.0 and 1.0 (e.g., 0.75).
- Do not include any explanation or symbols. Just the number.

Resume:
{resume_text}

Job Description:
{jd_text}

Score (decimal number only):
""".strip()

    try:
        logger.debug("Sending prompt to LLM server...")
        response = post_with_retries({
            "model": "phi-2",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a strict scoring assistant. Always respond with only a decimal number between 0.0 and 1.0."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.1,
            "max_tokens": 5,
            "stream": False
        })

        # Log the raw response for debugging
        logger.debug(f"Raw LLM response: {response.text}")
        
        try:
            response_data = response.json()
            logger.debug(f"Response data: {response_data}")
            
            # Try different response formats
            if "choices" in response_data and len(response_data["choices"]) > 0:
                if "message" in response_data["choices"][0]:
                    score_text = response_data["choices"][0]["message"]["content"].strip()
                else:
                    score_text = response_data["choices"][0]["text"].strip()
            elif "text" in response_data:
                score_text = response_data["text"].strip()
            else:
                # If no expected format found, use the raw text
                score_text = response.text.strip()
                
            logger.debug(f"Extracted score text: {score_text}")

            match = re.search(r"\b([01](?:\.\d+)?|0?\.\d+)\b", score_text)
            if not match:
                logger.warning(f"No valid score found in LLM output: '{score_text}'")
                return 0.0

            score = float(match.group(1))
            final_score = max(0.0, min(score, 1.0))  # Clamp value within range
            logger.info(f"Final LLM similarity score: {final_score}")
            return final_score

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            return 0.0

    except Exception as e:
        logger.error(f"LLM similarity scoring failed: {e}", exc_info=True)
        return 0.0

def extract_job_metadata(text: str) -> dict:
    """
    Extracts structured metadata from raw job description using local Phi-2 server.
    Returns a dictionary with Job Title, Company Name, etc.
    """
    prompt = f"""
    Extract job posting details from the following text and return as valid JSON with these keys:
    - Job Title
    - Company Name
    - Location
    - Job Type
    - Experience Level
    - Required Skills (as a list)

    Text:
    {text}

    Output:
    """.strip()

    try:
        logger.debug("Sending job metadata prompt to LLM server...")
        response = post_with_retries({
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "max_tokens": 512
        })

        raw_output = response.json()["choices"][0]["message"]["content"].strip()
        logger.debug(f"Raw LLM metadata output: {raw_output}")

        # Try to decode JSON from the response
        json_output = json.loads(raw_output)
        return json_output

    except Exception as e:
        logger.error(f"Error extracting job metadata: {e}", exc_info=True)
        return {
            "Job Title": None,
            "Company Name": None,
            "Location": None,
            "Job Type": None,
            "Experience Level": None,
            "Required Skills": []
        }