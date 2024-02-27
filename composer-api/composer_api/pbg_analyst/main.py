from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, Depends
from composer_api.pbg_analyst.datamodel import ProcessBigraphAnalyst


app = FastAPI()


class GPTRequest(BaseModel):
    prompt: str
    max_tokens: int = 100


process_bigraph_analyst = ProcessBigraphAnalyst(api_key="your_openai_api_key")


@app.post("/generate-text/")
async def generate_text(request: GPTRequest):
    try:
        generated_text = process_bigraph_analyst.generate_text(request.prompt, request.max_tokens)
        return {"generated_text": generated_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
