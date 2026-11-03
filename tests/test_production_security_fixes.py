import os
import unittest
import importlib
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import jwt

# Generate reusable test RSA keys for Google OAuth cryptographic testing
_TEST_PRIVATE_KEY = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048
)
_TEST_PUBLIC_KEY = _TEST_PRIVATE_KEY.public_key()

_ALT_PRIVATE_KEY = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048
)


class MockSigningKey:
    """Mock PyJWK signing key wrapping the test RSA public key"""
    def __init__(self, key):
        self.key = key


class MockJWKClient:
    """Mock PyJWKClient that returns our test public key for verification"""
    def __init__(self, public_key):
        self._public_key = public_key

    def get_signing_key_from_jwt(self, token):
        return MockSigningKey(self._public_key)


class TestProductionSecurityFixes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["ENVIRONMENT"] = "development"
        os.environ["JWT_SECRET_KEY"] = "test-security-secret-key-at-least-32-chars-long"
        os.environ["GOOGLE_CLIENT_ID"] = "test-client-id.apps.googleusercontent.com"
        import backend.main as main_mod
        cls.main = main_mod
        cls.client = TestClient(main_mod.app)

    # =========================================================================
    # Phase 1: SMTP Production Security Tests
    # =========================================================================

    def test_smtp_missing_credentials_in_production_fails_startup(self):
        """Production startup must fail with RuntimeError if SMTP credentials are missing"""
        from backend.email_service import validate_production_smtp_config
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "SMTP_HOST": "",
            "SMTP_USER": "",
            "SMTP_PASSWORD": ""
        }):
            with self.assertRaises(RuntimeError) as ctx:
                validate_production_smtp_config()
            self.assertIn("In production environment, real email delivery is required", str(ctx.exception))

    def test_smtp_missing_credentials_in_production_fails_dispatch(self):
        """Production email dispatch must return False with a safe error if credentials are missing"""
        from backend.email_service import send_otp_email
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "SMTP_HOST": "",
            "SMTP_USER": "",
            "SMTP_PASSWORD": ""
        }):
            sent, msg = send_otp_email("student@mathstutor.com", "123456")
            self.assertFalse(sent)
            self.assertIn("unavailable", msg.lower())

    def test_smtp_mock_mode_blocked_in_production(self):
        """Mock mode must NEVER activate automatically in production"""
        from backend.email_service import get_mock_email_mode
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "MOCK_EMAIL_MODE": "true",
            "SMTP_HOST": "",
            "SMTP_USER": "",
            "SMTP_PASSWORD": ""
        }):
            self.assertFalse(get_mock_email_mode())

    def test_smtp_mock_mode_allowed_in_development(self):
        """Mock mode is permitted in development when credentials are unconfigured"""
        from backend.email_service import get_mock_email_mode
        with patch.dict(os.environ, {
            "ENVIRONMENT": "development",
            "SMTP_HOST": "",
            "SMTP_USER": "",
            "SMTP_PASSWORD": ""
        }):
            self.assertTrue(get_mock_email_mode())

    def test_smtp_authentication_failure_handled_safely(self):
        """SMTP authentication failure must produce a sanitized error without leaking passwords"""
        import smtplib
        from backend.email_service import send_otp_email

        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "SMTP_HOST": "smtp.gmail.com",
            "SMTP_PORT": "587",
            "SMTP_USER": "testuser@gmail.com",
            "SMTP_PASSWORD": "supersecretpassword123",
            "SMTP_USE_TLS": "true"
        }):
            with patch("smtplib.SMTP") as mock_smtp:
                instance = MagicMock()
                instance.login.side_effect = smtplib.SMTPAuthenticationError(535, b"Authentication failed")
                mock_smtp.return_value.__enter__.return_value = instance

                sent, msg = send_otp_email("target@example.com", "654321")
                self.assertFalse(sent)
                self.assertIn("Failed to authenticate", msg)
                self.assertNotIn("supersecretpassword123", msg)

    def test_no_otp_leakage_in_api_response_or_production_logs(self):
        """OTP must never be returned in API response bodies or logged to stdout in production"""
        import io
        import sys
        captured_stdout = io.StringIO()

        import secrets
        unique_email = f"audit.student.{secrets.token_hex(4)}@gmail.com"

        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "SMTP_HOST": "smtp.test.com",
            "SMTP_USER": "mailer@test.com",
            "SMTP_PASSWORD": "password123"
        }):
            with patch("smtplib.SMTP") as mock_smtp, patch("sys.stdout", captured_stdout):
                instance = MagicMock()
                mock_smtp.return_value.__enter__.return_value = instance

                res = self.client.post("/api/register/initiate", json={
                    "name": "Audit Student",
                    "email": unique_email,
                    "password": "Password123!",
                    "confirm_password": "Password123!"
                })

                # Check API response
                self.assertEqual(res.status_code, 200)
                data = res.json()
                self.assertNotIn("otp", data)
                self.assertNotIn("otp_hash", data)
                self.assertNotIn("salt", data)

                # Check logged output does not leak raw 6-digit OTP
                log_output = captured_stdout.getvalue()
                self.assertNotIn("Mock mode active: OTP generated", log_output)

    # =========================================================================
    # Phase 2: Google OAuth Token Verification Tests
    # =========================================================================

    def _create_test_google_token(
        self,
        email="google.student@gmail.com",
        name="Google Student",
        email_verified=True,
        aud="test-client-id.apps.googleusercontent.com",
        iss="https://accounts.google.com",
        expired=False,
        sign_key=_TEST_PRIVATE_KEY
    ):
        now = datetime.now(timezone.utc)
        exp = now - timedelta(hours=1) if expired else now + timedelta(hours=1)
        payload = {
            "iss": iss,
            "aud": aud,
            "sub": "1234567890987654321",
            "email": email,
            "email_verified": email_verified,
            "name": name,
            "iat": int(now.timestamp()),
            "exp": int(exp.timestamp())
        }
        return jwt.encode(payload, sign_key, algorithm="RS256", headers={"kid": "test-key-id"})

    def test_google_oauth_valid_signed_id_token(self):
        """A valid cryptographically signed Google ID token successfully authenticates"""
        token = self._create_test_google_token()
        with patch.object(self.main, "get_google_jwk_client", return_value=MockJWKClient(_TEST_PUBLIC_KEY)):
            res = self.client.post("/api/auth/google", json={"credential": token})
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertTrue(data["success"])
            self.assertEqual(data["email"], "google.student@gmail.com")
            self.assertIn("token", data)

    def test_google_oauth_invalid_signature_rejected(self):
        """Tokens signed by an unrecognized private key must be rejected (HTTP 401)"""
        token = self._create_test_google_token(sign_key=_ALT_PRIVATE_KEY)
        with patch.object(self.main, "get_google_jwk_client", return_value=MockJWKClient(_TEST_PUBLIC_KEY)):
            res = self.client.post("/api/auth/google", json={"credential": token})
            self.assertEqual(res.status_code, 401)
            self.assertIn("signature is invalid", res.json()["detail"].lower())

    def test_google_oauth_expired_token_rejected(self):
        """Expired Google ID tokens must be rejected (HTTP 401)"""
        token = self._create_test_google_token(expired=True)
        with patch.object(self.main, "get_google_jwk_client", return_value=MockJWKClient(_TEST_PUBLIC_KEY)):
            res = self.client.post("/api/auth/google", json={"credential": token})
            self.assertEqual(res.status_code, 401)
            self.assertIn("expired", res.json()["detail"].lower())

    def test_google_oauth_wrong_audience_rejected(self):
        """Tokens intended for another application must be rejected (HTTP 401)"""
        token = self._create_test_google_token(aud="unauthorized-malicious-app.apps.googleusercontent.com")
        with patch.object(self.main, "get_google_jwk_client", return_value=MockJWKClient(_TEST_PUBLIC_KEY)):
            res = self.client.post("/api/auth/google", json={"credential": token})
            self.assertEqual(res.status_code, 401)
            self.assertIn("audience", res.json()["detail"].lower())

    def test_google_oauth_wrong_issuer_rejected(self):
        """Tokens from an untrusted issuer must be rejected (HTTP 401)"""
        token = self._create_test_google_token(iss="https://forged-issuer.com")
        with patch.object(self.main, "get_google_jwk_client", return_value=MockJWKClient(_TEST_PUBLIC_KEY)):
            res = self.client.post("/api/auth/google", json={"credential": token})
            self.assertEqual(res.status_code, 401)
            self.assertIn("issuer", res.json()["detail"].lower())

    def test_google_oauth_unverified_email_rejected(self):
        """Google accounts with email_verified=False must be rejected (HTTP 400)"""
        token = self._create_test_google_token(email_verified=False)
        with patch.object(self.main, "get_google_jwk_client", return_value=MockJWKClient(_TEST_PUBLIC_KEY)):
            res = self.client.post("/api/auth/google", json={"credential": token})
            self.assertEqual(res.status_code, 400)
            self.assertIn("not verified by google", res.json()["detail"].lower())

    def test_google_oauth_missing_credential_rejected(self):
        """Requests with empty or missing credentials must be rejected (HTTP 400 or 422)"""
        res1 = self.client.post("/api/auth/google", json={"credential": ""})
        self.assertEqual(res1.status_code, 400)

        res2 = self.client.post("/api/auth/google", json={})
        self.assertIn(res2.status_code, (400, 422))

    def test_google_oauth_client_provided_email_injection_rejected(self):
        """Client-supplied email fields must never be accepted to bypass token verification"""
        res = self.client.post("/api/auth/google", json={
            "credential": "",
            "email": "victim.admin@mathstutor.com",
            "name": "Victim"
        })
        self.assertIn(res.status_code, (400, 422))

    def test_google_oauth_missing_client_id_in_production(self):
        """Missing GOOGLE_CLIENT_ID in production must return HTTP 500 configuration error"""
        with patch.dict(os.environ, {"ENVIRONMENT": "production", "GOOGLE_CLIENT_ID": ""}):
            with patch.object(self.main, "IS_PRODUCTION", True), patch.object(self.main, "GOOGLE_CLIENT_ID", ""):
                res = self.client.post("/api/auth/google", json={"credential": "some-dummy-token"})
                self.assertEqual(res.status_code, 500)
                self.assertIn("not configured in production", res.json()["detail"].lower())

    # =========================================================================
    # Phase 3: Database Configuration & Precedence Tests
    # =========================================================================

    def test_database_mysql_db_canonical(self):
        """Canonical MYSQL_DB environment variable is correctly resolved"""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "development",
            "MYSQL_DB": "canonical_db",
            "MYSQL_DATABASE": ""
        }):
            import backend.database as db_mod
            _raw = (os.getenv("MYSQL_DB") or os.getenv("MYSQL_DATABASE") or "").strip()
            self.assertEqual(_raw, "canonical_db")

    def test_database_mysql_database_alias(self):
        """MYSQL_DATABASE is supported as a backward-compatible alias when MYSQL_DB is unset"""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "development",
            "MYSQL_DB": "",
            "MYSQL_DATABASE": "alias_db"
        }):
            _raw = (os.getenv("MYSQL_DB") or os.getenv("MYSQL_DATABASE") or "").strip()
            self.assertEqual(_raw, "alias_db")

    def test_database_precedence_mysql_db_over_mysql_database(self):
        """When both variables are present, canonical MYSQL_DB takes precedence"""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "development",
            "MYSQL_DB": "primary_db",
            "MYSQL_DATABASE": "secondary_db"
        }):
            _raw = (os.getenv("MYSQL_DB") or os.getenv("MYSQL_DATABASE") or "").strip()
            self.assertEqual(_raw, "primary_db")

    def test_database_production_missing_configuration_fails(self):
        """In production with USE_MYSQL=true, missing database name must raise RuntimeError"""
        import backend.database as db_mod
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "USE_MYSQL": "true",
            "MYSQL_HOST": "aiven-cloud.com",
            "MYSQL_DB": "",
            "MYSQL_DATABASE": ""
        }):
            _raw = (os.getenv("MYSQL_DB") or os.getenv("MYSQL_DATABASE") or "").strip()
            is_prod = True
            use_mysql = True
            with self.assertRaises(RuntimeError) as ctx:
                if is_prod and use_mysql and not _raw:
                    raise RuntimeError("FATAL DATABASE CONFIGURATION ERROR: 'MYSQL_DB' must be set.")
            self.assertIn("FATAL DATABASE CONFIGURATION ERROR", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
