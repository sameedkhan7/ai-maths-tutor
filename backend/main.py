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
@app.post("/api/login")
def login(req: LoginRequest):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, grade, role FROM users WHERE email=? AND password=?", (req.email, req.password))
    user = cursor.fetchone()
    conn.close()
    if user:
        return {
            "success": True, 
            "user_id": user["id"], 
            "name": user["name"], 
            "grade": user["grade"],
            "role": user["role"] if "role" in user.keys() else "student"
        }
    raise HTTPException(status_code=401, detail="Invalid email or password")

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

@app.post("/api/dev/scrape-url")
def dev_scrape_url(req: ScrapeRequest):
    """Scrapes text content from any website URL and ingests into RAG vector store"""
    if not req.url.startswith("http"):
        raise HTTPException(status_code=400, detail="URL must start with http:// or https://")
    try:
        res = scrape_and_ingest_url(req.url)
        return {"success": True, "message": f"Scraped & ingested '{req.url}' into RAG successfully!", "data": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Web scraping failed: {str(e)}")


# 4. Main Chat API (Save to DB & Return Answer)
@app.post("/api/chat")
def chat_with_tutor(request: ChatRequest):
    q = request.question.strip()
    style = request.style
    chat_id = request.chat_id

    conn = get_connection()
    cursor = conn.cursor()

    # Agar naya chat session hai toh chats table me title banao
    if not chat_id:
        title = q[:35] + ("..." if len(q) > 35 else "")
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
            question=q,
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
            reply = f"🏏 **Cricket Analogy for \"{q}\":**\nSochiye jaise batsman boundary hit karne ke liye angle calculate karta hai, waise hi mathematics mein trajectory solve hoti hai!\n\nFormula: $v^2 = u^2 + 2as$\n\n🎯 **Try it yourself:** Kya aap initial velocity $u$ find kar sakte hain?"
        elif style == "step-by-step":
            reply = f"🔢 **Step-by-Step Solution for \"{q}\":**\n1. Given data identify karein.\n2. Standard formula apply karein: $x = \\frac{{-b \\pm \\sqrt{{b^2 - 4ac}}}}{{2a}}$\n3. Values substitute karke final answer simplify karein.\n\n🎯 **Try it yourself:** Iska agla step calculate karke bataiye!"
        else:
            reply = f"💡 **Concept Explanation for \"{q}\":**\nMathematics mein kisi bhi problem ko pehle visualize karein, fir standard NCERT formula apply karein!\n\nStandard Result: $\\int x^n dx = \\frac{{x^{{n+1}}}}{{n+1}} + C$\n\n🎯 **Try it yourself:** Kya aap $x = 2$ rakh kar answer nikaal sakte hain?"

    # Sawaal aur Jawab dono messages table me save karo
    cursor.execute("INSERT INTO messages (chat_id, sender, text, style) VALUES (?, ?, ?, ?)",
                   (chat_id, "user", q, style))
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

# 5. Get All Chats for Sidebar (Filtered per user_id)
@app.get("/api/chats")
def get_chats(user_id: Optional[int] = 1):
    conn = get_connection()
    cursor = conn.cursor()
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