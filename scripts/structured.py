from dotenv import load_dotenv
from google import genai
from google.genai import types
from schema import ExtractedDocument

load_dotenv()

client = genai.Client()

sample_text = """
INVOICE #99482
From: SuperMart Retailers
Date: 12/04/2026

Items Ordered:
- Organic Milk 1L: $3.50
- Whole Wheat Bread: $2.20
- Apples (1kg): $4.00

Total Paid: $9.70 USD
Thank you for shopping with us!
"""

# Native Structured Output Call
response = client.models.generate_content(
    model="gemini-3.1-flash-lite",
    contents=f"Extract details from this document:\n\n{sample_text}",
    config=types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=ExtractedDocument,
    ),
)

print("--- Raw AI Output (Guaranteed Clean JSON) ---")
print(response.text)

# Parse directly with Pydantic without regex or string manipulation
validated_doc = ExtractedDocument.model_validate_json(response.text)
print("\n--- Validated Pydantic Object ---")
print(validated_doc)