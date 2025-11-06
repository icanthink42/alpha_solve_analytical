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

    # Simple pattern: \int _{ }^{ } ... dx
    # Capture everything between the empty bounds and dx
    pattern = r'\\int\s*_\s*\{\s*\}\s*\^\s*\{\s*\}\s*(.+?)\s*d\s*([a-zA-Z])\b'

    max_iterations = 10
    for _ in range(max_iterations):
        match = re.search(pattern, modified_latex)
        if not match:
            break

        integrand_latex = match.group(1).strip()
        var_name = match.group(2)

        try:
            # Parse the integrand
            integrand_expr = from_latex(integrand_latex)

            # Create the variable symbol
            var = Symbol(var_name)

            # Evaluate indefinite integral
            result = integrate(integrand_expr, var)

            # Convert result to LaTeX
            result_latex = to_latex(result)

            # Replace the integral with the result
            modified_latex = modified_latex[:match.start()] + result_latex + modified_latex[match.end():]

        except Exception as e:
            # If evaluation fails, skip this integral
            break

    return ProcMacroResult(modified_latex=modified_latex)


def meta_evaluate_integrals(input_data: ProcMacroInput) -> MetaFunctionResult:
    """
    Meta function that determines if evaluate_integrals should be used.
    """
    # Check if the latex contains \int _{ }^{ }
    has_integral = bool(re.search(r'\\int\s*_\s*\{\s*\}\s*\^\s*\{\s*\}', input_data.latex))

    return MetaFunctionResult(
        index=3,
        name="Evaluate Integrals",
        use_result=has_integral
    )

