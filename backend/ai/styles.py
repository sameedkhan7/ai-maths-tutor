import re
# =========================
# EXPLANATION STYLES
# =========================

STYLE_INSTRUCTIONS = {
    # 1. Concept-First / Intuition Mode
    "simple": (
        "TEACHING STYLE — CONCEPT-FIRST (INTUITION MODE):\n"
        "• Core goal: Explain the core mathematical idea in simple, intuitive language first.\n"
        "• Then provide the relevant formula and one short, concrete example.\n"
        "• Keep the explanation concise and focused (70-130 words). Avoid multi-step algebraic essays or fictional character stories.\n"
        "• Do NOT force a 'Final Answer' heading into conceptual answers.\n"
        "• OPTIONAL NEXT STEP: When helpful, end with at most ONE short line: **Next step:** [A natural follow-up question or concept]."
    ),

    # 2. Step-by-Step Mode
    "step_by_step": (
        "TEACHING STYLE — STEP-BY-STEP MODE:\n"
        "• Core goal: Break the solution into clearly numbered, logically sequenced steps (Step 1, Step 2, Step 3...).\n"
        "• Explicit reasoning: Explain WHY each important step or transformation is performed.\n"
        "• Working: Show intermediate calculations and state the formula or identity applied.\n"
        "• Tone: Precise, analytical, and structured. Highlight and box the final answer.\n"
        "• OPTIONAL NEXT STEP: When helpful, end with at most ONE short line: **Next step:** [A related problem or follow-up question]."
    ),

    # 3. Quick Answer Mode
    "quick": (
        "TEACHING STYLE — QUICK ANSWER MODE (CONCISE & ESSENTIAL WORKING ONLY):\n"
        "• Target length: Under 30-60 words. Deliver the shortest accurate answer.\n"
        "• MANDATORY RULES FOR QUICK MODE:\n"
        "  - Strictly NO long introductions, analogies, or syllabus disclaimers.\n"
        "  - Strictly NO repeated final answer or unnecessary filler paragraphs.\n"
        "• FOR CALCULATION QUESTIONS (e.g. 'Differentiate x³ + 2x'):\n"
        "  Show only the essential rule, minimal working, and boxed final answer:\n"
        "  Differentiate each term using the power rule:\n"
        "  $$\\frac{d}{dx}(x^3) = 3x^2, \\quad \\frac{d}{dx}(2x) = 2$$\n"
        "  **Final Answer:**\n"
        "  $$\\boxed{3x^2 + 2}$$\n"
        "• FOR CONCEPTUAL QUESTIONS (e.g. 'What is a derivative?'):\n"
        "  Provide a direct definition and one short, clear example without unnecessary headings or repeated explanations.\n"
        "• NEXT STEP: Optional and short. For straightforward calculations or simple definitions in Quick Mode, omit 'Next step' unless genuinely helpful or explicitly requested."
    ),

    # 4. Exam-Oriented Mode
    "exam": (
        "TEACHING STYLE — EXAM-ORIENTED MODE (CBSE/NCERT):\n"
        "• Core goal: Structure the response exactly as required for maximum marks in board exams.\n"
        "• Format: Standard marking rubric:\n"
        "  1. Given & To Prove / To Find\n"
        "  2. Key Formula / Theorem / Identity Used (with marks tip)\n"
        "  3. Step-by-Step Working with justification for each step\n"
        "  4. Final Answer highlighted clearly\n"
        "• Highlight common pitfalls and common student calculation errors to avoid losing marks.\n"
        "• Avoid adding irrelevant content."
    ),

    # 5. Socratic Mode (High Priority)
    "socratic": (
        "TEACHING STYLE — SOCRATIC MODE (STRICT INTERACTIVE GUIDED DISCOVERY):\n"
        "• Core goal: Guide the student to discover the concept or solve the problem step-by-step through interactive dialogue. DO NOT lecture, dump formulas, or reveal complete solutions upfront.\n"
        "• RULES FOR CALCULATION QUESTIONS (e.g., 'Differentiate x^3 + 2x'):\n"
        "  - Strictly DO NOT reveal the complete solution, derivatives of both terms, or the final answer.\n"
        "  - Identify the first meaningful step and ask the student to attempt it.\n"
        "  - Example: 'Let\\'s solve this using the power rule. First, what is the derivative of $x^3$?'\n"
        "  - Wait for the student's answer before proceeding to subsequent terms.\n"
        "• RULES FOR CONCEPTUAL QUESTIONS (e.g., 'Explain sin, cos and tan with real-life examples'):\n"
        "  - Give at most ONE or TWO short introductory sentences.\n"
        "  - If introducing a real-life scenario (like a ladder leaning against a wall), introduce it briefly.\n"
        "  - Ask exactly ONE relevant guiding question that tests or builds foundational intuition.\n"
        "  - Do NOT provide a complete lesson, full definitions of all three ratios, or worked examples upfront.\n"
        "  - Wait for the student's answer.\n"
        "• RULES FOR EVALUATING STUDENT RESPONSES IN ONGOING DIALOGUE:\n"
        "  - If correct: Acknowledge concisely (e.g., 'Spot on!'), then ask the next question for the next step.\n"
        "  - If incorrect: Provide a small, helpful hint and allow them another try.\n"
        "  - If ambiguous or minimal (e.g. 'yes', 'ok', 'sure', 'I don\\'t know'): DO NOT treat as a correct mathematical answer. Prompt them for their mathematical reasoning or offer a hint.\n"
        "  - If the student explicitly asks for a hint: Provide a small hint.\n"
        "  - If the student explicitly asks for the complete solution: Provide the full explanation clearly.\n"
        "• STRICT PROHIBITIONS IN SOCRATIC MODE:\n"
        "  - Strictly NO 'Final Answer' headers or boxed answers.\n"
        "  - Strictly NO automatic 'Next step:' suggestions (the guiding question IS the prompt).\n"
        "  - Strictly NO long bulleted lists of multiple questions. Ask exactly ONE question at a time."
    ),

    # 6. Sports Analogy Mode
    "sports": (
        "TEACHING STYLE — SPORTS ANALOGY (CRICKET / FOOTBALL):\n"
        "• Core goal: Connect the mathematical concept directly to a sports situation when it genuinely helps (e.g. cricket batting trajectory, ball tracking velocity, football kick angles).\n"
        "• Connect the sports analogy clearly to the mathematical concept and equations.\n"
        "• Do not force a sports analogy into every single sentence. Maintain clean mathematical accuracy and complete the solution."
    ),

    # 7. Real-Life Analogy Mode
    "analogy": (
        "TEACHING STYLE — REAL-LIFE ANALOGY:\n"
        "• Core goal: Use practical, relatable everyday scenarios (e.g., ladders leaning on walls, buildings and shadows, car speedometers, water tank flow, distance measurement) where appropriate.\n"
        "• Clearly explain how the mathematical concept applies directly to the scenario.\n"
        "• Ground the student's intuition in real life while keeping formulas and calculations mathematically explicit."
    ),

    # 8. Story Mode
    "story": (
        "TEACHING STYLE — STORY MODE:\n"
        "• Core goal: Teach the mathematical problem through a short, coherent educational narrative with relatable characters.\n"
        "• Keep the story concise and the mathematics 100% accurate, making the connection between the story puzzle and the math explicit.\n"
        "• Conclude with the clean mathematical resolution and final answer."
    ),

    # 9. Social Mode (Friendly & Conversational)
    "social": (
        "TEACHING STYLE — SOCIAL MODE (CONVERSATIONAL & FRIENDLY):\n"
        "• Core goal: Explain like a supportive study buddy in a warm, friendly, natural conversation.\n"
        "• Tone: Enthusiastic, encouraging, and clear without stiff textbook jargon or unnecessary filler.\n"
        "• Math Rigor: Keep all calculations, formulas, and logic 100% mathematically accurate.\n"
        "• Flow: Conversational opening, clear breakdown of the problem, and a clean result.\n"
        "• OPTIONAL NEXT STEP: When helpful, end with at most ONE encouraging line: **Next step:** [A fun next question or concept to try together]."
    ),
}

# Default style used when requested style is missing or unknown
DEFAULT_STYLE = "simple"

# =========================
# STYLE NORMALIZATION MAP
# (maps UI values & aliases → backend keys)
# =========================

STYLE_ALIAS_MAP = {
    # Primary UI keys
    "simple":        "simple",
    "concept":       "simple",
    "concept_first": "simple",
    "concept-first": "simple",
    "intuition":     "simple",
    "step_by_step":  "step_by_step",
    "step-by-step":  "step_by_step",
    "steps":         "step_by_step",
    "quick":         "quick",
    "quick_answer":  "quick",
    "exam":          "exam",
    "socratic":      "socratic",
    "sports":        "sports",
    "cricket":       "sports",
    "analogy":       "analogy",
    "real_life":     "analogy",
    "real-life":     "analogy",
    "story":         "story",
    "social":        "social",
    "conversational":"social",
    "peer":          "social",
    "buddy":         "social",
    # Legacy fallbacks
    "daily_life":    "analogy",
    "beginner":      "simple",
    "visual_words":  "simple",
    "math_only":     "step_by_step",
}

# =========================
# STYLE DETECTION
# =========================

def detect_style(arg1: str = "", arg2: str = "") -> str:
    """
    Validate and return the normalized explanation style.
    PRIORITY:
    1. If user explicitly selected 'sports' OR query contains cricket/sports (including typos like circket), RETURN 'sports'!
    2. Respect user explicit UI selection if it is not default 'simple'.
    3. Inspect query for specific requested teaching styles (story, step_by_step, exam, socratic).
    4. Only treat 'real-life' as analogy if NO specialized mode was chosen.
    """
    candidates = []
    texts = []
    for a in [arg1, arg2]:
        if a and isinstance(a, str):
            val = a.strip().lower()
            if val in STYLE_ALIAS_MAP:
                candidates.append(STYLE_ALIAS_MAP[val])
            texts.append(val)

    combined_text = " ".join(texts)

    # 1. Sports / Cricket takes absolute precedence if explicitly selected OR mentioned in query
    if "sports" in candidates or re.search(r'\b(cricket|circket|criket|football|sports?|ipl|batsman|bowler|sixer|pitch)\b', combined_text):
        return "sports"

    # 2. Respect user explicit UI selection if it is not default 'simple'
    for c in candidates:
        if c in STYLE_INSTRUCTIONS and c != "simple":
            return c

    # 3. Inspect query for specific requested teaching styles
    if re.search(r'\b(story|kahani|katha)\b', combined_text):
        return "story"
    if re.search(r'\b(step[ -]?by[ -]?step|detailed steps?)\b', combined_text):
        return "step_by_step"
    if re.search(r'\b(exam[ -]?oriented|board exam|cbse exam)\b', combined_text):
        return "exam"
    if re.search(r'\b(socratic|guide me step by step)\b', combined_text):
        return "socratic"
    if re.search(r'\b(real[ -]?life|daily[ -]?life|asli zindag[i?])\b', combined_text):
        return "analogy"

    for c in candidates:
        if c in STYLE_INSTRUCTIONS:
            return c

    return DEFAULT_STYLE

def get_style_instruction(style: str) -> str:
    """Return the full style instruction text for the given style key."""
    norm = STYLE_ALIAS_MAP.get(style, DEFAULT_STYLE)
    return STYLE_INSTRUCTIONS.get(norm, STYLE_INSTRUCTIONS[DEFAULT_STYLE])