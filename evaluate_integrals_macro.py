"""
Proc macro that evaluates definite integrals in LaTeX.

Finds patterns like:
- \int_a^b f(x) dx
- \int_{lower}^{upper} f(x) dx

Where a and b are either numbers or variables in the context,
and replaces them with the evaluated result.
"""

import re
from alpha_solve import ProcMacroInput, ProcMacroResult, MetaFunctionResult
from sympy_tools import from_latex, to_latex
from sympy import integrate, symbols, sympify, Symbol


def evaluate_integrals(input_data: ProcMacroInput) -> ProcMacroResult:
    """
    Proc macro that evaluates definite integrals in LaTeX.

    Finds integral patterns and evaluates them if the bounds are
    either numbers or variables defined in the context.

    Args:
        input_data: ProcMacroInput containing latex and context

    Returns:
        ProcMacroResult with integrals replaced by their evaluated results
    """
    modified_latex = input_data.latex

    # Pattern to match integrals with bounds in braces
    pattern_with_braces = r'\\int\s*_\s*\{([^}]*)\}\s*\^\s*\{([^}]*)\}\s*(.*?)\s*d\s*([a-zA-Z])'

    # Pattern for integrals without braces or bounds (indefinite)
    pattern_no_bounds = r'\\int\s+([^d]*?)\s*d\s*([a-zA-Z])'

    # Keep processing until no more integrals are found
    max_iterations = 10
    iteration = 0

    while iteration < max_iterations:
        # Try pattern with braces first
        match = re.search(pattern_with_braces, modified_latex)
        is_definite = True

        if not match:
            # Try pattern without bounds (indefinite integral)
            match = re.search(pattern_no_bounds, modified_latex)
            is_definite = False

        if not match:
            break

        iteration += 1

        if is_definite:
            lower_bound_str = (match.group(1) or '').strip()
            upper_bound_str = (match.group(2) or '').strip()
            integrand_latex = match.group(3).strip()
            var_name = match.group(4)
        else:
            # Indefinite integral
            lower_bound_str = ''
            upper_bound_str = ''
            integrand_latex = match.group(1).strip()
            var_name = match.group(2)

        try:
            # Parse the integrand
            integrand_expr = from_latex(integrand_latex)

            # Create the variable symbol
            var = Symbol(var_name)

            # Check if bounds are empty (indefinite integral)
            if not lower_bound_str or not upper_bound_str:
                # Evaluate indefinite integral
                result = integrate(integrand_expr, var)
            else:
                # Parse the bounds for definite integral
                lower_bound = parse_bound(lower_bound_str, input_data)
                upper_bound = parse_bound(upper_bound_str, input_data)

                if lower_bound is None or upper_bound is None:
                    # Can't evaluate bounds, skip this integral
                    marker = f"__INTEGRAL_SKIP_{match.start()}__"
                    full_match = modified_latex[match.start():match.end()]
                    modified_latex = modified_latex[:match.start()] + marker + modified_latex[match.end():]
                    modified_latex = modified_latex.replace(marker, full_match)
                    break

                # Evaluate definite integral
                result = integrate(integrand_expr, (var, lower_bound, upper_bound))

            # Convert result to LaTeX
            result_latex = to_latex(result)

            # Replace the integral with the result
            full_match = modified_latex[match.start():match.end()]
            modified_latex = modified_latex[:match.start()] + result_latex + modified_latex[match.end():]

        except Exception as e:
            # If evaluation fails, leave the integral as is and move on
            marker = f"__INTEGRAL_FAILED_{match.start()}__"
            full_match = modified_latex[match.start():match.end()]
            modified_latex = modified_latex[:match.start()] + marker + modified_latex[match.end():]
            modified_latex = modified_latex.replace(marker, full_match)
            break

    return ProcMacroResult(modified_latex=modified_latex)


def parse_bound(bound_str: str, input_data: ProcMacroInput):
    """
    Parse a bound string, checking if it's a number or a variable in context.

    Returns:
        The sympy value if successful, None otherwise
    """
    try:
        # Try to parse as a number first
        value = sympify(bound_str)
        return value
    except:
        pass

    # Check if it's a variable in the context
    for var in input_data.context.variables:
        if var.name == bound_str and var.values:
            try:
                # Use the first value
                return sympify(var.values[0])
            except:
                pass

    # Try parsing as LaTeX expression
    try:
        expr = from_latex(bound_str)
        # Substitute variables from context
        subs_dict = {}
        for var in input_data.context.variables:
            if var.values:
                try:
                    subs_dict[var.name] = sympify(var.values[0])
                except:
                    pass
        if subs_dict:
            expr = expr.subs(subs_dict)
        return expr
    except:
        pass

    return None


def meta_evaluate_integrals(input_data: ProcMacroInput) -> MetaFunctionResult:
    """
    Meta function that determines if evaluate_integrals should be used.

    This runs before the proc macro to decide if it should be applied.

    Args:
        input_data: ProcMacroInput containing latex and context

    Returns:
        MetaFunctionResult indicating whether to use this proc macro
    """
    # Check if the latex contains integral patterns (both definite and indefinite)
    # Match \int with optional bounds followed by d{variable}
    has_integral = bool(re.search(r'\\int.*?d[a-zA-Z]', input_data.latex))

    return MetaFunctionResult(
        index=3,  # Priority order (run before num() but after other transformations)
        name="Evaluate Integrals",
        use_result=has_integral
    )

