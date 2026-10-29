"""
backend/ai/guardrails.py — Ironclad Security & Mathematical Scope Guardrails
Strictly confines the AI Tutor to Mathematics and prevents Prompt Injection / Data Extraction.
"""

import re
import difflib
from typing import Optional, Tuple

# ==============================================================
# 1. IRONCLAD PROMPT INJECTION & SYSTEM LEAK PATTERNS
# ==============================================================
INJECTION_PATTERNS = [
    # System Prompt & Internal Instructions Leakage
    r"(?:system|base|hidden|initial|original|secret)\s+(?:prompt|instruction|rules?|message|directive)",
    r"(?:reveal|show|print|display|dump|repeat|leak|tell me|give me)\s+(?:all\s+)?(?:your\s+)?(?:system|internal|hidden|base|initial|secret)\s+(?:prompt|instruction|rules?|config|code)",
    r"(?:repeat|print|output)\s+(?:everything|all text|the text)\s+(?:above|before|prior)",
    r"what\s+(?:are|were)\s+your\s+(?:initial|original|system|hidden)\s+(?:instructions|prompts?|rules?)",
    
    # Jailbreaks & Instruction Overrides
    r"ignore\s+(?:all\s+)?(?:previous|prior|above|former)\s+(?:instructions|prompts?|rules?|directives|constraints)",
    r"disregard\s+(?:all\s+)?(?:previous|prior|above)\s+(?:instructions|rules?)",
    r"forget\s+(?:everything|all\s+instructions|your\s+rules)",
    r"(?:you\s+are\s+now|act\s+as|pretend\s+to\s+be)\s+(?:in\s+)?(?:dan|developer\s+mode|unrestricted|jailbreak|god\s+mode|root|admin\s+terminal)",
    r"\bdeveloper\s+mode\b",
    r"\b(?:dump|drop|delete|show)\s+(?:all\s+)?(?:db\s+|database\s+)?tables?\b",
    r"hypothetical\s+scenario\s+where\s+you\s+(?:have\s+no\s+rules|can\s+bypass)",
    r"bypass\s+(?:safety|filter|guardrail|security|rules)",
    
    # Database, Secrets, & Environment Theft
    r"(?:select\s+.*\s+from|insert\s+into|delete\s+from|drop\s+table|update\s+.*\s+set)\s+",
    r"(?:union\s+select|information_schema|show\s+tables|show\s+databases)",
    r"(?:users?\s+table|tutor\.db|maths_tutor_db|database\s+schema|db\s+password)",
    r"(?:api[_\s]?key|groq[_\s]?api|secret[_\s]?key|\.env\s+file|credentials|token)",
    r"(?:admin|root)\s+(?:password|credentials|login\s+details)",
    
    # Delimiter & System Message Spoofing
    r"(?:<\|im_start\|>|<\|system\|>|\[system\]|\[instruction\]|###\s*system:)",
    r"---end\s+of\s+instructions---",
]

COMPILED_INJECTION_REGEXES = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]


# ==============================================================
# 2. MATHEMATICAL SCOPE VOCABULARY & PATTERNS
# ==============================================================

# Common mathematical operators, symbols & KaTeX tokens
MATH_SYMBOL_PATTERN = re.compile(
    r"[\d]+[\s]*[\+\-\*\/\^=><÷×±√∫∑∏]\s*[\d]+|"  # 2 + 2, x = 5
    r"\\(?:frac|sqrt|sin|cos|tan|cot|sec|csc|int|lim|sum|pm|cdot|alpha|beta|theta|pi|partial|times|div)|"
    r"\b(?:dy\/dx|d\/dx|dx|dy|dt|f\(x\)|g\(x\)|x\^2|y\^2|x\^3)\b|"
    r"[\$]+[\s\S]+?[\$]+"  # Inline or display LaTeX
)

# Common conversational greetings & pleasantries
GREETING_WORDS = {
    "hi", "hello", "hey", "hola", "namaste", "namaskar", "salaam", "salam", 
    "good morning", "good afternoon", "good evening", "how are you", 
    "who are you", "kya haal", "kaise ho", "thank you", "thanks", "shukriya",
    "dhanyawad", "bye", "goodbye", "help", "help me"
}

# Math-specific core vocabulary (NCERT Classes 9-12 Curriculum)
MATH_TERMS = {
    # Numbers & Arithmetic
    "math", "maths", "mathematics", "number", "numbers", "digit", "fraction", "decimal",
    "prime number", "prime numbers", "prime factor", "prime factorisation", "composite", "rational", "irrational", "real number", "integer", "integers",
    "hcf", "lcm", "factor", "factorisation", "factorization", "multiple", "divisible",
    "remainder", "exponent", "power", "log", "logarithm", "modulus", "complex number",
    
    # Algebra
    "algebra", "equation", "equations", "quadratic", "linear", "polynomial", "polynomials",
    "variable", "variables", "constant", "coefficient", "degree", "root", "roots", "zeroes",
    "discriminant", "matrix", "matrices", "determinant", "determinants", "binomial",
    "sequence", "series", "progression", "arithmetic progression", "ap", "gp", "geometric",
    "permutation", "combination", "factorial", "inequality", "inequalities",
    
    # Geometry & Mensuration
    "geometry", "triangle", "triangles", "circle", "circles", "sphere", "cone", "cylinder",
    "cube", "cuboid", "hemisphere", "frustum", "angle", "angles", "area", "volume",
    "perimeter", "surface area", "circumference", "radius", "diameter", "chord", "secant",
    "tangent", "quadrilateral", "parallelogram", "rectangle", "square", "rhombus", "trapezium",
    "coordinate", "coordinates", "cartesian", "abscissa", "ordinate", "distance formula",
    "section formula", "collinear", "congruent", "congruence", "similar", "similarity",
    "pythagoras", "pythagorean", "hypotenuse", "conic", "ellipse", "parabola", "hyperbola",
    "straight line", "slope", "intercept", "vector", "3d", "three dimensional",
    
    # Trigonometry
    "trigonometry", "trigonometric", "sin", "cos", "tan", "cot", "sec", "cosec", "csc",
    "sine", "cosine", "tangent", "radian", "degree", "hypotenuse", "opposite", "adjacent",
    "height", "distance", "elevation", "depression", "identity", "identities",
    
    # Calculus
    "calculus", "derivative", "derivatives", "differentiate", "differentiation", "integral",
    "integrals", "integrate", "integration", "limit", "limits", "continuity", "continuous",
    "differentiable", "differentiability", "chain rule", "product rule", "quotient rule",
    "differential equation", "differential equations", "maxima", "minima", "rate of change",
    "tangent line", "normal line", "definite integral", "indefinite integral",
    
    # Statistics & Probability
    "statistics", "mean", "median", "mode", "frequency", "grouped data", "ogive", "histogram",
    "variance", "standard deviation", "probability", "event", "events", "outcome", "outcomes",
    "dice", "die", "coin", "coins", "card", "cards", "bayes", "random variable",
    
    # NCERT & Problem Solving
    "ncert", "cbse", "syllabus", "exercise", "chapter", "example", "formula", "formulas",
    "theorem", "theorems", "proof", "prove", "solve", "solution", "calculate", "evaluate",
    "simplify", "expand", "value of", "find x", "find y", "graph", "board exam", "marks",
    "class 9", "class 10", "class 11", "class 12", "step by step"
}


# ==============================================================
# 3. GUARDRAIL INSPECTION FUNCTIONS
# ==============================================================


# Common student misspellings & phonetic typos for NCERT math concepts
COMMON_MATH_TYPOS = {
    # Trigonometry
    "tignomatry": "trigonometry", "tignometry": "trigonometry", "trignomatry": "trigonometry",
    "trignometry": "trigonometry", "trignometery": "trigonometry", "trigonometery": "trigonometry",
    "trigonometri": "trigonometry", "trigo": "trigonometry", "tirgonometry": "trigonometry",
    "triganometry": "trigonometry", "trig": "trigonometry",
    # Calculus
    "calculas": "calculus", "calc": "calculus", "calclus": "calculus", "calcules": "calculus",
    # Derivative & Differentiation
    "derivetive": "derivative", "derivetives": "derivatives", "derivitive": "derivative",
    "derivitives": "derivatives", "drivative": "derivative", "drivatives": "derivatives",
    "derivation": "derivative", "differenciation": "differentiation", "diffrentiation": "differentiation",
    "diferentiation": "differentiation", "differenciate": "differentiate", "diffrenciate": "differentiate",
    # Integration & Integrals
    "integrasion": "integration", "intigration": "integration", "integretion": "integration",
    "integrel": "integral", "integrels": "integrals", "integar": "integral", "integ": "integration",
    # Algebra & Quadratic
    "quadretic": "quadratic", "quadratik": "quadratic", "quadretik": "quadratic", "quad": "quadratic",
    "algbra": "algebra", "aljebra": "algebra", "alzebra": "algebra", "polinomial": "polynomial",
    "polynomail": "polynomial", "polynimial": "polynomial",
    # Geometry
    "geometery": "geometry", "geomentry": "geometry", "geom": "geometry",
    "triangal": "triangle", "triangls": "triangles", "pythogoras": "pythagoras", "pythagores": "pythagoras",
    "hypotenuous": "hypotenuse", "hypotenus": "hypotenuse",
    # Arithmetic & Numbers
    "arithmatic": "arithmetic", "airthmetic": "arithmetic", "mathemetics": "mathematics",
    "mathmatics": "mathematics", "mathematic": "mathematics",
    # Statistics & Probability
    "probablity": "probability", "probabality": "probability", "probabiliti": "probability",
    "statstics": "statistics", "statictics": "statistics", "staticstics": "statistics"
}

FUZZY_MATH_ROOTS = [
    "trigonometry", "calculus", "derivative", "differentiation", "integral", "integration",
    "quadratic", "algebra", "polynomial", "geometry", "triangle", "pythagoras",
    "arithmetic", "probability", "statistics", "matrix", "determinant", "equation"
]

def inspect_guardrails(query: str, chat_history_len: int = 0) -> Tuple[bool, Optional[str]]:
    """
    Evaluates incoming query against Security and Math-Scope Guardrails.
    Returns: (is_allowed: bool, blocked_response: Optional[str])
    """
    clean_q = query.strip()
    q_lower = clean_q.lower()
    
    # ----------------------------------------------------------
    # GUARD 1: Ironclad Prompt Injection & System Leak Defense
    # ----------------------------------------------------------
    for pattern in COMPILED_INJECTION_REGEXES:
        if pattern.search(clean_q):
            blocked_reply = (
                "> 🛡️ **Security Alert: Unauthorized Query Pattern**\n\n"
                "Aapki query mein system instructions ya internal database inspection ka pattern detect hua hai.\n\n"
                "🔒 **Safety Rule:** Yeh AI Maths Tutor strictly **Mathematics Learning & NCERT Problem Solving** ke liye secure hai. "
                "System prompt, credentials, ya internal database schema reveal karna strictly prohibited hai.\n\n"
                "📐 *Kripya sirf mathematics aur syllabus se jude sawal puchein!*"
            )
            return False, blocked_reply

    # ----------------------------------------------------------
    # GUARD 2: Pure Greetings Handling
    # ----------------------------------------------------------
    words = [w.strip("?,.!") for w in q_lower.split() if w.strip("?,.!")]
    is_pure_greeting = (len(words) <= 3 and any(w in GREETING_WORDS for w in words)) or (q_lower in GREETING_WORDS)
    
    if is_pure_greeting:
        greeting_reply = (
            "👋 **Hello! Welcome to AI Maths Tutor.**\n\n"
            "Main aapka dedicated **Mathematics AI Tutor** hoon (NCERT Classes 9th to 12th).\n\n"
            "Aap mujhse kisi bhi maths topic par madad le sakte hain:\n"
            "* 📐 **Algebra & Polynomials** (Roots, Factorisation, Quadratic Formula)\n"
            "* 📏 **Trigonometry** (Ratios, Identities, Heights & Distances)\n"
            "* 📈 **Calculus** (Derivatives, Limits, Integrals, Chain Rule)\n"
            "* 📊 **Statistics & Probability**\n\n"
            "🎯 **Aap kaun sa maths question solve karna chahte hain?**"
        )
        return False, greeting_reply

    # If it's a short conversational follow-up in an ongoing chat, allow it through
    if chat_history_len > 0 and len(words) <= 5:
        follow_up_tokens = {"yes", "no", "ok", "next", "why", "how", "step", "again", "repeat", "continue", "samjha", "nahi"}
        if any(w in follow_up_tokens for w in words):
            return True, None

    # ----------------------------------------------------------
    # GUARD 3: Strict Mathematics Scope Enforcement
    # ----------------------------------------------------------
    # Check 1: Does it contain mathematical symbols/operators/numbers?
    has_math_symbols = bool(MATH_SYMBOL_PATTERN.search(clean_q))
    if has_math_symbols:
        return True, None

    # Check 2: Does it contain any NCERT/Mathematics terminology or student typos?
    has_math_terms = False
    # 2a. Direct match
    for term in MATH_TERMS:
        if " " in term:
            if term in q_lower:
                has_math_terms = True
                break
        else:
            if re.search(r'\b' + re.escape(term) + r'\b', q_lower):
                has_math_terms = True
                break

    # 2b. Check common student typos / phonetic spellings
    if not has_math_terms:
        for typo in COMMON_MATH_TYPOS:
            if re.search(r'\b' + re.escape(typo) + r'\b', q_lower):
                has_math_terms = True
                break

    # 2c. Fuzzy matching (difflib) for misspelled math concepts (min length 5)
    if not has_math_terms:
        tokens = [w for w in re.findall(r"[a-zA-Z]+", q_lower) if len(w) >= 5]
        for tok in tokens:
            close_matches = difflib.get_close_matches(tok, FUZZY_MATH_ROOTS, n=1, cutoff=0.70)
            if close_matches:
                has_math_terms = True
                break

    if has_math_terms:
        return True, None

    # If none of the mathematical checks passed -> It is OFF-TOPIC!
    off_topic_reply = (
        "> ⚠️ **Focus Notice: Mathematics Tutor Only**\n\n"
        f"Aapka sawaal mathematics se related nahi lag raha hai.\n\n"
        "🎯 **Hamara Scope:**\n"
        "Yeh application abhi vishesh roop se **Mathematics (NCERT Classes 9, 10, 11, 12)** ke liye banayi gayi hai. "
        "Science, Languages, Coding, ya General Knowledge filhal support nahi kiye jaate (Coming Soon).\n\n"
        "📐 **Aap in topics par sawal pooch sakte hain:**\n"
        "* Trigonometry, Calculus ($dy/dx$, $\\int f(x)dx$)\n"
        "* Quadratic Equations ($ax^2 + bx + c = 0$)\n"
        "* Coordinate Geometry, Triangles, Circles\n"
        "* Board Exam Important Formulas & Solutions\n\n"
        "💡 *Kripya koi bhi mathematical equation ya question type karein!*"
    )
    return False, off_topic_reply
