import json
import os
from typing import Optional
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import ValidationError
from schema import ExtractedDocument

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment or .env file.")

client = genai.Client(api_key=API_KEY)


def extract_with_retry(
    document_text: str, max_retries: int = 3
) -> Optional[ExtractedDocument]:
    # Frozen Model Choice
    model_name = "gemini-3.1-flash-lite"

    system_instruction = (
        "You are an expert financial document processing AI. Extract structured information "
        "from unstructured document text (invoices, receipts, utility bills). "
        "Strictly adhere to the provided JSON schema."
    )

    current_prompt = f"DOCUMENT TEXT:\n{document_text}"

    for attempt in range(1, max_retries + 1):
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=current_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    response_schema=ExtractedDocument,
                    temperature=0.1,
                ),
            )

            response_json = json.loads(response.text)
            response_json["raw_text_context"] = document_text

            validated_doc = ExtractedDocument.model_validate(response_json)
            return validated_doc

        except (ValidationError, Exception) as e:
            error_message = str(e)
            print(f"[Attempt {attempt}/{max_retries}] Extraction Error:\n{error_message}\n")

            if attempt < max_retries:
                current_prompt = (
                    f"DOCUMENT TEXT:\n{document_text}\n\n"
                    f"PREVIOUS ATTEMPT FAILED WITH VALIDATION ERROR:\n{error_message}\n\n"
                    f"Please correct the JSON output."
                )

    print(f"Failed to extract valid schema after {max_retries} attempts.")
    return None