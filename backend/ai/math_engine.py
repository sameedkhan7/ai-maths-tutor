import sympy as sp
import re

def evaluate_math_expression(expr_str: str) -> str | None:
    try:
        clean_expr = expr_str.replace('^', '**')
        result = sp.sympify(clean_expr)
        return str(result)
    except Exception:
        return None

def calculate_derivative(expr_str: str, var: str = 'x') -> dict | None:
    try:
        x = sp.Symbol(var)
        expr = sp.sympify(expr_str.replace('^', '**'))
        deriv = sp.diff(expr, x)
        return {
            "type": "derivative",
            "expression": str(expr),
            "variable": var,
            "solution": str(deriv),
            "latex_solution": sp.latex(deriv)
        }
    except Exception:
        return None

def calculate_integral(expr_str: str, var: str = 'x') -> dict | None:
    try:
        x = sp.Symbol(var)
        expr = sp.sympify(expr_str.replace('^', '**'))
        integral = sp.integrate(expr, x)
        return {
            "type": "integral",
            "expression": str(expr),
            "variable": var,
            "solution": str(integral),
            "latex_solution": sp.latex(integral)
        }
    except Exception:
        return None

def get_exact_math_context(question: str) -> str | None:
    q_lower = question.lower()
    
    # 1. Derivative
    if "derivative" in q_lower or "differentiate" in q_lower or "dy/dx" in q_lower:
        match = re.search(r'(?:of|for)\s+([a-zA-Z0-9\+\-\*\/\^\(\)\s]+)', question, re.IGNORECASE)
        if match:
            raw_expr = match.group(1).strip(' ?.')
            sol = calculate_derivative(raw_expr)
            if sol:
                return f"[SymPy Exact Computation: The exact analytical derivative d/dx({sol['expression']}) is {sol['solution']} (LaTeX: ${sol['latex_solution']}$)]"

    # 2. Integral
    if "integral" in q_lower or "integrate" in q_lower:
        match = re.search(r'(?:of|for)\s+([a-zA-Z0-9\+\-\*\/\^\(\)\s]+)', question, re.IGNORECASE)
        if match:
            raw_expr = match.group(1).strip(' ?.')
            sol = calculate_integral(raw_expr)
            if sol:
                return f"[SymPy Exact Computation: The exact analytical integral ∫({sol['expression']})dx is {sol['solution']} + C (LaTeX: ${sol['latex_solution']} + C$)]"

    return None