import json
from llama_cpp import Llama
import os

MODEL_PATH = os.getenv("MODEL_PATH", "/Users/Terobau69/.lmstudio/models/TheBloke/phi-2-GGUF/phi-2.Q4_K_M.gguf")
if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(
        "Phi-2 model file not found. Set the MODEL_PATH environment variable to the .gguf file."
    )
 
 
llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=2048,
    n_threads=4
)

def extract_job_metadata(text):
    prompt = f"""
Extract the following fields in JSON from this job ad:
- Job Title
- Company Name
- Location
- Job Type
- Experience Level
- Required Skills

Text:
{text}

Respond only with JSON.
"""
    try:
        result = llm(prompt, max_tokens=256, stop=["\n\n"])
        output = result["choices"][0]["text"].strip()
        return json.loads(output)
    except Exception as e:
        return {}
    
