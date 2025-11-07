"""
Proc macro that analytically evaluates definite integrals in LaTeX.

Expects format: \int_{lower}^{upper}\left(integrand\right)dvar
Examples:
  - \int_{0}^{2}\left(x^2\right)dx -> \frac{8}{3}
  - \int_{a}^{b}\left(x\right)dx -> \frac{b^2 - a^2}{2}
  - \int_{0}^{a}\left(x^2\right)dx -> \frac{a^3}{3}

All results are analytical (symbolic). Bounds and integrand can contain variables
from context or be symbolic expressions.
"""

import re
from alpha_solve import ProcMacroInput, ProcMacroResult, MetaFunctionResult
from sympy_tools import from_latex
from sympy import sympify, integrate, symbols


def evaluate_integrals(input_data: ProcMacroInput) -> ProcMacroResult:
    """
    Proc macro that analytically evaluates definite integrals in LaTeX.

    Expects format: \int_{lower}^{upper}\left(integrand\right)dvar
    Results are always analytical (symbolic).

    Args:
        input_data: ProcMacroInput containing latex and context

    Returns:
        ProcMacroResult with integrals replaced by their analytical results in LaTeX
    """
    modified_latex = input_data.latex
    print(f"[evaluate_integrals] Input LaTeX: {modified_latex}")

    # Pattern to match: \int_{...}^{...}\left(...\right)d{var}
    # OR: \int_x^y\left(...\right)d{var} (when bounds are single chars without braces)
    # MathQuill removes braces for single character subscripts/superscripts
    pattern = r'\\int_(?:\{([^}]+)\}|([^\s\^\\]+))\^(?:\{([^}]+)\}|([^\s\\]+))\\left\((.*?)\\right\)d([a-zA-Z])'

    while True:
        match = re.search(pattern, modified_latex)
        if not match:
            print(f"[evaluate_integrals] No match found for pattern: {pattern}")
            print(f"[evaluate_integrals] Current LaTeX: {modified_latex}")
            break

        start_pos = match.start()
        end_pos = match.end()

        # Extract components from the pattern
        # Groups: (1) lower with braces, (2) lower without braces, (3) upper with braces, (4) upper without braces, (5) integrand, (6) var
        lower_bound = (match.group(1) or match.group(2) or '').strip()
        upper_bound = (match.group(3) or match.group(4) or '').strip()
        integrand_latex = match.group(5).strip()
        var = match.group(6)

        # Skip empty integrals (template not filled in)
        if not lower_bound or not upper_bound or not integrand_latex:
            break

        try:
            # Parse bounds using from_latex
            from sympy_tools import from_latex

            # Convert bounds from LaTeX to sympy
            try:
                lower_sym = from_latex(lower_bound)
            except:
                # If parsing fails, try as a symbol
                lower_sym = symbols(lower_bound)

            try:
                upper_sym = from_latex(upper_bound)
            except:
                # If parsing fails, try as a symbol
                upper_sym = symbols(upper_bound)

            # Substitute context variables in bounds if they exist
            bound_subs_dict = {}
            for context_var in input_data.context.variables:
                try:
                    bound_subs_dict[symbols(context_var.name)] = sympify(context_var.values[0])
                except:
                    pass

            if bound_subs_dict:
                lower_sym = lower_sym.subs(bound_subs_dict)
                upper_sym = upper_sym.subs(bound_subs_dict)

            # Parse the integrand expression
            integrand = from_latex(integrand_latex)
            print(f"[evaluate_integrals] Integrand: {integrand}")

            # Create variable symbol
            var_symbol = symbols(var)

            # Substitute any other context variables in the integrand
            subs_dict = {}
            for context_var in input_data.context.variables:
                if context_var.name != var and context_var.values:
                    try:
                        subs_dict[symbols(context_var.name)] = sympify(context_var.values[0])
                    except:
                        pass

            if subs_dict:
                integrand = integrand.subs(subs_dict)

            # Evaluate the definite integral
            result = integrate(integrand, (var_symbol, lower_sym, upper_sym))

            # Simplify the result
            from sympy import simplify
            print(f"[evaluate_integrals] Result before simplify: {result}")
            result = simplify(result)

            # Always return as LaTeX (analytical result)
            from sympy_tools import to_latex
            result_str = to_latex(result)
            print(f"[evaluate_integrals] Analytical result (LaTeX): {result_str}")

            # Replace the integral with the result
            modified_latex = modified_latex[:start_pos] + result_str + modified_latex[end_pos:]
            print(f"Evaluated integral: {match.group(0)} -> {result_str}")

        except Exception as e:
            # If evaluation fails, skip this integral and try the next one
            print(f"Failed to evaluate integral: {e}")
            break

    return ProcMacroResult(modified_latex=modified_latex)


def meta_evaluate_integrals(input_data: ProcMacroInput) -> MetaFunctionResult:
    """
    Meta function that determines if evaluate_integrals should be used.

    Args:
        input_data: ProcMacroInput containing latex and context

    Returns:
        MetaFunctionResult indicating whether to use this proc macro
    """
    print(f"[meta_evaluate_integrals] Checking LaTeX: {input_data.latex}")

    # Check if the latex contains definite integral patterns with the expected format
    # Pattern handles both \int_{x}^{y} and \int_x^y (with or without braces)
    pattern = r'\\int_(?:\{[^}]+\}|[^\s\^\\]+)\^(?:\{[^}]+\}|[^\s\\]+)\\left\(.+?\\right\)d[a-zA-Z]'
    has_complete_integral = bool(re.search(pattern, input_data.latex))

    print(f"[meta_evaluate_integrals] Pattern: {pattern}")
    print(f"[meta_evaluate_integrals] Match found: {has_complete_integral}")

    return MetaFunctionResult(
        index=3,  # Priority order (run before num() at 5, after potential other macros)
        name="Evaluate Integrals",
        use_result=has_complete_integral
    )

