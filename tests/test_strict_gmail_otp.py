"""
Automated Test Suite for Strict Gmail Ownership Verification & Password Show/Hide Functionality
Verifies:
1. Random Gmail address without OTP verification -> blocked from activation & login.
2. Correct Gmail with incorrect OTP -> blocked with error feedback and remaining attempts.
3. Correct Gmail with correct OTP & password completion -> registration successful, JWT issued.
4. Duplicate Gmail registration -> blocked.
5. Non-Gmail addresses (e.g. @yahoo.com, @outlook.com) -> blocked.
6. Direct programmatic registration bypass (/api/register) -> blocked with 400.
7. Password show/hide toggle functionality and attributes in register.html & login.html.
8. Existing users -> login working.
9. Google Sign-In -> working.
"""
import os
import sys
import json
import secrets
import unittest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.main import app, is_valid_gmail
from backend.database import get_connection, init_db
from backend.email_service import _LAST_DISPATCHED_OTP


class TestStrictGmailOtpVerification(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["GOOGLE_CLIENT_ID"] = "165303629004-0thk2v4o8vn0m6eh6ug0kq4hgbn05nhh.apps.googleusercontent.com"
        cls.client = TestClient(app)
        init_db()

    def setUp(self):
        self.test_gmail = f"student.{secrets.token_hex(4)}@gmail.com"
        self.test_pwd = "StudentSecurePass123!"
        self.test_name = "Ananya Sen"
        self.clean_up(self.test_gmail)

    def tearDown(self):
        self.clean_up(self.test_gmail)

    def clean_up(self, email):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM email_verifications WHERE LOWER(email) = LOWER(?)", (email,))
        cursor.execute("DELETE FROM users WHERE LOWER(email) = LOWER(?)", (email,))
        conn.commit()
        conn.close()

    # 1. Non-Gmail Addresses Are Strictly Blocked
    def test_01_non_gmail_addresses_blocked(self):
        non_gmail_cases = [
            "student@yahoo.com",
            "student@outlook.com",
            "student@hotmail.com",
            "student@icloud.com",
            "fake@tempmail.com",
            "test@randomdomain.org"
        ]
        for bad_email in non_gmail_cases:
            with self.subTest(email=bad_email):
                valid, msg = is_valid_gmail(bad_email)
                self.assertFalse(valid)
                self.assertIn("@gmail.com", msg)

                res = self.client.post("/api/register/initiate", json={
                    "name": self.test_name,
                    "email": bad_email,
                    "grade": "Class 10"
                })
                self.assertEqual(res.status_code, 400)
                self.assertIn("@gmail.com", res.json().get("detail", ""))

    # 2. Random Gmail Address Without OTP Verification -> Blocked From Account Creation & Login
    def test_02_random_gmail_without_otp_blocked(self):
        # User initiates with a random Gmail address
        init_res = self.client.post("/api/register/initiate", json={
            "name": self.test_name,
            "email": self.test_gmail,
            "grade": "Class 10"
        })
        self.assertEqual(init_res.status_code, 200)

        # Account MUST NOT exist or be active in users table yet
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, is_verified FROM users WHERE LOWER(email) = LOWER(?)", (self.test_gmail,))
        user_row = cursor.fetchone()
        conn.close()
        self.assertIsNone(user_row, "User should not be created in database prior to OTP and password completion")

        # Attempting to log in without verifying OTP MUST fail
        login_res = self.client.post("/api/login", json={
            "email": self.test_gmail,
            "password": self.test_pwd
        })
        self.assertIn(login_res.status_code, (401, 403))

    # 3. Correct Gmail with Incorrect OTP -> Blocked
    def test_03_correct_gmail_incorrect_otp_blocked(self):
        self.client.post("/api/register/initiate", json={
            "name": self.test_name,
            "email": self.test_gmail,
            "grade": "Class 10"
        })

        # Submit wrong OTP
        wrong_otp_res = self.client.post("/api/register/verify-otp", json={
            "email": self.test_gmail,
            "otp": "999999"
        })
        self.assertEqual(wrong_otp_res.status_code, 400)
        self.assertIn("Incorrect verification code", wrong_otp_res.json().get("detail", ""))

        # Verify account still NOT created
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE LOWER(email) = LOWER(?)", (self.test_gmail,))
        user_row = cursor.fetchone()
        conn.close()
        self.assertIsNone(user_row)

    # 4. Correct Gmail with Correct OTP & Password Setup -> Registration Successful
    def test_04_correct_gmail_correct_otp_and_password_success(self):
        # Step 1: Initiate
        init_res = self.client.post("/api/register/initiate", json={
            "name": self.test_name,
            "email": self.test_gmail,
            "grade": "Class 11"
        })
        self.assertEqual(init_res.status_code, 200)

        # Retrieve mock dispatched OTP
        otp = _LAST_DISPATCHED_OTP.get(self.test_gmail)
        self.assertIsNotNone(otp)
        self.assertEqual(len(otp), 6)

        # Step 2: Verify OTP (Gmail Ownership Verification)
        verify_res = self.client.post("/api/register/verify-otp", json={
            "email": self.test_gmail,
            "otp": otp
        })
        self.assertEqual(verify_res.status_code, 200)
        verify_data = verify_res.json()
        self.assertTrue(verify_data.get("requires_password"))
        self.assertTrue(verify_data.get("verified"))
        verification_token = verify_data.get("verification_token")
        self.assertIsNotNone(verification_token)

        # User is still not in users table until Step 3 password completion
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE LOWER(email) = LOWER(?)", (self.test_gmail,))
        self.assertIsNone(cursor.fetchone())
        conn.close()

        # Step 3: Complete registration with AI Maths Tutor password
        complete_res = self.client.post("/api/register/complete", json={
            "email": self.test_gmail,
            "verification_token": verification_token,
            "password": self.test_pwd,
            "confirm_password": self.test_pwd
        })
        self.assertEqual(complete_res.status_code, 200)
        complete_data = complete_res.json()
        self.assertTrue(complete_data.get("success"))
        self.assertIn("token", complete_data)

        # Verify user is now created in DB with is_verified = 1
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, is_verified FROM users WHERE LOWER(email) = LOWER(?)", (self.test_gmail,))
        user_row = cursor.fetchone()
        conn.close()
        self.assertIsNotNone(user_row)
        self.assertEqual(user_row["is_verified"], 1)

        # Verify student can now log in with the new password
        login_res = self.client.post("/api/login", json={
            "email": self.test_gmail,
            "password": self.test_pwd
        })
        self.assertEqual(login_res.status_code, 200)
        self.assertTrue(login_res.json().get("success"))
        self.assertIn("token", login_res.json())

    # 5. Duplicate Gmail Registration Blocked
    def test_05_duplicate_gmail_registration_blocked(self):
        # First register user completely
        self.client.post("/api/register/initiate", json={
            "name": self.test_name,
            "email": self.test_gmail,
            "grade": "Class 10"
        })
        otp = _LAST_DISPATCHED_OTP.get(self.test_gmail)
        verify_data = self.client.post("/api/register/verify-otp", json={
            "email": self.test_gmail,
            "otp": otp
        }).json()
        self.client.post("/api/register/complete", json={
            "email": self.test_gmail,
            "verification_token": verify_data["verification_token"],
            "password": self.test_pwd,
            "confirm_password": self.test_pwd
        })

        # Try to register the same Gmail again -> MUST BE BLOCKED
        dup_res = self.client.post("/api/register/initiate", json={
            "name": "Another Student",
            "email": self.test_gmail,
            "grade": "Class 12"
        })
        self.assertEqual(dup_res.status_code, 400)
        self.assertIn("already registered", dup_res.json().get("detail", "").lower())

    # 6. Direct API Registration Bypass Blocked
    def test_06_direct_api_bypass_blocked(self):
        bypass_res = self.client.post("/api/register", json={
            "name": "Hacker",
            "email": f"hacker.{secrets.token_hex(4)}@gmail.com",
            "password": "Password123!",
            "grade": "Class 10"
        })
        self.assertEqual(bypass_res.status_code, 400)
        self.assertIn("Direct registration is disabled", bypass_res.json().get("detail", ""))

    # 7. Password Show/Hide Elements Verified in Frontend HTML
    def test_07_password_show_hide_elements_present(self):
        reg_html_path = os.path.join(BASE_DIR, "register.html")
        login_html_path = os.path.join(BASE_DIR, "login.html")

        with open(reg_html_path, "r", encoding="utf-8") as f:
            reg_html = f.read()

        with open(login_html_path, "r", encoding="utf-8") as f:
            login_html = f.read()

        # Check register.html for password show/hide and confirm password show/hide
        self.assertIn('id="toggle-step3-pwd"', reg_html)
        self.assertIn('id="toggle-step3-confirm-pwd"', reg_html)
        self.assertIn('class="password-toggle-btn"', reg_html)
        self.assertIn('setupPasswordToggle', reg_html)
        self.assertIn('EYE_OPEN_SVG', reg_html)
        self.assertIn('EYE_CLOSED_SVG', reg_html)
        # Check independent password disclaimer notice
        self.assertIn('Independent Password', reg_html)
        self.assertIn('completely independent of your Google account', reg_html)

        # Check login.html for password show/hide
        self.assertIn('id="toggle-login-pwd"', login_html)
        self.assertIn('class="password-toggle-btn"', login_html)

    # 8. Existing Users Login Retained
    def test_08_existing_user_login_working(self):
        # Developer admin login test
        dev_res = self.client.post("/api/login", json={
            "email": "dev@mathstutor.com",
            "password": "admin"
        })
        self.assertEqual(dev_res.status_code, 200)
        self.assertTrue(dev_res.json().get("success"))
        self.assertEqual(dev_res.json().get("role"), "developer")

    # 9. Google Sign-In Remains Functional
    def test_09_google_signin_endpoint_active(self):
        # Verifies /api/auth/google endpoint rejects invalid credentials safely
        res = self.client.post("/api/auth/google", json={"credential": "invalid.fake.jwt"})
        self.assertEqual(res.status_code, 401)
        self.assertIn("invalid", res.json().get("detail", "").lower())


if __name__ == "__main__":
    unittest.main()
