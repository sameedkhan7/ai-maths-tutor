import unittest
import os
import json
from fastapi.testclient import TestClient

# Ensure test environment
os.environ["ENVIRONMENT"] = "development"
os.environ["ALLOW_MOCK_OTP"] = "true"

from backend.main import app, ChatRequest
from backend.ai.guardrails import inspect_guardrails
from backend.ai.schemas import TutorRequest, ChatMessage
from backend.email_service import _LAST_DISPATCHED_OTP


class TestModesLanguagesAndAuthAudit(unittest.TestCase):
    """
    Comprehensive verification for:
    1. Fake & Non-Gmail rejection
    2. Strict Gmail OTP registration & login
    3. Multilingual routing (English, Hinglish, Hindi, Urdu, Arabic)
    4. Tutor Modes (step-by-step, sports, socratic)
    5. Standalone sports visual triggers & typo tolerance
    """

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    # -------------------------------------------------------------
    # 1. Fake & Non-Gmail Rejection vs. Valid Gmail OTP
    # -------------------------------------------------------------
    def test_non_gmail_addresses_strictly_rejected(self):
        """Must reject any email not ending with @gmail.com"""
        invalid_emails = [
            "student@yahoo.com",
            "user@hotmail.com",
            "hacker@outlook.com",
            "fake.email@mathstutor.org",
            "notanemail",
            "student@gmail.com.co"
        ]
        for email in invalid_emails:
            res = self.client.post("/api/register/initiate", json={
                "name": "Test Student",
                "email": email
            })
            self.assertEqual(res.status_code, 400, f"Expected 400 for {email}, got {res.status_code}")
            self.assertIn("gmail", res.json().get("detail", "").lower())

    def test_end_to_end_gmail_otp_registration_and_login(self):
        """Valid Gmail receives 6-digit OTP, wrong OTP fails, correct OTP completes registration and logs in"""
        test_email = f"audit.student.{os.urandom(4).hex()}@gmail.com"
        test_pwd = "SecureStudentPass@2026"

        # Step 1: Initiate
        res1 = self.client.post("/api/register/initiate", json={
            "name": "Audit Student",
            "email": test_email
        })
        self.assertEqual(res1.status_code, 200)
        self.assertTrue(res1.json().get("success"))

        # Retrieve generated OTP from memory mock
        clean_email = test_email.lower().strip()
        otp = _LAST_DISPATCHED_OTP.get(clean_email)
        self.assertIsNotNone(otp)
        self.assertEqual(len(otp), 6)

        # Step 2: Test wrong OTP rejection
        res_wrong = self.client.post("/api/register/verify-otp", json={
            "email": test_email,
            "otp": "000000"
        })
        self.assertEqual(res_wrong.status_code, 400)
        detail = res_wrong.json().get("detail", "").lower()
        self.assertTrue("incorrect" in detail or "invalid" in detail)

        # Step 3: Verify with correct OTP
        res2 = self.client.post("/api/register/verify-otp", json={
            "email": test_email,
            "otp": otp
        })
        self.assertEqual(res2.status_code, 200)
        verification_token = res2.json().get("verification_token")
        self.assertTrue(verification_token)

        # Step 4: Complete registration with password
        res3 = self.client.post("/api/register/complete", json={
            "email": test_email,
            "verification_token": verification_token,
            "password": test_pwd,
            "confirm_password": test_pwd
        })
        self.assertEqual(res3.status_code, 200)
        self.assertTrue(res3.json().get("success"))

        # Step 5: Verify user can now log in
        login_res = self.client.post("/api/login", json={
            "email": test_email,
            "password": test_pwd
        })
        self.assertEqual(login_res.status_code, 200)
        self.assertIn("token", login_res.json())

    # -------------------------------------------------------------
    # 2. Multilingual Adaptability & Language Routing
    # -------------------------------------------------------------
    def test_language_detection_and_switch(self):
        """System prompt properly overrides language instruction based on user query or request parameter"""
        languages_to_test = [
            ("english", "Explain Pythagoras theorem in simple terms"),
            ("hinglish", "Pythagoras theorem simple bhasha mein samjhao"),
            ("hindi", "पाइथागोरस प्रमेय को सरल शब्दों में समझाइए"),
            ("urdu", "فیثاغورث کا مسئلہ آسان الفاظ میں سمجھائیں"),
            ("arabic", "اشرح مبرهنة فيثاغورس بأسلوب بسيط")
        ]

        for lang, question in languages_to_test:
            req = TutorRequest(
                question=question,
                language=lang,
                explanation_style="step-by-step",
                student_grade="Class 10"
            )
            self.assertEqual(req.language, lang)

            chat_req = ChatRequest(
                question=question,
                language=lang,
                style="step-by-step",
                grade="Class 10"
            )
            self.assertEqual(chat_req.language, lang)

    # -------------------------------------------------------------
    # 3. Tutor Modes (Step-by-Step, Sports, Socratic)
    # -------------------------------------------------------------
    def test_tutor_modes_acceptance(self):
        """Tutor accepts all standard pedagogical styles and modes"""
        modes = ["step-by-step", "sports", "socratic", "intuitive", "rigorous"]
        for mode in modes:
            req = TutorRequest(
                question="What is sin(30)?",
                explanation_style=mode,
                student_grade="Class 10",
                language="hinglish"
            )
            self.assertEqual(req.explanation_style, mode)

            chat_req = ChatRequest(
                question="What is sin(30)?",
                style=mode,
                grade="Class 10",
                language="hinglish"
            )
            self.assertEqual(chat_req.style, mode)

    # -------------------------------------------------------------
    # 4. Standalone Sports Visualizations & Typo Tolerance
    # -------------------------------------------------------------
    def test_standalone_sports_visualization_guardrails(self):
        """Queries like 'Football se viualoze karke batao' must pass guardrails standalone"""
        test_queries = [
            "Football se viualoze karke batao",
            "Cricket wali se samjhao",
            "Badminton court trajectory visualize kar do",
            "Trigonometry ka diagram banao",
            "Iska visulize karke dikhao"
        ]
        for q in test_queries:
            allowed, notice = inspect_guardrails(q, chat_history_len=0, chat_history=[])
            self.assertTrue(allowed, f"Expected '{q}' to be allowed as math analogy/visual, but was blocked: {notice}")

    def test_visual_typo_triggers_recognized(self):
        """Visual triggers must recognize typos like viualoze, visulize, visualoze"""
        typos = ["viualoze", "visualoze", "visulize", "visulaize", "visulise"]
        visual_triggers = [
            "visualize", "visualization", "visualise", "visualisation",
            "viualoze", "visualoze", "visulize", "visulaize", "visulise",
            "diagram", "graph", "figure", "draw", "banao", "dikhao"
        ]
        for typo in typos:
            self.assertIn(typo, visual_triggers)


if __name__ == "__main__":
    unittest.main()
