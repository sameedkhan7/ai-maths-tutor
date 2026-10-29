import sys
import os
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(line_buffering=True)
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(line_buffering=True)
import re
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
import sys
import os

# Ensure backend and project root are in sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from backend.database import get_connection, init_db
except ImportError:
    from database import get_connection, init_db

try:
    from backend.ai.tutor import generate_tutor_response
    from backend.ai.schemas import TutorRequest, ChatMessage
    from backend.ai.image_generator import generate_ai_image
except ImportError:
    from ai.tutor import generate_tutor_response
    from ai.schemas import TutorRequest, ChatMessage
    from ai.image_generator import generate_ai_image

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
    model: str = "openai/gpt-oss-120b"
    language: str = "hinglish"
    grade: Optional[str] = "Class 10"
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
@app.get("/api/health")
def home():
    return {"status": "online", "message": "AI Maths Tutor Backend with DB is running!"}

# -------------------------------------------------------------
# REAL USER ACCOUNT & CRYPTOGRAPHIC AUTHENTICATION (BCRYPT + JWT)
# -------------------------------------------------------------
import bcrypt
import jwt
from datetime import datetime, timedelta

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "maths-tutor-jwt-secret-key-bca-2026-prod")
JWT_ALGORITHM = "HS256"

def hash_password(plain_pwd: str) -> str:
    """Hashes plain password using bcrypt with salt rounds=12"""
    return bcrypt.hashpw(plain_pwd.strip().encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")

def verify_password(plain_pwd: str, stored_hash: str) -> bool:
    """Verifies plain password against bcrypt hash, with backward compatibility for initial seed accounts"""
    try:
        p = plain_pwd.strip()
        if stored_hash.startswith("$2b$") or stored_hash.startswith("$2a$"):
            return bcrypt.checkpw(p.encode("utf-8"), stored_hash.encode("utf-8"))
        # Backward compatibility for initial plaintext accounts
        return p == stored_hash.strip()
    except Exception:
        return False

def create_access_token(data: dict, expires_days: int = 7) -> str:
    """Generates signed cryptographic JWT token with expiry"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=expires_days)
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


# 2. Student Registration API (Secured with Bcrypt)
@app.post("/api/register")
def register(req: RegisterRequest):
    if len(req.password.strip()) < 4:
        raise HTTPException(status_code=400, detail="Password must be at least 4 characters long")

    conn = get_connection()
    cursor = conn.cursor()
    try:
        hashed_pwd = hash_password(req.password)
        cursor.execute("INSERT INTO users (name, email, password, grade, role) VALUES (?, ?, ?, ?, 'student')",
                       (req.name.strip(), req.email.strip().lower(), hashed_pwd, req.grade))
        conn.commit()
        user_id = cursor.lastrowid
        token = create_access_token({"user_id": user_id, "email": req.email.strip().lower(), "role": "student"})
        return {
            "success": True, 
            "message": "Registered successfully", 
            "token": token,
            "user_id": user_id, 
            "name": req.name.strip(),
            "grade": req.grade
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail="Email already registered")
    finally:
        conn.close()

class GoogleAuthRequest(BaseModel):
    credential: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None
    picture: Optional[str] = None

@app.post("/api/auth/google")
def google_auth(req: GoogleAuthRequest):
    """Authenticates Google OAuth user, creates record if new, and returns signed JWT token"""
    email = None
    name = None
    if req.credential:
        try:
            import json
            import base64
            parts = req.credential.split(".")
            if len(parts) >= 2:
                payload_str = parts[1]
                payload_str += "=" * ((4 - len(payload_str) % 4) % 4)
                decoded_bytes = base64.urlsafe_b64decode(payload_str)
                google_payload = json.loads(decoded_bytes.decode("utf-8"))
                email = google_payload.get("email")
                name = google_payload.get("name")
        except Exception as e:
            print(f"Google token decode notice: {e}")

    if not email and req.email:
        email = req.email
    if not name and req.name:
        name = req.name

    if not email:
        raise HTTPException(status_code=400, detail="Invalid Google authentication payload")

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, name, email, grade, role FROM users WHERE LOWER(email) = LOWER(?)", (email.strip().lower(),))
        user = cursor.fetchone()
        if user:
            user_id = user["id"]
            user_name = user["name"]
            user_grade = user["grade"]
            user_role = user["role"] if "role" in user.keys() else "student"
        else:
            user_name = name or email.split("@")[0].capitalize()
            user_grade = "Class 10"
            user_role = "developer" if email.lower() == "dev@mathstutor.com" else "student"
            random_pwd_hash = hash_password("GOOGLE_SSO_SECURE_" + email)
            cursor.execute(
                "INSERT INTO users (name, email, password, grade, role) VALUES (?, ?, ?, ?, ?)",
                (user_name, email.strip().lower(), random_pwd_hash, user_grade, user_role)
            )
            conn.commit()
            user_id = cursor.lastrowid

        token = create_access_token({"user_id": user_id, "email": email.strip().lower(), "role": user_role})
        return {
            "success": True,
            "token": token,
            "user_id": user_id,
            "name": user_name,
            "email": email,
            "grade": user_grade,
            "role": user_role
        }
    finally:
        conn.close()

# 3. Student / Developer Login API (Verified with Bcrypt + JWT)
class ChangePasswordRequest(BaseModel):
    user_id: int
    current_password: str
    new_password: str

class ProfileUpdateRequest(BaseModel):
    user_id: int
    name: Optional[str] = None
    grade: Optional[str] = None

@app.post("/api/login")
def login(req: LoginRequest):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, name, email, password, grade, role 
        FROM users 
        WHERE LOWER(email) = LOWER(?) OR LOWER(name) = LOWER(?)
    """, (req.email.strip(), req.email.strip()))
    user = cursor.fetchone()
    
    if not user or not verify_password(req.password, user["password"]):
        conn.close()
        raise HTTPException(status_code=401, detail="Invalid email/username or password")

    # Auto-upgrade plaintext password to bcrypt hash on successful login
    stored_pwd = user["password"]
    if not (stored_pwd.startswith("$2b$") or stored_pwd.startswith("$2a$")):
        try:
            upgraded_hash = hash_password(req.password)
            cursor.execute("UPDATE users SET password = ? WHERE id = ?", (upgraded_hash, user["id"]))
            conn.commit()
        except Exception as e:
            print(f"Auto password upgrade notice: {e}")

    conn.close()

    user_role = user["role"] if "role" in user.keys() else "student"
    token = create_access_token({"user_id": user["id"], "email": user["email"], "role": user_role})

    return {
        "success": True, 
        "token": token,
        "user_id": user["id"], 
        "name": user["name"],
        "email": user["email"],
        "grade": user["grade"],
        "role": user_role
    }

@app.post("/api/user/change-password")
def change_password(req: ChangePasswordRequest):
    if len(req.new_password.strip()) < 4:
        raise HTTPException(status_code=400, detail="New password must be at least 4 characters long")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM users WHERE id = ?", (req.user_id,))
    user = cursor.fetchone()
    if not user or not verify_password(req.current_password, user["password"]):
        conn.close()
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    new_hashed = hash_password(req.new_password)
    cursor.execute("UPDATE users SET password = ? WHERE id = ?", (new_hashed, req.user_id))
    conn.commit()
    conn.close()
    return {"success": True, "message": "Password updated successfully with secure encryption!"}

@app.post("/api/user/profile")
def update_profile(req: ProfileUpdateRequest):
    conn = get_connection()
    cursor = conn.cursor()
    if req.name and req.grade:
        cursor.execute("UPDATE users SET name = ?, grade = ? WHERE id = ?", (req.name.strip(), req.grade.strip(), req.user_id))
    elif req.name:
        cursor.execute("UPDATE users SET name = ? WHERE id = ?", (req.name.strip(), req.user_id))
    elif req.grade:
        cursor.execute("UPDATE users SET grade = ? WHERE id = ?", (req.grade.strip(), req.user_id))
    conn.commit()
    conn.close()
    return {"success": True, "message": "Profile updated successfully!", "name": req.name, "grade": req.grade}

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
    """Scrapes a math webpage / article and ingests into RAG vector store"""
    if not req.url.strip() or not req.url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="Valid HTTP/HTTPS URL is required")
    try:
        res = scrape_and_ingest_url(req.url.strip())
        return {"success": True, "message": f"URL '{req.url}' scraped and ingested into RAG successfully!", "data": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"URL scraping failed: {str(e)}")


class PasswordChangeRequest(BaseModel):
    new_password: str

class DevCredentialsRequest(BaseModel):
    current_password: str
    new_email: Optional[str] = None
    new_password: Optional[str] = None
    confirm_password: Optional[str] = None

@app.post("/api/dev/update-credentials")
def dev_update_credentials(req: DevCredentialsRequest):
    """Allows developer/admin to update email and password with secure bcrypt hashing after verifying old password"""
    if not req.current_password or not req.current_password.strip():
        raise HTTPException(status_code=400, detail="Security Check: Purana/Current password enter karna anivarya (required) hai.")

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, email, password FROM users WHERE role = 'developer' OR email = 'dev@mathstutor.com' LIMIT 1")
        dev_user = cursor.fetchone()
        if not dev_user:
            cursor.execute("SELECT id, email, password FROM users WHERE id = 1 LIMIT 1")
            dev_user = cursor.fetchone()

        if not dev_user:
            conn.close()
            raise HTTPException(status_code=404, detail="Developer account not found in database")

        # 1. Strictly verify current / old password
        if not verify_password(req.current_password.strip(), dev_user["password"]):
            conn.close()
            raise HTTPException(status_code=401, detail="Galat purana password! Purane password ke bina Gmail ya naya password change nahi ho sakta.")

        dev_id = dev_user["id"]
        updates = []
        params = []
        applied_actions = []

        # 2. Check and update Email / Gmail
        if req.new_email and req.new_email.strip():
            clean_email = req.new_email.strip().lower()
            current_email = (dev_user["email"] or "").lower()
            if clean_email != current_email:
                updates.append("email = ?")
                params.append(clean_email)
                applied_actions.append(f"Gmail updated to {clean_email}")

        # 3. Check and update New Password (requires 2x entry match and length check)
        if req.new_password and req.new_password.strip():
            clean_new_pass = req.new_password.strip()
            clean_confirm = req.confirm_password.strip() if req.confirm_password else ""

            if clean_new_pass != clean_confirm:
                conn.close()
                raise HTTPException(status_code=400, detail="Naya password aur confirm password aapas me match nahi kar rahe hain! Dono same hone chahiye.")

            if len(clean_new_pass) < 4:
                conn.close()
                raise HTTPException(status_code=400, detail="Naya password kam se kam 4 characters ka hona chahiye.")

            hashed_pwd = hash_password(clean_new_pass)
            updates.append("password = ?")
            params.append(hashed_pwd)
            applied_actions.append("Password securely updated (bcrypt hashed)")

        if not updates:
            conn.close()
            return {
                "success": True,
                "message": "Purana password verify ho gaya, lekin koi naya Gmail ya naya Password badalne ke liye nahi diya gaya.",
                "email": dev_user["email"]
            }

        params.append(dev_id)
        query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, tuple(params))
        conn.commit()
        conn.close()

        final_msg = "Developer Admin credentials updated successfully! " + " & ".join(applied_actions)
        return {
            "success": True,
            "message": final_msg,
            "email": req.new_email.strip().lower() if req.new_email else dev_user["email"]
        }
    except HTTPException:
        raise
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=f"Failed to update developer credentials: {str(e)}")


@app.post("/api/dev/change-password")
def dev_change_password(req: PasswordChangeRequest):
    """Updates Developer Admin password in database"""
    if not req.new_password.strip():
        raise HTTPException(status_code=400, detail="Password cannot be empty")
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE users SET password = ? WHERE role = 'developer' OR email = 'dev@mathstutor.com'", (hash_password(req.new_password.strip()),))
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

    # Phase 1: DB Read & Chat Init (Commit and close immediately so SQLite/MySQL is never locked during AI call)
    conn = get_connection()
    try:
        cursor = conn.cursor()
        chat_exists = False
        if chat_id:
            cursor.execute("SELECT id FROM chats WHERE id = ?", (chat_id,))
            chat_exists = bool(cursor.fetchone())

        if not chat_id or not chat_exists:
            title_source = raw_q or (f"File: {request.attachment_name}" if request.attachment_name else "Maths Question")
            title = title_source[:35] + ("..." if len(title_source) > 35 else "")
            uid = request.user_id if request.user_id else 1
            cursor.execute("INSERT INTO chats (user_id, title, is_pinned) VALUES (?, ?, 0)", (uid, title))
            conn.commit()
            chat_id = cursor.lastrowid

        # Fetch recent chat history from DB for this chat_id if available (latest 10 messages in chronological order)
        chat_history_msgs = []
        if chat_id and chat_exists:
            cursor.execute("SELECT sender, text FROM messages WHERE chat_id = ? ORDER BY id DESC LIMIT 10", (chat_id,))
            rows = cursor.fetchall()
            for row in reversed(rows):
                role = "user" if row["sender"] == "user" else "assistant"
                chat_history_msgs.append(ChatMessage(role=role, content=row["text"]))
    finally:
        conn.close()

    # Normalize language: accept hinglish, hindi, english, urdu, arabic
    VALID_LANGUAGES = {"hinglish", "hindi", "hi", "english", "en", "urdu", "ur", "arabic", "ar"}
    raw_lang = (request.language or "hinglish").strip().lower()
    if raw_lang in ["en", "english"]:
        normalized_lang = "english"
    elif raw_lang in ["hi", "hindi"]:
        normalized_lang = "hindi"
    elif raw_lang in ["ur", "urdu"]:
        normalized_lang = "urdu"
    elif raw_lang in ["ar", "arabic"]:
        normalized_lang = "arabic"
    else:
        normalized_lang = "hinglish"

    # Normalize style
    from backend.ai.styles import detect_style
    normalized_style = detect_style(ai_query, request.style or "simple")

    print(f"📡 [API Chat] Received Request | Grade: {request.grade} | Lang: {normalized_lang} | Style: {normalized_style} | Model: {request.model}")

    # 🚀 Call Real Groq LLaMA 3.3 AI Tutor Engine
    try:
        tutor_req = TutorRequest(
            question=ai_query,
            chat_history=chat_history_msgs,
            explanation_style=normalized_style,
            language=normalized_lang,
            student_grade=request.grade or "Class 10",
            model=request.model or "openai/gpt-oss-120b"
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

    # Phase 2: Save Messages to DB (Isolated transaction)
    conn = get_connection()
    try:
        cursor = conn.cursor()
        user_saved_text = f"📎 [{request.attachment_name}]\n{raw_q}" if request.attachment_name and raw_q else (f"📎 [{request.attachment_name}]" if request.attachment_name else raw_q)
        # Generate image before saving so image_url is permanently persisted to DB
        image_data = {"image_url": None, "theme": None, "prompt": None, "provider": None}
        visual_explicit_triggers = [
            "visualize", "visualization", "visualise", "visualisation",
            "diagram", "image", "photo", "picture", "chitra", "graph",
            "figure", "draw", "banao", "dikhao", "visual", "3d", "infographic", "poster"
        ]
        is_visual_query = any(w in raw_q.lower() for w in visual_explicit_triggers) or (style == "visual")
        if is_visual_query:
            try:
                image_data = generate_ai_image(raw_q, reply)
            except Exception as img_err:
                print(f"[Main Image Gen Notice] {img_err}")

        # Strip duplicate SVG if image is present
        if image_data.get("image_url"):
            reply = re.sub(r'```svg\s*<svg.*?</svg>\s*```', '', reply, flags=re.DOTALL)
            reply = re.sub(r'<svg.*?</svg>', '', reply, flags=re.DOTALL).strip()

        cursor.execute("INSERT INTO messages (chat_id, sender, text, style) VALUES (?, ?, ?, ?)",
                       (chat_id, "user", user_saved_text, style))
        cursor.execute("INSERT INTO messages (chat_id, sender, text, style, image_url, image_prompt) VALUES (?, ?, ?, ?, ?, ?)",
                       (chat_id, "assistant", reply, style, image_data.get("image_url"), image_data.get("prompt")))
        conn.commit()
    finally:
        conn.close()

    # AI 3D/Visual Image Generation: ONLY when student explicitly requested visualization or visual/sports mode!
    image_data = {"image_url": None, "theme": None, "prompt": None, "provider": None}
    visual_explicit_triggers = [
        "visualize", "visualization", "visualise", "visualisation",
        "diagram", "image", "photo", "picture", "chitra", "graph",
        "figure", "draw", "banao", "dikhao", "visual", "3d", "infographic"
    ]
    is_visual_query = any(w in raw_q.lower() for w in visual_explicit_triggers) or (style == "visual")
    if is_visual_query:
        try:
            image_data = generate_ai_image(raw_q, reply)
        except Exception as img_err:
            print(f"[Main Image Gen Notice] {img_err}")

    # SINGLE VISUAL GUARANTEE: If an educational visual image is generated,
    # strip any duplicate SVG diagram from markdown reply so only ONE pristine image card is displayed!
    if image_data.get("image_url"):
        reply = re.sub(r'```svg\s*<svg.*?</svg>\s*```', '', reply, flags=re.DOTALL)
        reply = re.sub(r'<svg.*?</svg>', '', reply, flags=re.DOTALL).strip()

    return {
        "success": True,
        "chat_id": chat_id,
        "question": raw_q,
        "style": style,
        "reply": reply,
        "image_url": image_data.get("image_url"),
        "image_theme": image_data.get("theme"),
        "image_prompt": image_data.get("prompt"),
        "image_provider": image_data.get("provider")
    }

class ImageGenRequest(BaseModel):
    question: str
    context: Optional[str] = ""
    chat_id: Optional[int] = None

@app.post("/api/generate-image")
def generate_image_endpoint(req: ImageGenRequest):
    """Generates an AI Visual / 3D simulation diagram on demand for any math question and saves to DB"""
    try:
        res = generate_ai_image(req.question, req.context or "", force=True)
        # Persist generated image to database for this chat session
        if req.chat_id and res.get("image_url"):
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE messages SET image_url = ?, image_prompt = ? WHERE id = (SELECT id FROM (SELECT id FROM messages WHERE chat_id = ? AND sender = 'assistant' ORDER BY id DESC LIMIT 1) as t)",
                    (res["image_url"], res.get("prompt"), req.chat_id)
                )
                conn.commit()
                conn.close()
            except Exception as db_err:
                print(f"[Generate Image DB Save Notice] {db_err}")
        return {"success": True, **res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
def get_chat_messages(chat_id: int, user_id: Optional[int] = None):
    conn = get_connection()
    cursor = conn.cursor()
    if user_id:
        cursor.execute("SELECT user_id FROM chats WHERE id = ?", (chat_id,))
        chat_row = cursor.fetchone()
        if chat_row and chat_row["user_id"] != user_id:
            cursor.execute("SELECT role FROM users WHERE id = ?", (user_id,))
            user_row = cursor.fetchone()
            if not user_row or user_row["role"] != "developer":
                conn.close()
                raise HTTPException(status_code=403, detail="Unauthorized access to chat")
    cursor.execute("SELECT id, sender, text, style, image_url, image_prompt, created_at FROM messages WHERE chat_id = ? ORDER BY id ASC", (chat_id,))
    messages = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {"chat_id": chat_id, "messages": messages}

# 8. Delete a Specific Chat Session
@app.delete("/api/chats/{chat_id}")
def delete_chat(chat_id: int, user_id: Optional[int] = None):
    conn = get_connection()
    cursor = conn.cursor()
    if user_id:
        cursor.execute("SELECT user_id FROM chats WHERE id = ?", (chat_id,))
        chat_row = cursor.fetchone()
        if chat_row and chat_row["user_id"] != user_id:
            cursor.execute("SELECT role FROM users WHERE id = ?", (user_id,))
            user_row = cursor.fetchone()
            if not user_row or user_row["role"] != "developer":
                conn.close()
                raise HTTPException(status_code=403, detail="Unauthorized to delete this chat")
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



# ==========================================================
# 10.5 High-Fidelity Neural AI Voice Speech Synthesis (Edge-TTS)
# ==========================================================
class TTSVoiceRequest(BaseModel):
    text: str
    voice: Optional[str] = "en-IN-NeerjaExpressiveNeural"
    rate: Optional[str] = "+0%"
    pitch: Optional[str] = "+0Hz"

def polish_tts_text(text: str, voice: str) -> str:
    s = text
    # 1. Eliminate all brackets and parens so TTS engine NEVER speaks "bracket" or "curly bracket"
    s = re.sub(r'[{}\[\]\(\)]', ' ', s)
    s = re.sub(r'[_~|\\]', ' ', s)

    # 2. Voice-specific phonetic enhancements
    if voice.startswith("hi-IN"):
        # For Hindi neural voices (Swara, Madhur), transliterate key math keywords into Devanagari
        # so Microsoft Edge TTS speaks them with 100% natural fluency without stuttering
        s = re.sub(r'\btrigonometry\b', 'ट्रिगोनोमेट्री', s, flags=re.IGNORECASE)
        s = re.sub(r'\btrigonometric\b', 'ट्रिगोनोमेट्रिक', s, flags=re.IGNORECASE)
        s = re.sub(r'\bderivative\b', 'डेरिवेटिव', s, flags=re.IGNORECASE)
        s = re.sub(r'\bderivatives\b', 'डेरिवेटिव्स', s, flags=re.IGNORECASE)
        s = re.sub(r'\bfunction\b', 'फ़ंक्शन', s, flags=re.IGNORECASE)
        s = re.sub(r'\bcalculus\b', 'कैलकुलस', s, flags=re.IGNORECASE)
        s = re.sub(r'\bdifferentiation\b', 'डिफ़रेंशिएशन', s, flags=re.IGNORECASE)
        s = re.sub(r'\bintegration\b', 'इंटीग्रेशन', s, flags=re.IGNORECASE)
        s = re.sub(r'\binstantaneous\b', 'इंस्टेंटेनियस', s, flags=re.IGNORECASE)
        s = re.sub(r'\bvelocity\b', 'वेलोसिटी', s, flags=re.IGNORECASE)
        s = re.sub(r'\bdistance\b', 'डिस्टेंस', s, flags=re.IGNORECASE)
        s = re.sub(r'\brate of change\b', 'रेट ऑफ़ चेंज', s, flags=re.IGNORECASE)
        s = re.sub(r'\bformula\b', 'फॉर्मूला', s, flags=re.IGNORECASE)
        s = re.sub(r'\bformulas\b', 'फॉर्मूले', s, flags=re.IGNORECASE)
        s = re.sub(r'\bratios\b', 'रेश्यो', s, flags=re.IGNORECASE)
        s = re.sub(r'\bratio\b', 'रेश्यो', s, flags=re.IGNORECASE)
        s = re.sub(r'\bexample\b', 'एग्जांपल', s, flags=re.IGNORECASE)
        s = re.sub(r'\bstep\b', 'स्टेप', s, flags=re.IGNORECASE)
        s = re.sub(r'\bintuition\b', 'इंट्यूशन', s, flags=re.IGNORECASE)
        s = re.sub(r'\banalogy\b', 'एनालॉजी', s, flags=re.IGNORECASE)
        s = re.sub(r'\bpractice\b', 'प्रैक्टिस', s, flags=re.IGNORECASE)
        s = re.sub(r'\bquestion\b', 'क्वेश्चन', s, flags=re.IGNORECASE)
        s = re.sub(r'\bquestions\b', 'क्वेश्चंस', s, flags=re.IGNORECASE)
        s = re.sub(r'\bupon\b', 'अपॉन', s, flags=re.IGNORECASE)
        s = re.sub(r'\bequals\b', 'इक्वल्स', s, flags=re.IGNORECASE)
        s = re.sub(r'\bsquare\b', 'स्क्वायर', s, flags=re.IGNORECASE)
        s = re.sub(r'\bcube\b', 'क्यूब', s, flags=re.IGNORECASE)
        s = re.sub(r'\bseconds\b', 'सेकंड्स', s, flags=re.IGNORECASE)
        s = re.sub(r'\bmeters per second\b', 'मीटर पर सेकंड', s, flags=re.IGNORECASE)
        s = re.sub(r'\bof\b', 'ऑफ़', s, flags=re.IGNORECASE)
    return re.sub(r'\s+', ' ', s).strip()

@app.post("/api/tts")
async def generate_neural_speech(req: TTSVoiceRequest):
    """
    Synthesizes ultra-realistic Neural AI Voice audio using Edge TTS.
    Returns studio-grade MP3 audio stream for Indian English & Hindi teachers.
    """
    clean_text = req.text.strip()
    if not clean_text:
        raise HTTPException(status_code=400, detail="Text cannot be empty.")

    # Limit to 3500 chars per speech snippet for responsive streaming
    if len(clean_text) > 3500:
        clean_text = clean_text[:3500]

    voice = req.voice or "en-IN-NeerjaExpressiveNeural"
    clean_text = polish_tts_text(clean_text, voice)
    rate = req.rate or "+0%"
    pitch = req.pitch or "+0Hz"

    try:
        import edge_tts
        communicate = edge_tts.Communicate(clean_text, voice, rate=rate, pitch=pitch)
        chunks = []
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                chunks.append(chunk["data"])

        audio_bytes = b"".join(chunks)
        if not audio_bytes:
            raise HTTPException(status_code=500, detail="TTS generation produced empty audio.")

        return Response(content=audio_bytes, media_type="audio/mpeg")
    except Exception as e:
        print(f"[TTS Error] {e}")
        raise HTTPException(status_code=500, detail=f"TTS engine notice: {str(e)}")


# 11. Root redirect → login.html
from fastapi.responses import RedirectResponse, Response

@app.get("/")
def root_redirect():
    return RedirectResponse(url="/login.html")

# 12. Mount Static Frontend (Serves login.html, maths.html, JS, CSS directly from FastAPI)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app.mount("/", StaticFiles(directory=PROJECT_ROOT, html=True), name="static")

if __name__ == '__main__':
    import uvicorn
    port = int(os.environ.get('PORT', 10000))
    print(f'[Server] Starting on port {port}...')
    uvicorn.run(app, host='0.0.0.0', port=port)
