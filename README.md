

---

```markdown
# DocSchema-AI – Structured LLM Prompt Pipeline & JSON Extractor

A Python pipeline that extracts structured data from unstructured invoice text using an LLM (Google Gemini) with strictly validated JSON output via Pydantic.

Built for **Datheon Task 1**: connect Python to an LLM API, use parameterized prompt templates, enforce validated JSON schemas, and ship an executable script.

---

## ✨ Features

- **LLM-powered extraction** – Sends raw, unstructured document text to Google Gemini.
- **Pydantic V2 validation** – Every response is validated against a strict schema (`InvoiceSchema`, `VendorInfo`, `InvoiceItem`, `TaxDetail`, …).
- **Self-correction retry loop** – On validation failure, the validation error is fed back to the model for up to N retries.
- **Parameterized prompt templates** – Prompt templates are reusable and driven by a schema + few-shot examples.
- **Cross-field validation** – e.g. sum of line items is checked against the invoice total.
- **Streamlit UI** – Paste text, extract, and view the validated JSON instantly.
- **CLI entry point** – Run extraction from the command line.

---

## 📁 Project Structure

```
task1daton/
├── app.py                  # Streamlit UI entry point
├── retry_loop.py           # Core extraction + validation retry loop
├── schemas.py              # Pydantic models (InvoiceSchema, etc.)
├── prompts.py              # Parameterized prompt templates + few-shot examples
├── extractor.py            # Gemini client wrapper / API integration
├── requirements.txt
├── .env                    # GEMINI_API_KEY (not committed)
└── README.md
```

> File names may vary slightly depending on your local setup.

---

## ⚙️ Requirements

- Python **3.11**
- A Google Gemini API key
- Dependencies listed in `requirements.txt` (key ones: `google-genai`, `pydantic`, `python-dotenv`, `streamlit`)

> ⚠️ **NumPy note:** if you are on Python 3.11, use `numpy==2.4.6` (or any version supporting 3.11). `numpy==2.5.x` requires Python ≥ 3.12 and will fail to install on 3.11.

---

## 🚀 Setup

### 1. Clone / navigate to the project

```bash
cd D:\ultimate-proj\task1daton
```

### 2. Create and activate a virtual environment

**Windows (PowerShell):**

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks activation:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure the API key

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_actual_api_key_here
```

Get a key from [Google AI Studio](https://aistudio.google.com/apikey).

> The app loads this file via `python-dotenv`. If `GEMINI_API_KEY` is missing, `retry_loop.py` raises a `ValueError` at startup.

---

## ▶️ Running the App

### Streamlit UI

```bash
python -m streamlit run app.py --server.port 9876 --server.headless true
```

Then open:

```
http://localhost:9876
```

> Use `python -m streamlit` instead of `streamlit` if the executable is not on your `PATH`.

### CLI (if implemented)

```bash
python extractor.py --input samples/invoice_01.txt --output out.json
```

---

## 🧠 How It Works

1. **Schema definition** – Pydantic models describe the target structure (vendor, items, taxes, totals).
2. **Prompt construction** – A system prompt defines the extraction role; few-shot examples demonstrate messy input → clean JSON.
3. **LLM call** – Gemini is invoked with `temperature=0.0` and a JSON-schema/structured-output constraint.
4. **Validation** – The raw response is parsed with `Model.model_validate_json(...)`.
5. **Retry loop** – If validation fails, the error message + previous output are sent back to the model (up to `MAX_RETRIES`).
6. **Output** – A validated JSON object is returned to the UI / CLI.

---

## 🧪 Testing

Sample inputs live under `samples/`. Expected outputs are validated against the Pydantic schema.

---

## 🛠 Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| `streamlit` not recognized | `Scripts` not on `PATH` | Use `python -m streamlit ...` |
| `No matching distribution found for numpy==2.5.2` | NumPy 2.5.x requires Python ≥ 3.12 | Pin `numpy==2.4.6` for Python 3.11 |
| `GEMINI_API_KEY not found` | Missing `.env` or key | Create `.env` with `GEMINI_API_KEY=...` and restart |
| `ModuleNotFoundError: streamlit` | Not installed in active venv | `pip install streamlit` inside the activated venv |

---

## 📄 License

For internal / educational use as part of the Datheon task submission.


```

---
 
