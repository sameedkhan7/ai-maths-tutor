# 📚 AI Maths Tutor — Project Documentation

> **An Intelligent, Curriculum-Aligned Mathematics Tutoring & Learning Platform for NCERT Classes 9–12**

---

## 👥 1. Team Members & Roles

| # | Name | Core Responsibility | Key Contributions |
| :---: | :--- | :--- | :--- |
| **1** | **Syed Alkab Hussain Rizvi** | **LLM Specialist** | • Prompt engineering & multi-persona system instruction design.<br>• Groq Cloud API integration & multi-model failover cascading.<br>• Mathematical reasoning tuning & guardrail enforcement. |
| **2** | **Sameed Khan** | **Testing & Feature Integration** | • End-to-end QA testing & cross-browser compatibility.<br>• Feature branch merging & conflict resolution.<br>• Frontend bug isolation, UI/UX polish, and workflow verification. |
| **3** | **Rumman Siddiqui** | **RAG (Retrieval-Augmented Generation)** | • Vector embeddings & semantic retrieval pipeline.<br>• NCERT Class 9–12 textbook ingestion & chunking strategy.<br>• Real-time official textbook chapter citation & PDF deep-linking. |
| **4** | **Arman Khan** | **Backend Engineering (Core & Database)** | • FastAPI core server setup & route orchestration.<br>• MySQL relational database architecture & schema design.<br>• Google OAuth 2.0 & Bcrypt + JWT authentication security. |
| **5** | **Kazim Shaikh** | **Backend Engineering (APIs & Services)** | • RESTful API endpoints for chat sessions and history pagination.<br>• Multi-format document parser & image OCR integration.<br>• Database connection pooling, performance tuning, and error handling. |

---

## 🚀 2. Project Overview

**AI Maths Tutor** is an interactive, full-stack web application engineered to bridge the gap between abstract mathematical concepts and student comprehension. Specifically calibrated for CBSE and NCERT curricula (Grades 9 through 12), the platform combines advanced Large Language Models (LLMs) with Retrieval-Augmented Generation (RAG) to provide rigorous, hallucination-free, and pedagogically tailored math explanations.

---

## ✨ 3. Key Features & Capabilities

### 🧠 3.1 Multi-Model AI Engine with Automatic Failover
- **Groq Cloud Acceleration**: Ultra-fast inference with sub-second token generation.
- **Dynamic Model Selection**:
  1. `openai/gpt-oss-120b` (120B Versatile) — Complex proofs, calculus derivations, and detailed pedagogy.
  2. `qwen/qwen3.8-27b` (27B Math) — High-precision algebraic manipulations and olympiad reasoning.
  3. `openai/gpt-oss-20b` (20B Fast) — Rapid answers, concept verification, and arithmetic.
  4. `allam-2-7b` (7B Multilingual) — Multilingual language support.
- **Self-Healing Fallback Cascade**: If the primary model encounters a temporary rate limit (HTTP 429), the backend automatically reroutes the prompt to the next available model without interrupting the student's session.

### 🎭 3.2 Nine Pedagogical Teaching Styles
Students can customize how concepts are taught to match their individual learning style:
1. **⚡ Quick Answer**: Direct numerical result with minimal essential steps.
2. **💡 Concept First**: Intuition and foundational theorems explained prior to calculations.
3. **🔢 Step-by-Step**: Explicit, numbered algebraic steps with intermediate working.
4. **🎯 Exam-Oriented**: Formatted strictly to CBSE/NCERT marking schemes with scoring tips.
5. **🏏 Sports Mode**: Real-world athletic and cricket analogies (trajectories, run rates, angles).
6. **🌍 Real-Life Mode**: Practical everyday scenarios (finance, architecture, daily physics).
7. **📖 Story Mode**: Narrative-driven lessons featuring relatable characters.
8. **💬 Social Mode**: Conversational, encouraging peer study-buddy tone.
9. **🧭 Socratic Mode**: Guided questioning and incremental hints rather than immediate answers.

### 📚 3.3 NCERT-Grounded RAG Pipeline
- Textbooks for **Class 9, 10, 11, and 12 Mathematics** are chunked and embedded in a vector database.
- AI answers include explicit **NCERT Book References** (e.g., *Class 12 Maths · Chapter 6: Applications of Derivatives*) with direct links to view the official PDF chapters.

### 🛡️ 3.4 Security Guardrails & Phonetic Typo Tolerance
- **Strict Math Guardrails**: Detects and politely deflects non-math queries, hacking attempts, prompt injections, and database leak exploits.
- **Fuzzy Math Typo Engine**: Accommodates student spelling errors (e.g., `"what is tignomatry"` or `"definit integral"`) and resolves them to their correct NCERT syllabus topic.

### 📐 3.5 Rich Mathematical Presentation
- **KaTeX LaTeX Engine**: Flawless rendering of formulas, matrices, integrals ($$\int$$), summations ($$\sum$$), square roots, and fractions.
- **Interactive SVG Diagrams**: Dynamic generation of coordinate graphs, geometric triangles, and function curves directly inside the chat.
- **Floating Math Shortcuts Toolbar**: Instant insertion of symbols ($$x^2, x^3, \sqrt{}, \pi, \theta, \pm, \int, \frac{d}{dx}$$) on both mobile and desktop.

### 🎙️ 3.6 Multimodal Inputs & AI Voice (TTS / STT)
- **Voice Input (STT)**: Speech-to-text dictation allows students to ask questions verbally.
- **AI Read-Aloud (TTS)**: Math-aware text-to-speech converter translates LaTeX equations into naturally spoken English/Hinglish phrasing (e.g., converting `\frac{dy}{dx}` into *"derivative of y with respect to x"*).
- **Multi-Format Attachment**: Upload problem photos, PDFs, or text notes with OCR parsing.

### 🔐 3.7 Authentication & User Isolation
- **Dual Authentication**: Google Sign-In (OAuth 2.0) alongside standard Email/Password accounts.
- **Security-First**: Passwords secured via **Bcrypt** salt hashing; sessions managed via **JWT (JSON Web Tokens)**.
- **Strict Data Isolation**: Each student's chat history and pinned notes are isolated by `user_id` in MySQL.

### 🛠️ 3.8 Developer Knowledge Base Center
- Dedicated administration panel for ingesting new PDF textbooks, custom study notes, or scraping web articles directly into the RAG vector store.

---

## 🏗️ 4. Technical Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            FRONTEND CLIENT LAYER                            │
│  • HTML5 / CSS3 (Dark Slate Theme)    • KaTeX Equation Engine               │
│  • Vanilla ES6+ JavaScript            • Web Speech API (Voice STT / TTS)    │
│  • Responsive Design (Desktop/Mobile) • Interactive SVG Renderer            │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ HTTPS / REST API
┌──────────────────────────────────────▼──────────────────────────────────────┐
│                        FASTAPI BACKEND SERVICES                             │
│  • Route Orchestration (main.py)      • Security Guardrails & Typo Matcher  │
│  • Bcrypt + JWT Authentication Engine • Multi-Model Groq Client & Cascade   │
│  • RAG Retrieval & Ingestion Pipeline • File & Image OCR Parser             │
└───────────────────┬─────────────────────────────────────┬───────────────────┘
                    │                                     │
┌───────────────────▼─────────────────┐ ┌─────────────────▼───────────────────┐
│        DATABASE STORAGE LAYER       │ │         EXTERNAL AI CLOUD           │
│  • MySQL (Users, Chats, History)    │ │  • Groq Cloud API LPU Accelerators  │
│  • Relational Schema with Foreign   │ │  • Llama-3, Qwen, & OSS Architectures│
│    Keys & Indexed user_id Lookups   │ │  • Continuous Token Window (TPM)    │
└─────────────────────────────────────┘ └─────────────────────────────────────┘
```

---

## 💻 5. Technology Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend** | HTML5, CSS3, JavaScript (ES6+) | Lightweight, dependency-free UI |
| **Math Typography** | KaTeX | High-performance LaTeX formula rendering |
| **Backend Framework** | FastAPI (Python 3.13) | Asynchronous, high-throughput REST API |
| **Database** | MySQL (XAMPP / Cloud Ready) | Persistent user accounts, chats, and pins |
| **Authentication** | Google OAuth 2.0, Bcrypt, PyJWT | Industry-standard security and session tokens |
| **AI / LLM Engine** | Groq Cloud SDK | Ultra-fast token generation & inference |
| **RAG / Vector Store** | LangChain & Vector Embeddings | NCERT textbook indexing & semantic search |
| **Deployment Target** | Vercel (Frontend) + Railway (Backend/DB) | Production-ready cloud infrastructure |

---

## 📂 6. Directory Structure

```
maths-project/
├── backend/
│   ├── ai/
│   │   ├── config.py             # Groq & LLM hyperparameter configurations
│   │   ├── groq_client.py        # API client with multi-model fallback cascade
│   │   ├── guardrails.py         # Anti-injection, database defense & typo fuzzy matcher
│   │   ├── prompts.py            # 9 pedagogical teaching persona prompts
│   │   ├── schemas.py            # Pydantic data validation schemas
│   │   └── tutor.py              # Core conversation reasoning coordinator
│   ├── rag/
│   │   ├── curriculum.py         # NCERT chapter lookup & curriculum mapping
│   │   └── ingest.py             # PDF chunking, vector indexing & web scraper
│   ├── database.py               # MySQL connection pool, table schemas & seeders
│   └── main.py                   # FastAPI application routes & middleware
├── maths.html                    # Main interactive student chat application
├── login.html                    # Unified Student & Developer login portal
├── privacy.html                  # Privacy policy & data protection terms
├── style.css                     # Premium dark-slate responsive stylesheet
├── script.js                     # Complete client-side application controller
├── .env                          # Secret environment variables (API keys, DB config)
└── PROJECT_DOCUMENTATION.md      # Official project documentation
```

---

## 🔒 7. Security & Compliance Highlights

1. **Zero Plaintext Passwords**: Every credential passes through Bcrypt with automatic salt generation.
2. **Encrypted Network Traffic**: All client-server communication runs over HTTPS / TLS.
3. **SSRF & Ingestion Defense**: URL scraping tools enforce private IP rejection (`127.0.0.1`, `localhost` blocks).
4. **Input Sanitization**: LaTeX blocks are parsed in sandboxed DOM nodes to prevent Cross-Site Scripting (XSS).
5. **Air-Gapped Developer Architecture**: Developer admin routes can be restricted to local development environments (`localhost`), leaving zero administrative attack surface on public cloud deployments.

---

*Authored by the **AI Maths Tutor Team** — Syed Alkab Hussain Rizvi, Sameed Khan, Rumman Siddiqui, Arman Khan, and Kazim Shaikh.*
