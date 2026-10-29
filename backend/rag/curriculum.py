
ORDINAL_CHAPTER_MAP = {
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

def extract_chapter_number_from_query(q_lower: str):
    m = re.search(r'\bchapter\s*([0-9]{1,2})\b', q_lower)
    if m:
        return int(m.group(1))
    for word, num in ORDINAL_CHAPTER_MAP.items():
        if re.search(r'\b' + re.escape(word) + r'\s*(?:chapter|adheyaay|paath)?\b', q_lower):
            if any(k in q_lower for k in ["chapter", "adheyaay", "paath", "pehla", "first", "1st", "dusra", "2nd"]):
                return num
    return None

def extract_explicit_class_from_query(q_lower: str):
    m = re.search(r'\b(?:class|grade|kaksha)\s*(9|10|11|12)(?:th)?\b|\b(9|10|11|12)(?:th)?\s*(?:class|grade|kaksha)\b', q_lower)
    if m:
        c = m.group(1) or m.group(2)
        return f"Class {c}"
    return None

"""
backend/rag/curriculum.py — Official NCERT Mathematics Syllabus Knowledge Graph
Covers Classes 9, 10, 11, and 12 with comprehensive chapter mapping, key topics,
and lightning-fast class-priority search.
"""

import re
from typing import Optional, Dict, Any, List

NCERT_CURRICULUM = {
    "Class 9": [
        {
            "chapter_no": 1,
            "title": "Number Systems",
            "keywords": ["number system", "rational number", "irrational number", "real number", "terminating", "non-terminating", "repeating decimal", "number line", "laws of exponents", "surd", "radicals"],
            "summary": "Covers rational and irrational numbers, representation of real numbers on the number line, operations on real numbers, and laws of exponents."
        },
        {
            "chapter_no": 2,
            "title": "Polynomials",
            "keywords": ["polynomial", "zero of polynomial", "degree of polynomial", "monomial", "binomial", "trinomial", "remainder theorem", "factor theorem", "factorisation", "algebraic identities"],
            "summary": "Definition of polynomials in one variable, coefficients, zeroes, Remainder Theorem, Factor Theorem, and standard algebraic identities."
        },
        {
            "chapter_no": 3,
            "title": "Coordinate Geometry",
            "keywords": ["coordinate geometry", "cartesian plane", "x-axis", "y-axis", "origin", "quadrant", "abscissa", "ordinate", "coordinates", "ordered pair"],
            "summary": "Cartesian plane, coordinates of a point, names and terms associated with the coordinate plane, notations, plotting points in the plane."
        },
        {
            "chapter_no": 4,
            "title": "Linear Equations in Two Variables",
            "keywords": ["linear equation in two variables", "ax + by + c = 0", "graph of linear equation", "solutions of linear equation"],
            "summary": "Introduction to the equation in two variables: ax + by + c = 0. Infinitely many solutions, graph of a linear equation."
        },
        {
            "chapter_no": 5,
            "title": "Introduction to Euclid's Geometry",
            "keywords": ["euclid", "euclidean geometry", "axiom", "postulate", "theorem", "fifth postulate"],
            "summary": "History of geometry in India and Greece, Euclid's method of formalizing geometry through undefined terms, axioms, and 5 postulates."
        },
        {
            "chapter_no": 6,
            "title": "Lines and Angles",
            "keywords": ["lines and angles", "acute angle", "obtuse angle", "right angle", "straight angle", "reflex angle", "complementary", "supplementary", "adjacent angles", "linear pair", "vertically opposite", "transversal", "alternate interior angles", "corresponding angles", "angle sum property"],
            "summary": "Basic terms and definitions, intersecting lines, pairs of angles, parallel lines and a transversal, angle sum property of a triangle."
        },
        {
            "chapter_no": 7,
            "title": "Triangles (Congruence)",
            "keywords": ["congruence of triangles", "congruent triangles", "sas congruence", "asa congruence", "aas congruence", "sss congruence", "rhs congruence", "isosceles triangle property", "inequalities in triangle"],
            "summary": "Congruence of triangles, criteria for congruence (SAS, ASA, SSS, RHS), properties of isosceles triangles, triangle inequalities."
        },
        {
            "chapter_no": 8,
            "title": "Quadrilaterals",
            "keywords": ["quadrilateral", "parallelogram", "rhombus", "rectangle", "square", "trapezium", "kite", "mid-point theorem", "midpoint theorem"],
            "summary": "Angle sum property of quadrilateral, properties of a parallelogram, conditions for a quadrilateral to be a parallelogram, Mid-point Theorem."
        },
        {
            "chapter_no": 9,
            "title": "Circles",
            "keywords": ["circle", "radius", "diameter", "chord", "arc", "subtended angle", "perpendicular from center to chord", "equal chords", "cyclic quadrilateral", "concyclic points"],
            "summary": "Circles and related terms, angle subtended by a chord, perpendicular from the centre to a chord, equal chords and their distances, cyclic quadrilaterals."
        },
        {
            "chapter_no": 10,
            "title": "Heron's Formula",
            "keywords": ["heron's formula", "heron formula", "semi-perimeter", "area of triangle with sides", "sqrt(s(s-a)(s-b)(s-c))"],
            "summary": "Area of a triangle using Heron's formula: Area = √[s(s-a)(s-b)(s-c)], application in finding areas of quadrilaterals."
        },
        {
            "chapter_no": 11,
            "title": "Surface Areas and Volumes",
            "keywords": ["surface area", "volume of cone", "volume of sphere", "hemisphere", "curved surface area", "total surface area"],
            "summary": "Surface areas and volumes of right circular cones, spheres, and hemispheres."
        },
        {
            "chapter_no": 12,
            "title": "Statistics",
            "keywords": ["statistics", "bar graph", "histogram", "frequency polygon", "mean", "median", "mode", "ungrouped data"],
            "summary": "Collection and presentation of data, graphical representation (bar graphs, histograms, frequency polygons), measures of central tendency."
        }
    ],

    "Class 10": [
        {
            "chapter_no": 1,
            "title": "Real Numbers",
            "keywords": ["real numbers", "euclid's division lemma", "fundamental theorem of arithmetic", "prime factorisation", "hcf", "lcm", "irrational number proof", "terminating decimal expansion"],
            "summary": "Fundamental Theorem of Arithmetic, statements of Euclid's division lemma, proofs of irrationality of √2, √3, √5, decimal expansions."
        },
        {
            "chapter_no": 2,
            "title": "Polynomials",
            "keywords": ["polynomials", "geometrical meaning of zeroes", "sum of zeroes", "product of zeroes", "alpha beta", "cubic polynomial", "division algorithm for polynomials"],
            "summary": "Geometrical meaning of zeroes of a polynomial, relationship between zeroes and coefficients of quadratic and cubic polynomials."
        },
        {
            "chapter_no": 3,
            "title": "Pair of Linear Equations in Two Variables",
            "keywords": ["pair of linear equations", "substitution method", "elimination method", "cross multiplication", "consistent", "inconsistent", "intersecting lines", "parallel lines", "coincident lines"],
            "summary": "Graphical and algebraic methods (substitution, elimination, cross-multiplication) for solving a pair of linear equations, consistency conditions."
        },
        {
            "chapter_no": 4,
            "title": "Quadratic Equations",
            "keywords": ["quadratic equation", "quadratic formula", "shreedharacharya", "discriminant", "nature of roots", "b^2 - 4ac", "distinct real roots", "equal roots", "factorisation method", "completing square"],
            "summary": "Standard form ax² + bx + c = 0, solution of quadratic equations by factorisation and by quadratic formula, discriminant and nature of roots."
        },
        {
            "chapter_no": 5,
            "title": "Arithmetic Progressions",
            "keywords": ["arithmetic progression", "ap", "common difference", "nth term", "first term", "sum of first n terms", "an = a + (n-1)d", "sn = n/2"],
            "summary": "Understanding AP, common difference d, nth term an = a + (n-1)d, sum of first n terms Sn = n/2 [2a + (n-1)d], real-world word problems."
        },
        {
            "chapter_no": 6,
            "title": "Triangles (Similarity & Pythagoras)",
            "keywords": ["similarity of triangles", "similar triangles", "thales theorem", "basic proportionality theorem", "bpt", "pythagoras", "pythagorean", "pythagoras theorem", "hypotenuse", "right-angled triangle", "a^2 + b^2 = c^2", "aaa similarity", "sas similarity", "sss similarity"],
            "summary": "Definitions and criteria for similarity of triangles (AAA, SSS, SAS), Basic Proportionality Theorem (Thales), Pythagoras Theorem and its converse."
        },
        {
            "chapter_no": 7,
            "title": "Coordinate Geometry",
            "keywords": ["distance formula", "section formula", "midpoint formula", "area of a triangle coordinate", "collinear points", "sqrt((x2-x1)^2 + (y2-y1)^2)"],
            "summary": "Distance formula between two points, Section formula (internal division), Midpoint formula, Area of triangle using coordinates."
        },
        {
            "chapter_no": 8,
            "title": "Introduction to Trigonometry",
            "keywords": ["trigonometry", "trigonometric ratios", "sin", "cos", "tan", "cot", "sec", "cosec", "sin^2 + cos^2 = 1", "trig identities", "trigonometric values", "t-ratios"],
            "summary": "Trigonometric ratios of acute angles in a right triangle, values of trigonometric ratios at 0°, 30°, 45°, 60°, 90°, fundamental identities: sin²θ + cos²θ = 1."
        },
        {
            "chapter_no": 9,
            "title": "Some Applications of Trigonometry",
            "keywords": ["heights and distances", "angle of elevation", "angle of depression", "line of sight", "horizontal level", "tower shadow"],
            "summary": "Simple problems on heights and distances involving line of sight, angle of elevation, and angle of depression using single or double right triangles."
        },
        {
            "chapter_no": 10,
            "title": "Circles",
            "keywords": ["tangent to circle", "point of contact", "radius perpendicular to tangent", "lengths of tangents from external point", "two tangents equal"],
            "summary": "Tangent to a circle, theorem that tangent is perpendicular to radius at point of contact, theorem that lengths of tangents from external point are equal."
        },
        {
            "chapter_no": 11,
            "title": "Areas Related to Circles",
            "keywords": ["area of circle", "sector of circle", "segment of circle", "minor sector", "major sector", "arc length", "theta/360"],
            "summary": "Area of sectors and segments of a circle, problems based on areas and perimeter/circumference of planar figures."
        },
        {
            "chapter_no": 12,
            "title": "Surface Areas and Volumes",
            "keywords": ["surface area of combination", "volume of combination", "solid sphere", "frustum of cone", "cylinder", "cone", "conversion of solids"],
            "summary": "Surface areas and volumes of combinations of cuboid, cone, cylinder, sphere, hemisphere; conversion of solids from one shape to another."
        },
        {
            "chapter_no": 13,
            "title": "Statistics",
            "keywords": ["mean of grouped data", "median of grouped data", "mode of grouped data", "assumed mean method", "step deviation", "ogive"],
            "summary": "Mean, median, and mode of grouped data (bimodal situation avoided), cumulative frequency distribution."
        },
        {
            "chapter_no": 14,
            "title": "Probability",
            "keywords": ["probability", "classical probability", "theoretical probability", "favourable outcomes", "deck of cards", "tossing coins", "rolling die", "p(e) + p(not e) = 1"],
            "summary": "Classical definition of probability, simple problems on finding probability of an event, complementary events."
        }
    ],

    "Class 11": [
        {
            "chapter_no": 1,
            "title": "Sets",
            "keywords": ["sets", "subset", "power set", "universal set", "venn diagram", "union of sets", "intersection of sets", "difference of sets", "complement of set", "de morgan's laws"],
            "summary": "Sets and their representations, empty set, finite and infinite sets, subsets, power set, universal set, Venn diagrams, operations on sets, De Morgan's laws."
        },
        {
            "chapter_no": 2,
            "title": "Relations and Functions",
            "keywords": ["cartesian product", "relation", "function", "domain", "codomain", "range", "identity function", "modulus function", "signum function", "greatest integer function"],
            "summary": "Cartesian product of sets, definition of relation, pictorial diagrams, domain, codomain, range; function as a special relation, real functions."
        },
        {
            "chapter_no": 3,
            "title": "Trigonometric Functions",
            "keywords": ["radian measure", "degree measure", "trigonometric functions", "compound angles", "sin(x+y)", "cos(x+y)", "tan(x+y)", "double angle", "sin 2x", "cos 2x", "transformation formulas"],
            "summary": "Angles in radians and degrees, trigonometric functions for real numbers, signs of trig functions, addition/subtraction formulas, multiple angles."
        },
        {
            "chapter_no": 4,
            "title": "Complex Numbers and Quadratic Equations",
            "keywords": ["complex numbers", "imaginary number", "iota", "i^2 = -1", "real part", "imaginary part", "argand plane", "modulus of complex number", "conjugate", "polar representation"],
            "summary": "Need for complex numbers (√-1 = i), algebraic properties of complex numbers, Argand plane, modulus and conjugate, solutions of quadratic equations with negative discriminant."
        },
        {
            "chapter_no": 5,
            "title": "Linear Inequalities",
            "keywords": ["linear inequalities", "algebraic solution of inequalities", "graphical representation of inequalities", "solution region"],
            "summary": "Linear inequalities, algebraic solutions in one variable and graphical representations on number line, graphical solution of linear inequalities in two variables."
        },
        {
            "chapter_no": 6,
            "title": "Permutations and Combinations",
            "keywords": ["fundamental principle of counting", "factorial", "n!", "permutation", "combination", "npr", "ncr", "arrangements", "selections"],
            "summary": "Fundamental principle of counting, factorial n!, Permutations (nPr) and Combinations (nCr), simple applications."
        },
        {
            "chapter_no": 7,
            "title": "Binomial Theorem",
            "keywords": ["binomial theorem", "pascal's triangle", "expansion of (a+b)^n", "general term", "middle term", "binomial coefficients"],
            "summary": "Historical perspective, statement and proof of Binomial Theorem for positive integral indices, Pascal's triangle, general and middle terms."
        },
        {
            "chapter_no": 8,
            "title": "Sequences and Series",
            "keywords": ["sequence", "series", "geometric progression", "gp", "common ratio", "nth term of gp", "sum of n terms of gp", "infinite gp", "geometric mean", "gm", "am gm inequality"],
            "summary": "Sequences and Series, Geometric Progression (GP), general term of GP, sum of n terms of GP, infinite GP and its sum, geometric mean (GM), AM-GM relation."
        },
        {
            "chapter_no": 9,
            "title": "Straight Lines",
            "keywords": ["straight lines", "slope of a line", "angle between two lines", "point slope form", "slope intercept form", "two point form", "intercept form", "distance of point from line", "parallel lines distance"],
            "summary": "Slope of line and angle between two lines, various forms of equations of a line (point-slope, slope-intercept, intercept), distance of point from line."
        },
        {
            "chapter_no": 10,
            "title": "Conic Sections",
            "keywords": ["conic section", "circle equation", "parabola", "ellipse", "hyperbola", "focus", "directrix", "eccentricity", "latus rectum", "vertex"],
            "summary": "Sections of a cone: circles, ellipse, parabola, hyperbola; standard equations and simple properties of parabola, ellipse, and hyperbola."
        },
        {
            "chapter_no": 11,
            "title": "Introduction to Three Dimensional Geometry",
            "keywords": ["3d geometry", "three dimensional geometry", "coordinate axes in 3d", "coordinate planes in 3d", "3d distance formula", "3d section formula"],
            "summary": "Coordinate axes and coordinate planes in three dimensions, coordinates of a point, distance between two points, section formula."
        },
        {
            "chapter_no": 12,
            "title": "Limits and Derivatives",
            "keywords": ["limits", "derivatives", "limit of function", "lim x->0", "sin x / x", "derivative of function", "first principle", "power rule", "product rule", "quotient rule", "dy/dx"],
            "summary": "Intuitive idea of limit, limits of polynomials and trigonometric functions, derivative introduced as rate of change / slope of tangent, standard rules (product, quotient, power)."
        },
        {
            "chapter_no": 13,
            "title": "Statistics",
            "keywords": ["measures of dispersion", "range", "mean deviation", "variance", "standard deviation", "coefficient of variation"],
            "summary": "Measures of dispersion: range, mean deviation about mean and median, variance, and standard deviation of ungrouped and grouped data."
        },
        {
            "chapter_no": 14,
            "title": "Probability",
            "keywords": ["axiomatic probability", "random experiment", "outcomes", "sample space", "event", "mutually exclusive events", "exhaustive events"],
            "summary": "Random experiments, outcomes, sample spaces; events, types of events (impossible, sure, mutually exclusive, exhaustive), axiomatic approach to probability."
        }
    ],

    "Class 12": [
        {
            "chapter_no": 1,
            "title": "Relations and Functions",
            "keywords": ["types of relations", "reflexive", "symmetric", "transitive", "equivalence relation", "one-one", "injective", "onto", "surjective", "bijective", "composite functions", "invertible function", "inverse function"],
            "summary": "Types of relations: reflexive, symmetric, transitive, equivalence relations; one-one and onto functions, composite functions, inverse of a function."
        },
        {
            "chapter_no": 2,
            "title": "Inverse Trigonometric Functions",
            "keywords": ["inverse trigonometric functions", "sin^-1", "cos^-1", "tan^-1", "principal value branch", "domain and range of inverse trig", "properties of inverse trig"],
            "summary": "Definition, range, domain, principal value branch of inverse trigonometric functions; graphs of inverse trig functions, elementary properties."
        },
        {
            "chapter_no": 3,
            "title": "Matrices",
            "keywords": ["matrices", "matrix", "order of matrix", "types of matrices", "matrix addition", "matrix multiplication", "scalar multiplication", "transpose of matrix", "symmetric matrix", "skew-symmetric matrix", "invertible matrices"],
            "summary": "Concept, notation, order, equality, types of matrices, zero and identity matrix, operations on matrices (addition, multiplication), transpose, symmetric and skew-symmetric."
        },
        {
            "chapter_no": 4,
            "title": "Determinants",
            "keywords": ["determinant", "determinants", "minors", "cofactors", "adjoint of matrix", "inverse of matrix", "a^-1 = (1/|a|) adj a", "cramer's rule", "system of linear equations matrix method"],
            "summary": "Determinant of a square matrix (up to 3x3), minors, cofactors, adjoint and inverse of a square matrix, solving system of linear equations using inverse matrix."
        },
        {
            "chapter_no": 5,
            "title": "Continuity and Differentiability",
            "keywords": ["continuity", "differentiability", "continuous function", "chain rule", "derivative of composite functions", "derivative of implicit functions", "logarithmic differentiation", "parametric differentiation", "second order derivative", "rolle's theorem", "mean value theorem"],
            "summary": "Continuity and differentiability, derivative of composite functions, chain rule, derivative of inverse trigonometric functions, implicit functions, exponential and logarithmic functions, logarithmic differentiation, second order derivatives."
        },
        {
            "chapter_no": 6,
            "title": "Applications of Derivatives",
            "keywords": ["application of derivatives", "aod", "rate of change", "increasing and decreasing functions", "tangents and normals", "maxima and minima", "first derivative test", "second derivative test", "point of inflection"],
            "summary": "Applications of derivatives: rate of change of quantities, increasing/decreasing functions, tangents and normals, maxima and minima (first and second derivative tests), optimization word problems."
        },
        {
            "chapter_no": 7,
            "title": "Integrals",
            "keywords": ["integral", "integrals", "integration", "antiderivative", "indefinite integral", "integration by substitution", "integration by parts", "partial fractions", "definite integral", "fundamental theorem of calculus", "properties of definite integrals"],
            "summary": "Integration as inverse process of differentiation, integration by substitution, partial fractions, and integration by parts; evaluation of simple integrals, Fundamental Theorem of Calculus, properties of definite integrals."
        },
        {
            "chapter_no": 8,
            "title": "Applications of Integrals",
            "keywords": ["applications of integrals", "aoi", "area under curve", "area between two curves", "area of circle by integration", "area of ellipse by integration", "area under parabola"],
            "summary": "Applications in finding the area under simple curves, especially lines, circles, parabolas, and ellipses; area between two curves."
        },
        {
            "chapter_no": 9,
            "title": "Differential Equations",
            "keywords": ["differential equation", "order of differential equation", "degree of differential equation", "general solution", "particular solution", "variable separable", "homogeneous differential equation", "linear differential equation", "integrating factor", "dy/dx + py = q"],
            "summary": "Definition, order and degree, general and particular solutions of a differential equation; solution of first-order differential equations by variable separable, homogeneous, and linear form."
        },
        {
            "chapter_no": 10,
            "title": "Vector Algebra",
            "keywords": ["vectors", "vector algebra", "position vector", "magnitude of vector", "direction cosines", "unit vector", "dot product", "scalar product", "cross product", "vector product", "projection of vector", "a.b", "a x b"],
            "summary": "Vectors and scalars, magnitude and direction of a vector, direction cosines/ratios; types of vectors, position vector, scalar (dot) product and vector (cross) product of vectors."
        },
        {
            "chapter_no": 11,
            "title": "Three Dimensional Geometry",
            "keywords": ["3d lines", "direction cosines of line", "equation of a line in 3d", "angle between lines", "skew lines", "shortest distance between two lines", "equation of plane", "coplanar lines"],
            "summary": "Direction cosines and direction ratios of a line, equation of a line in space (vector and Cartesian), angle between two lines, shortest distance between two skew lines."
        },
        {
            "chapter_no": 12,
            "title": "Linear Programming",
            "keywords": ["linear programming", "lpp", "objective function", "constraints", "feasible region", "bounded region", "unbounded region", "corner point method", "optimal solution"],
            "summary": "Introduction, related terminology such as constraints, objective function, optimization, graphical method of solution for problems in two variables, feasible and infeasible regions."
        },
        {
            "chapter_no": 13,
            "title": "Probability",
            "keywords": ["conditional probability", "multiplication theorem of probability", "independent events", "bayes' theorem", "bayes theorem", "total probability", "random variable", "probability distribution", "mean of random variable"],
            "summary": "Conditional probability, multiplication rule of probability, independent events, total probability, Bayes' Theorem, random variables and probability distributions."
        }
    ]
}

def normalize_class_name(grade_str: Optional[str]) -> str:
    """Normalizes string like 'Class 12', '12th', 'class 12th', 'Grade 10' to standard 'Class 12'."""
    if not grade_str:
        return "Class 10"
    s = str(grade_str).lower().strip()
    if "12" in s:
        return "Class 12"
    if "11" in s:
        return "Class 11"
    if "10" in s:
        return "Class 10"
    if "9" in s or "ix" in s:
        return "Class 9"
    return "Class 10"


def find_matching_chapter(query: str, class_key: str) -> Optional[Dict[str, Any]]:
    """Scores chapters within a single class based on query keyword matches."""
    q_lower = query.lower()
    
    # Normalize common student math typos so NCERT chapters match flawlessly
    try:
        from backend.ai.guardrails import COMMON_MATH_TYPOS
    except ImportError:
        try:
            from ai.guardrails import COMMON_MATH_TYPOS
        except ImportError:
            COMMON_MATH_TYPOS = {}
            
    for typo, correction in COMMON_MATH_TYPOS.items():
        q_lower = re.sub(r'\b' + re.escape(typo) + r'\b', correction, q_lower)
    words = set(re.findall(r'[a-zA-Z0-9_\^]+', q_lower))
    best_match = None
    best_score = 0

    target_ch_num = extract_chapter_number_from_query(q_lower)
    chapters = NCERT_CURRICULUM.get(class_key, [])
    for ch in chapters:
        score = 0
        if target_ch_num and ch["chapter_no"] == target_ch_num:
            score += 25.0  # Dominant exact chapter number match
        # Exact keyword phrase match (high weight)
        for kw in ch["keywords"]:
            if kw in q_lower:
                score += 4
            else:
                # Word-level match (only for meaningful words > 2 chars, excluding single math variables like 2x, 3x)
                kw_words = {w for w in kw.split() if len(w) > 2 and not re.match(r'^[0-9]+[a-z]$', w)}
                overlap = words.intersection(kw_words)
                if overlap:
                    score += len(overlap) * 1.5

        # Title match
        title_lower = ch["title"].lower()
        if any(w in title_lower for w in words if len(w) > 3):
            score += 3

        # Add calculus / differentiation intent bonus for Class 11 Ch 12 or Class 12 Ch 5
        if ("differentiate" in q_lower or "derivative" in q_lower) and class_key in ["Class 11", "Class 12"]:
            if ch["title"] in ["Limits and Derivatives", "Continuity and Differentiability"]:
                score += 5.0

        if score > best_score and score >= 3.0:
            best_score = score
            best_match = {
                "class": class_key,
                "chapter_no": ch["chapter_no"],
                "title": ch["title"],
                "summary": ch["summary"],
                "score": best_score
            }

    return best_match


def classify_question_curriculum(query: str, student_class: Optional[str] = "Class 10") -> Dict[str, Any]:
    """
    Main Priority Search Function:
    1. Checks explicit class mentioned in query first, or student's selected class (Priority 1).
    2. If strong match found in selected class, returns immediately with target class.
    3. If not found in selected class, scans other NCERT classes (Priority 2 Fallback).
    4. Detects whether this is a cross-class topic (e.g. User selected Class 12 but asked Class 10/9 question).
    """
    q_lower = query.lower() if query else ""
    explicit_cls = extract_explicit_class_from_query(q_lower)
    if explicit_cls:
        selected_class = explicit_cls
        # If student explicitly specified a class, confine curriculum to that class!
        other_classes = []
    else:
        selected_class = normalize_class_name(student_class)
        all_classes = ["Class 12", "Class 11", "Class 10", "Class 9"]
        other_classes = [c for c in all_classes if c != selected_class]

    # 1. First search in selected class
    target_match = find_matching_chapter(query, selected_class)

    other_matches = []
    for c in other_classes:
        m = find_matching_chapter(query, c)
        if m:
            other_matches.append(m)

    # Sort other matches by score
    other_matches.sort(key=lambda x: x["score"], reverse=True)
    best_other = other_matches[0] if other_matches else None

    # Determine final decision
    if target_match and (not best_other or target_match["score"] >= best_other["score"] - 1.0):
        # Found in selected class!
        return {
            "has_curriculum_match": True,
            "matched_class": selected_class,
            "target_class": selected_class,
            "is_cross_class": False,
            "chapter_no": target_match["chapter_no"],
            "chapter_title": target_match["title"],
            "chapter_summary": target_match["summary"],
            "reference_badge": f"📚 NCERT Reference: {selected_class} Maths · Chapter {target_match['chapter_no']}: {target_match['title']}",
            "note_text": None
        }
    elif best_other:
        # Cross-class match! (e.g. Student selected Class 12, but question is from Class 10)
        matched_cls = best_other["class"]
        
        # Build friendly note explaining relation to selected class
        order = {"Class 9": 9, "Class 10": 10, "Class 11": 11, "Class 12": 12}
        sel_num = order.get(selected_class, 10)
        match_num = order.get(matched_cls, 10)

        if match_num < sel_num:
            note = f"Yeh concept aapki selected {selected_class} se pehle ka ({matched_cls}) foundational topic hai."
        else:
            note = f"Yeh concept higher syllabus ({matched_cls}) mein cover hota hai."

        return {
            "has_curriculum_match": True,
            "matched_class": matched_cls,
            "target_class": selected_class,
            "is_cross_class": True,
            "chapter_no": best_other["chapter_no"],
            "chapter_title": best_other["title"],
            "chapter_summary": best_other["summary"],
            "reference_badge": f"📚 NCERT Reference: {matched_cls} Maths · Chapter {best_other['chapter_no']}: {best_other['title']}",
            "note_text": note
        }
    else:
        # General math topic
        return {
            "has_curriculum_match": False,
            "matched_class": selected_class,
            "target_class": selected_class,
            "is_cross_class": False,
            "chapter_no": None,
            "chapter_title": "General Mathematics",
            "chapter_summary": "Standard mathematical fundamentals.",
            "reference_badge": f"📚 NCERT Reference: {selected_class} Mathematics",
            "note_text": None
        }
