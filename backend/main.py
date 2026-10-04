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

# 3. Student Login API
@app.post("/api/login")
def login(req: LoginRequest):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, grade FROM users WHERE email=? AND password=?", (req.email, req.password))
    user = cursor.fetchone()
    conn.close()
    if user:
        return {"success": True, "user_id": user["id"], "name": user["name"], "grade": user["grade"]}
    raise HTTPException(status_code=401, detail="Invalid email or password")

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
        cursor.execute("INSERT INTO chats (title, is_pinned) VALUES (?, 0)", (title,))
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

# 5. Get All Chats for Sidebar
@app.get("/api/chats")
def get_chats():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, is_pinned, created_at FROM chats ORDER BY created_at DESC")
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