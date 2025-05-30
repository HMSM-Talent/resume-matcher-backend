import json
from llama_cpp import Llama

# Path to your Phi-2 model (update if yours is different)
LLM_MODEL_PATH = "/Users/Terobau69/.lmstudio/models/TheBloke/phi-2-GGUF/phi-2.Q4_K_M.gguf"

# Initialize the model only once
llm = Llama(
    model_path=LLM_MODEL_PATH,
    n_ctx=2048,
    n_threads=4,  # Tune this depending on your CPU cores
    verbose=False
)

def extract_job_metadata(text: str) -> dict:
    """
    Uses Phi-2 LLM to extract structured metadata from raw job description text.
    Returns a dict with standard keys used in JobDescription model.
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
    """
    
    response = llm(prompt, max_tokens=512, stop=["}"], echo=False)

    try:
        raw_output = response["choices"][0]["text"].strip()
        json_output = json.loads(raw_output + "}")  # Fix missing brace if needed
    except Exception:
        # Fallback in case LLM fails
        return {
            "Job Title": None,
            "Company Name": None,
            "Location": None,
            "Job Type": None,
            "Experience Level": None,
            "Required Skills": []
        }

    return json_output

def get_similarity_score_from_llm(resume_text: str, jd_text: str) -> float:
    """
    Uses Phi-2 LLM to calculate a similarity score between resume and job description.
    Returns a float between 0.0 and 1.0. Output should only be a number.
    """
    prompt = f"""
You are an assistant that evaluates how well a resume matches a job description.
Give a single number between 0 and 1:
- 1 = perfect match
- 0 = no match

Don't explain. Just give the number.

Resume:
{resume_text}

Job Description:
{jd_text}

Score:
"""

    try:
        response = llm(prompt, max_tokens=5, echo=False)
        score_text = response["choices"][0]["text"].strip()
        score = float(score_text)
        return max(0.0, min(score, 1.0))  # Clamp score safely
    except Exception as e:
        print(f"Phi-2 similarity scoring failed: {e}")
        return 0.0