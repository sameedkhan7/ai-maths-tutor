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

ENVIRONMENT = os.getenv("ENVIRONMENT", "development").strip().lower()

def _determine_production_status() -> bool:
    raw_env = os.getenv("ENVIRONMENT", "").strip().lower()
    if raw_env:
        return raw_env in ("production", "prod")
    if bool(os.getenv("RENDER")):
        if os.getenv("REQUIRE_SMTP", "").lower() in ("true", "1", "yes"):
            return True
        from backend.email_service import is_smtp_configured
        return is_smtp_configured()
    return False

IS_PRODUCTION = _determine_production_status()

# CORS setup with explicit allowed origins (Never use wildcard with credentials)
DEFAULT_PROD_ORIGINS = [
    "https://ai-maths-tutor.onrender.com",
]
DEV_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5000",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5000",
    "http://127.0.0.1:5500",
    "http://127.0.0.1:8000",
]

env_origins = os.getenv("ALLOWED_ORIGINS", "")
if env_origins.strip():
    allowed_origins = [o.strip() for o in env_origins.split(",") if o.strip()]
else:
    allowed_origins = list(DEFAULT_PROD_ORIGINS)

if not IS_PRODUCTION:
    for dev_o in DEV_ORIGINS:
        if dev_o not in allowed_origins:
            allowed_origins.append(dev_o)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
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

class RegisterInitiateRequest(BaseModel):
    name: str
    email: str
    password: Optional[str] = None
    confirm_password: Optional[str] = None
    grade: Optional[str] = "Class 10"

class VerifyOtpRequest(BaseModel):
    email: str
    otp: str

class CompleteRegistrationRequest(BaseModel):
    email: str
    verification_token: str
    password: str
    confirm_password: Optional[str] = None

class ResendOtpRequest(BaseModel):
    email: str

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
import json
import secrets
from datetime import datetime, timedelta, timezone
from fastapi import Header, Depends
from backend.email_service import (
    generate_secure_otp, hash_otp, verify_otp_hash, send_otp_email,
    validate_production_smtp_config
)

JWT_ALGORITHM = "HS256"
_RAW_JWT_KEY = os.getenv("JWT_SECRET_KEY")

INSECURE_SECRETS = {
    None, "", "maths-tutor-jwt-secret-key-bca-2026-prod", "secret", "change-me", "default"
}

if IS_PRODUCTION:
    if not _RAW_JWT_KEY or _RAW_JWT_KEY.strip() in INSECURE_SECRETS or len(_RAW_JWT_KEY.strip()) < 32:
        raise RuntimeError(
            "FATAL SECURITY ERROR: In production environment, 'JWT_SECRET_KEY' must be set to a cryptographically "
            "secure secret (minimum 32 characters) via environment variables. Do NOT use default or fallback keys."
        )
    JWT_SECRET_KEY = _RAW_JWT_KEY.strip()
    # Enforce real SMTP configuration in production (fail startup early)
    validate_production_smtp_config()
else:
    # Safe fallback strictly for local development testing
    JWT_SECRET_KEY = _RAW_JWT_KEY.strip() if _RAW_JWT_KEY else "maths-tutor-dev-only-secret-do-not-use-in-production-12345"

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
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=expires_days)
    to_encode.update({"exp": expire, "iat": now})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def get_current_user_payload(authorization: Optional[str] = Header(None)) -> dict:
    """
    Validates JWT token from Authorization header (Bearer <token>).
    Rejects missing, expired, or invalid tokens with HTTP 401 Unauthorized.
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization header. Please log in.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Invalid Authorization header format. Expected 'Bearer <token>'.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    token = parts[1]
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or malformed token.",
            headers={"WWW-Authenticate": "Bearer"}
        )

@app.get("/api/auth/me")
def get_me(current_user: dict = Depends(get_current_user_payload)):
    """Protected endpoint: Returns verified identity for authenticated user"""
    return {
        "success": True,
        "user_id": current_user.get("user_id"),
        "email": current_user.get("email"),
        "role": current_user.get("role", "student")
    }


def is_valid_real_email(email: str) -> tuple[bool, str]:
    """Validates real syntax, legitimate domain MX/DNS reachability, and blocks disposable/fake emails"""
    import socket
    clean_email = email.strip().lower()

    # 1. Regex Syntax Check
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    if not re.match(email_regex, clean_email):
        return False, "Invalid email format. Please enter a valid email address (e.g. name@gmail.com)."

    username, domain = clean_email.split('@', 1)

    # 2. Block Disposable / Trash Temporary Email Providers
    DISPOSABLE_DOMAINS = {
        'tempmail.com', '10minutemail.com', 'guerrillamail.com', 'sharklasers.com',
        'throwawaymail.com', 'yopmail.com', 'mailinator.com', 'getnada.com',
        'dispostable.com', 'trashmail.com', 'fakeinbox.com', 'burnermail.io'
    }
    if domain in DISPOSABLE_DOMAINS:
        return False, "Disposable or temporary emails are not allowed. Please use your genuine Google/Yahoo/Outlook email."

    # 3. Check Real Domain Existence via DNS
    try:
        socket.gethostbyname(domain)
    except Exception:
        return False, f"Domain '@{domain}' does not exist on the internet. Please provide a real email domain."

def is_valid_gmail(email: str) -> tuple[bool, str]:
    """
    Validates that an email is a strict, well-formed Gmail address ending in @gmail.com.
    Blocks non-Gmail domains, random non-existent patterns, and invalid Gmail usernames.
    """
    clean_email = email.strip().lower()

    # 1. Regex Syntax Check
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    if not re.match(email_regex, clean_email):
        return False, "Invalid email format. Manual signup accepts only valid Gmail addresses ending in @gmail.com."

    parts = clean_email.split('@', 1)
    if len(parts) != 2:
        return False, "Invalid email format. Manual signup accepts only valid Gmail addresses ending in @gmail.com."

    username, domain = parts[0], parts[1]

    # 2. Strict Domain Check
    if domain != "gmail.com":
        return False, "Manual signup accepts only valid Gmail addresses ending in @gmail.com."

    # 3. Gmail Username Restrictions
    if len(username) < 3 or len(username) > 30:
        return False, "Gmail username must be between 3 and 30 characters long."

    if username.startswith(".") or username.endswith("."):
        return False, "Gmail username cannot start or end with a dot."

    if ".." in username:
        return False, "Gmail username cannot contain consecutive dots."

    if not re.match(r"^[a-z0-9.]+$", username):
        return False, "Gmail username can only contain letters (a-z), numbers (0-9), and dots (.)."

    return True, "OK"


def parse_dt_safe(val) -> datetime:
    """Safely converts SQLite/MySQL timestamp values to timezone-aware UTC datetime"""
    if isinstance(val, datetime):
        if val.tzinfo is None:
            return val.replace(tzinfo=timezone.utc)
        return val
    val_str = str(val).strip().replace(" ", "T")
    if not val_str.endswith("Z") and "+" not in val_str and "-" not in val_str[10:]:
        val_str += "+00:00"
    return datetime.fromisoformat(val_str)


def row_val(row, key, default=None):
    """Safely reads a field from either sqlite3.Row or dict object"""
    if not row:
        return default
    if isinstance(row, dict):
        return row.get(key, default)
    try:
        return row[key] if key in row.keys() else default
    except Exception:
        return default


# 2. Student Registration Flow (Strict Gmail Ownership Verification via 6-digit OTP)
@app.post("/api/register/initiate")
def register_initiate(req: RegisterInitiateRequest):
    """
    Step 1 of Registration:
    Validates form data, enforces strict @gmail.com address, checks uniqueness,
    generates 6-digit OTP, hashes OTP securely, and dispatches verification email.
    """
    if len(req.name.strip()) < 2:
        raise HTTPException(status_code=400, detail="Please enter your real full name.")

    clean_email = req.email.strip().lower()
    is_valid, reason = is_valid_gmail(clean_email)
    if not is_valid:
        raise HTTPException(status_code=400, detail=reason)

    if req.password is not None and req.password.strip():
        if len(req.password.strip()) < 8:
            raise HTTPException(status_code=400, detail="Password must be at least 8 characters long.")
        if req.confirm_password is not None and req.password.strip() != req.confirm_password.strip():
            raise HTTPException(status_code=400, detail="Password and Confirm Password do not match.")

    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Check if already registered and verified
        cursor.execute("SELECT id, is_verified FROM users WHERE LOWER(email) = LOWER(?)", (clean_email,))
        existing_user = cursor.fetchone()
        if existing_user and row_val(existing_user, "is_verified", 1) == 1:
            raise HTTPException(status_code=400, detail="This Gmail address is already registered and verified. Please log in.")

        now = datetime.now(timezone.utc)

        # Check for active cooldown on existing pending verification (60 seconds)
        cursor.execute("SELECT id, last_sent_at FROM email_verifications WHERE LOWER(email) = LOWER(?) ORDER BY id DESC LIMIT 1", (clean_email,))
        active_verif = cursor.fetchone()
        if active_verif:
            last_sent = parse_dt_safe(active_verif["last_sent_at"])
            elapsed = (now - last_sent).total_seconds()
            if elapsed < 60:
                remaining = int(60 - elapsed)
                raise HTTPException(status_code=429, detail=f"Please wait {remaining} seconds before requesting a new verification code.")

        # Generate cryptographic 6-digit OTP & salt (never stored in plaintext)
        otp = generate_secure_otp()
        salt = secrets.token_hex(16)
        otp_hash = hash_otp(otp, salt)

        # Hash student password if provided (for backward test compatibility)
        hashed_pwd = hash_password(req.password.strip()) if (req.password and req.password.strip()) else None
        user_payload = json.dumps({
            "name": req.name.strip(),
            "email": clean_email,
            "password": hashed_pwd,
            "grade": req.grade or "Class 10",
            "verified": False
        })

        now_str = now.strftime("%Y-%m-%d %H:%M:%S")
        exp_str = (now + timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S")

        # Delete any previous stale verification requests for this email
        cursor.execute("DELETE FROM email_verifications WHERE LOWER(email) = LOWER(?)", (clean_email,))

        cursor.execute("""
            INSERT INTO email_verifications (email, otp_hash, salt, user_data, attempts, max_attempts, resend_count, last_sent_at, expires_at)
            VALUES (?, ?, ?, ?, 0, 5, 0, ?, ?)
        """, (clean_email, otp_hash, salt, user_payload, now_str, exp_str))
        conn.commit()

        # Dispatch OTP via email service
        sent, send_msg = send_otp_email(clean_email, otp, recipient_name=req.name.strip())
        if not sent:
            print(f"[Email Notice] Could not deliver email to {clean_email}: {send_msg}")
            cursor.execute("DELETE FROM email_verifications WHERE LOWER(email) = LOWER(?)", (clean_email,))
            conn.commit()
            raise HTTPException(
                status_code=500,
                detail=send_msg if "unavailable" in send_msg.lower() else "Failed to send verification email. Please try again later."
            )

        return {
            "success": True,
            "message": "A 6-digit verification code has been sent to your Gmail inbox. Please check your inbox.",
            "email": clean_email,
            "cooldown_seconds": 60,
            "expires_in_minutes": 5
        }
    finally:
        conn.close()


@app.post("/api/register/verify-otp")
def register_verify_otp(req: VerifyOtpRequest):
    """
    Step 2 of Registration:
    Validates entered OTP against stored hash, checks 5-minute expiry and attempt limit.
    If password was provided in Step 1 (backward compatibility), creates verified user record and returns JWT token.
    If password is not yet set, verifies Gmail ownership and issues a verification_token for Step 3 password creation.
    """
    clean_email = req.email.strip().lower()
    clean_otp = req.otp.strip()

    if len(clean_otp) != 6 or not clean_otp.isdigit():
        raise HTTPException(status_code=400, detail="Invalid code format. Please enter a 6-digit numeric OTP.")

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT id, otp_hash, salt, user_data, attempts, max_attempts, expires_at
            FROM email_verifications
            WHERE LOWER(email) = LOWER(?)
            ORDER BY id DESC LIMIT 1
        """, (clean_email,))
        record = cursor.fetchone()

        if not record:
            raise HTTPException(status_code=400, detail="No active verification session found. Please start registration again.")

        now = datetime.now(timezone.utc)
        expires_dt = parse_dt_safe(record["expires_at"])

        # 1. Check expiration (5 minutes)
        if now > expires_dt:
            cursor.execute("DELETE FROM email_verifications WHERE id = ?", (record["id"],))
            conn.commit()
            raise HTTPException(status_code=400, detail="Verification code has expired (valid for 5 minutes). Please request a new code.")

        # 2. Check attempt limit
        attempts = record["attempts"] or 0
        max_attempts = record["max_attempts"] or 5
        if attempts >= max_attempts:
            cursor.execute("DELETE FROM email_verifications WHERE id = ?", (record["id"],))
            conn.commit()
            raise HTTPException(status_code=400, detail="Too many failed attempts. Verification session expired. Please register again.")

        # 3. Cryptographic hash comparison
        is_match = verify_otp_hash(clean_otp, record["salt"], record["otp_hash"])
        if not is_match:
            new_attempts = attempts + 1
            cursor.execute("UPDATE email_verifications SET attempts = ? WHERE id = ?", (new_attempts, record["id"]))
            conn.commit()
            remaining = max(0, max_attempts - new_attempts)
            if remaining == 0:
                cursor.execute("DELETE FROM email_verifications WHERE id = ?", (record["id"],))
                conn.commit()
                raise HTTPException(status_code=400, detail="Incorrect verification code. Maximum attempts reached. Please register again.")
            raise HTTPException(status_code=400, detail=f"Incorrect verification code. {remaining} attempt(s) remaining.")

        # 4. Success: Gmail ownership verified
        user_data = json.loads(record["user_data"])
        name = user_data["name"]
        hashed_pwd = user_data.get("password")
        grade = user_data.get("grade", "Class 10")

        # Case A: Password already present (legacy 2-step flow)
        if hashed_pwd:
            cursor.execute("DELETE FROM users WHERE LOWER(email) = LOWER(?) AND is_verified = 0", (clean_email,))

            cursor.execute("SELECT id FROM users WHERE LOWER(email) = LOWER(?)", (clean_email,))
            existing = cursor.fetchone()
            if existing:
                cursor.execute(
                    "UPDATE users SET name = ?, password = ?, grade = ?, is_verified = 1 WHERE id = ?",
                    (name, hashed_pwd, grade, existing["id"])
                )
                user_id = existing["id"]
            else:
                cursor.execute(
                    "INSERT INTO users (name, email, password, grade, role, is_verified) VALUES (?, ?, ?, ?, 'student', 1)",
                    (name, clean_email, hashed_pwd, grade)
                )
                user_id = cursor.lastrowid

            cursor.execute("DELETE FROM email_verifications WHERE id = ?", (record["id"],))
            conn.commit()

            token = create_access_token({"user_id": user_id, "email": clean_email, "role": "student"})
            return {
                "success": True,
                "message": "Account verified and registered successfully!",
                "token": token,
                "user_id": user_id,
                "name": name,
                "email": clean_email,
                "grade": grade
            }

        # Case B: Password to be created in Step 3 (strict Gmail ownership verification)
        verification_token = secrets.token_urlsafe(32)
        user_data["verified"] = True
        user_data["verification_token"] = verification_token
        exp_str = (now + timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute(
            "UPDATE email_verifications SET user_data = ?, expires_at = ?, attempts = 0 WHERE id = ?",
            (json.dumps(user_data), exp_str, record["id"])
        )
        conn.commit()

        return {
            "success": True,
            "verified": True,
            "requires_password": True,
            "verification_token": verification_token,
            "email": clean_email,
            "name": name,
            "grade": grade,
            "message": "Gmail ownership verified successfully! Please set your AI Maths Tutor password."
        }
    finally:
        conn.close()


@app.post("/api/register/complete")
def register_complete(req: CompleteRegistrationRequest):
    """
    Step 3 of Registration:
    Sets student's AI Maths Tutor password after verified Gmail ownership.
    Inserts verified student into users table and issues JWT session token.
    """
    clean_email = req.email.strip().lower()
    is_valid, reason = is_valid_gmail(clean_email)
    if not is_valid:
        raise HTTPException(status_code=400, detail=reason)

    if not req.verification_token or not req.verification_token.strip():
        raise HTTPException(status_code=400, detail="Missing verification token.")

    clean_pwd = req.password.strip()
    if len(clean_pwd) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters long.")

    if req.confirm_password is not None and clean_pwd != req.confirm_password.strip():
        raise HTTPException(status_code=400, detail="Password and Confirm Password do not match.")

    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Check active verification session
        cursor.execute("""
            SELECT id, user_data, expires_at
            FROM email_verifications
            WHERE LOWER(email) = LOWER(?)
            ORDER BY id DESC LIMIT 1
        """, (clean_email,))
        record = cursor.fetchone()

        if not record:
            raise HTTPException(status_code=400, detail="No active verification session found. Please verify your Gmail first.")

        now = datetime.now(timezone.utc)
        expires_dt = parse_dt_safe(record["expires_at"])
        if now > expires_dt:
            cursor.execute("DELETE FROM email_verifications WHERE id = ?", (record["id"],))
            conn.commit()
            raise HTTPException(status_code=400, detail="Verification session has expired. Please verify your Gmail again.")

        user_data = json.loads(record["user_data"])
        if not user_data.get("verified") or user_data.get("verification_token") != req.verification_token.strip():
            raise HTTPException(status_code=400, detail="Invalid verification token. Please verify your Gmail again.")

        # Duplicate check against verified accounts
        cursor.execute("SELECT id, is_verified FROM users WHERE LOWER(email) = LOWER(?)", (clean_email,))
        existing = cursor.fetchone()
        if existing and row_val(existing, "is_verified", 1) == 1:
            raise HTTPException(status_code=400, detail="This Gmail address is already registered and verified. Please log in.")

        name = user_data.get("name", "Student")
        grade = user_data.get("grade", "Class 10")
        hashed_pwd = hash_password(clean_pwd)

        cursor.execute("DELETE FROM users WHERE LOWER(email) = LOWER(?) AND is_verified = 0", (clean_email,))

        if existing:
            cursor.execute(
                "UPDATE users SET name = ?, password = ?, grade = ?, is_verified = 1 WHERE id = ?",
                (name, hashed_pwd, grade, existing["id"])
            )
            user_id = existing["id"]
        else:
            cursor.execute(
                "INSERT INTO users (name, email, password, grade, role, is_verified) VALUES (?, ?, ?, ?, 'student', 1)",
                (name, clean_email, hashed_pwd, grade)
            )
            user_id = cursor.lastrowid

        # Clean verification session
        cursor.execute("DELETE FROM email_verifications WHERE id = ?", (record["id"],))
        conn.commit()

        token = create_access_token({"user_id": user_id, "email": clean_email, "role": "student"})
        return {
            "success": True,
            "message": "AI Maths Tutor account created successfully!",
            "token": token,
            "user_id": user_id,
            "name": name,
            "email": clean_email,
            "grade": grade
        }
    finally:
        conn.close()


@app.post("/api/register/resend-otp")
def register_resend_otp(req: ResendOtpRequest):
    """
    Resends OTP with a strict 60-second cooldown and a maximum of 5 resends.
    """
    clean_email = req.email.strip().lower()
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT id, user_data, resend_count, last_sent_at
            FROM email_verifications
            WHERE LOWER(email) = LOWER(?)
            ORDER BY id DESC LIMIT 1
        """, (clean_email,))
        record = cursor.fetchone()

        if not record:
            raise HTTPException(status_code=400, detail="No active registration session found for this email. Please register first.")

        now = datetime.now(timezone.utc)
        last_sent = parse_dt_safe(record["last_sent_at"])
        elapsed = (now - last_sent).total_seconds()

        if elapsed < 60:
            remaining = int(60 - elapsed)
            raise HTTPException(status_code=429, detail=f"Please wait {remaining} seconds before requesting a new code.")

        resend_count = record["resend_count"] or 0
        if resend_count >= 5:
            raise HTTPException(status_code=400, detail="Maximum resend limit reached. Please restart registration.")

        otp = generate_secure_otp()
        salt = secrets.token_hex(16)
        otp_hash = hash_otp(otp, salt)

        now_str = now.strftime("%Y-%m-%d %H:%M:%S")
        exp_str = (now + timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
            UPDATE email_verifications
            SET otp_hash = ?, salt = ?, attempts = 0, resend_count = resend_count + 1, last_sent_at = ?, expires_at = ?
            WHERE id = ?
        """, (otp_hash, salt, now_str, exp_str, record["id"]))
        conn.commit()

        user_data = json.loads(record["user_data"])
        sent, send_msg = send_otp_email(clean_email, otp, recipient_name=user_data.get("name", "Student"))
        if not sent:
            raise HTTPException(
                status_code=500,
                detail=send_msg if "unavailable" in send_msg.lower() else "Failed to send verification email. Please try again later."
            )

        return {
            "success": True,
            "message": "A new verification code has been sent to your email.",
            "cooldown_seconds": 60
        }
    finally:
        conn.close()


# Fallback / Direct Programmatic Registration (Blocked to prevent OTP bypass)
@app.post("/api/register")
def register(req: RegisterRequest):
    raise HTTPException(
        status_code=400,
        detail="Direct registration is disabled. You must verify ownership of your Gmail address via 6-digit OTP."
    )

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "").strip()
_GOOGLE_JWKS_URL = "https://www.googleapis.com/oauth2/v3/certs"
_google_jwk_client = None


def get_google_jwk_client():
    global _google_jwk_client
    if _google_jwk_client is None:
        _google_jwk_client = jwt.PyJWKClient(_GOOGLE_JWKS_URL)
    return _google_jwk_client


def verify_google_id_token(token: str, client_id: str) -> dict:
    """
    Cryptographically verifies Google ID Token (JWT) against Google's public JWKS certificates.
    Enforces signature, expiration, issuer, audience, and email_verified=true.
    """
    if not token or not token.strip():
        raise HTTPException(status_code=400, detail="Google credential token is required.")

    effective_client_id = client_id.strip() if client_id else os.getenv("GOOGLE_CLIENT_ID", "").strip()
    if not effective_client_id:
        if IS_PRODUCTION:
            raise HTTPException(
                status_code=500,
                detail="Google authentication is not configured in production (missing GOOGLE_CLIENT_ID)."
            )
        raise HTTPException(
            status_code=500,
            detail="Google authentication is not configured (missing GOOGLE_CLIENT_ID)."
        )

    try:
        jwks_client = get_google_jwk_client()
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=effective_client_id,
            issuer=["https://accounts.google.com", "accounts.google.com"],
            options={
                "verify_signature": True,
                "verify_aud": True,
                "verify_iss": True,
                "verify_exp": True
            }
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Google credential token has expired. Please sign in again.")
    except jwt.InvalidAudienceError:
        raise HTTPException(status_code=401, detail="Google credential audience does not match this application.")
    except jwt.InvalidIssuerError:
        raise HTTPException(status_code=401, detail="Google credential issuer is invalid.")
    except (jwt.InvalidSignatureError, jwt.DecodeError):
        raise HTTPException(status_code=401, detail="Google credential token signature is invalid or forged.")
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=401, detail=f"Google credential token verification failed: {type(e).__name__}")
    except Exception as e:
        print(f"[Google Auth Error] JWKS resolution failed: {type(e).__name__}")
        raise HTTPException(status_code=500, detail="Unable to verify Google credentials at this time.")

    # Enforce verified email
    email_verified = payload.get("email_verified")
    if email_verified is not True and str(email_verified).lower() != "true":
        raise HTTPException(status_code=400, detail="Google account email is not verified by Google.")

    email = payload.get("email")
    if not email or not isinstance(email, str) or not email.strip():
        raise HTTPException(status_code=400, detail="Google token does not contain a valid email address.")

    return payload


class GoogleAuthRequest(BaseModel):
    credential: str  # Mandatory Google ID token (JWT)


@app.post("/api/auth/google")
def google_auth(req: GoogleAuthRequest):
    """
    Authenticates Google OAuth user using cryptographically verified ID tokens.
    Untrusted client overrides are strictly rejected.
    """
    if not req.credential or not req.credential.strip():
        raise HTTPException(status_code=400, detail="Google credential token is required.")

    # Cryptographically verify the Google ID token
    google_payload = verify_google_id_token(req.credential.strip(), GOOGLE_CLIENT_ID)

    email = google_payload["email"].strip().lower()
    name = google_payload.get("name") or email.split("@")[0].capitalize()

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, name, email, grade, role, is_verified FROM users WHERE LOWER(email) = LOWER(?)", (email,))
        user = cursor.fetchone()
        if user:
            user_id = user["id"]
            user_name = user["name"]
            user_grade = user["grade"]
            user_role = user["role"] if "role" in user.keys() else "student"
            # If account existed but was pending email verification, mark verified via trusted Google SSO
            if row_val(user, "is_verified", 1) == 0:
                cursor.execute("UPDATE users SET is_verified = 1 WHERE id = ?", (user_id,))
                conn.commit()
        else:
            user_name = name
            user_grade = "Class 10"
            user_role = "developer" if email == "dev@mathstutor.com" else "student"
            random_pwd_hash = hash_password(secrets.token_urlsafe(32))
            cursor.execute(
                "INSERT INTO users (name, email, password, grade, role, is_verified) VALUES (?, ?, ?, ?, ?, 1)",
                (user_name, email, random_pwd_hash, user_grade, user_role)
            )
            conn.commit()
            user_id = cursor.lastrowid

        token = create_access_token({"user_id": user_id, "email": email, "role": user_role})
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

# 3. Student / Developer Login API (Verified with Bcrypt + JWT + Verification Check)
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
        SELECT id, name, email, password, grade, role, is_verified
        FROM users 
        WHERE LOWER(email) = LOWER(?) OR LOWER(name) = LOWER(?)
    """, (req.email.strip(), req.email.strip()))
    user = cursor.fetchone()
    
    if not user or not verify_password(req.password, user["password"]):
        conn.close()
        raise HTTPException(status_code=401, detail="Invalid email/username or password")

    # Guard: Unverified accounts cannot log in
    if row_val(user, "is_verified", 1) == 0:
        conn.close()
        raise HTTPException(status_code=403, detail="Email is not verified. Please complete email verification before logging in.")

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


@app.get("/api/admin/analytics")
def get_admin_analytics():
    """Returns aggregated stats, student directory, class breakdowns, and recent student questions for the Admin Dashboard"""
    conn = get_connection()
    cursor = conn.cursor()
    total_students = 0
    total_questions = 0
    total_visuals = 0
    grade_dist = []
    lang_dist = []
    students = []
    recent_questions = []

    # 1. Total Registered Students
    try:
        cursor.execute("SELECT COUNT(*) as cnt FROM users WHERE role != 'developer' AND role != 'admin'")
        row = cursor.fetchone()
        total_students = (row["cnt"] if isinstance(row, dict) else row[0]) if row else 0
    except Exception as e:
        print(f"[Analytics Notice: students] {e}")

    # 2. Total Questions Asked by students
    try:
        cursor.execute("SELECT COUNT(*) as cnt FROM messages WHERE sender NOT IN ('ai', 'tutor', 'assistant')")
        row = cursor.fetchone()
        total_questions = (row["cnt"] if isinstance(row, dict) else row[0]) if row else 0
    except Exception as e:
        print(f"[Analytics Notice: questions] {e}")

    # 3. Total Visuals / Diagrams Generated
    try:
        cursor.execute("SELECT COUNT(*) as cnt FROM messages WHERE image_url IS NOT NULL AND image_url != ''")
        row = cursor.fetchone()
        total_visuals = (row["cnt"] if isinstance(row, dict) else row[0]) if row else 0
    except Exception as e:
        print(f"[Analytics Notice: visuals] {e}")

    # 4. Grade / Class Distribution
    try:
        cursor.execute("SELECT grade, COUNT(*) as cnt FROM users WHERE role != 'developer' AND role != 'admin' GROUP BY grade")
        grade_rows = cursor.fetchall() or []
        for r in grade_rows:
            g = r["grade"] if isinstance(r, dict) else r[0]
            c = r["cnt"] if isinstance(r, dict) else r[1]
            if g:
                grade_dist.append({"grade": str(g), "count": int(c)})
    except Exception as e:
        print(f"[Analytics Notice: grades] {e}")

    # 5. Teaching Styles & Modes Distribution
    try:
        cursor.execute("SELECT style, COUNT(*) as cnt FROM messages WHERE style IS NOT NULL AND style != '' GROUP BY style")
        style_rows = cursor.fetchall() or []
        for r in style_rows:
            s_name = r["style"] if isinstance(r, dict) else r[0]
            c = r["cnt"] if isinstance(r, dict) else r[1]
            if s_name:
                lang_dist.append({"language": str(s_name).capitalize(), "count": int(c)})
    except Exception as e:
        print(f"[Analytics Notice: styles] {e}")

    if not lang_dist:
        lang_dist = [{"language": "Hinglish (Sports Mode)", "count": total_questions or 1}]

    # 6. Student Directory (All registered students with question counts)
    try:
        cursor.execute("""
            SELECT u.id, u.name, u.email, u.grade, u.created_at,
                   (SELECT COUNT(*) FROM messages m JOIN chats c ON m.chat_id = c.id WHERE c.user_id = u.id AND m.sender NOT IN ('ai', 'tutor', 'assistant')) as questions_count
            FROM users u
            WHERE u.role != 'developer' AND u.role != 'admin'
            ORDER BY u.id DESC LIMIT 100
        """)
        user_rows = cursor.fetchall() or []
        for u in user_rows:
            if isinstance(u, dict):
                students.append({
                    "id": u.get("id"),
                    "name": u.get("name") or "Student",
                    "email": u.get("email") or "N/A",
                    "grade": u.get("grade") or "Class 10",
                    "created_at": str(u.get("created_at") or ""),
                    "questions_count": int(u.get("questions_count") or 0)
                })
            else:
                students.append({
                    "id": u[0],
                    "name": u[1] or "Student",
                    "email": u[2] or "N/A",
                    "grade": u[3] or "Class 10",
                    "created_at": str(u[4] or ""),
                    "questions_count": int(u[5] or 0)
                })
    except Exception as e:
        print(f"[Analytics Notice: student directory] {e}")
        try:
            # Simple fallback if subquery fails
            cursor.execute("SELECT id, name, email, grade, created_at FROM users WHERE role != 'developer' AND role != 'admin' ORDER BY id DESC LIMIT 50")
            for u in cursor.fetchall() or []:
                students.append({
                    "id": u["id"] if isinstance(u, dict) else u[0],
                    "name": (u["name"] if isinstance(u, dict) else u[1]) or "Student",
                    "email": (u["email"] if isinstance(u, dict) else u[2]) or "N/A",
                    "grade": (u["grade"] if isinstance(u, dict) else u[3]) or "Class 10",
                    "created_at": str(u["created_at"] if isinstance(u, dict) else u[4] or ""),
                    "questions_count": 0
                })
        except Exception:
            pass

    # 7. Recent Student Questions (Latest 25)
    try:
        cursor.execute("""
            SELECT m.id, m.text, m.created_at, m.style, u.name as student_name, u.grade
            FROM messages m
            LEFT JOIN chats c ON m.chat_id = c.id
            LEFT JOIN users u ON c.user_id = u.id
            WHERE m.sender NOT IN ('ai', 'tutor', 'assistant')
            ORDER BY m.id DESC LIMIT 25
        """)
        q_rows = cursor.fetchall() or []
        for q in q_rows:
            if isinstance(q, dict):
                recent_questions.append({
                    "id": q.get("id"),
                    "question": q.get("text") or "",
                    "timestamp": str(q.get("created_at") or ""),
                    "type": q.get("style") or "General",
                    "student_name": q.get("student_name") or "Student",
                    "grade": q.get("grade") or "Class 10"
                })
            else:
                recent_questions.append({
                    "id": q[0],
                    "question": q[1] or "",
                    "timestamp": str(q[2] or ""),
                    "type": q[3] or "General",
                    "student_name": q[4] or "Student",
                    "grade": q[5] or "Class 10"
                })
    except Exception as e:
        print(f"[Analytics Notice: questions log] {e}")

    conn.close()

    return {
        "success": True,
        "total_students": total_students,
        "total_questions": total_questions,
        "total_visuals": total_visuals,
        "grade_distribution": grade_dist,
        "language_distribution": lang_dist,
        "students": students,
        "recent_questions": recent_questions
    }



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
            "viualoze", "visualoze", "visulize", "visulaize", "visulise",
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
