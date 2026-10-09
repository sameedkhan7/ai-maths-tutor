from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import sys
import os

# Ensure backend and project root are in sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_connection, init_db

try:
    from backend.ai.tutor import generate_tutor_response
    from backend.ai.schemas import TutorRequest, ChatMessage
except ImportError:
    from ai.tutor import generate_tutor_response
    from ai.schemas import TutorRequest, ChatMessage

# App start hote hi DB tables verify karo
init_db()

app = FastAPI(title="AI Maths Tutor API", version="1.0")

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request Schemas
class ChatRequest(BaseModel):
    question: str
    style: str = "simple"
    model: str = "llama3.3"
    language: str = "hinglish"
    chat_id: Optional[int] = None
    user_id: Optional[int] = 1
    attachment_name: Optional[str] = None
    attachment_text: Optional[str] = None

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    grade: str = "Class 10"

class LoginRequest(BaseModel):
    email: str
    password: str

# 1. Health Check
@app.get("/")
def home():
    return {"status": "online", "message": "AI Maths Tutor Backend with DB is running!"}

# 2. Student Registration API
@app.post("/api/register")
def register(req: RegisterRequest):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (name, email, password, grade) VALUES (?, ?, ?, ?)",
                       (req.name, req.email, req.password, req.grade))
        conn.commit()
        user_id = cursor.lastrowid
        return {"success": True, "message": "Registered successfully", "user_id": user_id, "name": req.name}
    except Exception as e:
        raise HTTPException(status_code=400, detail="Email already registered")
    finally:
        conn.close()

# 3. Student / Developer Login API
class ChangePasswordRequest(BaseModel):
    user_id: int
    current_password: str
    new_password: str

@app.post("/api/login")
def login(req: LoginRequest):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, name, email, grade, role 
        FROM users 
        WHERE (LOWER(email) = LOWER(?) OR LOWER(name) = LOWER(?)) AND password = ?
    """, (req.email, req.email, req.password))
    user = cursor.fetchone()
    conn.close()
    if user:
        return {
            "success": True, 
            "user_id": user["id"], 
            "name": user["name"],
            "email": user["email"],
            "grade": user["grade"],
            "role": user["role"] if "role" in user.keys() else "student"
        }
    raise HTTPException(status_code=401, detail="Invalid email/username or password")

@app.post("/api/user/change-password")
def change_password(req: ChangePasswordRequest):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM users WHERE id = ?", (req.user_id,))
    user = cursor.fetchone()
    if not user or user["password"] != req.current_password:
        conn.close()
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    cursor.execute("UPDATE users SET password = ? WHERE id = ?", (req.new_password, req.user_id))
    conn.commit()
    conn.close()
    return {"success": True, "message": "Password updated successfully!"}

# ==========================================
# DEVELOPER / ADMIN CONTROL PANEL ENDPOINTS
# ==========================================
from fastapi import UploadFile, File

try:
    from backend.rag.ingest import ingest_pdf_bytes, ingest_text_content, scrape_and_ingest_url, get_rag_stats
except ImportError:
    from rag.ingest import ingest_pdf_bytes, ingest_text_content, scrape_and_ingest_url, get_rag_stats

class TextIngestRequest(BaseModel):
    title: str
    content: str

class ScrapeRequest(BaseModel):
    url: str

@app.get("/api/dev/rag-stats")
def dev_rag_stats():
    """Returns RAG Knowledge Base Stats for Developer Dashboard"""
    try:
        stats = get_rag_stats()
        return {"success": True, "stats": stats}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/dev/upload-pdf")
async def dev_upload_pdf(file: UploadFile = File(...)):
    """Uploads a PDF file and ingests it into RAG vector store"""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    try:
        contents = await file.read()
        res = ingest_pdf_bytes(contents, file.filename)
        return {"success": True, "message": f"PDF '{file.filename}' ingested into RAG successfully!", "data": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF ingestion failed: {str(e)}")

@app.post("/api/dev/upload-text")
def dev_upload_text(req: TextIngestRequest):
    """Ingests custom text notes/curriculum into RAG vector store"""
    if not req.content.strip():
        raise HTTPException(status_code=400, detail="Content cannot be empty")
    try:
        res = ingest_text_content(req.title, req.content)
        return {"success": True, "message": f"Text document '{req.title}' ingested into RAG successfully!", "data": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Text ingestion failed: {str(e)}")

class PasswordChangeRequest(BaseModel):
    new_password: str

@app.post("/api/dev/change-password")
def dev_change_password(req: PasswordChangeRequest):
    """Updates Developer Admin password in database"""
    if not req.new_password.strip():
        raise HTTPException(status_code=400, detail="Password cannot be empty")
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE users SET password = ? WHERE role = 'developer' OR email = 'dev@mathstutor.com'", (req.new_password.strip(),))
        conn.commit()
        conn.close()
        return {"success": True, "message": "Developer Admin password updated successfully in Database!"}
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=f"Failed to update password: {str(e)}")


# 4. Student Chat File Parser API (Supports PDF, TXT, ZIP, Images)
@app.post("/api/chat/parse-file")
async def chat_parse_file(file: UploadFile = File(...)):
    """Parses student uploaded file (PDF, TXT, DOC, ZIP, Image) for AI tutor context"""
    filename = file.filename.lower()
    contents = await file.read()
    extracted_text = ""
    file_type = "file"

    if filename.endswith(".pdf"):
        file_type = "pdf"
        try:
            import io
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(contents))
            pages_text = []
            for p in reader.pages[:10]:
                t = p.extract_text()
                if t: pages_text.append(t)
            extracted_text = "\n".join(pages_text).strip()
        except Exception as e:
            extracted_text = f"Error reading PDF: {e}"

    elif filename.endswith((".txt", ".md", ".py", ".csv", ".json")):
        file_type = "text"
        try:
            extracted_text = contents.decode("utf-8", errors="ignore").strip()
        except Exception as e:
            extracted_text = str(e)

    elif filename.endswith(".zip"):
        file_type = "zip"
        try:
            import io, zipfile
            with zipfile.ZipFile(io.BytesIO(contents)) as z:
                names = z.namelist()
                extracted_text = f"ZIP Archive containing {len(names)} files: " + ", ".join(names[:10])
        except Exception as e:
            extracted_text = f"Error reading ZIP: {e}"

    elif filename.endswith((".png", ".jpg", ".jpeg", ".webp")):
        file_type = "image"
        extracted_text = ""

    size_kb = round(len(contents) / 1024, 1)
    size_str = f"{size_kb} KB" if size_kb < 1024 else f"{round(size_kb/1024, 2)} MB"

    return {
        "success": True,
        "filename": file.filename,
        "file_type": file_type,
        "size_str": size_str,
        "extracted_text": extracted_text[:5000]
    }


# 5. Main Chat API (Save to DB & Return Answer)
@app.post("/api/chat")
def chat_with_tutor(request: ChatRequest):
    raw_q = request.question.strip()
    style = request.style
    chat_id = request.chat_id

    # If student attached a file, combine with question prompt
    if request.attachment_text:
        doc_header = f"[Student Attached Document/Homework: {request.attachment_name or 'File'}]\nDocument Content:\n{request.attachment_text.strip()}\n\n"
        ai_query = doc_header + (f"Student Question: {raw_q}" if raw_q else "Please explain and solve the math problems in this document step by step.")
    else:
        ai_query = raw_q

    conn = get_connection()
    cursor = conn.cursor()

    # Agar naya chat session hai toh chats table me title banao
    if not chat_id:
        title_source = raw_q or (f"File: {request.attachment_name}" if request.attachment_name else "Maths Question")
        title = title_source[:35] + ("..." if len(title_source) > 35 else "")
        uid = request.user_id if request.user_id else 1
        cursor.execute("INSERT INTO chats (user_id, title, is_pinned) VALUES (?, ?, 0)", (uid, title))
        chat_id = cursor.lastrowid

    # Fetch recent chat history from DB for this chat_id if available
    chat_history_msgs = []
    if chat_id:
        cursor.execute("SELECT sender, text FROM messages WHERE chat_id = ? ORDER BY id ASC LIMIT 6", (chat_id,))
        for row in cursor.fetchall():
            role = "user" if row["sender"] == "user" else "assistant"
            chat_history_msgs.append(ChatMessage(role=role, content=row["text"]))

    # 🚀 Call Real Groq LLaMA 3.3 AI Tutor Engine
    try:
        tutor_req = TutorRequest(
            question=ai_query,
            chat_history=chat_history_msgs,
            explanation_style=style,
            language=request.language if request.language in ["english", "hindi", "hinglish", "urdu"] else "hinglish",
            model=request.model or "llama-3.3-70b-versatile"
        )
        tutor_res = generate_tutor_response(tutor_req)
        reply = tutor_res.answer
    except Exception as e:
        print(f"AI Generation Error (Fallback used): {e}")
        if style == "sports":
            reply = f"🏏 **Cricket Analogy for \"{raw_q}\":**\nSochiye jaise batsman boundary hit karne ke liye angle calculate karta hai, waise hi mathematics mein trajectory solve hoti hai!\n\nFormula: $v^2 = u^2 + 2as$\n\n🎯 **Try it yourself:** Kya aap initial velocity $u$ find kar sakte hain?"
        elif style == "step-by-step":
            reply = f"🔢 **Step-by-Step Solution for \"{raw_q}\":**\n1. Given data identify karein.\n2. Standard formula apply karein: $x = \\frac{{-b \\pm \\sqrt{{b^2 - 4ac}}}}{{2a}}$\n3. Values substitute karke final answer simplify karein.\n\n🎯 **Try it yourself:** Iska agla step calculate karke bataiye!"
        else:
            reply = f"💡 **Concept Explanation for \"{raw_q}\":**\nMathematics mein kisi bhi problem ko pehle visualize karein, fir standard NCERT formula apply karein!\n\nStandard Result: $\\int x^n dx = \\frac{{x^{{n+1}}}}{{n+1}} + C$\n\n🎯 **Try it yourself:** Kya aap $x = 2$ rakh kar answer nikaal sakte hain?"

    # Sawaal aur Jawab dono messages table me save karo
    user_saved_text = f"📎 [{request.attachment_name}]\n{raw_q}" if request.attachment_name and raw_q else (f"📎 [{request.attachment_name}]" if request.attachment_name else raw_q)
    cursor.execute("INSERT INTO messages (chat_id, sender, text, style) VALUES (?, ?, ?, ?)",
                   (chat_id, "user", user_saved_text, style))
    cursor.execute("INSERT INTO messages (chat_id, sender, text, style) VALUES (?, ?, ?, ?)",
                   (chat_id, "assistant", reply, style))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "chat_id": chat_id,
        "question": q,
        "style": style,
        "reply": reply
    }

# 5. Get Chats for Sidebar (Isolated per user_id, optional show_all for Dev Admin)
@app.get("/api/chats")
def get_chats(user_id: Optional[int] = 1, show_all: Optional[bool] = False):
    conn = get_connection()
    cursor = conn.cursor()
    if show_all:
        cursor.execute("SELECT id, title, is_pinned, created_at, user_id FROM chats ORDER BY created_at DESC")
    else:
        target_uid = user_id if user_id else 1
        cursor.execute("SELECT id, title, is_pinned, created_at FROM chats WHERE user_id = ? ORDER BY created_at DESC", (target_uid,))
    chats = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {"chats": chats}

# 6. Toggle Pin / Unpin
@app.put("/api/chats/{chat_id}/pin")
def toggle_pin(chat_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE chats SET is_pinned = 1 - is_pinned WHERE id = ?", (chat_id,))
    conn.commit()
    conn.close()
    return {"success": True}

# 7. Get All Messages for a Specific Chat Session (Restore History on Click)
@app.get("/api/chats/{chat_id}/messages")
def get_chat_messages(chat_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, sender, text, style, created_at FROM messages WHERE chat_id = ? ORDER BY id ASC", (chat_id,))
    messages = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {"chat_id": chat_id, "messages": messages}

# 8. Delete a Specific Chat Session
@app.delete("/api/chats/{chat_id}")
def delete_chat(chat_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM messages WHERE chat_id = ?", (chat_id,))
    cursor.execute("DELETE FROM chats WHERE id = ?", (chat_id,))
    conn.commit()
    conn.close()
    return {"success": True, "deleted_chat_id": chat_id}

# 9. Clear All Chats for a specific user
@app.delete("/api/chats")
def clear_all_chats(user_id: Optional[int] = None):
    conn = get_connection()
    cursor = conn.cursor()
    if user_id:
        cursor.execute("DELETE FROM messages WHERE chat_id IN (SELECT id FROM chats WHERE user_id = ?)", (user_id,))
        cursor.execute("DELETE FROM chats WHERE user_id = ?", (user_id,))
    else:
        cursor.execute("DELETE FROM messages")
        cursor.execute("DELETE FROM chats")
    conn.commit()
    conn.close()
    return {"success": True, "message": "Chats cleared"}

# 10. Rename Chat Title
@app.put("/api/chats/{chat_id}/title")
def rename_chat_title(chat_id: int, payload: dict):
    new_title = payload.get("title", "Maths Question").strip()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE chats SET title = ? WHERE id = ?", (new_title, chat_id))
    conn.commit()
    conn.close()
    return {"success": True, "new_title": new_title}