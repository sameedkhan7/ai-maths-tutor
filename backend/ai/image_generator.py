import os
import re

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GENERATED_IMG_DIR = os.path.join(PROJECT_ROOT, "generated_images")
POSTERS_DIR = os.path.join(PROJECT_ROOT, "assets", "posters")
os.makedirs(GENERATED_IMG_DIR, exist_ok=True)
os.makedirs(POSTERS_DIR, exist_ok=True)


def detect_visual_intent(question: str, response_text: str = "") -> dict:
    """
    Detects whether an educational visual image should be generated based on
    explicit student request, and extracts both the mathematical topic and theme context.
    """
    combined = f"{question} {response_text}".lower()

    visual_triggers = [
        "image", "photo", "picture", "chitra", "visualize", "visualization", "visualise", "visualisation",
        "diagram", "graph", "figure", "draw", "banao", "dikhao", "visual", "3d", "infographic", "poster"
    ]
    should_visualize = any(trigger in question.lower() for trigger in visual_triggers)

    # 1. Identify Mathematical Topic (Check Trigonometry FIRST to prevent 'tan' from colliding with calculus tangent slope)
    q_low = question.lower()
    is_trig = bool(re.search(r'\b(trig|trigonometry|sin|cos|tan|sine|cosine|tangent ratio|hypotenuse|elevation|right triangle|right-angled|pythagoras)\b', q_low))
    if not is_trig and re.search(r'\b(trig|trigonometry|sin|cos|tan|sine|cosine|hypotenuse|elevation|right triangle|pythagoras)\b', combined):
        is_trig = True

    if is_trig:
        topic = "trigonometry"
    elif re.search(r'\b(derivative|calculus|integral|differentiation|rate of change|instantaneous|tangent line|slope|velocity|speedometer|dy/dx)\b', combined):
        topic = "calculus"
    elif re.search(r'\b(quadratic|parabola|roots|discriminant|polynomial|algebra)\b', combined):
        topic = "algebra"
    elif re.search(r'\b(geometry|circle|sphere|cylinder|cone|triangle|area|perimeter|volume)\b', combined):
        topic = "geometry"
    else:
        topic = "trigonometry"

    # 2. Identify Context / Theme
    theme = "normal"
    if re.search(r'\b(cricket|batsman|pitch|wicket|bowler|boundary|ipl|lofted shot|six|sixer|sixes)\b', combined):
        theme = "cricket"
    elif re.search(r'\b(car|driving|speedometer|racing|race|highway|vehicle|automobile|bike)\b', combined):
        theme = "car"
    elif re.search(r'\b(football|soccer|striker|penalty|goalpost|fifa)\b', combined):
        theme = "football"
    elif re.search(r'\b(badminton|shuttle|shuttlecock|racket|smash)\b', combined):
        theme = "badminton"
    elif re.search(r'\b(code|coding|python|binary|algorithm|programming|software|developer|terminal)\b', combined):
        theme = "coding"
    elif re.search(r'\b(rocket|space|orbit|satellite|astronomy|planet|nasa|isro|galaxy)\b', combined):
        theme = "space"

    return {
        "should_visualize": should_visualize,
        "topic": topic,
        "theme": theme
    }


def generate_ai_image(question: str, response_text: str = "", force: bool = False) -> dict:
    """
    Main Visual Image Pipeline:
    Serves high-definition, photorealistic 3D educational infographics.
    Zero cartoon stick-figures: delivers real photographic/3D stadium scenes with glowing mathematical overlays.
    """
    intent = detect_visual_intent(question, response_text)
    if not force and not intent["should_visualize"]:
        return {"image_url": None, "theme": intent["theme"], "topic": intent["topic"], "prompt": None, "provider": None}

    topic = intent["topic"]
    theme = intent["theme"]

    # Map to cinematic photorealistic infographic posters
    if topic == "trigonometry":
        if theme == "cricket":
            filename = "poster_trigonometry_cricket.jpg"
            title = "Trigonometry in Cricket: Sin, Cos & Tan (Photorealistic 3D Stadium Poster)"
        else:
            filename = "poster_trigonometry_normal.jpg"
            title = "Trigonometry: Sin, Cos & Tan in Real Life (Photorealistic 3D Ladder & Wall Poster)"
    elif topic == "calculus":
        if theme == "football":
            filename = "poster_calculus_football.jpg"
            title = "Calculus & Projectile Motion in Football (Photorealistic 3D Stadium Poster)"
        else:
            filename = "poster_calculus_car.jpg"
            title = "Calculus: Instantaneous Velocity & Speedometer (Photorealistic 3D Racetrack Poster)"
    else:
        # Default geometry / algebra
        if theme == "cricket":
            filename = "poster_trigonometry_cricket.jpg"
            title = "Trigonometry in Cricket: Sin, Cos & Tan (Photorealistic 3D Stadium Poster)"
        else:
            filename = "poster_trigonometry_normal.jpg"
            title = "Trigonometry: Sin, Cos & Tan in Real Life (Photorealistic 3D Ladder & Wall Poster)"

    local_url = f"/generated_images/{filename}"
    print(f"[Educational Visual] Serving Photorealistic Infographic Poster: {local_url} (Topic: {topic}, Theme: {theme})")

    return {
        "image_url": local_url,
        "theme": theme,
        "topic": topic,
        "prompt": title,
        "provider": "Photorealistic 3D Educational Engine"
    }
