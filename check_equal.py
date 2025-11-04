from sympy import symbols, sympify, simplify
from sympy.core.relational import Equality
from alpha_solve import CellFunctionInput, CellFunctionResult, MetaFunctionResult
from sympy_tools import from_latex


def meta_check_equal(input_data: CellFunctionInput) -> MetaFunctionResult:
    """
    Check if an equation can be verified.
    Returns use_result=True only if:
    - Cell has LaTeX content
    - LaTeX can be parsed into a SymPy expression
    - Expression is an equation (Equality type)
    - ALL variables in the equation are defined in the context
    """
    try:
        latex = input_data.cell.get('latex', '').strip()

        # Check if there's any content
        if not latex:
            return MetaFunctionResult(index=25, name='Check Equality', use_result=False)

        # Try to parse it
        expr = from_latex(latex)

        # Check if it's an equation (Equality type)
        if not isinstance(expr, Equality):
            return MetaFunctionResult(index=25, name='Check Equality', use_result=False)

        # Check if ALL variables are in the context
        context_var_names = {v.name for v in input_data.context.variables}
        all_vars_defined = all(
            str(symbol) in context_var_names
            for symbol in expr.free_symbols
        )

        if not all_vars_defined:
            # Not all variables defined, can't check
            return MetaFunctionResult(index=25, name='Check Equality', use_result=False)

        # All variables are defined, we can check!
        return MetaFunctionResult(index=25, name='Check Equality', use_result=True)
    except Exception as e:
        # If anything fails, don't use this checker
        return MetaFunctionResult(index=25, name='Check Equality', use_result=False)


def check_equal(input_data: CellFunctionInput) -> CellFunctionResult:
    """
    Check if an equation is true by substituting all known variables.
    For simple variable equality (e.g., x = y), checks if both variables have the same set of values (ignoring order).
    For other equations, checks if the equation holds for all combinations of variable values.
    """
    latex = input_data.cell.get('latex', '').strip()

    try:
        # Parse the LaTeX equation
        expr = from_latex(latex)

        # It should be an Equality
        if not isinstance(expr, Equality):
            return CellFunctionResult(
                visible_solutions=['Not an equation'],
                new_context=input_data.context
            )

        # Build list of context variables and their values
        from itertools import product

        context_vars_with_values = []
        for context_var in input_data.context.variables:
            var_symbol = symbols(context_var.name)
            if var_symbol in expr.free_symbols and context_var.values:
                context_vars_with_values.append((var_symbol, context_var.values))

        # If no context variables to check, just check the equation as-is
        if not context_vars_with_values:
            lhs = simplify(expr.lhs)
            rhs = simplify(expr.rhs)
            is_equal = simplify(lhs - rhs) == 0
            result_text = 'True' if is_equal else 'False'
            return CellFunctionResult(
                visible_solutions=[result_text],
                new_context=input_data.context
            )

        # Check all combinations of variable values
        var_symbols = [v[0] for v in context_vars_with_values]
        value_lists = [v[1] for v in context_vars_with_values]

        left_hand_sides = []
        right_hand_sides = []
        for value_combo in product(*value_lists):
            # Create substitution dictionary
            subs_dict = dict(zip(var_symbols, [sympify(v) for v in value_combo]))

            # Substitute and simplify
            lhs_result = simplify(expr.lhs.subs(subs_dict))
            rhs_result = simplify(expr.rhs.subs(subs_dict))

            left_hand_sides.append(lhs_result)
            right_hand_sides.append(rhs_result)

        # Sort by string representation for comparison
        left_hand_sides_sorted = sorted(left_hand_sides, key=str)
        right_hand_sides_sorted = sorted(right_hand_sides, key=str)

        # Compare element-by-element
        all_equal = True
        for i in range(len(left_hand_sides_sorted)):
            if simplify(left_hand_sides_sorted[i] - right_hand_sides_sorted[i]) != 0:
                all_equal = False
                break

        # Return result
        result_text = 'True' if all_equal else 'False'

        return CellFunctionResult(
            visible_solutions=[result_text],
            new_context=input_data.context
        )

    except Exception as e:
        # If checking fails, return error message
        return CellFunctionResult(
            visible_solutions=[f"Error checking equality: {str(e)}"],
            new_context=input_data.context
        )

