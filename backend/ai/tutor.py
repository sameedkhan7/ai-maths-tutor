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

<svg viewBox="0 0 380 220" width="100%" xmlns="http://www.w3.org/2000/svg" class="math-svg-diagram">

  <rect width="100%" height="100%" fill="#090d16" rx="12"/>

  <rect x="0" y="170" width="380" height="50" fill="#064e3b"/>

  <line x1="10" y1="170" x2="370" y2="170" stroke="#10b981" stroke-width="2"/>

  <rect x="30" y="170" width="70" height="12" fill="#78350f" opacity="0.6"/>

  <circle cx="50" cy="170" r="5" fill="#f43f5e"/>

  <text x="50" y="196" fill="#f8fafc" font-size="11.5" font-weight="bold" text-anchor="middle">🏏 Batsman (A)</text>

  <line x1="50" y1="170" x2="260" y2="170" stroke="#38bdf8" stroke-width="2.5"/>

  <line x1="260" y1="170" x2="260" y2="45" stroke="#f43f5e" stroke-width="2.5" stroke-dasharray="5,4"/>

  <line x1="50" y1="170" x2="260" y2="45" stroke="#fbbf24" stroke-width="3"/>

  <path d="M 50,170 Q 155,10 260,45" fill="none" stroke="rgba(251, 191, 36, 0.4)" stroke-width="2" stroke-dasharray="4,4"/>

  <circle cx="260" cy="45" r="7" fill="#ef4444" stroke="#ffffff" stroke-width="1.5"/>

  <text x="260" y="32" fill="#f87171" font-size="11.5" font-weight="bold" text-anchor="middle">⚾ Ball at Height (C)</text>

  <path d="M 245,170 L 245,155 L 260,155" fill="none" stroke="#f43f5e" stroke-width="2"/>

  <path d="M 78,170 A 28 28 0 0 0 74,152" fill="none" stroke="#38bdf8" stroke-width="2.5"/>

  <text x="86" y="162" fill="#38bdf8" font-size="12" font-weight="bold">θ</text>

  <circle cx="260" cy="170" r="4" fill="#10b981"/>

  <rect x="285" y="152" width="85" height="26" rx="6" fill="#1e293b" stroke="#10b981" stroke-width="1.5"/>

  <text x="327" y="169" fill="#10b981" font-size="11" font-weight="bold" text-anchor="middle">6️⃣ Boundary (B)</text>

  <text x="140" y="95" fill="#fbbf24" font-size="11.5" font-weight="bold" transform="rotate(-31, 140, 95)">Flight Path (h)</text>

  <text x="272" y="105" fill="#f43f5e" font-size="11.5" font-weight="bold">Height (p)</text>

  <text x="155" y="188" fill="#38bdf8" font-size="11.5" font-weight="bold" text-anchor="middle">Ground Distance (b)</text>

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

            from backend.ai.guardrails import inspect_guardrails

        except ImportError:

            from ai.guardrails import inspect_guardrails



        history_len = len(req.chat_history) if req.chat_history else 0

        is_allowed, guard_reply = inspect_guardrails(req.question, chat_history_len=history_len)



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

                        # Generate direct official NCERT PDF link

                        ch_no = rag_res.get("chapter_no")

                        matched_class_name = rag_res.get("matched_class", "Class 10")

                        book_codes = {"Class 9": "iemh1", "Class 10": "jemh1", "Class 11": "kemh1", "Class 12": "lemh1"}

                        pdf_link_md = ""

                        if ch_no and matched_class_name in book_codes:

                            b_code = book_codes[matched_class_name]

                            pdf_url = f"https://ncert.nic.in/textbook/pdf/{b_code}{int(ch_no):02d}.pdf"

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

        lang_str = (req.language or "hinglish").strip().lower()



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

   - For Calculus/Derivatives: Explain using a Footballer / Striker taking a curved free-kick or penalty kick. The ball flight curve is s(t). The derivative is the instantaneous kick speed v(t) = s'(t) = lim_{h->0} [s(t+h) - s(t)] / h (the tangent line slope to the ball trajectory as it curls into the top-corner of the goal net).

   - For Trigonometry: Striker shooting towards the top corner of the goal net at elevation angle theta θ. Crossbar height is Perpendicular p, distance from penalty spot to goal line is Base b, direct flight trajectory is Hypotenuse h.

2. Include a clean SVG diagram showing the Football Pitch, Striker kicking, goalpost, and ball trajectory!

"""

            elif active_theme == "badminton":

                sports_directive = """



STRICT CONTEXT THEME DIRECTIVE — BADMINTON (HIGHEST PRIORITY):

The student asked for BADMINTON!

1. EXPLAIN 100% USING BADMINTON: Player executing a jump smash over the net. Shuttlecock trajectory dipping steeply into opponent court. Instantaneous smash speed is derivative v(t) = s'(t).

2. Include Badminton Court SVG diagram with player, net, and shuttlecock path!

"""

            elif active_theme == "car":

                sports_directive = """



STRICT CONTEXT THEME DIRECTIVE — CAR RACING & SPEEDOMETER (HIGHEST PRIORITY):

The student asked for CAR DRIVING / RACING!

1. EXPLAIN 100% USING A RACING CAR: Car accelerating along highway track. Speedometer needle shows instantaneous speed v(t) = ds/dt at that exact second. Distance vs time curve s(t).

2. Include Car / Speedometer SVG diagram!

"""

            elif active_theme == "coding":

                sports_directive = """



STRICT CONTEXT THEME DIRECTIVE — CODING & GAME PHYSICS (HIGHEST PRIORITY):

The student asked for CODING / GAMING!

1. EXPLAIN USING GAME DEVELOPMENT: Frame delta time (dt), player velocity update (position += velocity * dt), and physics engine collision calculations.

"""

            else:

                sports_directive = """



STRICT CONTEXT THEME DIRECTIVE — CRICKET (HIGHEST PRIORITY):

The student asked for CRICKET!

1. EXPLAIN 100% USING CRICKET: Batsman hitting a lofted shot / sixer over the boundary rope.

   - For Calculus: Ball flight trajectory s(t) and instantaneous velocity tangent line v(t) = s'(t).

   - For Trigonometry: Launch angle θ at bat, flight path h, ball height p, ground distance to boundary b.

2. Include the Cricket Stadium SVG diagram showing pitch, batsman in action, and boundary!

"""



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
        is_visual_topic = has_explicit_visual_word or (explanation_style == "visual")



        if is_visual_topic:

            if active_theme == "football":

                system_prompt += (

                    f"\n\n{'='*50}\n"

                    f"MANDATORY FOOTBALL SVG DIAGRAM & VISUALIZATION (STRICT):\n"

                    f"{'='*50}\n"

                    f"The student explicitly asked for FOOTBALL visualization!\n"

                    f"1. Provide a Football Stadium SVG diagram showing the green turf, striker kicking the ball, goalpost net, and ball trajectory curve s(t) with tangent kick speed v(t)!\n"

                    f"2. EXPLANATION MUST BE 100% FOOTBALL BASED: Do NOT mention cricket, pitch, or batsman!\n"

                    f"{'='*50}\n"

                )

            elif active_theme == "badminton":

                system_prompt += (

                    f"\n\n{'='*50}\n"

                    f"MANDATORY BADMINTON SVG DIAGRAM & VISUALIZATION (STRICT):\n"

                    f"{'='*50}\n"

                    f"1. Provide a Badminton Court SVG diagram showing the net, player jump smash, and shuttlecock trajectory!\n"

                    f"2. EXPLANATION MUST BE 100% BADMINTON BASED!\n"

                    f"{'='*50}\n"

                )

            elif active_theme == "car":

                system_prompt += (

                    f"\n\n{'='*50}\n"

                    f"MANDATORY CAR RACING SVG DIAGRAM & VISUALIZATION (STRICT):\n"

                    f"{'='*50}\n"

                    f"1. Provide a Sports Car and Speedometer HUD SVG diagram!\n"

                    f"2. EXPLANATION MUST BE 100% CAR / DRIVING BASED!\n"

                    f"{'='*50}\n"

                )

            elif active_theme == "cricket":

                system_prompt += (

                    f"\n\n{'='*50}\n"

                    f"MANDATORY CRICKET SPORTS SVG DIAGRAM & VISUALIZATION (STRICT):\n"

                    f"{'='*50}\n"

                    f"1. Provide the Cricket Stadium SVG diagram showing the pitch, batsman hitting the shot, and ball trajectory!\n"

                    f"2. EXPLANATION MUST BE 100% CRICKET BASED!\n"

                    f"{'='*50}\n"

                )

            else:

                mode_visual_cue = ""

                if explanation_style == "story":

                    mode_visual_cue = "In STORY MODE: Show the story scenario in SVG (e.g. lighthouse/tower, elevation angle θ, distance to ship/ground)."

                elif explanation_style == "step_by_step":

                    mode_visual_cue = "In STEP-BY-STEP MODE: Show a clean labeled SVG diagram at the start, then explicitly reference its vertices/sides in Step 1, Step 2, Step 3."

                elif explanation_style == "quick":

                    mode_visual_cue = "In QUICK MODE: Include a compact, clean SVG diagram alongside the boxed formula."

                else:

                    mode_visual_cue = "In CONCEPT-FIRST MODE: Include a clean blueprint SVG diagram showing the triangle with vertices A, B, C, 90° right angle symbol, angle θ, and sides Base, Perpendicular, Hypotenuse."



                system_prompt += (

                    f"\n\n{'='*50}\n"

                    f"MANDATORY EDUCATIONAL VISUAL DIAGRAM DIRECTIVE:\n"

                    f"{'='*50}\n"

                    f"The student is asking about a visual mathematical topic: '{req.question}'.\n"

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

        answer = call_groq(messages, model=req.model)



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

            import re

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

        print(f"[Tutor Error Exception]: {error}")

        import traceback

        traceback.print_exc()



        return TutorResponse(

            answer="Sorry, I could not generate the answer right now.",

            question_type=detect_question_type(req.question),

            explanation_style=detect_style(req.question, req.explanation_style),

            used_rag=False,

            sources=[],

            prompt_version=PROMPT_VERSION,

            model=req.model or GROQ_MODEL or "llama-3.3-70b-versatile",

            error=str(error),

        )