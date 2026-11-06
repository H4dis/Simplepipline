from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from schema import ExtractedDocument
from retry_loop import extract_with_retry

app = FastAPI(title="Messy Text to Structured JSON API")


class ExtractRequest(BaseModel):
    text: str


@app.post("/extract", response_model=ExtractedDocument)
def extract_document_endpoint(request: ExtractRequest):
    result = extract_with_retry(request.text)

    if not result:
        raise HTTPException(
            status_code=422,
            detail="Failed to extract valid structured data after maximum retry attempts.",
        )

    return result