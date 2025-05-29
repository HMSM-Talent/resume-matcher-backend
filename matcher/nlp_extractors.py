import json
from llama_cpp import Llama

llm = Llama(
    model_path="/Users/Terobau69/.lmstudio/models/TheBloke/phi-2-GGUF/phi-2.Q4_K_M.gguf",
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