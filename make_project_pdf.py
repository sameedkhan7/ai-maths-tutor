import os
import pypdf

class PDFCanvas:
    def __init__(self):
        self.pages = []
        self.fonts = {
            '/F1': 'Helvetica',
            '/F2': 'Helvetica-Bold',
            '/F3': 'Helvetica-Oblique',
            '/F4': 'Courier'
        }
        self.curr_stream = None

    def new_page(self):
        self.curr_stream = []
        self.pages.append(self.curr_stream)
        return self.curr_stream

    def escape(self, s):
        if not s:
            return ""
        return s.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')

    def rect(self, x, y, w, h, fill=None, stroke=None, line_width=1):
        ops = []
        if line_width:
            ops.append(f"{line_width:.2f} w")
        if fill:
            ops.append(f"{fill[0]:.3f} {fill[1]:.3f} {fill[2]:.3f} rg")
        if stroke:
            ops.append(f"{stroke[0]:.3f} {stroke[1]:.3f} {stroke[2]:.3f} RG")
        ops.append(f"{x:.2f} {y:.2f} {w:.2f} {h:.2f} re")
        if fill and stroke:
            ops.append("B")
        elif fill:
            ops.append("f")
        elif stroke:
            ops.append("S")
        self.curr_stream.append(" ".join(ops))

    def line(self, x1, y1, x2, y2, stroke=(0.8, 0.8, 0.8), line_width=1):
        self.curr_stream.append(
            f"{line_width:.2f} w {stroke[0]:.3f} {stroke[1]:.3f} {stroke[2]:.3f} RG {x1:.2f} {y1:.2f} m {x2:.2f} {y2:.2f} l S"
        )

    def text(self, x, y, text_str, font='/F1', size=11, color=(0, 0, 0)):
        if not text_str:
            return
        esc = self.escape(text_str)
        self.curr_stream.append(
            f"BT {color[0]:.3f} {color[1]:.3f} {color[2]:.3f} rg {font} {size:.2f} Tf {x:.2f} {y:.2f} Td ({esc}) Tj ET"
        )

    def wrap_text(self, text_str, max_chars):
        words = text_str.split(' ')
        lines = []
        cur = []
        cur_len = 0
        for w in words:
            if cur_len + len(w) + 1 > max_chars:
                lines.append(" ".join(cur))
                cur = [w]
                cur_len = len(w)
            else:
                cur.append(w)
                cur_len += len(w) + 1
        if cur:
            lines.append(" ".join(cur))
        return lines

    def draw_wrapped(self, x, y, text_str, max_chars, font='/F1', size=11, leading=14, color=(0, 0, 0)):
        lines = self.wrap_text(text_str, max_chars)
        curr_y = y
        for l in lines:
            self.text(x, curr_y, l, font=font, size=size, color=color)
            curr_y -= leading
        return curr_y

    def save(self, filepath):
        num_pages = len(self.pages)
        catalog_id = 1
        pages_id = 2
        page_ids = [3 + i for i in range(num_pages)]
        font_base_id = 3 + num_pages
        font_map = {}
        curr_id = font_base_id
        for alias, font_name in self.fonts.items():
            font_map[alias] = curr_id
            curr_id += 1
        
        content_ids = [curr_id + i for i in range(num_pages)]
        total_objects = curr_id + num_pages

        obj_data = {}
        obj_data[catalog_id] = f'<< /Type /Catalog /Pages {pages_id} 0 R >>'
        kids_str = ' '.join(f'{pid} 0 R' for pid in page_ids)
        obj_data[pages_id] = f'<< /Type /Pages /Kids [{kids_str}] /Count {num_pages} >>'

        font_res_str = ' '.join(f'{alias} {fid} 0 R' for alias, fid in font_map.items())
        res_dict = f'<< /Font << {font_res_str} >> >>'

        for i in range(num_pages):
            pid = page_ids[i]
            cid = content_ids[i]
            obj_data[pid] = f'<< /Type /Page /Parent {pages_id} 0 R /MediaBox [0 0 595.28 841.89] /Resources {res_dict} /Contents {cid} 0 R >>'

        for alias, fid in font_map.items():
            fname = self.fonts[alias]
            obj_data[fid] = f'<< /Type /Font /Subtype /Type1 /BaseFont /{fname} /Encoding /WinAnsiEncoding >>'

        for i in range(num_pages):
            cid = content_ids[i]
            stream_body = '\n'.join(self.pages[i]).encode('latin-1', 'replace')
            stream_len = len(stream_body)
            header = f'<< /Length {stream_len} >>\nstream\n'
            footer = '\nendstream'
            obj_data[cid] = header.encode('ascii') + stream_body + footer.encode('ascii')

        out = bytearray()
        out.extend(b'%PDF-1.4\n%\xe2\xe3\xcf\xd3\n')
        xref = {}
        for oid in range(1, total_objects):
            xref[oid] = len(out)
            data = obj_data[oid]
            if isinstance(data, str):
                data = data.encode('latin-1')
            out.extend(f'{oid} 0 obj\n'.encode('ascii'))
            out.extend(data)
            out.extend(b'\nendobj\n')

        xref_start = len(out)
        out.extend(f'xref\n0 {total_objects}\n'.encode('ascii'))
        out.extend(b'0000000000 65535 f \n')
        for oid in range(1, total_objects):
            out.extend(f'{xref[oid]:010d} 00000 n \n'.encode('ascii'))

        out.extend(f'trailer\n<< /Size {total_objects} /Root {catalog_id} 0 R >>\nstartxref\n{xref_start}\n%%EOF\n'.encode('ascii'))

        with open(filepath, 'wb') as f:
            f.write(out)
        print(f"Generated PDF: {filepath} ({len(out)} bytes)")


def generate_documentation_pdf(output_path):
    pdf = PDFCanvas()

    # Colors
    c_primary = (0.31, 0.27, 0.90)   # Indigo #4f46e5
    c_dark = (0.06, 0.09, 0.16)      # Slate-900 #0f172a
    c_muted = (0.30, 0.35, 0.44)     # Slate-600 #475569
    c_light_bg = (0.97, 0.98, 0.99)  # Slate-50 #f8fafc
    c_border = (0.85, 0.88, 0.92)    # Slate-200
    c_badge_bg = (0.93, 0.95, 1.0)   # Indigo-50
    c_badge_txt = (0.26, 0.22, 0.79) # Indigo-700
    c_card_bg = (0.98, 0.99, 1.00)
    c_green_bg = (0.94, 0.99, 0.95)
    c_green_border = (0.09, 0.64, 0.29)

    # -------------------------------------------------------------
    # PAGE 1: Team, Overview & System Capabilities
    # -------------------------------------------------------------
    pdf.new_page()

    # Header top accent bar
    pdf.rect(40, 808, 515, 4, fill=c_primary)

    # Header Title
    pdf.text(40, 782, "AI Maths Tutor - Official Project Documentation", font='/F2', size=19, color=c_dark)
    pdf.text(40, 765, "Curriculum-Aligned Intelligent Mathematics Platform (NCERT Classes 9-12)", font='/F1', size=11, color=c_primary)

    # Header Badge Pill
    pdf.rect(435, 760, 120, 20, fill=c_badge_bg, stroke=c_primary, line_width=0.8)
    pdf.text(447, 766, "CBSE / NCERT 2026", font='/F2', size=8.5, color=c_badge_txt)

    # Header divider
    pdf.line(40, 748, 555, 748, stroke=c_border, line_width=1)

    # Section 1: Team Members & Roles
    pdf.text(40, 730, "1. Team Members & Core Responsibilities", font='/F2', size=13, color=c_dark)

    # Team Table
    table_x = 40
    table_y = 718
    row_heights = [22, 34, 34, 34, 34, 34]
    col_w = [25, 135, 135, 220]

    # Header row
    pdf.rect(table_x, table_y - 20, 515, 20, fill=c_light_bg, stroke=c_border, line_width=1)
    pdf.text(table_x + 8, table_y - 14, "#", font='/F2', size=9, color=c_dark)
    pdf.text(table_x + col_w[0] + 6, table_y - 14, "Team Member", font='/F2', size=9, color=c_dark)
    pdf.text(table_x + col_w[0] + col_w[1] + 6, table_y - 14, "Core Responsibility", font='/F2', size=9, color=c_dark)
    pdf.text(table_x + col_w[0] + col_w[1] + col_w[2] + 6, table_y - 14, "Key Deliverables & Contributions", font='/F2', size=9, color=c_dark)

    members = [
        ("1", "Syed Alkab Hussain Rizvi", "LLM Specialist", "Prompt engineering, Groq Cloud API integration, multi-model failover cascading & math reasoning tuning."),
        ("2", "Sameed Khan", "Testing & Feature Integration", "End-to-end QA testing, cross-browser UX, git branch merging, conflict resolution & frontend bug isolation."),
        ("3", "Rumman Siddiqui", "RAG & Knowledge Architecture", "Vector embeddings pipeline, NCERT textbook ingestion (Cl 9-12), semantic search & chapter PDF deep-linking."),
        ("4", "Arman Khan", "Backend Engineering (Core & DB)", "FastAPI core server architecture, MySQL relational database schema, Google OAuth 2.0 & Bcrypt + JWT security."),
        ("5", "Kazim Shaikh", "Backend Engineering (APIs & Services)", "RESTful endpoints for chat sessions/history pagination, multi-format file/OCR document parser & DB pooling.")
    ]

    curr_y = table_y - 20
    for idx, (num, name, role, contrib) in enumerate(members):
        rh = 32
        bg = c_card_bg if idx % 2 == 1 else (1, 1, 1)
        pdf.rect(table_x, curr_y - rh, 515, rh, fill=bg, stroke=c_border, line_width=0.8)
        
        pdf.text(table_x + 8, curr_y - 16, num, font='/F2', size=9, color=c_dark)
        pdf.text(table_x + col_w[0] + 6, curr_y - 16, name, font='/F2', size=8.5, color=c_dark)
        pdf.text(table_x + col_w[0] + col_w[1] + 6, curr_y - 16, role, font='/F3', size=8, color=c_primary)
        
        # Wrapped contributions
        pdf.draw_wrapped(table_x + col_w[0] + col_w[1] + col_w[2] + 6, curr_y - 12, contrib, max_chars=46, font='/F1', size=7.5, leading=10, color=c_muted)
        curr_y -= rh

    # Section 2: Project Overview
    curr_y -= 16
    pdf.text(40, curr_y, "2. Project Overview & Problem Statement", font='/F2', size=13, color=c_dark)
    curr_y -= 8
    pdf.line(40, curr_y, 555, curr_y, stroke=c_border, line_width=0.8)
    curr_y -= 14

    overview_p1 = "Mathematics education often suffers from high friction due to a lack of interactive, step-by-step guidance. AI Maths Tutor is an intelligent, full-stack learning platform designed specifically for CBSE and NCERT curricula (Grades 9 through 12). By coupling state-of-the-art Large Language Models with Retrieval-Augmented Generation (RAG), the system provides mathematically accurate, syllabus-aligned, and hallucination-free explanations in real time."
    curr_y = pdf.draw_wrapped(40, curr_y, overview_p1, max_chars=112, font='/F1', size=9, leading=13, color=c_muted)

    # Section 3: Core Features (Part 1)
    curr_y -= 8
    pdf.text(40, curr_y, "3. Core System Capabilities", font='/F2', size=13, color=c_dark)
    curr_y -= 8
    pdf.line(40, curr_y, 555, curr_y, stroke=c_border, line_width=0.8)
    curr_y -= 14

    # 4 Feature Cards (2x2 Grid)
    card_w = 250
    card_h = 68
    grid_data = [
        ("Multi-Model Engine with Failover", "Groq Cloud accelerated inference with GPT-OSS 120B, Qwen 3.8 (27B Math), and GPT-OSS 20B. Automated cascading failover seamlessly re-routes queries if token limits occur."),
        ("9 Pedagogical Teaching Styles", "Personalized modes: Quick Answer, Concept First, Step-by-Step, Exam-Oriented (CBSE marking criteria), Sports Mode (Cricket analogies), Real-Life, Story, Social, and Socratic hints."),
        ("NCERT Grounding & RAG Verification", "Full curriculum grounding across Classes 9 to 12. Every explanation provides exact NCERT chapter titles with clickable links to download official PDF textbook chapters."),
        ("Defensive Guardrails & Typo Engine", "Anti-injection filters block non-math prompts, while a specialized fuzzy-matching algorithm accommodates student spelling typos (e.g., 'what is tignomatry' -> Chapter 8).")
    ]

    card_x1 = 40
    card_x2 = 305
    y_row1 = curr_y - card_h
    y_row2 = y_row1 - card_h - 10

    # Card 1
    pdf.rect(card_x1, y_row1, card_w, card_h, fill=c_light_bg, stroke=c_border, line_width=0.8)
    pdf.text(card_x1 + 10, y_row1 + card_h - 14, grid_data[0][0], font='/F2', size=9, color=c_dark)
    pdf.draw_wrapped(card_x1 + 10, y_row1 + card_h - 26, grid_data[0][1], max_chars=50, font='/F1', size=7.8, leading=10.5, color=c_muted)

    # Card 2
    pdf.rect(card_x2, y_row1, card_w, card_h, fill=c_light_bg, stroke=c_border, line_width=0.8)
    pdf.text(card_x2 + 10, y_row1 + card_h - 14, grid_data[1][0], font='/F2', size=9, color=c_dark)
    pdf.draw_wrapped(card_x2 + 10, y_row1 + card_h - 26, grid_data[1][1], max_chars=50, font='/F1', size=7.8, leading=10.5, color=c_muted)

    # Card 3
    pdf.rect(card_x1, y_row2, card_w, card_h, fill=c_light_bg, stroke=c_border, line_width=0.8)
    pdf.text(card_x1 + 10, y_row2 + card_h - 14, grid_data[2][0], font='/F2', size=9, color=c_dark)
    pdf.draw_wrapped(card_x1 + 10, y_row2 + card_h - 26, grid_data[2][1], max_chars=50, font='/F1', size=7.8, leading=10.5, color=c_muted)

    # Card 4
    pdf.rect(card_x2, y_row2, card_w, card_h, fill=c_light_bg, stroke=c_border, line_width=0.8)
    pdf.text(card_x2 + 10, y_row2 + card_h - 14, grid_data[3][0], font='/F2', size=9, color=c_dark)
    pdf.draw_wrapped(card_x2 + 10, y_row2 + card_h - 26, grid_data[3][1], max_chars=50, font='/F1', size=7.8, leading=10.5, color=c_muted)

    # Footer Page 1
    pdf.line(40, 48, 555, 48, stroke=c_border, line_width=0.8)
    pdf.text(40, 36, "AI Maths Tutor - Comprehensive Project Documentation", font='/F1', size=8, color=c_muted)
    pdf.text(500, 36, "Page 1 of 3", font='/F1', size=8, color=c_muted)

    # -------------------------------------------------------------
    # PAGE 2: Additional Capabilities & Technical Architecture
    # -------------------------------------------------------------
    pdf.new_page()

    # Header top accent bar
    pdf.rect(40, 808, 515, 3, fill=c_primary)
    pdf.text(40, 788, "AI Maths Tutor - System Capabilities (Cont.) & Architecture", font='/F2', size=13, color=c_dark)
    pdf.line(40, 778, 555, 778, stroke=c_border, line_width=0.8)

    # 4 Additional Feature Cards
    grid_data2 = [
        ("KaTeX Equations & Dynamic SVG Graphs", "Flawless rendering of complex formulas (integrals, summations, radicals, fractions) plus on-the-fly rendering of interactive SVG geometric triangles and coordinate plots."),
        ("Multimodal Audio & Document OCR", "Speech-to-text dictation allows students to ask questions verbally. AI Read-Aloud (TTS) translates LaTeX equations into naturally spoken math. Supports PDF and image problem uploads."),
        ("Dual Auth & User Data Isolation", "Google OAuth 2.0 integration alongside standard email/password logins with Bcrypt salt hashing. Each student's chat history and pinned notes are isolated by user_id in MySQL."),
        ("Developer RAG Knowledge Base Center", "Dedicated administrative console permitting educators to ingest new NCERT chapters, custom coaching notes, or scrape mathematical web articles directly into the vector database.")
    ]

    curr_y = 765
    y_row1 = curr_y - card_h
    y_row2 = y_row1 - card_h - 10

    # Card 5
    pdf.rect(card_x1, y_row1, card_w, card_h, fill=c_light_bg, stroke=c_border, line_width=0.8)
    pdf.text(card_x1 + 10, y_row1 + card_h - 14, grid_data2[0][0], font='/F2', size=9, color=c_dark)
    pdf.draw_wrapped(card_x1 + 10, y_row1 + card_h - 26, grid_data2[0][1], max_chars=50, font='/F1', size=7.8, leading=10.5, color=c_muted)

    # Card 6
    pdf.rect(card_x2, y_row1, card_w, card_h, fill=c_light_bg, stroke=c_border, line_width=0.8)
    pdf.text(card_x2 + 10, y_row1 + card_h - 14, grid_data2[1][0], font='/F2', size=9, color=c_dark)
    pdf.draw_wrapped(card_x2 + 10, y_row1 + card_h - 26, grid_data2[1][1], max_chars=50, font='/F1', size=7.8, leading=10.5, color=c_muted)

    # Card 7
    pdf.rect(card_x1, y_row2, card_w, card_h, fill=c_light_bg, stroke=c_border, line_width=0.8)
    pdf.text(card_x1 + 10, y_row2 + card_h - 14, grid_data2[2][0], font='/F2', size=9, color=c_dark)
    pdf.draw_wrapped(card_x1 + 10, y_row2 + card_h - 26, grid_data2[2][1], max_chars=50, font='/F1', size=7.8, leading=10.5, color=c_muted)

    # Card 8
    pdf.rect(card_x2, y_row2, card_w, card_h, fill=c_light_bg, stroke=c_border, line_width=0.8)
    pdf.text(card_x2 + 10, y_row2 + card_h - 14, grid_data2[3][0], font='/F2', size=9, color=c_dark)
    pdf.draw_wrapped(card_x2 + 10, y_row2 + card_h - 26, grid_data2[3][1], max_chars=50, font='/F1', size=7.8, leading=10.5, color=c_muted)

    # Section 4: Technical Architecture Diagram
    curr_y = y_row2 - 20
    pdf.text(40, curr_y, "4. Technical System Architecture", font='/F2', size=13, color=c_dark)
    curr_y -= 8
    pdf.line(40, curr_y, 555, curr_y, stroke=c_border, line_width=0.8)
    curr_y -= 14

    arch_lines = [
        "+-----------------------------------------------------------------------------------------+",
        "|                              FRONTEND CLIENT LAYER                                      |",
        "|  * HTML5 / CSS3 (Dark Slate Theme)             * KaTeX Equation Engine                  |",
        "|  * Vanilla ES6+ JavaScript                     * Web Speech API (Voice STT / TTS)       |",
        "|  * Responsive Design (Desktop & Mobile)        * Interactive SVG Vector Renderer        |",
        "+--------------------------------------------+--------------------------------------------+",
        "                                             | HTTPS / REST API",
        "+--------------------------------------------v--------------------------------------------+",
        "|                          FASTAPI BACKEND SERVICES                                       |",
        "|  * Route Orchestration (main.py)               * Security Guardrails & Typo Matcher     |",
        "|  * Bcrypt + JWT Authentication Engine          * Multi-Model Groq Client & Cascade      |",
        "|  * RAG Retrieval & Ingestion Pipeline          * Multi-format File & OCR Parser         |",
        "+--------------------+-----------------------------------------------+--------------------+",
        "                     |                                               |                     ",
        "+--------------------v-------------------+       +-------------------v--------------------+",
        "|        DATABASE STORAGE LAYER          |       |           EXTERNAL AI CLOUD            |",
        "|  * MySQL Relational Database           |       |  * Groq Cloud API LPU Accelerators     |",
        "|  * Users, Chats, Messages & Pins       |       |  * Llama-3, Qwen & OSS Architectures   |",
        "|  * Isolated User ID Foreign Keys       |       |  * Continuous Rolling Token Pool (TPM) |",
        "+----------------------------------------+       +----------------------------------------+"
    ]

    pdf.rect(40, curr_y - 235, 515, 235, fill=(0.06, 0.09, 0.16), stroke=c_primary, line_width=1)
    arch_y = curr_y - 18
    for al in arch_lines:
        pdf.text(50, arch_y, al, font='/F4', size=7.8, color=(0.88, 0.92, 0.98))
        arch_y -= 11.2

    # Footer Page 2
    pdf.line(40, 48, 555, 48, stroke=c_border, line_width=0.8)
    pdf.text(40, 36, "AI Maths Tutor - Comprehensive Project Documentation", font='/F1', size=8, color=c_muted)
    pdf.text(500, 36, "Page 2 of 3", font='/F1', size=8, color=c_muted)

    # -------------------------------------------------------------
    # PAGE 3: Tech Stack, File Structure & Security Guarantees
    # -------------------------------------------------------------
    pdf.new_page()

    # Header top accent bar
    pdf.rect(40, 808, 515, 3, fill=c_primary)
    pdf.text(40, 788, "AI Maths Tutor - Technology Stack, Codebase & Security", font='/F2', size=13, color=c_dark)
    pdf.line(40, 778, 555, 778, stroke=c_border, line_width=0.8)

    # Section 5: Tech Stack Table
    curr_y = 765
    pdf.text(40, curr_y, "5. Technology Stack Breakdown", font='/F2', size=13, color=c_dark)
    curr_y -= 8
    pdf.line(40, curr_y, 555, curr_y, stroke=c_border, line_width=0.8)
    curr_y -= 14

    stack_headers = ["Layer", "Technology Used", "Role in System"]
    stack_data = [
        ("Frontend UI", "HTML5, CSS3, Vanilla JavaScript (ES6+)", "Lightweight, responsive, zero-dependency client interface"),
        ("Formula Typography", "KaTeX (Fast LaTeX Renderer)", "Client-side high performance formula rendering (fractions, integrals)"),
        ("Backend Framework", "FastAPI (Python 3.13), Uvicorn", "Asynchronous, high-throughput microservices architecture"),
        ("Database Storage", "MySQL 8.0 (XAMPP / Cloud Ready)", "Relational storage of students, conversations, pins & preferences"),
        ("Authentication", "Google OAuth 2.0, Bcrypt, PyJWT", "Salted password hashing and cryptographic session verification"),
        ("AI Inference Engine", "Groq Cloud LPU Accelerators", "Sub-second token generation across multiple LLM weights"),
        ("RAG Pipeline", "LangChain, Vector Embeddings", "Semantic document chunking, indexing, and textbook search"),
        ("Deployment Target", "Vercel (Frontend) + Railway (Backend/DB)", "Production-ready, highly secure serverless cloud infrastructure")
    ]

    t_w = [115, 170, 230]
    pdf.rect(40, curr_y - 18, 515, 18, fill=c_light_bg, stroke=c_border, line_width=1)
    pdf.text(48, curr_y - 13, stack_headers[0], font='/F2', size=8.5, color=c_dark)
    pdf.text(40 + t_w[0] + 6, curr_y - 13, stack_headers[1], font='/F2', size=8.5, color=c_dark)
    pdf.text(40 + t_w[0] + t_w[1] + 6, curr_y - 13, stack_headers[2], font='/F2', size=8.5, color=c_dark)

    curr_y -= 18
    for idx, (l, t, r) in enumerate(stack_data):
        rh = 19
        bg = c_card_bg if idx % 2 == 1 else (1, 1, 1)
        pdf.rect(40, curr_y - rh, 515, rh, fill=bg, stroke=c_border, line_width=0.8)
        pdf.text(48, curr_y - 13, l, font='/F2', size=8, color=c_dark)
        pdf.text(40 + t_w[0] + 6, curr_y - 13, t, font='/F1', size=8, color=c_primary)
        pdf.text(40 + t_w[0] + t_w[1] + 6, curr_y - 13, r, font='/F1', size=7.8, color=c_muted)
        curr_y -= rh

    # Section 6: Codebase Structure
    curr_y -= 16
    pdf.text(40, curr_y, "6. Clean Codebase & Directory Structure", font='/F2', size=13, color=c_dark)
    curr_y -= 8
    pdf.line(40, curr_y, 555, curr_y, stroke=c_border, line_width=0.8)
    curr_y -= 14

    code_tree = [
        "maths-project/",
        "  |-- backend/",
        "  |     |-- ai/          (config.py, groq_client.py, guardrails.py, prompts.py, schemas.py, tutor.py)",
        "  |     |-- rag/         (curriculum.py, ingest.py, vector stores & NCERT chapter mappers)",
        "  |     |-- database.py  (MySQL connection pooling, auto-table migrations & schema seeders)",
        "  |     +-- main.py      (FastAPI application routes, middleware, and dev admin endpoints)",
        "  |-- maths.html         (Main student learning portal, formula toolbars & chat canvas)",
        "  |-- login.html         (Unified Student & Developer login interface with Google OAuth)",
        "  |-- style.css          (Dark slate stylesheet with responsive mobile breakpoints)",
        "  |-- script.js          (Client application controller, speech TTS/STT, and message caching)",
        "  +-- PROJECT_DOCUMENTATION.md / .pdf (Official project specifications)"
    ]

    pdf.rect(40, curr_y - 120, 515, 120, fill=(0.98, 0.98, 0.99), stroke=c_border, line_width=0.8)
    tree_y = curr_y - 14
    for tl in code_tree:
        pdf.text(50, tree_y, tl, font='/F4', size=7.8, color=c_dark)
        tree_y -= 10

    # Section 7: Security & Compliance Highlights
    curr_y -= 134
    pdf.text(40, curr_y, "7. Security & Compliance Highlights", font='/F2', size=13, color=c_dark)
    curr_y -= 8
    pdf.line(40, curr_y, 555, curr_y, stroke=c_border, line_width=0.8)
    curr_y -= 14

    # Green Callout Box
    sec_box_h = 75
    pdf.rect(40, curr_y - sec_box_h, 515, sec_box_h, fill=c_green_bg, stroke=c_green_border, line_width=1)
    pdf.rect(40, curr_y - sec_box_h, 4, sec_box_h, fill=c_green_border)

    pdf.text(52, curr_y - 14, "Enterprise Security Standards Enforced:", font='/F2', size=9, color=(0.08, 0.40, 0.18))
    sec_items = [
        "- Zero Plaintext Passwords: Every credential is encrypted using Bcrypt with automatic salt rounds.",
        "- Row-Level User Isolation: Chat queries are strictly bounded by WHERE user_id = :authenticated_user_id.",
        "- SSRF Prevention: Developer web scrapers explicitly reject private internal networks (127.0.0.1, localhost).",
        "- Air-Gapped Developer Admin: Admin endpoints can be locked to local development environments (localhost)."
    ]
    s_y = curr_y - 27
    for si in sec_items:
        pdf.text(52, s_y, si, font='/F1', size=7.8, color=(0.08, 0.35, 0.16))
        s_y -= 11.5

    # Footer Page 3 & Author Signature
    pdf.line(40, 48, 555, 48, stroke=c_border, line_width=0.8)
    pdf.text(40, 36, "Authored by: Syed Alkab Hussain Rizvi, Sameed Khan, Rumman Siddiqui, Arman Khan, and Kazim Shaikh", font='/F2', size=8, color=c_dark)
    pdf.text(500, 36, "Page 3 of 3", font='/F1', size=8, color=c_muted)

    # Save PDF
    pdf.save(output_path)


if __name__ == "__main__":
    out_dir = r"C:\Users\SK\OneDrive\Desktop\maths project"
    pdf_path = os.path.join(out_dir, "PROJECT_DOCUMENTATION.pdf")
    generate_documentation_pdf(pdf_path)
