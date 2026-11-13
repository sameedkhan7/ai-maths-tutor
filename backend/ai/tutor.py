import re
from backend.ai.config import (

    GROQ_MODEL,

    PROMPT_VERSION,

)



from backend.ai.schemas import TutorRequest, TutorResponse, RAGChunk

from backend.ai.styles import detect_style, get_style_instruction

from backend.ai.intent import detect_question_type

from backend.ai.prompts import MASTER_SYSTEM_PROMPT

from backend.ai.context_builder import build_messages

from backend.ai.groq_client import call_groq

from backend.ai.math_engine import get_exact_math_context

from backend.rag.retriever import retrieve_math_context
try:
    from backend.rag.curriculum import get_official_ncert_pdf_url
except ImportError:
    from rag.curriculum import get_official_ncert_pdf_url



# ==========================================================

# 📐 HIGH-PRECISION MATHEMATICAL & SPORTS SVG DIAGRAMS

# ==========================================================

FALLBACK_SVG_RIGHT_TRIANGLE = """```svg

<svg viewBox="0 0 340 210" xmlns="http://www.w3.org/2000/svg" class="math-svg-diagram">

  <rect width="100%" height="100%" fill="#0f172a" rx="10"/>

  <!-- Triangle vertices: A(50, 160), B(240, 160), C(240, 40) -->

  <polygon points="50,160 240,160 240,40" fill="rgba(56, 189, 248, 0.08)" stroke="#38bdf8" stroke-width="2.5" stroke-linejoin="round"/>

  <!-- Right Angle Square at B -->

  <path d="M 225,160 L 225,145 L 240,145" fill="none" stroke="#f43f5e" stroke-width="2"/>

  <!-- Small Angle θ Arc at A -->

  <path d="M 76,160 A 26 26 0 0 0 72,143" fill="none" stroke="#fbbf24" stroke-width="2"/>

  <text x="82" y="154" fill="#fbbf24" font-size="13" font-weight="bold">θ</text>

  <!-- Vertex labels -->

  <text x="32" y="165" fill="#94a3b8" font-size="13" font-weight="bold">A</text>

  <text x="248" y="172" fill="#94a3b8" font-size="13" font-weight="bold">B (90°)</text>

  <text x="240" y="28" fill="#94a3b8" font-size="13" font-weight="bold" text-anchor="middle">C</text>

  <!-- Non-overlapping side labels with generous clearance -->

  <text x="145" y="185" fill="#38bdf8" font-size="13" font-weight="600" text-anchor="middle">Base (b)</text>

  <text x="252" y="105" fill="#38bdf8" font-size="13" font-weight="600">Perpendicular (p)</text>

  <text x="125" y="90" fill="#a78bfa" font-size="13" font-weight="600" transform="rotate(-32, 125, 90)">Hypotenuse (h)</text>

</svg>

```"""



FALLBACK_SVG_SPORTS_PARABOLA = """```svg
<svg viewBox="0 0 420 230" width="100%" xmlns="http://www.w3.org/2000/svg" class="math-svg-diagram">
  <rect width="100%" height="100%" fill="#090d16" rx="12"/>
  <!-- Ground Pitch -->
  <rect x="0" y="175" width="420" height="55" fill="#064e3b"/>
  <line x1="15" y1="175" x2="405" y2="175" stroke="#10b981" stroke-width="2"/>

  <!-- Launch point (Batsman / Kick) at (50, 175) -->
  <circle cx="50" cy="175" r="5" fill="#38bdf8"/>
  <text x="50" y="200" fill="#94a3b8" font-size="11" font-weight="bold" text-anchor="middle">Launch (0, 0)</text>

  <!-- Parabolic Trajectory Curve: (50, 175) -> Apex (210, 45) -> Landing (370, 175) -->
  <!-- Quadratic bezier control point: y_c = 2*45 - 175 = -85 -->
  <path d="M 50,175 Q 210,-85 370,175" fill="none" stroke="#38bdf8" stroke-width="2.8"/>

  <!-- Tangent Initial Velocity Vector u at launch -->
  <line x1="50" y1="175" x2="115" y2="110" stroke="#fbbf24" stroke-width="2.5" stroke-linecap="round"/>
  <!-- Arrowhead for vector u -->
  <polygon points="115,110 102,114 111,123" fill="#fbbf24"/>
  <text x="120" y="105" fill="#fbbf24" font-size="12" font-weight="bold">Initial Velocity (u)</text>

  <!-- Launch Angle θ Arc -->
  <path d="M 85,175 A 35 35 0 0 0 75,150" fill="none" stroke="#fbbf24" stroke-width="2"/>
  <text x="92" y="166" fill="#fbbf24" font-size="12" font-weight="bold">θ</text>

  <!-- Apex (Peak Height H_max) at (210, 45) -->
  <line x1="210" y1="175" x2="210" y2="45" stroke="#f43f5e" stroke-width="2" stroke-dasharray="4,4"/>
  <circle cx="210" cy="45" r="6" fill="#ef4444" stroke="#ffffff" stroke-width="1.5"/>
  <text x="210" y="32" fill="#f87171" font-size="11.5" font-weight="bold" text-anchor="middle">Peak / Apex</text>

  <!-- Maximum Height Label -->
  <rect x="218" y="95" width="92" height="22" rx="4" fill="#1e293b" stroke="#f43f5e" stroke-width="1"/>
  <text x="264" y="110" fill="#f43f5e" font-size="11" font-weight="bold" text-anchor="middle">H_max = u²sin²θ/2g</text>

  <!-- Landing Point at (370, 175) -->
  <circle cx="370" cy="175" r="5" fill="#10b981"/>
  <text x="370" y="200" fill="#10b981" font-size="11" font-weight="bold" text-anchor="middle">Landing (R, 0)</text>

  <!-- Total Horizontal Range R dimension line -->
  <line x1="50" y1="215" x2="370" y2="215" stroke="#64748b" stroke-width="1.5"/>
  <line x1="50" y1="210" x2="50" y2="220" stroke="#64748b" stroke-width="1.5"/>
  <line x1="370" y1="210" x2="370" y2="220" stroke="#64748b" stroke-width="1.5"/>
  <text x="210" y="212" fill="#e2e8f0" font-size="11" font-weight="bold" text-anchor="middle">Horizontal Range R = u²sin(2θ)/g</text>
</svg>
```"""



def generate_tutor_response(req: TutorRequest) -> TutorResponse:

    """

    Main function for generating an AI Maths Tutor response.



    This function never raises an exception.

    Errors are returned inside TutorResponse.error.

    """



    try:

        # 🛡️ Ironclad AI Guardrails Check (Maths-Only Scope & Anti-Prompt-Injection)

        try:

            from backend.ai.guardrails import inspect_guardrails, normalize_math_query

        except ImportError:

            from ai.guardrails import inspect_guardrails, normalize_math_query

        req.question = normalize_math_query(req.question)

        history_len = len(req.chat_history) if req.chat_history else 0

        is_allowed, guard_reply = inspect_guardrails(
            req.question,
            chat_history_len=history_len,
            chat_history=req.chat_history
        )



        if not is_allowed and guard_reply:

            return TutorResponse(

                answer=guard_reply,

                question_type="guardrail_intercepted",

                explanation_style=req.explanation_style or "simple",

                used_rag=False,

                sources=[],

                prompt_version=PROMPT_VERSION,

                model=req.model or GROQ_MODEL or "llama-3.3-70b-versatile",

                error=None,

            )



        # Detect question type

        question_type = detect_question_type(req.question)



        # Validate / normalize explanation style

        explanation_style = detect_style(

            req.question,

            req.explanation_style

        )



        # 📚 Member 2: Auto-retrieve NCERT RAG chunks from Knowledge Base (Class-Priority First)

        curriculum_badge_instruction = ""

        badge_markdown = None

        if not req.rag_chunks:

            try:

                student_cls = getattr(req, "student_grade", "Class 10") or "Class 10"

                rag_res = retrieve_math_context(req.question, student_class=student_cls, top_k=2)



                # Check if question is a simple calculation where NCERT badge is not relevant

                q_lower = req.question.lower().strip()

                is_quick = explanation_style == "quick"

                wants_ncert = any(k in q_lower for k in ["ncert", "syllabus", "cbse", "chapter", "exercise", "exam"])



                if rag_res and rag_res.get("has_context"):

                    for c in rag_res.get("chunks", []):

                        req.rag_chunks.append(RAGChunk(

                            text=c["text"],

                            source=c.get("source", "NCERT Mathematics"),

                            page=c.get("page", 1),

                            score=c.get("score", 0.8)

                        ))



                    # Determine active language early for proper badge localization

                    lang_str = (req.language or "hinglish").strip().lower()



                    # Only show badge if user asked about syllabus/exam OR style is exam OR relevant chunks exist and it's not quick mode

                    is_ongoing_dialogue = bool(req.chat_history and len(req.chat_history) > 0)

                    if (wants_ncert or explanation_style == "exam" or rag_res.get("chunks")) and not is_quick and not (explanation_style == "socratic" and is_ongoing_dialogue):

                        ref_badge = rag_res.get("reference_badge", "")

                        note_text = rag_res.get("note_text")

                        # Generate direct verified official NCERT PDF link
                        ch_no = rag_res.get("chapter_no")
                        matched_class_name = rag_res.get("matched_class", "Class 10")
                        pdf_url = get_official_ncert_pdf_url(matched_class_name, ch_no)
                        pdf_link_md = ""
                        if pdf_url and ch_no:
                            pdf_link_md = f'  \n> 🔗 **Official Textbook:** <a href="{pdf_url}" target="_blank" rel="noopener noreferrer" class="chat-ncert-btn">📖 Open NCERT Chapter {ch_no} PDF ↗</a>'

                        is_cross = rag_res.get("is_cross_class", False)

                        matched_cls = rag_res.get("matched_class", "Class 12")



                        if is_cross and note_text:

                            if lang_str in ["en", "english"]:

                                note_text = f"This concept is covered in the {matched_cls} syllabus."

                            elif lang_str in ["hi", "hindi"]:

                                note_text = f"यह अवधारणा {matched_cls} के पाठ्यक्रम में शामिल है।"

                            elif lang_str in ["ur", "urdu"]:

                                note_text = f"یہ تصور {matched_cls} کے نصاب میں شامل ہے۔"

                            elif lang_str in ["ar", "arabic"]:

                                note_text = f"هذا المفهوم مشمول في منهج {matched_cls}."

                            badge_markdown = f"> {ref_badge}{pdf_link_md}  \n> *(ℹ️ Note: {note_text})*"

                        else:

                            badge_markdown = f"> {ref_badge}{pdf_link_md}"



                        curriculum_badge_instruction = (

                            f"\n\nMANDATORY NCERT SYLLABUS REFERENCE BADGE:\n"

                            f"At the VERY TOP of your response (before any other text or explanation), render this exact compact markdown blockquote badge:\n"

                            f"{badge_markdown}\n\n"

                        )

            except Exception as e:

                print(f"RAG retrieval notice: {e}")



        # Define explicit language instructions (HIGHEST PRIORITY — overrides all other rules)

        q_raw_lower_early = req.question.lower().strip()
        lang_str = (req.language or "hinglish").strip().lower()
        if re.search(r'\b(english mein|english me|in english|explain in english)\b', q_raw_lower_early):
            lang_str = "english"
        elif re.search(r'\b(hindi mein|hindi me|in hindi|explain in hindi|shuddh hindi)\b', q_raw_lower_early):
            lang_str = "hindi"
        elif re.search(r'\b(urdu mein|urdu me|in urdu|explain in urdu)\b', q_raw_lower_early):
            lang_str = "urdu"
        elif re.search(r'\b(arabic mein|arabic me|in arabic|explain in arabic)\b', q_raw_lower_early):
            lang_str = "arabic"
        elif re.search(r'\b(hinglish mein|hinglish me|in hinglish)\b', q_raw_lower_early):
            lang_str = "hinglish"



        if lang_str in ["hi", "hindi"]:

            lang_rule = (

                "══════════════════════════════════════\n"

                "🌐 ACTIVE LANGUAGE = हिंदी (DEVANAGARI SCRIPT ONLY)\n"

                "══════════════════════════════════════\n"

                "नियम: आपको अपना पूरा विवरण केवल शुद्ध और सरल हिंदी (देवनागरी लिपि) में लिखना है।\n"

                "अंग्रेजी या हिंग्लिश में वाक्य न लिखें।\n"

                "गणितीय सूत्र मानक LaTeX में रहेंगे: जैसे $x^2$, $\\frac{dy}{dx}$, $\\sin(x)$।"

            )

        elif lang_str in ["en", "english"]:

            lang_rule = (

                "══════════════════════════════════════\n"

                "🌐 ACTIVE LANGUAGE = ENGLISH (CLEAR & NATURAL)\n"

                "══════════════════════════════════════\n"

                "Rule: Write your entire response in clear, fluent English.\n"

                "DO NOT use Hindi, Hinglish, or Urdu words in your explanation.\n"

                "Mathematical notation stays in clean LaTeX format ($...$ and $$...$$)."

            )

        elif lang_str in ["ur", "urdu"]:

            lang_rule = (

                "══════════════════════════════════════\n"

                "🌐 ACTIVE LANGUAGE = اردو (URDU SCRIPT ONLY)\n"

                "══════════════════════════════════════\n"

                "Rule: Write your entire mathematical explanation in fluent, natural Urdu (اردو رسم الخط).\n"

                "Keep mathematical formulas in standard clean LaTeX format ($...$ and $$...$$)."

            )

        elif lang_str in ["ar", "arabic"]:

            lang_rule = (

                "══════════════════════════════════════\n"

                "🌐 ACTIVE LANGUAGE = العربية (ARABIC SCRIPT ONLY)\n"

                "══════════════════════════════════════\n"

                "Rule: Write your entire mathematical explanation in fluent, standard Arabic (اللغة العربية).\n"

                "Keep mathematical formulas in standard clean LaTeX format ($...$ and $$...$$)."

            )

        else:

            lang_rule = (

                "══════════════════════════════════════\n"

                "🌐 ACTIVE LANGUAGE = HINGLISH (ROMAN SCRIPT HINDI + ENGLISH MATH TERMS)\n"

                "══════════════════════════════════════\n"

                "Rule: Write your explanation in natural conversational Hinglish (Hindi written in English alphabets).\n"

                "Example: 'Derivative ka matlab hota hai rate of change. Chaliye formula apply karte hain.'\n"

                "DO NOT write in Devanagari script. Use standard LaTeX for equations."

            )



        # Get the full style instruction text

        style_instruction = get_style_instruction(explanation_style)



        # Conversational greetings & voice check detector

        q_raw_lower = req.question.lower().strip()

        has_voice_greeting = any(k in q_raw_lower for k in [

            "can you listen", "can you hear", "are you listening",

            "can you type", "voice check", "mic test", "testing mic",

            "hello can you", "hi can you", "hello tutor", "hello sir", "namaste"

        ])



        greeting_directive = ""

        if has_voice_greeting:

            greeting_directive = (

                "\n\nCONVERSATIONAL GREETING & VOICE CHECK DIRECTIVE:\n"

                "The student opened with a voice/mic check or greeting (e.g. 'Can you listen to me?').\n"

                "Start your response with a natural, friendly 1-sentence acknowledgment before addressing the question:\n"

                "- If in Hinglish: 'Hello! Yes, I can hear you clearly and I am ready to help. 😊'\n"

                "- If in English: 'Hello! Yes, I can hear you loud and clear. 😊'\n"

                "- If in Hindi: 'नमस्ते! हाँ, मैं आपको साफ़ सुन सकता हूँ और आपकी मदद के लिए तैयार हूँ। 😊'\n"

            )



        syllabus_info_directive = ""

        if question_type == "syllabus_info":

            syllabus_info_directive = (

                "\n\nSYLLABUS & CHAPTER INFO DIRECTIVE (HIGHEST PRIORITY):\n"

                "The student is asking an informational/syllabus question (e.g. 'What is the first chapter of Class 10th?').\n"

                "1. DIRECT FACTUAL ANSWER: State the chapter number and official title immediately and clearly in bold (e.g. 'Class 10th Maths (NCERT) ka Chapter 1 **Real Numbers** hai.').\n"

                "2. CORE TOPICS OVERVIEW: Provide a clean, structured 2-3 bullet point summary of what topics are in this chapter (e.g. Fundamental Theorem of Arithmetic, proving irrationality of square root 2).\n"

                "3. STRICT PROHIBITIONS: DO NOT dump random formulas or irrelevant equations (like Pythagoras theorem a^2 + b^2 = c^2). DO NOT force calculation working.\n"

                "4. INVITING NEXT STEP: Conclude with a friendly question asking if they want to study a specific topic or exercise from this chapter.\n"

            )



                # Dynamic Context & Sport Theme Detector (Football, Cricket, Badminton, Car, Coding)

        q_raw_lower = req.question.lower()

        active_theme = None

        if any(k in q_raw_lower for k in ["football", "soccer", "penalty", "free kick", "goal post", "fifa"]):

            active_theme = "football"

        elif any(k in q_raw_lower for k in ["badminton", "shuttle", "shuttlecock", "racket", "smash"]):

            active_theme = "badminton"

        elif any(k in q_raw_lower for k in ["car", "racing", "speedometer", "driving", "vehicle", "highway"]):

            active_theme = "car"

        elif any(k in q_raw_lower for k in ["basketball", "hoop", "dunk", "3-pointer"]):

            active_theme = "basketball"

        elif any(k in q_raw_lower for k in ["code", "coding", "game", "gaming", "fps"]):

            active_theme = "coding"

        elif any(k in q_raw_lower for k in ["cricket", "batsman", "bowler", "pitch", "sixer", "wicket", "ipl", "stumps"]):

            active_theme = "cricket"

        elif explanation_style == "sports":

            active_theme = "cricket" # Default when in sports mode without specific sport

        wants_sports = bool(active_theme)



        sports_directive = ""

        if active_theme:

            if active_theme == "football":

                sports_directive = """



STRICT CONTEXT THEME DIRECTIVE — FOOTBALL (HIGHEST PRIORITY):
The student asked for FOOTBALL!
1. EXPLAIN THE CONCEPT 100% USING FOOTBALL (STRICT PROHIBITION: DO NOT mention cricket, pitch, batsman, wickets, or ladders!):
   - For Calculus/Derivatives: Explain using a Footballer / Striker taking a curved free-kick. The ball position vector is s(t). The derivative is the instantaneous velocity v(t) = s'(t) = lim_{h->0} [s(t+h) - s(t)] / h (the tangent vector slope to the trajectory curve as it curls towards the goal).
   - For Class 10 Trigonometry (Heights and Distances): Straight line-of-sight from penalty spot to the top crossbar of the goal net at angle of elevation theta θ. Crossbar vertical height is Perpendicular (p), ground distance is Base (b), and straight sightline distance is Hypotenuse (h) [tan θ = p/b, sin θ = p/h].
   - For Class 11 Projectile Motion: The ball follows a true parabolic path under gravity: y(x) = x tan θ - (g x²) / (2 u² cos² θ). Range R = u² sin(2θ) / g, Max Height H_max = u² sin²θ / (2g). DO NOT confuse the curved trajectory with a straight hypotenuse!
2. STRICT PROHIBITION: DO NOT generate any SVG diagram or visualization unless the student EXPLICITLY asks (e.g. "diagram banao", "visualize", "draw").
"""

            elif active_theme == "badminton":
                sports_directive = """
STRICT CONTEXT THEME DIRECTIVE — BADMINTON (HIGHEST PRIORITY):
The student asked for BADMINTON!
1. EXPLAIN 100% USING BADMINTON: Player executing a jump smash over the net. Shuttlecock trajectory dipping steeply into opponent court. Instantaneous smash speed is derivative v(t) = s'(t).
2. STRICT PROHIBITION: DO NOT generate any SVG diagram or visualization unless the student EXPLICITLY asks (e.g. "diagram banao", "visualize", "draw").
"""

            elif active_theme == "car":
                sports_directive = """
STRICT CONTEXT THEME DIRECTIVE — CAR RACING & SPEEDOMETER (HIGHEST PRIORITY):
The student asked for CAR DRIVING / RACING!
1. EXPLAIN 100% USING A RACING CAR: Car accelerating along highway track. Speedometer needle shows instantaneous speed v(t) = ds/dt at that exact second. Distance vs time curve s(t).
2. STRICT PROHIBITION: DO NOT generate any SVG diagram or visualization unless the student EXPLICITLY asks (e.g. "diagram banao", "visualize", "draw").
"""

            elif active_theme == "coding":
                sports_directive = """
STRICT CONTEXT THEME DIRECTIVE — CODING & GAME PHYSICS (HIGHEST PRIORITY):
The student asked for CODING / GAMING!
1. EXPLAIN USING GAME DEVELOPMENT: Frame delta time (dt), player velocity update (position += velocity * dt), and physics engine collision calculations.
2. STRICT PROHIBITION: DO NOT generate any SVG diagram or visualization unless the student EXPLICITLY asks.
"""

            else:
                sports_directive = """
STRICT CONTEXT THEME DIRECTIVE — CRICKET (HIGHEST PRIORITY):
The student asked for CRICKET!
1. EXPLAIN 100% USING CRICKET:
   - For Calculus: Ball trajectory s(t) and instantaneous velocity tangent vector v(t) = s'(t).
   - For Class 10 Trigonometry (Heights & Distances): Straight sightline from a fielder/batsman to the top of a floodlight tower or stadium roof at elevation angle θ. Vertical height is Perpendicular (p), ground distance is Base (b), straight line-of-sight is Hypotenuse (h) [tan θ = p/b, sin θ = p/h].
   - For Class 11 Projectile Motion: Batsman hitting a lofted sixer. The ball follows a parabolic path under gravity: y(x) = x tan θ - (g x²) / (2 u² cos² θ).
     * Range: R = u² sin(2θ) / g
     * Maximum Height: H_max = u² sin²θ / (2g)
     * Time of Flight: T = 2u sin θ / g
     * STRICT PROHIBITION: NEVER describe a curved projectile flight path as a straight-line hypotenuse!
2. STRICT PROHIBITION: DO NOT generate any SVG diagram or visualization unless the student EXPLICITLY asks (e.g. "diagram banao", "visualize", "cricket ka diagram banao").
"""



        # Visual request detector
        visual_triggers = [
            "visualize", "visualization", "visualise", "visualisation",
            "viualoze", "visualoze", "visulize", "visulaize", "visulise",
            "diagram", "graph", "figure", "draw", "banao", "dikhao", "visual", "3d", "infographic"
        ]
        is_visual_request = any(k in q_raw_lower for k in visual_triggers)

        visual_directive = ""
        if is_visual_request:
            visual_directive = (
                "\n\nSTRICT VISUALIZATION DIRECTIVE (HIGHEST PRIORITY):\n"
                "The student explicitly requested a VISUALIZATION / DIAGRAM ('visualization kar do' / 'diagram banao').\n"
                "1. DIRECT VISUAL DELIVERY: Do NOT lecture with socratic back-and-forth questions or ask them to restate formulas.\n"
                "2. RENDER SVG DIAGRAM: Provide a complete, high-quality SVG diagram inside a ```svg fenced block clearly illustrating the concept (e.g. right triangle with labelled Base, Perpendicular, Hypotenuse, and elevation angle theta, or the requested sport field/goalpost).\n"
                "3. VISUAL EXPLANATION: In 2-4 bullet points, clearly explain how the visual diagram connects directly to the mathematical formulas.\n"
            )

        # Mathematical problem-solving workflow detector
        workflow_directive = ""
        if any(w in q_raw_lower for w in ["workflow", "tareeka", "tarika", "vidhi"]):
            workflow_directive = (
                "\n\nMATHEMATICAL WORKFLOW DIRECTIVE (HIGHEST PRIORITY):\n"
                "The student asked for the mathematical problem-solving workflow (e.g. 'Trigonometry ka workflow samjhao').\n"
                "1. BREAK DOWN THE MATHEMATICAL WORKFLOW: Present the standard 5-step problem-solving method:\n"
                "   - Step 1: Identify Given Information & Objective (Identify angle theta, known sides, target side/ratio)\n"
                "   - Step 2: Select the Right Ratio / Formula (Choose sin theta = p/h, cos theta = b/h, or tan theta = p/b based on which side is known)\n"
                "   - Step 3: Formulate Equation & Substitute Values\n"
                "   - Step 4: Solve & Simplify Algebraically\n"
                "   - Step 5: Verification Check (Apply Pythagoras Theorem p^2 + b^2 = h^2)\n"
                "2. STRICT PROHIBITION: DO NOT explain internal software engineering, backend code, or AI architecture. Focus 100% on the MATHEMATICAL problem-solving workflow.\n"
            )

        # Add style, question type, and formatting instructions to system prompt

        system_prompt = (

            f"{MASTER_SYSTEM_PROMPT}\n\n"

            f"{'='*50}\n"

            f"ACTIVE SESSION CONFIGURATION\n"

            f"{'='*50}\n"

            f"{lang_rule}\n\n"

            f"QUESTION TYPE: {question_type}\n"

            f"STUDENT GRADE: {getattr(req, 'student_grade', 'Class 10')}\n"

            f"STUDENT LEVEL: {req.student_level}\n\n"

            f"{style_instruction}\n\n"

            f"{curriculum_badge_instruction}\n"

            f"{greeting_directive}"

            f"{syllabus_info_directive}"

            f"{sports_directive}"
            f"{visual_directive}"
            f"{workflow_directive}"

            f"{'='*50}\n"

            f"RESPONSE QUALITY RULES:\n"

            f"{'='*50}\n"

            f"1. CONCISENESS: Target 60-140 words for standard queries. Be crisp and organized like modern educational AI. No redundant essay text.\n"

            f"2. NO QUESTION REPETITION: Do not repeat or restate the student's question.\n"

            f"3. MATH DELIMITERS: Always use $...$ for inline math and $$...$$ for display equations so KaTeX renders them perfectly.\n"

            f"4. DIAGRAMS: If a diagram is helpful, provide clean SVG code inside a ```svg fenced block. Never use broken ASCII art.\n"

            f"5. LANGUAGE AND STYLE ARE MANDATORY: Adhere 100% to the active language and active teaching style specified above.\n"

        )



        # Check exact mathematical verification with SymPy

        exact_math = get_exact_math_context(req.question)

        if exact_math:

            if explanation_style == "socratic":

                system_prompt += (

                    f"\n\nEXACT MATHEMATICAL VERIFICATION (FOR TUTOR REFERENCE ONLY — DO NOT REVEAL TO STUDENT):\n"

                    f"{exact_math}\n"

                    f"Use this verified answer internally to check the student's reasoning as they work through the steps, but DO NOT reveal the final solution upfront."

                )

            else:

                system_prompt += f"\n\nEXACT MATHEMATICAL VERIFICATION:\n{exact_math}\nEnsure your response strictly matches this verified analytical solution."



        # Socratic Mode Highest Priority Directive (Guarantees no regression from history or RAG)

        if explanation_style == "socratic":

            system_prompt += (

                f"\n\n{'='*50}\n"

                f"SOCRATIC MODE STRICT OVERRIDE (HIGHEST PRIORITY):\n"

                f"{'='*50}\n"

                f"1. CALCULATION QUESTIONS: Ask the student to differentiate or solve the FIRST term/step only (e.g. for d/dx(x^3 + 2x), ask: 'First, what is the derivative of x^3?'). DO NOT reveal the full solution or final boxed answer.\n"

                f"2. CONCEPTUAL QUESTIONS: Provide at most 1-2 short intro sentences and ask exactly ONE guiding question. DO NOT define all terms or write all formulas.\n"

                f"3. EVALUATING STUDENT ANSWERS: Minimal words like 'yes', 'ok', or 'I don\\'t know' are NOT correct mathematical answers. Ask them to attempt the calculation or offer a hint.\n"

                f"4. STRICTLY NO 'Final Answer' headers, NO boxed equations, and NO 'Next step:' suggestions.\n"

                f"5. DIALOGUE CONSISTENCY: Even if previous conversation history has full worked steps, you MUST strictly respond as a Socratic tutor.\n"

            )



                # Intelligent Educational Visual / Diagram Injector (Trigonometry, Right Angle, Sports, Story)

        # CRITICAL USER DIRECTIVE: ONLY visualize when student EXPLICITLY asks for visual/diagram/image,
        # or when active explanation style is sports/visual mode. Normal questions get pure mathematical text!
        visual_explicit_triggers = [
            "visualize", "visualization", "visualise", "visualisation",
            "diagram", "image", "photo", "picture", "chitra", "graph",
            "figure", "draw", "banao", "dikhao", "visual", "3d", "infographic"
        ]
        q_lower = req.question.lower()
        has_explicit_visual_word = any(kw in q_lower for kw in visual_explicit_triggers)
        # FIX: ONLY trigger visual injection when student EXPLICITLY asks. Never auto-trigger for sports/visual mode.
        is_visual_topic = has_explicit_visual_word



        if is_visual_topic:

            if active_theme == "football":

                system_prompt += (

                    f"\n\n{'='*50}\n"

                    f"FOOTBALL SVG DIAGRAM & VISUALIZATION (Student explicitly asked):\n"

                    f"{'='*50}\n"

                    f"The student explicitly asked for FOOTBALL visualization!\n"

                    f"1. Provide a Football Stadium SVG diagram showing the green turf, striker kicking the ball, goalpost net, and ball trajectory curve s(t) with tangent kick speed v(t)!\n"

                    f"2. EXPLANATION MUST BE 100% FOOTBALL BASED: Do NOT mention cricket, pitch, or batsman!\n"

                    f"{'='*50}\n"

                )

            elif active_theme == "badminton":

                system_prompt += (

                    f"\n\n{'='*50}\n"

                    f"BADMINTON SVG DIAGRAM & VISUALIZATION (Student explicitly asked):\n"

                    f"{'='*50}\n"

                    f"1. Provide a Badminton Court SVG diagram showing the net, player jump smash, and shuttlecock trajectory!\n"

                    f"2. EXPLANATION MUST BE 100% BADMINTON BASED!\n"

                    f"{'='*50}\n"

                )

            elif active_theme == "car":

                system_prompt += (

                    f"\n\n{'='*50}\n"

                    f"CAR RACING SVG DIAGRAM & VISUALIZATION (Student explicitly asked):\n"

                    f"{'='*50}\n"

                    f"1. Provide a Sports Car and Speedometer HUD SVG diagram!\n"

                    f"2. EXPLANATION MUST BE 100% CAR / DRIVING BASED!\n"

                    f"{'='*50}\n"

                )

            elif active_theme == "cricket":

                system_prompt += (

                    f"\n\n{'='*50}\n"

                    f"CRICKET SPORTS SVG DIAGRAM & VISUALIZATION (Student explicitly asked):\n"

                    f"{'='*50}\n"

                    f"1. Provide the Cricket Stadium SVG diagram showing the pitch, batsman hitting the shot, and ball trajectory!\n"

                    f"2. EXPLANATION MUST BE 100% CRICKET BASED!\n"

                    f"{'='*50}\n"

                )

            else:

                mode_visual_cue = ""

                if explanation_style == "story":

                    mode_visual_cue = "In STORY MODE: If student asked for a diagram, show the story scenario in SVG (e.g. lighthouse/tower, elevation angle θ, distance to ship/ground)."

                elif explanation_style == "step_by_step":

                    mode_visual_cue = "In STEP-BY-STEP MODE: If student asked for a diagram, show a clean labeled SVG diagram at the start, then explicitly reference its vertices/sides in Step 1, Step 2, Step 3."

                elif explanation_style == "quick":

                    mode_visual_cue = "In QUICK MODE: If student asked for a diagram, include a compact, clean SVG diagram alongside the boxed formula."

                else:

                    mode_visual_cue = "In CONCEPT-FIRST MODE: If student asked for a diagram, include a clean blueprint SVG diagram showing the triangle with vertices A, B, C, 90° right angle symbol, angle θ, and sides Base, Perpendicular, Hypotenuse."



                system_prompt += (

                    f"\n\n{'='*50}\n"

                    f"EDUCATIONAL VISUAL DIAGRAM DIRECTIVE (ONLY IF STUDENT EXPLICITLY ASKED FOR DIAGRAM/VISUAL):\n"

                    f"{'='*50}\n"

                    f"The student asked for a visual diagram of: '{req.question}'.\n"

                    f"You MUST include a clean, complete, valid SVG diagram wrapped in a ```svg ... ``` code block right at the beginning of your explanation.\n"

                    f"{mode_visual_cue}\n"

                    f"SVG styling guidelines: viewBox='0 0 340 210', dark card rect fill='#0f172a' rx='10'. Triangle vertices A(50,160), B(240,160 90°), C(240,40). Labels: Base(b) at x='145' y='185' text-anchor='middle', Perpendicular(p) at x='252' y='105' (outside vertical leg), Hypotenuse(h) at x='125' y='90' transform='rotate(-32, 125, 90)'. STRICTLY ZERO TEXT OVERLAP.\n"

                    f"STRICTLY NO ASCII drawings.\n"

                )



        # Build final messages

        messages, sources, used_rag = build_messages(

            req=req,

            system_prompt=system_prompt,

        )



        # Call Groq with selected model
        is_adm = getattr(req, "is_admin", False)
        answer = call_groq(messages, model=req.model, is_admin=is_adm)



        # Fail-safe Sports Mode Guarantee: If sports mode was requested but model used ladder/wall, replace with pristine cricket explanation

        # Preserved contextual multi-theme response (Football, Cricket, Badminton, Car, etc.)
        # Fail-safe Visual Diagram Guarantee: Ensure student ALWAYS receives a visual diagram

        if is_visual_topic and '<svg' not in answer and '<img' not in answer:
            is_trig = bool(re.search(r'\b(trig|sin|cos|tan|hypotenuse|angle|triangle)\b', q_lower))
            if is_trig:
                answer = f"{FALLBACK_SVG_RIGHT_TRIANGLE}\n\n{answer}"
            elif wants_sports:
                answer = f"{FALLBACK_SVG_SPORTS_PARABOLA}\n\n{answer}"
            else:
                answer = f"{FALLBACK_SVG_RIGHT_TRIANGLE}\n\n{answer}"

        if badge_markdown:


            # Strip any leading blockquote or note lines generated by LLM (NCERT Reference, Textbook link, or Note)

            answer = re.sub(r'^(?:>\s*[^\n]*(?:NCERT|Textbook|Note|ℹ️)[^\n]*\n*)+', '', answer, flags=re.IGNORECASE).strip()

            answer = re.sub(r'^(?:\*\(?ℹ️[^\n]*\)?\*\n*)+', '', answer, flags=re.IGNORECASE).strip()

            answer = f"{badge_markdown}\n\n{answer}"



        return TutorResponse(

            answer=answer,

            question_type=question_type,

            explanation_style=explanation_style,

            used_rag=used_rag,

            sources=sources,

            prompt_version=PROMPT_VERSION,

            model=req.model or GROQ_MODEL or "llama-3.3-70b-versatile",

            error=None,

        )



    except Exception as error:
        err_msg = str(error)
        print(f"[Tutor Error Exception]: {type(error).__name__} - {err_msg}")
        import traceback
        traceback.print_exc()

        # Friendly recovery message adapted to language without revealing raw internal traces
        is_hinglish = any(w in req.question.lower() for w in ["kya", "kaise", "batao", "samjhao", "hai", "hota", "karo"])
        if is_hinglish:
            friendly_answer = (
                "Maaf kijiye, abhi AI server response me temporary delay ya issue aa gaya hai. "
                "Aap kripya **Retry** button par click karein ya apna sawal dobara bhejein, main turant solve karne ki koshish karunga! 🔄📐"
            )
        else:
            friendly_answer = (
                "I apologize, but there was a temporary delay connecting to the AI inference service. "
                "Please click **Retry** or ask your question again, and I will be happy to solve it for you! 🔄📐"
            )

        return TutorResponse(
            answer=friendly_answer,
            question_type=detect_question_type(req.question),
            explanation_style=detect_style(req.question, req.explanation_style),
            used_rag=False,
            sources=[],
            prompt_version=PROMPT_VERSION,
            model=req.model or GROQ_MODEL or "openai/gpt-oss-120b",
            error=f"{type(error).__name__}: {err_msg}",
        )
