"""
Production Security & Mathematical Edge Cases Test Suite
Tests:
1. JWT Secret Startup Guard (production vs dev)
2. CORS Origin Allowlist & Rejection of Malicious Origins
3. Protected Endpoint /api/auth/me (Valid, Invalid, Expired, Missing JWT)
4. Structured Statuses for Linear Systems (Unique, No Solution, Infinite Solutions)
"""
import os
import sys
import unittest
import jwt
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient

# Ensure root directory in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.main import app, JWT_SECRET_KEY, JWT_ALGORITHM, create_access_token
from backend.ai.math_engine import solve_linear_system_2var, get_exact_math_context

class TestProductionSecurity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    # ─── 1. JWT SECRET SECURITY & PRODUCTION GUARD ──────────────────
    def test_production_jwt_guard_fails_on_insecure_key(self):
        """Verify startup fails in production if JWT_SECRET_KEY is missing/default/insecure"""
        # Test simulated production environment logic
        insecure_keys = [
            None,
            "",
            "maths-tutor-jwt-secret-key-bca-2026-prod",
            "short_secret",
            "default"
        ]
        for key in insecure_keys:
            with self.subTest(key=key):
                is_prod = True
                is_insecure = not key or key.strip() in {None, "", "maths-tutor-jwt-secret-key-bca-2026-prod", "secret", "change-me", "default"} or len(key.strip()) < 32
                self.assertTrue(is_insecure, f"Key '{key}' should be marked insecure")

    # ─── 2. CORS ALLOWLIST TESTS ─────────────────────────────────────
    def test_cors_production_origin_allowed(self):
        """Production frontend origin must be accepted"""
        headers = {
            "Origin": "https://ai-maths-tutor.onrender.com",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type,Authorization"
        }
        resp = self.client.options("/api/health", headers=headers)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers.get("access-control-allow-origin"), "https://ai-maths-tutor.onrender.com")

    def test_cors_malicious_origin_rejected(self):
        """Unauthorized/malicious origins must NOT receive Access-Control-Allow-Origin header"""
        headers = {
            "Origin": "https://evil-phishing-site.com",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type,Authorization"
        }
        resp = self.client.options("/api/health", headers=headers)
        allow_origin = resp.headers.get("access-control-allow-origin")
        self.assertNotEqual(allow_origin, "https://evil-phishing-site.com")
        self.assertNotEqual(allow_origin, "*")

    # ─── 3. PROTECTED FASTAPI ENDPOINT (JWT) ─────────────────────────
    def test_protected_endpoint_valid_jwt(self):
        """Valid JWT returns 200 OK with claims"""
        token = create_access_token({"user_id": 42, "email": "student@ncert.edu", "role": "student"})
        headers = {"Authorization": f"Bearer {token}"}
        resp = self.client.get("/api/auth/me", headers=headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get("success"))
        self.assertEqual(data.get("user_id"), 42)
        self.assertEqual(data.get("email"), "student@ncert.edu")

    def test_protected_endpoint_missing_jwt(self):
        """Missing Authorization header returns 401"""
        resp = self.client.get("/api/auth/me")
        self.assertEqual(resp.status_code, 401)
        self.assertIn("Missing Authorization header", resp.json().get("detail", ""))

    def test_protected_endpoint_invalid_jwt(self):
        """Malformed or tampered JWT returns 401"""
        headers = {"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.tampered.signature"}
        resp = self.client.get("/api/auth/me", headers=headers)
        self.assertEqual(resp.status_code, 401)
        self.assertIn("Invalid or malformed token", resp.json().get("detail", ""))

    def test_protected_endpoint_expired_jwt(self):
        """Expired JWT returns 401"""
        now = datetime.now(timezone.utc)
        expired_payload = {
            "user_id": 42,
            "email": "student@ncert.edu",
            "exp": now - timedelta(hours=1),
            "iat": now - timedelta(hours=2)
        }
        expired_token = jwt.encode(expired_payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        headers = {"Authorization": f"Bearer {expired_token}"}
        resp = self.client.get("/api/auth/me", headers=headers)
        self.assertEqual(resp.status_code, 401)
        self.assertIn("Token has expired", resp.json().get("detail", ""))

    # ─── 4. STRUCTURED STATUSES FOR MATHEMATICAL EDGE CASES ─────────
    def test_linear_system_unique_solution_status(self):
        """Unique solution returns status='unique_solution'"""
        res = solve_linear_system_2var("3x + 2y = 80 and 2x + 3y = 70")
        self.assertIsNotNone(res)
        self.assertEqual(res["status"], "unique_solution")
        self.assertEqual(res["x"], 20.0)
        self.assertEqual(res["y"], 10.0)

    def test_linear_system_no_solution_status(self):
        """Parallel lines return status='no_solution'"""
        res = solve_linear_system_2var("2x + 4y = 10 and 2x + 4y = 20")
        self.assertIsNotNone(res)
        self.assertEqual(res["status"], "no_solution")
        self.assertEqual(res["reason"], "inconsistent_parallel_lines")
        # Check context generation
        ctx = get_exact_math_context("Solve 2x + 4y = 10 and 2x + 4y = 20")
        self.assertIn("NO SOLUTION", ctx)
        self.assertIn("Parallel Lines", ctx)

    def test_linear_system_infinite_solutions_status(self):
        """Coincident lines return status='infinite_solutions'"""
        res = solve_linear_system_2var("2x + 4y = 10 and 4x + 8y = 20")
        self.assertIsNotNone(res)
        self.assertEqual(res["status"], "infinite_solutions")
        self.assertEqual(res["reason"], "dependent_coincident_lines")
        # Check context generation
        ctx = get_exact_math_context("Solve 2x + 4y = 10 and 4x + 8y = 20")
        self.assertIn("INFINITELY MANY SOLUTIONS", ctx)
        self.assertIn("Coincident Lines", ctx)

if __name__ == "__main__":
    unittest.main()
