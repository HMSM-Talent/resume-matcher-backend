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