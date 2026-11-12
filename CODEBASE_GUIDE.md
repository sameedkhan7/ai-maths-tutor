# 🏛️ AI Maths Tutor — Senior Architecture & Codebase Guide

> **Project Name:** AI Maths Tutor (Production & Research System)  
> **Repository Root:** `C:\Users\SK\OneDrive\Desktop\maths project`  
> **Tech Stack:** FastAPI, Python 3.10+, SQLite/MySQL (Aiven), SymPy, Groq API (Llama 3.3/Qwen), Local Ollama (Qwen 2.5 7B GPU), KaTeX, Vanilla JS/CSS3.  

---

## 📌 Executive Summary

**AI Maths Tutor** is an interactive, pedagogically grounded Mathematics Tutoring Platform designed for NCERT curriculum (Grades 6–12 and higher competitive levels). Unlike generic chat systems, it implements a **Hybrid Dual-Engine Architecture**:
1. **Deterministic Exact Mathematics:** SymPy symbolic computation engine for derivatives, integrals, quadratic equations, and linear systems.
2. **Pedagogical AI Synthesis:** Cascade router bridging a **Local RTX GPU (Qwen 2.5 7B)** and **Groq Cloud Inference (LLaMA 3.3 / GPT-OSS / Qwen Math)**.
3. **Retrieval-Augmented Generation (RAG):** Context-aware textbook grounding linking concepts directly to NCERT chapters.
4. **Contextual Guardrails:** 14-suite automated security filter blocking prompt injections and non-math queries before LLM invocation.

---

## 🗂️ Project Directory & File Map

```
maths-project/
├── 🌐 Presentation & Frontend
│   ├── maths.html                 # Core Interactive Workspace, Chat Canvas, KaTeX formulas, Developer Modal
│   ├── script.js                  # Frontend State Machine, Mathjax/KaTeX renderer, TTS/STT, Model Toggles
│   ├── style.css                  # Modern Glassmorphic Dark UI, Responsive Drawer, Animation Engine
│   ├── login.html                 # Secure Authentication Portal (Bcrypt, JWT sessions)
│   ├── register.html              # Multi-step Student Registration with Email/OTP verification
│   ├── admin.html                 # Comprehensive Administrative & Developer Dashboard
│   ├── terms.html & privacy.html  # Compliance, Legal & Terms of Service documentation
│
├── ⚙️ Backend API Gateway (`backend/`)
│   ├── main.py                    # FastAPI Application, Route definitions, OCR integration, CORS policies
│   ├── database.py                # Dual DB Engine: Automatic SQLite fallback for local dev & MySQL for cloud
│   ├── models.py                  # Pydantic Schemas for Requests, Responses, and Audit trails
│   ├── security.py                # Bcrypt password hashing, session tokens, CSRF protection
│   ├── email_service.py           # SMTP OTP Dispatcher with demo-mode fallback
│
├── 🧠 AI Engine & Inference (`backend/ai/`)
│   ├── tutor.py                   # Master Tutoring Orchestrator, SymPy execution, Multimodal prompt builder
│   ├── groq_client.py             # Hybrid Inference Cascade (Local RTX GPU -> Cloud Groq Fallback)
│   ├── model_manager.py           # Dynamic runtime model configuration & preset toggles
│   ├── guardrails.py              # Contextual math validator & prompt injection defense
│   ├── context_builder.py         # Dynamic prompt conditioning based on Grade, Tutor Style, and Language
│   ├── styles.py                  # Tutoring persona definitions (Socratic, Friendly, Step-by-Step, Sports)
│   └── config.py                  # System hyperparameters & environment configuration
│
├── 📚 RAG Knowledge Base (`backend/rag/`)
│   ├── retriever.py               # Vector similarity search & NCERT book chapter mapping
│   ├── ingest.py                  # PDF parser, text chunking & embedding pipeline
│   └── vector_store.py            # Local in-memory / persistent vector index
│
├── 🛠️ DevOps, Scripts & Automation
│   ├── start_backend.bat          # 1-Click Launch: Uvicorn API server on port 8000
│   ├── start_tutor_with_qwen.bat  # 1-Click Launch: Local Ollama RTX + Cloudflare Tunnel + Backend
│   ├── start_all_servers.bat      # Complete ecosystem orchestrator
│   ├── stop_all_servers.bat       # Clean process termination script
│   ├── Procfile                   # Cloud PaaS entrypoint (Render deployment)
│   └── requirements.txt           # Explicit Python dependencies with pinned versions
│
└── 🧪 Verification Suite (`tests/`)
    ├── test_contextual_guardrails.py # 14/14 automated test cases for safety & math domain checks
    ├── test_phase2_phase3.py         # Comprehensive mathematical reasoning & API verification
    └── test_audit_auth.py            # Security audit tests for authentication & role permissions
```

---

## 🔍 Module-by-Module Breakdown (For Senior Review)

### 1. Presentation Layer (`maths.html`, `script.js`, `style.css`)
- **Mathematical Rendering:** Integrates **KaTeX** and custom regex parsers to cleanly render LaTeX equations (`$$...$$` block, `$...$` inline) without hydration jitter.
- **Model Switcher Hub:** Features an in-app developer modal allowing real-time switching between:
  - *Local RTX GPU (Private Offline Testing)*
  - *Cloud Groq Inference (High Throughput Production)*
  - *Hybrid Dual-Mode (Automatic RTX failover to Cloud)*
- **Speech & Multimodal:** Supports client-side Speech-to-Text (Web Speech API) and Text-to-Speech audio streaming directly from the FastAPI backend.

### 2. Backend Orchestration (`backend/main.py`)
- **FastAPI Framework:** High-performance asynchronous REST endpoints:
  - `POST /api/chat`: Primary interactive tutoring route with multi-turn memory.
  - `GET /api/dev/model-config`: Retrieves active dynamic model toggles.
  - `POST /api/dev/model-config`: Persists live toggles into `data/model_config.json`.
  - `POST /api/ocr`: Mathematical formula extraction from uploaded camera snaps / images.
- **CORS Architecture:** Configured for both local development (`127.0.0.1:5500`, `localhost:8000`) and the production domain (`ai-maths-tutor.onrender.com`).

### 3. Hybrid AI Inference Layer (`backend/ai/groq_client.py` & `model_manager.py`)
- **Local-First Architecture:** Queries local RTX GPU (Ollama `qwen2.5:7b` via Cloudflare Tunnel). If the tunnel/PC is offline or busy:
  - When `force_local_only = true`: Immediately returns an educational status message without exposing cloud keys.
  - When `hybrid = true`: Transparently falls back to Groq Cloud API with sub-second latency.
- **Dynamic Hot-Reload:** `model_manager.py` maintains runtime toggles in `data/model_config.json` so models can be enabled/disabled on-the-fly without restarting the server.

### 4. Mathematical Grounding & Guardrails (`backend/ai/tutor.py` & `guardrails.py`)
- **SymPy Symbolic Core:** Before or alongside LLM reasoning, equations are parsed into computer algebra expressions to compute verified ground truths (derivatives, roots, integrals).
- **Security Guardrails:** Pre-screening pipeline prevents jailbreaks, role reversals, and non-math off-topic requests.

### 5. Persistence & Multi-Environment Strategy (`backend/database.py`)
- **Production (Render Cloud):** Automatically connects to **Aiven Managed MySQL** via SSL connection pooling.
- **Local Dev (VS Code / Offline):** Automatically initializes **SQLite (`backend/tutor.db`)** if cloud credentials are absent, guaranteeing offline portability.

---

## 💡 Quick Presentation Talking Points (When presenting to Seniors)

1. **"Why did you choose a Hybrid Local + Cloud setup?"**
   > *"Local RTX GPU gives complete privacy, zero API costs, and lets us benchmark open-weight models like Qwen 2.5 7B offline. Cloud Groq provides lightning-fast production failover when the local GPU workstation is powered off."*

2. **"How do you handle mathematical hallucinations in LLMs?"**
   > *"We pair the LLM with SymPy. For core computational problems, the deterministic engine solves the equation symbolically first, giving the LLM verified step-by-step mathematical facts to explain."*

3. **"How does the security guardrail work?"**
   > *"We have 14 unit-tested contextual guardrails that intercept queries before they reach the inference pipeline. Non-mathematical questions and prompt injection attempts are rejected at zero LLM token cost."*

4. **"How is database synchronization handled across environments?"**
   > *"The application uses a polymorphic database layer in `database.py`. In production on Render, it targets Aiven Cloud MySQL over TLS; during local workstation testing, it automatically defaults to an embedded SQLite database."*
