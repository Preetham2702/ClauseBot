# ClauseBot 📄🤖

ClauseBot is an AI-driven system for analyzing lease agreements that combines document processing, large language models, and interactive querying. The platform extracts and summarizes critical lease terms and enables context-aware question answering directly from the uploaded document.

---

## 🚀 Features

### 📂 Document Upload & Preview
- Upload lease PDFs via drag-and-drop
- View **scrollable page previews** on the left panel
- Clear document anytime with one click

### 🧠 Automatic Lease Analysis
Once a document is uploaded, ClauseBot automatically:
- Generates a **clear summary**
- Identifies **pros for the tenant**
- Flags **cons, risks, and red flags**
- Highlights **important clauses** (termination, renewal, penalties, etc.)
_No button clicks required — analysis runs automatically.

### 💬 AI Chat (Context-Aware)
- Ask natural language questions
- AI responds **only using the uploaded lease**
- Friendly, ChatGPT-style responses

### 🔁 Persistent State
- Document and analysis persist across page refresh
- Resume exactly where you left off

---

## 🖥️ Tech Stack

### Frontend
- **React (Vite)**
- **Tailwind CSS**
- **pdf.js** (PDF rendering)
- **react-dropzone**
- **Axios**

### Backend
- **FastAPI**
- **Groq LLM API (Llama 3.1 8B Instant – free tier)**
- **PyMuPDF (fitz)** – text extraction
- **pdfplumber** – table extraction

