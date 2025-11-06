from sympy import symbols, sympify, simplify
from sympy.core.relational import Equality
from alpha_solve import CellFunctionInput, CellFunctionResult, MetaFunctionResult
from sympy_tools import from_latex, to_latex


def meta_simple_simplify(input_data: CellFunctionInput) -> MetaFunctionResult:
    """
    Check if the expression can be simplified.
    Returns use_result=True only if:
    - Cell has LaTeX content
    - LaTeX does NOT contain an equals sign (=)
    - LaTeX can be parsed into a SymPy expression
    """
    try:
        latex = input_data.cell.get('latex', '').strip()

        # Check if there's any content
        if not latex:
            return MetaFunctionResult(index=50, name='Simplify', use_result=False)

        # Try to parse it first
        expr = from_latex(latex)

        # Check if the parsed expression is an equation
        if isinstance(expr, Equality):
            return MetaFunctionResult(index=50, name='Simplify', use_result=False)

        # Double-check for equals sign in raw LaTeX
        if '=' in latex:
            return MetaFunctionResult(index=50, name='Simplify', use_result=False)

        # It's simplifiable!
        return MetaFunctionResult(index=50, name='Simplify', use_result=True)
    except Exception as e:
        # If anything fails, don't use this simplifier
        return MetaFunctionResult(index=50, name='Simplify', use_result=False)


def simple_simplify(input_data: CellFunctionInput) -> CellFunctionResult:
    """
    Simplify an expression and display the result.
    Substitutes known variables from context before simplifying.
    Generates one solution for each combination of context variable values.
    """
    latex = input_data.cell.get('latex', '').strip()

    try:
        # Parse the LaTeX expression
        expr = from_latex(latex)

        # Build list of context variables and their values
        from itertools import product

        context_vars_with_values = []
        for context_var in input_data.context.variables:
            var_symbol = symbols(context_var.name)
            if var_symbol in expr.free_symbols and context_var.values:
                context_vars_with_values.append((var_symbol, context_var.values))

        visible_solutions = []

        if context_vars_with_values:
            # Get all variable symbols and their value lists
            var_symbols = [v[0] for v in context_vars_with_values]
            value_lists = [v[1] for v in context_vars_with_values]

            # Generate all combinations
            for value_combo in product(*value_lists):
                # Create substitution dictionary
                subs_dict = dict(zip(var_symbols, [sympify(v) for v in value_combo]))

                # Substitute and simplify
                substituted_expr = expr.subs(subs_dict)
                simplified = simplify(substituted_expr)

                # Add to solutions
                visible_solutions.append(to_latex(simplified))
        else:
            # No context variables to substitute, just simplify
            simplified = simplify(expr)
            visible_solutions.append(to_latex(simplified))

        # Remove duplicates while preserving order
        visible_solutions = list(dict.fromkeys(visible_solutions))

        # Context remains unchanged
        return CellFunctionResult(
            visible_solutions=visible_solutions,
            new_context=input_data.context
        )

    except Exception as e:
        # If simplification fails, return error message
        return CellFunctionResult(
            visible_solutions=[f"Error simplifying expression: {str(e)}"],
            new_context=input_data.context
        )

