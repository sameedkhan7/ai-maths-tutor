"""
NCERT & CBSE MCP Server
Model Context Protocol (MCP) server for live NCERT textbook lookup and CBSE curriculum verification.
Supports: Class 9, 10, 11, and 12 Mathematics.
"""

import json

try:
    from mcp.server.mcpserver import MCPServer
except ImportError:
    from mcp.server.fastmcp import FastMCP as MCPServer

# 1. Initialize MCP Server instance
mcp = MCPServer("NCERT-CBSE-Tutor-Service")

# Official NCERT Class & Book Codes for Mathematics
NCERT_CATALOG = {
    "9": {
        "title": "NCERT Class 9 Mathematics",
        "code": "iemh1",
        "chapters": {
            1: "Number Systems",
            2: "Polynomials",
            3: "Coordinate Geometry",
            4: "Linear Equations in Two Variables",
            5: "Introduction to Euclid's Geometry",
            6: "Lines and Angles",
            7: "Triangles",
            8: "Quadrilaterals",
            9: "Circles",
            10: "Heron's Formula",
            11: "Surface Areas and Volumes",
            12: "Statistics"
        }
    },
    "10": {
        "title": "NCERT Class 10 Mathematics",
        "code": "jemh1",
        "chapters": {
            1: "Real Numbers",
            2: "Polynomials",
            3: "Pair of Linear Equations in Two Variables",
            4: "Quadratic Equations",
            5: "Arithmetic Progressions",
            6: "Triangles",
            7: "Coordinate Geometry",
            8: "Introduction to Trigonometry",
            9: "Some Applications of Trigonometry",
            10: "Circles",
            11: "Areas Related to Circles",
            12: "Surface Areas and Volumes",
            13: "Statistics",
            14: "Probability"
        }
    },
    "11": {
        "title": "NCERT Class 11 Mathematics",
        "code": "kemh1",
        "chapters": {
            1: "Sets",
            2: "Relations and Functions",
            3: "Trigonometric Functions",
            4: "Complex Numbers and Quadratic Equations",
            5: "Linear Inequalities",
            6: "Permutations and Combinations",
            7: "Binomial Theorem",
            8: "Sequences and Series",
            9: "Straight Lines",
            10: "Conic Sections",
            11: "Introduction to Three Dimensional Geometry",
            12: "Limits and Derivatives",
            13: "Statistics",
            14: "Probability"
        }
    },
    "12": {
        "title": "NCERT Class 12 Mathematics Part 1 & 2",
        "code": "lemh1",
        "chapters": {
            1: "Relations and Functions",
            2: "Inverse Trigonometric Functions",
            3: "Matrices",
            4: "Determinants",
            5: "Continuity and Differentiability",
            6: "Application of Derivatives",
            7: "Integrals",
            8: "Application of Integrals",
            9: "Differential Equations",
            10: "Vector Algebra",
            11: "Three Dimensional Geometry",
            12: "Linear Programming",
            13: "Probability"
        }
    }
}


# ==========================================
# TOOL 1: Get Chapter Info and Official PDF URL
# ==========================================
@mcp.tool()
def build_ncert_pdf_url(clean_cls: str, chapter_num: int) -> str:
    """Accurately generates official NCERT textbook PDF URL, including Class 12 Part 1 & 2."""
    if clean_cls == "9" and 1 <= chapter_num <= 12:
        return f"https://ncert.nic.in/textbook/pdf/iemh1{chapter_num:02d}.pdf"
    elif clean_cls == "10" and 1 <= chapter_num <= 14:
        return f"https://ncert.nic.in/textbook/pdf/jemh1{chapter_num:02d}.pdf"
    elif clean_cls == "11" and 1 <= chapter_num <= 14:
        return f"https://ncert.nic.in/textbook/pdf/kemh1{chapter_num:02d}.pdf"
    elif clean_cls == "12":
        if 1 <= chapter_num <= 6:
            return f"https://ncert.nic.in/textbook/pdf/lemh1{chapter_num:02d}.pdf"
        elif 7 <= chapter_num <= 13:
            part2_ch = chapter_num - 6
            return f"https://ncert.nic.in/textbook/pdf/lemh2{part2_ch:02d}.pdf"
    return f"https://ncert.nic.in/textbook/pdf/{NCERT_CATALOG.get(clean_cls, {}).get('code', 'jemh1')}{chapter_num:02d}.pdf"

def get_ncert_chapter_info(class_num: str, chapter_num: int) -> str:
    """
    Returns official chapter details and direct NCERT official PDF textbook link.
    Example: class_num="10", chapter_num=8
    """
    clean_cls = str(class_num).strip().replace("Class ", "")
    if clean_cls not in NCERT_CATALOG:
        return json.dumps({
            "status": "error",
            "message": f"Class {clean_cls} not found. Available classes: 9, 10, 11, 12."
        })

    cat = NCERT_CATALOG[clean_cls]
    ch_title = cat["chapters"].get(chapter_num, f"Chapter {chapter_num}")
    pdf_url = build_ncert_pdf_url(clean_cls, chapter_num)

    return json.dumps({
        "status": "success",
        "class": f"Class {clean_cls}",
        "book": cat["title"],
        "chapter_number": chapter_num,
        "chapter_title": ch_title,
        "official_pdf_url": pdf_url,
        "source": "Official NCERT Textbook Portal (ncert.nic.in)"
    }, indent=2)


# ==========================================
# TOOL 2: List All Chapters in a Class
# ==========================================
@mcp.tool()
def list_ncert_chapters(class_num: str) -> str:
    """
    Returns complete table of contents for an NCERT class.
    Example: class_num="10"
    """
    clean_cls = str(class_num).strip().replace("Class ", "")
    if clean_cls not in NCERT_CATALOG:
        return json.dumps({"status": "error", "message": f"Class {clean_cls} not found."})

    cat = NCERT_CATALOG[clean_cls]
    return json.dumps({
        "status": "success",
        "class": f"Class {clean_cls}",
        "book": cat["title"],
        "total_chapters": len(cat["chapters"]),
        "chapters": [{"number": k, "title": v} for k, v in cat["chapters"].items()]
    }, indent=2)


# ==========================================
# TOOL 3: Verify CBSE Curriculum & Deleted Topics
# ==========================================
@mcp.tool()
def check_cbse_curriculum(class_num: str, topic: str) -> str:
    """
    Checks if a topic is active in the latest CBSE Rationalized Syllabus or deleted.
    Example: class_num="10", topic="Euclid's division lemma"
    """
    clean_cls = str(class_num).strip().replace("Class ", "")
    t = topic.lower()

    # Rationalized / Deleted Content knowledge base
    if clean_cls == "10":
        if "euclid" in t or "division lemma" in t:
            return json.dumps({
                "status": "deleted",
                "topic": topic,
                "curriculum": "CBSE Class 10 (Rationalized 2024-2026)",
                "note": "Euclid's Division Lemma (Ex 1.1) has been removed from NCERT Class 10. Start directly with Fundamental Theorem of Arithmetic (Prime Factorisation)."
            })
        if "frustum" in t:
            return json.dumps({
                "status": "deleted",
                "topic": topic,
                "curriculum": "CBSE Class 10",
                "note": "Frustum of a Cone (Surface Areas & Volumes) has been deleted from Class 10 syllabus."
            })
        if "cross-multiplication" in t or "cross multiplication" in t:
            return json.dumps({
                "status": "deleted",
                "topic": topic,
                "curriculum": "CBSE Class 10",
                "note": "Cross-multiplication method for linear equations has been removed. Use Substitution or Elimination."
            })

    return json.dumps({
        "status": "active",
        "topic": topic,
        "class": f"Class {clean_cls}",
        "curriculum": "CBSE Official Curriculum",
        "note": f"Topic '{topic}' is part of the standard active CBSE Mathematics syllabus."
    })


# Helper function for direct Python calls from FastAPI tutor
def fetch_ncert_context_for_query(query: str, student_grade: str = "Class 10") -> dict:
    """
    Quick helper for FastAPI backend to fetch NCERT context without starting subprocess.
    Supports explicit class detection and ordinal chapter number queries (e.g. 'first chapter').
    """
    import re
    q_lower = query.lower()
    
    # Check explicit class in query
    class_match = re.search(r'\b(?:class|grade|kaksha)\s*(9|10|11|12)(?:th)?\b|\b(9|10|11|12)(?:th)?\s*(?:class|grade|kaksha)\b', q_lower)
    if class_match:
        c_num = class_match.group(1) or class_match.group(2)
        clean_cls = c_num
    else:
        clean_cls = str(student_grade).strip().replace("Class ", "")
        
    if clean_cls not in NCERT_CATALOG:
        clean_cls = "10"
        
    cat = NCERT_CATALOG[clean_cls]
    matched_chapter = None
    
    # Ordinal chapter numbers map
    ordinal_map = {
        "first": 1, "1st": 1, "one": 1, "pehla": 1, "1": 1,
        "second": 2, "2nd": 2, "two": 2, "dusra": 2, "doosra": 2, "2": 2,
        "third": 3, "3rd": 3, "three": 3, "teesra": 3, "3": 3,
        "fourth": 4, "4th": 4, "four": 4, "chautha": 4, "4": 4,
        "fifth": 5, "5th": 5, "five": 5, "panchwa": 5, "5": 5,
        "sixth": 6, "6th": 6, "six": 6, "chatha": 6, "6": 6,
        "seventh": 7, "7th": 7, "seven": 7, "saatwa": 7, "7": 7,
        "eighth": 8, "8th": 8, "eight": 8, "aathwa": 8, "8": 8,
        "ninth": 9, "9th": 9, "nine": 9, "nauwa": 9, "9": 9,
        "tenth": 10, "10th": 10, "ten": 10, "daswa": 10, "10": 10,
        "eleventh": 11, "11th": 11, "11": 11,
        "twelfth": 12, "12th": 12, "12": 12,
        "thirteenth": 13, "13th": 13, "13": 13,
        "fourteenth": 14, "14th": 14, "14": 14,
    }
    
    # 1. Match numeric chapter X
    ch_num_match = re.search(r'\bchapter\s*([0-9]{1,2})\b', q_lower)
    target_num = None
    if ch_num_match:
        target_num = int(ch_num_match.group(1))
    else:
        for word, num in ordinal_map.items():
            if re.search(r'\b' + re.escape(word) + r'\s*(?:chapter|adheyaay|paath)?\b', q_lower):
                if any(k in q_lower for k in ["chapter", "adheyaay", "paath", "pehla", "first", "1st", "dusra", "2nd"]):
                    target_num = num
                    break

    if target_num and target_num in cat["chapters"]:
        matched_chapter = (target_num, cat["chapters"][target_num])

    # 2. Match curated math concept & topic synonyms (handles phonetic & sub-chapter concepts)
    NCERT_TOPIC_ALIASES = {
        "10": [
            (6, "Triangles", ["pythagoras", "pytha gouras", "pytha", "prama", "pramin", "prameya", "thales", "bpt", "similarity"]),
            (8, "Introduction to Trigonometry", ["trigonometry", "trigo", "sin cos tan", "sin theta", "cos theta", "tan theta", "trigonometric ratio", "trig identity"]),
            (9, "Some Applications of Trigonometry", ["heights and distances", "elevation", "depression", "line of sight", "tower shadow"]),
            (4, "Quadratic Equations", ["quadratic", "shridharacharya", "roots of quadratic", "b^2 - 4ac", "discriminant"]),
            (5, "Arithmetic Progressions", ["arithmetic progression", "difine ap", "what is ap", "common difference", "nth term of ap"]),
            (3, "Pair of Linear Equations in Two Variables", ["linear equations", "elimination method", "substitution method"]),
            (1, "Real Numbers", ["euclid", "prime factorisation", "irrational number proof", "hcf", "lcm"]),
        ],
        "11": [
            (12, "Limits and Derivatives", ["limit", "limits", "derivative", "derivatives", "differentiate", "dy/dx", "first principle", "power rule"]),
            (3, "Trigonometric Functions", ["trigonometric functions", "radian", "compound angles", "double angle"]),
            (10, "Conic Sections", ["parabola", "ellipse", "hyperbola", "conic"]),
            (1, "Sets", ["sets", "subset", "venn diagram"]),
        ],
        "12": [
            (5, "Continuity and Differentiability", ["derivative", "derivatives", "differentiate", "differentiation", "continuity", "differentiability", "dy/dx", "chain rule", "logarithmic differentiation", "avkalana", "अवकलन"]),
            (6, "Application of Derivatives", ["rate of change", "tangent", "normal", "maxima", "minima", "increasing decreasing", "optimization"]),
            (7, "Integrals", ["integral", "integrals", "integration", "antiderivative", "samakalan", "समाकलन", "by parts"]),
            (3, "Matrices", ["matrix", "matrices", "transpose", "symmetric matrix"]),
            (4, "Determinants", ["determinant", "determinants", "cramer"]),
            (9, "Differential Equations", ["differential equation", "differential equations", "degree and order"]),
            (10, "Vector Algebra", ["vector", "vectors", "cross product", "dot product"]),
            (11, "Three Dimensional Geometry", ["3d geometry", "direction cosines", "plane equation", "line in space"]),
        ]
    }

    # First check aliases for the current selected class
    if not matched_chapter and clean_cls in NCERT_TOPIC_ALIASES:
        for ch_num, ch_title, aliases in NCERT_TOPIC_ALIASES[clean_cls]:
            if any(alias in q_lower for alias in aliases):
                matched_chapter = (ch_num, ch_title)
                break

    # If still not matched, check other classes for topic alias (cross-class fallback)
    matched_cls_final = clean_cls
    if not matched_chapter:
        for other_cls, alias_list in NCERT_TOPIC_ALIASES.items():
            if other_cls != clean_cls:
                for ch_num, ch_title, aliases in alias_list:
                    if any(alias in q_lower for alias in aliases):
                        matched_chapter = (ch_num, ch_title)
                        matched_cls_final = other_cls
                        break
                if matched_chapter:
                    break

    # 3. Match chapter title keywords fallback
    if not matched_chapter:
        for ch_num, ch_title in cat["chapters"].items():
            words = [w.lower() for w in ch_title.split() if len(w) > 3]
            if any(w in q_lower for w in words):
                matched_chapter = (ch_num, ch_title)
                break
                
    if matched_chapter:
        pdf_link = build_ncert_pdf_url(matched_cls_final, matched_chapter[0])
        return {
            "found": True,
            "class": f"Class {matched_cls_final}",
            "chapter_number": matched_chapter[0],
            "chapter_title": matched_chapter[1],
            "official_link": pdf_link
        }
    return {"found": False}


if __name__ == "__main__":
    print("[*] Starting NCERT & CBSE MCP Server on stdio...")
    mcp.run()
