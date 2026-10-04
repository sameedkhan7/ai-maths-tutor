# =========================
# EXPLANATION STYLES
# =========================

STYLE_INSTRUCTIONS = {
    "simple": "Explain in simple and clear English using short sentences.",

    "real_life": "Explain using practical real-life examples and analogies.",

    "story": "Explain the concept through a short and simple story.",

    "sports": "Explain using sports-related examples or analogies when useful.",

    "daily_life": "Explain using examples from common daily life situations.",

    "exam": "Explain in an exam-focused way with important points and steps.",

    "step_by_step": "Explain the solution clearly one step at a time.",

    "beginner": "Assume the student is a complete beginner. Avoid difficult terminology.",

    "visual_words": "Use text-based visual representations, arrows, boxes, and simple layouts.",

    "math_only": "Focus only on the mathematical reasoning and calculations. Avoid unnecessary examples."
}


# =========================
# STYLE DETECTION
# =========================

def detect_style(
    question: str,
    requested_style: str = "simple"
) -> str:
    """
    Detect explanation style from the student's question.
    If no style keyword is found, use the requested style.
    If the requested style is invalid, use 'simple'.
    """

    question_lower = question.lower()

    style_keywords = {
        "real_life": [
            "real life",
            "real-life",
            "real world",
            "real-world",
        ],

        "story": [
            "story",
            "story style",
        ],

        "sports": [
            "sports",
            "cricket",
            "football",
            "game",
        ],

        "daily_life": [
            "daily life",
            "everyday life",
        ],

        "exam": [
            "exam",
            "exam friendly",
            "exam point",
        ],

        "step_by_step": [
            "step by step",
            "step-by-step",
            "stepwise",
        ],

        "beginner": [
            "beginner",
            "from basics",
            "i am new",
            "i'm new",
        ],

        "visual_words": [
            "visual",
            "visualize",
            "visualise",
            "in words",
            "diagram",
        ],

        "math_only": [
            "math only",
            "maths only",
            "only mathematics",
        ],

        "simple": [
            "simple",
            "easy",
            "easy words",
        ],
    }

    # First check the student's question
    for style, keywords in style_keywords.items():
        for keyword in keywords:
            if keyword in question_lower:
                return style

    # Otherwise use requested style
    if requested_style in STYLE_INSTRUCTIONS:
        return requested_style

    return "simple"