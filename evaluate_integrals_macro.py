"""
Proc macro that evaluates definite integrals in LaTeX.

Expects format: \int_{lower}^{upper}\left(integrand\right)dvar
For example: \int_{0}^{2}\left(x^2\right)dx

The bounds and integrand are evaluated, with variables substituted from context.
"""

import re
from alpha_solve import ProcMacroInput, ProcMacroResult, MetaFunctionResult
from sympy_tools import from_latex
from sympy import sympify, integrate, symbols, N


def evaluate_integrals(input_data: ProcMacroInput) -> ProcMacroResult:
    """
    Proc macro that evaluates definite integrals in LaTeX.

    Expects format: \int_{lower}^{upper}\left(integrand\right)dvar

    Args:
        input_data: ProcMacroInput containing latex and context

    Returns:
        ProcMacroResult with integrals replaced by their evaluated values
    """
    modified_latex = input_data.latex
    print(f"[evaluate_integrals] Input LaTeX: {modified_latex}")

    # Pattern to match: \int_{...}^{...}\left(...\right)d{var}
    # This matches the template created by the int command
    # Note: \right) in LaTeX is the closing delimiter, so we match up to \right
    pattern = r'\\int_\{([^}]*)\}\^\{([^}]*)\}\\left\((.*?)\\right\)d([a-zA-Z])'

    while True:
        match = re.search(pattern, modified_latex)
        if not match:
            print(f"[evaluate_integrals] No match found for pattern: {pattern}")
            print(f"[evaluate_integrals] Current LaTeX: {modified_latex}")
            break

        start_pos = match.start()
        end_pos = match.end()

        # Extract components from the pattern
        lower_bound = match.group(1).strip()
        upper_bound = match.group(2).strip()
        integrand_latex = match.group(3).strip()
        var = match.group(4)

        # Skip empty integrals (template not filled in)
        if not lower_bound or not upper_bound or not integrand_latex:
            break

        try:
            # Parse bounds - substitute context variables if needed
            lower_val = lower_bound
            upper_val = upper_bound

            # Try to substitute context variables in bounds
            for context_var in input_data.context.variables:
                if context_var.name == lower_bound and context_var.values:
                    lower_val = context_var.values[0]
                if context_var.name == upper_bound and context_var.values:
                    upper_val = context_var.values[0]

            # Parse the integrand expression
            from sympy_tools import _latex_to_sympy_str
            integrand_str = _latex_to_sympy_str(integrand_latex)
            integrand = sympify(integrand_str)

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
            lower_sym = sympify(lower_val)
            upper_sym = sympify(upper_val)
            result = integrate(integrand, (var_symbol, lower_sym, upper_sym))

            # Simplify the result
            from sympy import simplify
            result = simplify(result)

            # Only convert to numerical if both bounds are pure numbers (not symbolic)
            if lower_sym.is_number and upper_sym.is_number and not lower_sym.free_symbols and not upper_sym.free_symbols:
                # Both bounds are numbers, evaluate numerically
                result_val = N(result)
                result_str = str(result_val)
            else:
                # At least one bound is symbolic, keep it symbolic
                # Convert to LaTeX for display
                from sympy_tools import to_latex
                result_str = to_latex(result)

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
    # Check if the latex contains definite integral patterns with the expected format
    # Pattern: \int_{...}^{...}\left(...\right)d{var} with all fields filled in
    pattern = r'\\int_\{[^}]+\}\^\{[^}]+\}\\left\(.+?\\right\)d[a-zA-Z]'
    has_complete_integral = bool(re.search(pattern, input_data.latex))

    return MetaFunctionResult(
        index=3,  # Priority order (run before num() at 5, after potential other macros)
        name="Evaluate Integrals",
        use_result=has_complete_integral
    )

