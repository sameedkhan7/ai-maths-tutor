import os
import smtplib
import secrets
import hashlib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Tuple

# Environment Detection
def is_production_env() -> bool:
    raw_env = os.getenv("ENVIRONMENT", "").strip().lower()
    if raw_env:
        return raw_env in ("production", "prod")
    # On Render: strict production applies if SMTP is configured or REQUIRE_SMTP is enabled
    if bool(os.getenv("RENDER")):
        if os.getenv("REQUIRE_SMTP", "").lower() in ("true", "1", "yes"):
            return True
        return is_smtp_configured()
    return False


def is_smtp_configured() -> bool:
    """Checks whether valid SMTP host, user, and password are configured"""
    host = os.getenv("SMTP_HOST", "").strip()
    user = os.getenv("SMTP_USER", "").strip()
    pwd = os.getenv("SMTP_PASSWORD", "").strip()
    return bool(host and user and pwd)


def get_mock_email_mode() -> bool:
    """
    Determines if Mock Mode is active.
    STRICT SECURITY RULE: Mock Mode is NEVER automatically allowed in production.
    """
    if is_production_env():
        return False
    # In development or testing: explicit env setting OR fallback when SMTP is unconfigured
    explicit = os.getenv("MOCK_EMAIL_MODE", "").lower() in ("true", "1", "yes")
    return explicit or not is_smtp_configured()


def validate_production_smtp_config():
    """
    Validates SMTP configuration for production environments.
    Fails startup with RuntimeError if required credentials are missing.
    """
    if is_production_env() and not is_smtp_configured():
        raise RuntimeError(
            "FATAL CONFIGURATION ERROR: In production environment, real email delivery is required. "
            "SMTP_HOST, SMTP_USER, and SMTP_PASSWORD must be configured via environment variables. "
            "Automatic Mock Mode is strictly forbidden in production."
        )


# In-memory storage for test/debug retrieval when running automated unit tests
_LAST_DISPATCHED_OTP = {}


def generate_secure_otp() -> str:
    """Generates a cryptographically secure 6-digit numeric OTP (100000 - 999999)"""
    return str(secrets.randbelow(900000) + 100000)


def hash_otp(otp: str, salt: str) -> str:
    """Hashes OTP with a secret salt using SHA-256 (Never stores OTP in plaintext)"""
    return hashlib.sha256(f"{otp}:{salt}".encode("utf-8")).hexdigest()


def verify_otp_hash(otp: str, salt: str, expected_hash: str) -> bool:
    """Verifies user-entered OTP against the stored cryptographic hash"""
    computed = hash_otp(otp.strip(), salt)
    return secrets.compare_digest(computed, expected_hash)


def get_otp_html_template(otp: str, recipient_name: str = "Student") -> str:
    """Returns a responsive HTML email template for the OTP code"""
    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Your AI Maths Tutor Verification Code</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; margin: 0; padding: 24px; color: #1e293b;">
  <table width="100%" border="0" cellspacing="0" cellpadding="0">
    <tr>
      <td align="center">
        <table width="100%" max-width="500" style="max-width: 500px; background-color: #ffffff; border-radius: 16px; border: 1px solid #e2e8f0; padding: 36px 32px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);">
          <tr>
            <td align="center">
              <div style="width: 56px; height: 56px; background-color: #e0e7ff; border-radius: 14px; display: inline-flex; align-items: center; justify-content: center; font-size: 28px; font-weight: bold; color: #4f46e5; line-height: 56px;">∑</div>
              <h2 style="margin: 16px 0 6px 0; font-size: 22px; color: #0f172a;">Verify Your Email Address</h2>
              <p style="margin: 0 0 24px 0; font-size: 14px; color: #64748b;">Welcome to AI Maths Tutor! Use this code to complete your registration:</p>

              <div style="background-color: #f1f5f9; border: 2px dashed #cbd5e1; border-radius: 12px; padding: 18px 24px; display: inline-block; margin-bottom: 24px;">
                <span style="font-family: 'Courier New', Courier, monospace; font-size: 36px; font-weight: 800; letter-spacing: 8px; color: #4f46e5;">{otp}</span>
              </div>

              <p style="margin: 0 0 12px 0; font-size: 13px; color: #64748b;">
                ⏰ This code will expire in <strong>5 minutes</strong>.<br>
                If you did not request this verification, please safely ignore this email.
              </p>

              <hr style="border: none; border-top: 1px solid #f1f5f9; margin: 24px 0 16px 0;">

              <p style="margin: 0; font-size: 11.5px; color: #94a3b8; text-align: center;">
                AI Maths Tutor · Empowering students with NCERT Mathematics & Physics
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def send_otp_email(recipient_email: str, otp: str, recipient_name: str = "Student") -> Tuple[bool, str]:
    """
    Sends the OTP verification email using configured SMTP provider.
    In development or mock mode, records the OTP securely for automated tests without failing.
    In production, strictly requires valid SMTP configuration and never logs raw OTP.
    """
    clean_email = recipient_email.strip().lower()
    is_prod = is_production_env()

    # Guard: Production requires live SMTP configuration; automatic mock mode is forbidden
    if is_prod and not is_smtp_configured():
        return False, "Email verification service is currently unavailable. Please contact support."

    # In development/test mode when Mock Mode is active
    if get_mock_email_mode():
        _LAST_DISPATCHED_OTP[clean_email] = otp
        print(f"[Email Service Notice] Mock/Demo mode active: OTP generated for {clean_email} -> {otp} (Length: {len(otp)})")
        return True, "Verification code generated (Mock/Local mode active)."

    # Load dynamic SMTP settings from environment
    smtp_host = os.getenv("SMTP_HOST", "").strip()
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "").strip()
    smtp_password = os.getenv("SMTP_PASSWORD", "").strip()
    smtp_from_email = os.getenv("SMTP_FROM_EMAIL", "").strip() or smtp_user
    smtp_from_name = os.getenv("SMTP_FROM_NAME", "AI Maths Tutor").strip()
    smtp_use_tls = os.getenv("SMTP_USE_TLS", "true").lower() in ("true", "1", "yes")

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"{otp} is your AI Maths Tutor verification code"
        msg["From"] = f"{smtp_from_name} <{smtp_from_email}>"
        msg["To"] = clean_email

        text_content = f"Your AI Maths Tutor verification code is: {otp}\nThis code will expire in 5 minutes."
        html_content = get_otp_html_template(otp, recipient_name)

        msg.attach(MIMEText(text_content, "plain"))
        msg.attach(MIMEText(html_content, "html"))

        if smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=10) as server:
                server.login(smtp_user, smtp_password)
                server.sendmail(smtp_from_email, [clean_email], msg.as_string())
        else:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
                if smtp_use_tls:
                    server.starttls()
                server.login(smtp_user, smtp_password)
                server.sendmail(smtp_from_email, [clean_email], msg.as_string())

        return True, "Verification code sent to your email."

    except smtplib.SMTPAuthenticationError:
        print("[Email Service Error] SMTP Authentication failed: Invalid SMTP credentials.")
        return False, "Failed to authenticate with email delivery server."
    except smtplib.SMTPException as e:
        print(f"[Email Service Error] SMTP delivery failure: {type(e).__name__}")
        return False, "Failed to deliver email through SMTP service."
    except Exception as e:
        print(f"[Email Service Error] Email delivery exception: {type(e).__name__}")
        return False, "Email verification service encountered an unexpected error."
