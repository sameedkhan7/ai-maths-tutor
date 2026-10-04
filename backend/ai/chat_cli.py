from backend.ai.schemas import TutorRequest
from backend.ai.tutor import generate_tutor_response


def main():
    print("=== AI Maths Tutor ===")
    print("Type 'exit' to stop.\n")

    # Temporary chat history for CLI testing
    # Database se connected nahi hai
    chat_history = []

    while True:
        question = input("You: ").strip()

        if question.lower() == "exit":
            print("Goodbye!")
            break

        if not question:
            print("Please enter a question.\n")
            continue

        request = TutorRequest(
            question=question,
            chat_history=chat_history,
            student_level="beginner",
            explanation_style="simple",
            language="english",
        )

        response = generate_tutor_response(request)

        print("\nTutor:")
        print(response.answer)

        if response.error:
            print("\nError:", response.error)

        # Save current conversation for follow-up questions
        chat_history.append({
            "role": "user",
            "content": question,
        })

        chat_history.append({
            "role": "assistant",
            "content": response.answer,
        })

        print("\n" + "-" * 50 + "\n")


if __name__ == "__main__":
    main()