"""
Proc macro that evaluates definite integrals in LaTeX.

Finds patterns like \int_a^b f(x) dx and replaces them with their evaluated result.
The bounds can be numbers or variables from the context.
"""

import re
from alpha_solve import ProcMacroInput, ProcMacroResult, MetaFunctionResult
from sympy_tools import from_latex
from sympy import sympify, integrate, symbols, N


def evaluate_integrals(input_data: ProcMacroInput) -> ProcMacroResult:
    """
    Proc macro that evaluates definite integrals in LaTeX.

    Finds patterns like \int_0^2 (2x) dx and replaces them with their numerical result.

    Args:
        input_data: ProcMacroInput containing latex and context

    Returns:
        ProcMacroResult with integrals replaced by their evaluated values
    """
    modified_latex = input_data.latex

    # Pattern to match definite integrals: \int_{lower}^{upper} ... d{var}
    # or \int_lower^upper ... d{var}
    # This is a simplified pattern - we'll use a more manual approach

    # Look for \int patterns
    while True:
        # Find \int with bounds
        match = re.search(r'\\int\s*_', modified_latex)
        if not match:
            break

        start_pos = match.start()
        pos = match.end()

        # Parse the lower bound
        if pos < len(modified_latex) and modified_latex[pos] == '{':
            # Bound is in braces: _{lower}
            pos += 1
            brace_count = 1
            lower_start = pos
            while pos < len(modified_latex) and brace_count > 0:
                if modified_latex[pos] == '{':
                    brace_count += 1
                elif modified_latex[pos] == '}':
                    brace_count -= 1
                pos += 1
            lower_bound = modified_latex[lower_start:pos-1]
        else:
            # Bound is a single character: _a
            lower_bound = modified_latex[pos] if pos < len(modified_latex) else ''
            pos += 1

        # Look for upper bound: ^
        if pos < len(modified_latex) and modified_latex[pos] == '^':
            pos += 1
            if pos < len(modified_latex) and modified_latex[pos] == '{':
                # Bound is in braces: ^{upper}
                pos += 1
                brace_count = 1
                upper_start = pos
                while pos < len(modified_latex) and brace_count > 0:
                    if modified_latex[pos] == '{':
                        brace_count += 1
                    elif modified_latex[pos] == '}':
                        brace_count -= 1
                    pos += 1
                upper_bound = modified_latex[upper_start:pos-1]
            else:
                # Bound is a single character: ^b
                upper_bound = modified_latex[pos] if pos < len(modified_latex) else ''
                pos += 1
        else:
            # No upper bound found, skip this integral
            modified_latex = modified_latex[:start_pos] + '__SKIP_INTEGRAL__' + modified_latex[match.end():]
            modified_latex = modified_latex.replace('__SKIP_INTEGRAL__', '\\int_')
            break

        # Now find the integrand and differential
        # Look for d{var} pattern
        d_pattern = r'd([a-zA-Z])'
        remaining = modified_latex[pos:]
        d_match = re.search(d_pattern, remaining)

        if not d_match:
            # No differential found, skip
            modified_latex = modified_latex[:start_pos] + '__SKIP_INTEGRAL__' + modified_latex[match.end():]
            modified_latex = modified_latex.replace('__SKIP_INTEGRAL__', '\\int_')
            break

        var = d_match.group(1)
        integrand_end = pos + d_match.start()
        integrand_latex = modified_latex[pos:integrand_end].strip()
        integral_end = pos + d_match.end()

        # Remove \left( and \right) if present
        integrand_latex = re.sub(r'\\left\(', '(', integrand_latex)
        integrand_latex = re.sub(r'\\right\)', ')', integrand_latex)
        integrand_latex = integrand_latex.strip()

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
            result = integrate(integrand, (var_symbol, sympify(lower_val), sympify(upper_val)))

            # Simplify and convert to numerical if possible
            result_val = N(result)
            result_str = str(result_val)

            # Replace the integral with the result
            full_integral = modified_latex[start_pos:integral_end]
            modified_latex = modified_latex[:start_pos] + result_str + modified_latex[integral_end:]

        except Exception as e:
            # If evaluation fails, skip this integral
            modified_latex = modified_latex[:start_pos] + '__SKIP_INTEGRAL__' + modified_latex[match.end():]
            modified_latex = modified_latex.replace('__SKIP_INTEGRAL__', '\\int_')
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
    # Check if the latex contains definite integral patterns
    has_definite_integral = bool(re.search(r'\\int\s*_', input_data.latex))

    return MetaFunctionResult(
        index=3,  # Priority order (run before num() at 5, after potential other macros)
        name="Evaluate Integrals",
        use_result=has_definite_integral
    )

