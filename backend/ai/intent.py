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
    # Syllabus & Chapter Info
    # -------------------------
    syllabus_keywords = [
        "first chapter", "1st chapter", "chapter 1", "chapter one", "pehla chapter",
        "second chapter", "2nd chapter", "chapter 2", "chapter two", "dusra chapter", "doosra chapter",
        "third chapter", "3rd chapter", "chapter 3", "chapter three", "teesra chapter",
        "fourth chapter", "4th chapter", "chapter 4", "chautha chapter",
        "fifth chapter", "5th chapter", "chapter 5", "panchwa chapter",
        "sixth chapter", "6th chapter", "chapter 6",
        "seventh chapter", "7th chapter", "chapter 7",
        "eighth chapter", "8th chapter", "chapter 8",
        "ninth chapter", "9th chapter", "chapter 9",
        "tenth chapter", "10th chapter", "chapter 10",
        "syllabus", "how many chapters", "list of chapters",
        "all chapters", "table of contents", "which chapter",
        "what is the chapter", "what does the chapter",
        "what is the first chapter", "what does the first chapter",
        "what is chapter", "chapters in class",
        "curriculum", "course structure"
    ]

    if any(keyword in q for keyword in syllabus_keywords):
        return "syllabus_info"

    # -------------------------
    # Voice / Pure Greeting Check
    # -------------------------
    greeting_voice_keywords = [
        "can you listen", "can you hear", "are you listening",
        "can you type", "voice check", "mic test", "testing mic",
        "hello tutor", "hello sir", "namaste", "hey tutor"
    ]
    if any(k in q for k in greeting_voice_keywords) and len(q.split()) <= 8:
        return "greeting"

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