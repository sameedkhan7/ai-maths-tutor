# backend/rag/sample_data.py
import os
from backend.rag.config import SAMPLE_DOCS_DIR

NCERT_SAMPLES = {
    "ncert_class11_calculus.txt": """
# NCERT Class 11 Mathematics — Chapter 13: Limits and Derivatives
## Section 13.5: Derivative of a Function
The derivative of a function f at a point x is defined as the limit of the difference quotient:
f'(x) = lim (h -> 0) [f(x + h) - f(x)] / h

### Key Standard Derivative Formulas:
1. Power Rule: d/dx (x^n) = n * x^(n-1)
2. Constant Rule: d/dx (c) = 0
3. Trigonometric Derivatives:
   - d/dx (sin x) = cos x
   - d/dx (cos x) = -sin x
   - d/dx (tan x) = sec^2 x
   - d/dx (sec x) = sec x * tan x
   - d/dx (cot x) = -csc^2 x
   - d/dx (csc x) = -csc x * cot x
4. Exponential and Logarithmic:
   - d/dx (e^x) = e^x
   - d/dx (ln x) = 1/x

### Physical Interpretation:
In physics and geometry, the derivative represents the instantaneous rate of change of y with respect to x, and geometrically it gives the slope of the tangent to the curve y = f(x) at any given point.
""",

    "ncert_class10_quadratic_equations.txt": """
# NCERT Class 10 Mathematics — Chapter 4: Quadratic Equations
## Section 4.3: Solution of Quadratic Equations
A quadratic equation in variable x is an equation of the standard form:
ax^2 + bx + c = 0, where a != 0 and a, b, c are real numbers.

### Quadratic Formula (Shreedharacharya Rule):
The roots of the equation ax^2 + bx + c = 0 are given by:
x = (-b ± sqrt(b^2 - 4ac)) / (2a)

### Discriminant (D = b^2 - 4ac) Nature of Roots:
1. If D > 0: Two distinct real roots exist.
2. If D = 0: Two equal real roots exist (x = -b / 2a).
3. If D < 0: No real roots exist (roots are complex/imaginary).

### Relationship between roots and coefficients:
If alpha and beta are roots of ax^2 + bx + c = 0:
- Sum of roots (alpha + beta) = -b/a
- Product of roots (alpha * beta) = c/a
""",

    "ncert_class10_trigonometry.txt": """
# NCERT Class 10 & 11 Mathematics — Introduction to Trigonometry
## Basic Trigonometric Ratios (Right-Angled Triangle):
For an angle theta in a right-angled triangle ABC with right angle at B:
- sin(theta) = Opposite Side / Hypotenuse = AC / BC
- cos(theta) = Adjacent Side / Hypotenuse = AB / BC
- tan(theta) = Opposite Side / Adjacent Side = sin(theta) / cos(theta)
- csc(theta) = 1 / sin(theta)
- sec(theta) = 1 / cos(theta)
- cot(theta) = 1 / tan(theta)

### Fundamental Pythagorean Identities:
1. sin^2(theta) + cos^2(theta) = 1
2. 1 + tan^2(theta) = sec^2(theta)
3. 1 + cot^2(theta) = csc^2(theta)

### Standard Angles Values (0°, 30°, 45°, 60°, 90°):
- sin 0° = 0, sin 30° = 1/2, sin 45° = 1/sqrt(2), sin 60° = sqrt(3)/2, sin 90° = 1
- cos 0° = 1, cos 30° = sqrt(3)/2, cos 45° = 1/sqrt(2), cos 60° = 1/2, cos 90° = 0
- tan 0° = 0, tan 30° = 1/sqrt(3), tan 45° = 1, tan 60° = sqrt(3), tan 90° = Undefined
""",

    "ncert_class11_sets_relations.txt": """
# NCERT Class 11 Mathematics — Chapter 1: Sets & Relations
## Section 1.4: Operations on Sets
- Union of Sets (A U B): The set of all elements which belong to either A or B or both.
  A U B = {x : x in A or x in B}
- Intersection of Sets (A ∩ B): The set of all elements which belong to both A and B.
  A ∩ B = {x : x in A and x in B}
- Difference of Sets (A - B): The set of elements which belong to A but not to B.
- Complement of a Set (A'): All elements in universal set U that do not belong to A.

### De Morgan's Laws:
1. (A U B)' = A' ∩ B'
2. (A ∩ B)' = A' U B'
"""
}

def create_default_ncert_samples():
    """Writes default NCERT textbook sample chapters into data/sample_docs."""
    os.makedirs(SAMPLE_DOCS_DIR, exist_ok=True)
    for filename, content in NCERT_SAMPLES.items():
        file_path = os.path.join(SAMPLE_DOCS_DIR, filename)
        if not os.path.exists(file_path):
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content.strip())
            print(f"📖 Created default sample: {filename}")

if __name__ == "__main__":
    create_default_ncert_samples()
