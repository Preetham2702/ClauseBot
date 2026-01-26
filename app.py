import os
import io
import json
from typing import List, Optional

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

class AskRequest(BaseModel):
    question: str

class AskResponse(BaseModel):
    answer: str

# ---------- In-memory "current lease" store ----------
# (Simple for now. Later we can store per-user/session in DB.)
CURRENT_LEASE_TEXT: Optional[str] = None
CURRENT_LEASE_TABLES: Optional[list] = None

# ---------- Helper functions ---------- #

def extract_text_and_tables(pdf_bytes: bytes):
    text = ""
    tables = []

    # Text extraction (PyMuPDF)
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()

    # Table extraction (pdfplumber)
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            page_tables = page.extract_tables()
            if page_tables:
                tables.extend(page_tables)

    return text, tables


def ask_groq_for_analysis(full_text: str, tables: list) -> LeaseAnalysis:
    if len(full_text) > 20000:
        text_for_model = full_text[:20000]
    else:
        text_for_model = full_text

    table_hint = ""
    if tables:
        table_hint = (
            "The lease also contains tables (fees/payment schedules). "
            "If those include important fees, dates, or penalties, include them. "
        )

    prompt = f"""
You are an expert legal assistant helping a tenant understand a lease.

--- LEASE START ---
{text_for_model}
--- LEASE END ---

{table_hint}

Return valid JSON ONLY:

{{
  "summary": "2–4 sentence summary",
  "pros": ["..."],
  "cons": ["..."],
  "important_points": ["..."]
}}

Rules:
- Do not invent anything.
- If unclear, say "Not clearly specified in the lease text provided."
- Tenant-focused.
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You are careful and accurate. You do not hallucinate."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )

    raw_content = response.choices[0].message.content

    try:
        data = json.loads(raw_content)
    except json.JSONDecodeError:
        return LeaseAnalysis(
            summary="Could not parse JSON. Raw response below:",
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


def ask_groq_for_qa(question: str, lease_text: str, tables: Optional[list]) -> str:
    # keep prompt size safe
    lease_slice = lease_text[:20000] if len(lease_text) > 20000 else lease_text

    table_hint = ""
    if tables:
        table_hint = "There may be tables (fees/dates). Use them if relevant."

    prompt = f"""
You are Clause Bot — a friendly legal assistant.

Use ONLY the lease text below to answer the user's question.
If the lease does not clearly say it, respond politely like:
"Not clearly specified in the lease I received."

Reply like normal ChatGPT:
- No labels like "Direct Answer" or "Explanation"
- No markdown symbols like ** or *
- Just give a clear short answer, and then 1–2 short sentences of helpful context.
- If possible, mention the section title you used (don’t guess page numbers).

--- LEASE START ---
{lease_slice}
--- LEASE END ---

{table_hint}

User question: {question}
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You are friendly, clear, and precise. No hallucination."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )

    return response.choices[0].message.content.strip()


# ---------- API endpoints ---------- #

@app.post("/analyze-lease", response_model=LeaseAnalysis)
async def analyze_lease(file: UploadFile = File(...)):
    global CURRENT_LEASE_TEXT, CURRENT_LEASE_TABLES

    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    pdf_bytes = await file.read()
    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    text, tables = extract_text_and_tables(pdf_bytes)

    if not text.strip():
        raise HTTPException(status_code=400, detail="Could not extract text from the PDF.")

    # ✅ STORE lease content so /ask can use it
    CURRENT_LEASE_TEXT = text
    CURRENT_LEASE_TABLES = tables

    analysis = ask_groq_for_analysis(text, tables)
    return analysis


@app.post("/ask", response_model=AskResponse)
async def ask_question(payload: AskRequest):
    if not payload.question.strip():
        raise HTTPException(status_code=400, detail="Question is empty.")

    if not CURRENT_LEASE_TEXT:
        raise HTTPException(
            status_code=400,
            detail="No lease uploaded yet. Upload a lease first."
        )

    answer = ask_groq_for_qa(payload.question, CURRENT_LEASE_TEXT, CURRENT_LEASE_TABLES)
    return AskResponse(answer=answer)
