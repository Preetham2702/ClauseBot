import os
import io
import json
from typing import List

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

import fitz  # PyMuPDF
import pdfplumber
from groq import Groq

# ---------- Load environment ---------- #

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
  raise RuntimeError("GROQ_API_KEY is not set in .env")

client = Groq(api_key=GROQ_API_KEY)

# ---------- FastAPI app ---------- #

app = FastAPI(title="Clause Bot Backend")

# Allow your React app (Vite default: http://localhost:5173) to call this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Models ---------- #

class LeaseAnalysis(BaseModel):
    summary: str
    pros: List[str]
    cons: List[str]
    important_points: List[str]


# ---------- Helper functions ---------- #

def extract_text_and_tables(pdf_bytes: bytes):
    """
    Extracts all text and tables from a PDF (in memory).
    Uses:
      - PyMuPDF (fitz) for text
      - pdfplumber for tables
    """
    text = ""
    tables = []

    # Text extraction
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()

    # Table extraction
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            page_tables = page.extract_tables()
            if page_tables:
                tables.extend(page_tables)

    return text, tables


def ask_groq_for_analysis(full_text: str, tables: list) -> LeaseAnalysis:
    """
    Sends the lease content to Groq (Llama 3) and asks for:
      - summary
      - pros (for tenant)
      - cons / risks / red flags
      - important points
    Returns a LeaseAnalysis object.
    """

    # Truncate very long text so prompt is manageable
    if len(full_text) > 20000:
        text_for_model = full_text[:20000]
    else:
        text_for_model = full_text

    table_hint = ""
    if tables:
        table_hint = (
            "The lease also contains tables (like fee schedules or payment tables). "
            "If those contain any important fees, dates, or penalties, include them in your analysis. "
        )

    prompt = f"""
You are an expert legal assistant helping a tenant understand a residential or commercial lease.

Here is the lease text:

--- LEASE START ---
{text_for_model}
--- LEASE END ---

{table_hint}

Your job:

1. Give a short, clear summary of what this lease is about (2–4 sentences).
2. List the most important PROS for the tenant (good things / protections / benefits).
3. List the most important CONS / RISKS / RED FLAGS for the tenant (fees, penalties, strict rules, one-sided terms, etc.).
4. List any KEY THINGS THE TENANT SHOULD KNOW, such as:
   - notice periods,
   - automatic renewals,
   - early termination rules,
   - maintenance responsibilities,
   - penalties for late payment,
   - unusual or harsh clauses.

Very important:
- Be precise and do NOT invent terms that are not clearly supported by the text.
- If something is unclear or missing, say that it is not clearly specified.
- Focus on the tenant's point of view.

Respond in valid JSON ONLY, in this exact format:

{{
  "summary": "short summary here",
  "pros": ["item 1", "item 2"],
  "cons": ["item 1", "item 2"],
  "important_points": ["item 1", "item 2"]
}}
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": "You are a careful legal assistant for lease agreements. You do not guess or hallucinate."
            },
            {
                "role": "user",
                "content": prompt
            },
        ],
        temperature=0.2,
    )

    raw_content = response.choices[0].message.content

    # Try to parse JSON strictly
    try:
        data = json.loads(raw_content)
    except json.JSONDecodeError:
        # If the model didn't return valid JSON, wrap everything in a simple response
        return LeaseAnalysis(
            summary="I could not parse a structured JSON response. Here is the raw analysis:",
            pros=[raw_content],
            cons=[],
            important_points=[],
        )

    return LeaseAnalysis(
        summary=data.get("summary", ""),
        pros=data.get("pros", []),
        cons=data.get("cons", []),
        important_points=data.get("important_points", []),
    )


# ---------- API endpoint ---------- #

@app.post("/analyze-lease", response_model=LeaseAnalysis)
async def analyze_lease(file: UploadFile = File(...)):
    """
    Endpoint:
      - Accepts a single PDF file upload
      - Extracts text + tables
      - Sends to Groq for analysis
      - Returns summary, pros, cons, important points
    """
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    pdf_bytes = await file.read()
    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # 1. Extract text + tables
    text, tables = extract_text_and_tables(pdf_bytes)

    if not text.strip():
        raise HTTPException(status_code=400, detail="Could not extract text from the PDF.")

    # 2. Ask Groq for structured analysis
    analysis = ask_groq_for_analysis(text, tables)

    return analysis
