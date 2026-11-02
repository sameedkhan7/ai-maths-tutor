import os
import sys
import unittest
import math

# Add root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.ai.math_engine import (
    calculate_derivative,
    calculate_integral,
    solve_quadratic_equation,
    solve_linear_system_2var,
    solve_projectile_motion,
    get_exact_math_context,
)
from backend.ai.schemas import TutorRequest
from backend.ai.tutor import generate_tutor_response


class TestMathReasoningAndAPI(unittest.TestCase):
    """
    Test suite for Phase 2 (Mathematical Reasoning) & Phase 3 (API Reliability).
    """

    def test_case_1_derivative(self):
        """Case 1: Differentiate x³ sin(x)"""
        expr = "x^3 sin(x)"
        res = calculate_derivative(expr)
        self.assertIsNotNone(res, "Derivative should not be None")
        # Expected derivative: 3*x^2*sin(x) + x^3*cos(x)
        self.assertIn("cos", res["solution"])
        self.assertIn("sin", res["solution"])
        # Verification via reverse integration
        self.assertIn("x**3*sin(x)", res["verification"])
        print("\n[TEST 1 PASS] Differentiate x³ sin(x):")
        print(f"  Expected: 3x² sin(x) + x³ cos(x)")
        print(f"  Actual:   {res['solution']}")
        print(f"  Verified by Reverse Integration: {res['verification']}")

    def test_case_2_integral(self):
        """Case 2: Integrate 2x + 3"""
        expr = "2x + 3"
        res = calculate_integral(expr)
        self.assertIsNotNone(res, "Integral should not be None")
        # Expected integral: x^2 + 3*x
        self.assertIn("x**2", res["solution"])
        self.assertIn("3*x", res["solution"])
        # Verification via derivative
        self.assertIn("2*x + 3", res["verification"])
        print("\n[TEST 2 PASS] Integrate 2x + 3:")
        print(f"  Expected: x² + 3x + C")
        print(f"  Actual:   {res['solution']} + C")
        print(f"  Verified by Differentiation: {res['verification']}")

    def test_case_3_quadratic(self):
        """Case 3: Solve x² - 5x + 6 = 0"""
        eq_text = "Solve x^2 - 5x + 6 = 0"
        res = solve_quadratic_equation(eq_text)
        self.assertIsNotNone(res, "Quadratic solver should not be None")
        self.assertEqual(res["discriminant"], 1.0)
        self.assertEqual(sorted(res["roots"]), [2.0, 3.0])
        print("\n[TEST 3 PASS] Solve x² - 5x + 6 = 0:")
        print(f"  Expected: Discriminant D = 1, Roots = [2, 3]")
        print(f"  Actual:   Discriminant D = {res['discriminant']}, Roots = {res['roots']}")

    def test_case_4_linear_system(self):
        """Case 4: Solve a two-variable linear equation system: 3x + 2y = 80 and 2x + 3y = 70"""
        sys_text = "Solve 3x + 2y = 80 and 2x + 3y = 70"
        res = solve_linear_system_2var(sys_text)
        self.assertIsNotNone(res, "Linear system solver should not be None")
        self.assertEqual(res["x"], 20.0)
        self.assertEqual(res["y"], 10.0)
        print("\n[TEST 4 PASS] Solve 3x + 2y = 80 and 2x + 3y = 70:")
        print(f"  Expected: x = 20, y = 10")
        print(f"  Actual:   x = {res['x']}, y = {res['y']}")

    def test_case_5_projectile_motion(self):
        """
        Case 5: Projectile motion: 45° launch angle and 40 m range,
        equal launch and landing heights, g = 9.8 m/s².
        Expected: Initial velocity ≈ 19.80 m/s, Maximum height = 10 m.
        """
        prompt = (
            "A ball is projected at 45 degrees and has a horizontal range of 40 metres. "
            "Assuming equal launch and landing heights and no air resistance, "
            "calculate maximum height and initial velocity."
        )
        res = solve_projectile_motion(prompt)
        self.assertIsNotNone(res, "Projectile solver should not be None")
        self.assertAlmostEqual(res["initial_velocity"], 19.80, places=1)
        self.assertEqual(res["max_height"], 10.0)
        print("\n[TEST 5 PASS] Projectile Motion (θ = 45°, R = 40m, g = 9.8 m/s²):")
        print(f"  Expected: Initial velocity ≈ 19.80 m/s, Maximum height = 10 m")
        print(f"  Actual:   Initial velocity = {res['initial_velocity']} m/s, Maximum height = {res['max_height']} m, Time of flight = {res['time_of_flight']} s")

    def test_end_to_end_projectile_llm(self):
        """End-to-End LLM Tutor Generation for Case 5"""
        req = TutorRequest(
            question=(
                "A ball is projected at 45 degrees and has a horizontal range of 40 metres. "
                "Assuming equal launch and landing heights and no air resistance, "
                "calculate maximum height and initial velocity."
            ),
            explanation_style="step_by_step",
            language="english"
        )
        resp = generate_tutor_response(req)
        self.assertIsNone(resp.error, f"Tutor returned error: {resp.error}")
        self.assertTrue(len(resp.answer) > 50, "Answer should be generated")
        # Ensure correct physical numbers appear in the answer
        self.assertTrue("19.8" in resp.answer or "19.80" in resp.answer, "Answer should contain initial velocity 19.80 m/s")
        self.assertTrue("10" in resp.answer, "Answer should contain maximum height 10 m")
        print("\n[END-TO-END LLM TEST PASS] Projectile Response Verified:")
        print("  Snippet of LLM Response:")
        for line in resp.answer.splitlines()[:10]:
            print("   ", line)


if __name__ == "__main__":
    unittest.main()
