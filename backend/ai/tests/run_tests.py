import json

from backend.ai.schemas import TutorRequest
from backend.ai.tutor import generate_tutor_response


TEST_FILE = "backend/ai/tests/test_cases.json"


def load_test_cases():
    with open(TEST_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def run_tests():
    test_cases = load_test_cases()

    total = len(test_cases)
    passed = 0

    print("=" * 60)
    print("AI MATHS TUTOR - TEST REPORT")
    print("=" * 60)

    for index, test in enumerate(test_cases, start=1):

        request = TutorRequest(
            question=test["question"],
            student_level=test["student_level"],
            explanation_style=test["explanation_style"],
        )

        response = generate_tutor_response(request)

        expected = test["expected_type"]
        actual = response.question_type

        if actual == expected and response.error is None:
            status = "PASS"
            passed += 1
        else:
            status = "FAIL"

        print(f"\nTest {index}: {test['name']}")
        print(f"Expected: {expected}")
        print(f"Actual:   {actual}")
        print(f"Status:   {status}")

        if response.error:
            print(f"Error:    {response.error}")

    print("\n" + "=" * 60)
    print(f"TOTAL: {total}")
    print(f"PASSED: {passed}")
    print(f"FAILED: {total - passed}")
    print("=" * 60)


if __name__ == "__main__":
    run_tests()