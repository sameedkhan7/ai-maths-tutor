# =========================
# QUESTION TYPE DETECTION
# =========================


def detect_question_type(question: str) -> str:
    """
    Detect the type of maths question using simple rules.
    No LLM/API call is used here.
    """

    q = question.lower().strip()

    # -------------------------
    # Explain Again
    # -------------------------

    explain_again_keywords = [
        "explain again",
        "again please",
        "explain once more",
        "i don't understand",
        "i dont understand",
        "not understand",
        "make me understand",
        "simpler way",
    ]

    if any(keyword in q for keyword in explain_again_keywords):
        return "explain_again"

    # -------------------------
    # Student Mistake
    # -------------------------

    mistake_keywords = [
        "my answer",
        "my answer is",
        "i got",
        "i get",
        "wrong answer",
        "why is my answer wrong",
        "where did i go wrong",
        "mistake",
        "incorrect",
        "book says",
        "answer key says",
    ]

    if any(keyword in q for keyword in mistake_keywords):
        return "student_mistake"    

    # -------------------------
    # Homework
    # -------------------------

    homework_keywords = [
        "homework",
        "assignment",
        "question given",
        "teacher gave",
        "solve this question",
        "help me solve",
    ]

    if any(keyword in q for keyword in homework_keywords):
        return "homework"

    # -------------------------
    # Numerical
    # -------------------------

    numerical_keywords = [
    "solve",
    "calculate",
    "find the value",
    "find x",
    "evaluate",
    "simplify",
    "how much",
    "what is the answer",
]

    if any(keyword in q for keyword in numerical_keywords):
        return "numerical"

    # -------------------------
    # Follow-up
    # -------------------------

    follow_up_phrases = [
        "what about",
        "why is that",
        "how is that",
        "what does it mean",
        "why does it",
        "how does it",
        "and then",
        "then what",
    ]

    if any(phrase in q for phrase in follow_up_phrases):
        return "follow_up"

    # Very short follow-up questions
    follow_up_words = {
        "it",
        "this",
        "that",
        "why",
        "how",
        "then",
    }

    words = set(q.replace("?", "").replace(".", "").split())

    if len(q.split()) <= 8 and words.intersection(follow_up_words):
        return "follow_up"
    # -------------------------
    # Concept
    # -------------------------

    concept_keywords = [
        "what is",
        "what are",
        "explain",
        "define",
        "meaning of",
        "concept",
        "difference between",
        "why do we use",
        "how does",
    ]

    if any(keyword in q for keyword in concept_keywords):
        return "concept"

    # -------------------------
    # Default
    # -------------------------

    return "concept"