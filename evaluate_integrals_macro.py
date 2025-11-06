"""
Proc macro that evaluates definite integrals in LaTeX.
"""

import re
from alpha_solve import ProcMacroInput, ProcMacroResult, MetaFunctionResult
from sympy_tools import from_latex, to_latex
from sympy import integrate, Symbol


def evaluate_integrals(input_data: ProcMacroInput) -> ProcMacroResult:
    """
    Proc macro that evaluates indefinite integrals.

    Matches: \int _{ }^{ } EQUATION dx
    """
    modified_latex = input_data.latex

    print(f"[INTEGRAL DEBUG] Input LaTeX: {modified_latex}")

    # Simple pattern: \int _{ }^{ } ... dx
    # Capture everything between the empty bounds and dx
    pattern = r'\\int\s*_\s*\{\s*\}\s*\^\s*\{\s*\}\s*(.+?)\s*d\s*([a-zA-Z])\b'

    print(f"[INTEGRAL DEBUG] Pattern: {pattern}")

    max_iterations = 10
    for iteration in range(max_iterations):
        match = re.search(pattern, modified_latex)
        if not match:
            print(f"[INTEGRAL DEBUG] No match found on iteration {iteration}")
            break

        print(f"[INTEGRAL DEBUG] Match found! Full match: {match.group(0)}")

        integrand_latex = match.group(1).strip()
        var_name = match.group(2)

        print(f"[INTEGRAL DEBUG] Integrand: {integrand_latex}")
        print(f"[INTEGRAL DEBUG] Variable: {var_name}")

        try:
            # Parse the integrand
            integrand_expr = from_latex(integrand_latex)
            print(f"[INTEGRAL DEBUG] Parsed expression: {integrand_expr}")

            # Create the variable symbol
            var = Symbol(var_name)

            # Evaluate indefinite integral
            result = integrate(integrand_expr, var)
            print(f"[INTEGRAL DEBUG] Integration result: {result}")

            # Convert result to LaTeX
            result_latex = to_latex(result)
            print(f"[INTEGRAL DEBUG] Result LaTeX: {result_latex}")

            # Replace the integral with the result
            modified_latex = modified_latex[:match.start()] + result_latex + modified_latex[match.end():]
            print(f"[INTEGRAL DEBUG] Modified LaTeX: {modified_latex}")

        except Exception as e:
            # If evaluation fails, skip this integral
            print(f"[INTEGRAL DEBUG] ERROR: {e}")
            break

    print(f"[INTEGRAL DEBUG] Final output: {modified_latex}")
    return ProcMacroResult(modified_latex=modified_latex)


def meta_evaluate_integrals(input_data: ProcMacroInput) -> MetaFunctionResult:
    """
    Meta function that determines if evaluate_integrals should be used.
    """
    print(f"[INTEGRAL META DEBUG] Checking LaTeX: {input_data.latex}")

    # Check if the latex contains \int _{ }^{ }
    has_integral = bool(re.search(r'\\int\s*_\s*\{\s*\}\s*\^\s*\{\s*\}', input_data.latex))

    print(f"[INTEGRAL META DEBUG] Has integral: {has_integral}")

    return MetaFunctionResult(
        index=3,
        name="Evaluate Integrals",
        use_result=has_integral
    )

