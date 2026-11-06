import json
import re
from dotenv import load_dotenv
from google import genai
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

prompt = f"""
Extract details from the following document into a JSON object matching this schema:
- biller_name (string or null)
- document_type (string or null)
- document_date (YYYY-MM-DD format or null)
- total_amount (number or null)
- currency (3-letter code or null)
- summary (string or null)

Document Text:
{sample_text}

Return ONLY valid JSON.
"""

response = client.models.generate_content(
    model="gemini-3.1-flash-lite",
    contents=prompt,
)

raw_text = response.text
print("--- Raw AI Output ---")
print(raw_text)

# Helper function to clean Markdown code fences
def clean_json_string(text: str) -> str:
    cleaned = re.sub(r"^```(?:json)?\s*", "", text.strip(), flags=re.MULTILINE)
    cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE)
    return cleaned.strip()

# Attempt parsing again after cleaning
try:
    cleaned_text = clean_json_string(raw_text)
    parsed_json = json.loads(cleaned_text)
    validated_doc = ExtractedDocument(**parsed_json)
    
    print("\nSUCCESS: Successfully parsed and validated into Pydantic model!")
    print(validated_doc)
except Exception as e:
    print(f"\nFAILURE: Validation or Parsing failed with error:\n{e}")