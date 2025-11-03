from sympy import solve, symbols, sympify, Eq, simplify
from sympy.core.relational import Equality


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
    Returns "True" or "False" as the solution.
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

        # Substitute all variables from context on both sides separately
        lhs = expr.lhs
        rhs = expr.rhs

        for context_var in input_data.context.variables:
            var_symbol = symbols(context_var.name)
            # Use the first value if multiple exist
            if context_var.values:
                var_value = sympify(context_var.values[0])
                lhs = lhs.subs(var_symbol, var_value)
                rhs = rhs.subs(var_symbol, var_value)

        # Simplify both sides
        lhs = simplify(lhs)
        rhs = simplify(rhs)

        # Check if they're equal
        is_equal = simplify(lhs - rhs) == 0

        # Return result
        result_text = 'True' if is_equal else 'False'

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


def meta_solve_simple(input_data: CellFunctionInput) -> MetaFunctionResult:
    """
    Check if the equation can be solved.
    Returns use_result=True only if:
    - Cell has LaTeX content
    - LaTeX can be parsed into a SymPy expression
    - Expression is an equation (Equality type)
    - Expression has at least one variable
    - At least one variable is NOT already defined in the context
    """
    try:
        latex = input_data.cell.get('latex', '').strip()

        # Check if there's any content
        if not latex:
            return MetaFunctionResult(index=100, name='Simple Solver', use_result=False)

        # Try to parse it
        expr = from_latex(latex)

        # Check if it's an equation (Equality type)
        if not isinstance(expr, Equality):
            return MetaFunctionResult(index=100, name='Simple Solver', use_result=False)

        # Check if it has free symbols (variables)
        if not expr.free_symbols:
            return MetaFunctionResult(index=100, name='Simple Solver', use_result=False)

        # Check if at least one variable is NOT in the context
        context_var_names = {v.name for v in input_data.context.variables}
        has_unsolved_variable = any(
            str(symbol) not in context_var_names
            for symbol in expr.free_symbols
        )

        if not has_unsolved_variable:
            # All variables are already defined, don't use this solver
            return MetaFunctionResult(index=100, name='Simple Solver', use_result=False)

        # It's solvable!
        return MetaFunctionResult(index=100, name='Simple Solver', use_result=True)
    except Exception as e:
        # If anything fails, don't use this solver
        return MetaFunctionResult(index=100, name='Simple Solver', use_result=False)


def solve_simple(input_data: CellFunctionInput) -> CellFunctionResult:
    """
    Solve a simple equation and update the context with the solution.
    Displays result as "varname = value"
    """
    latex = input_data.cell.get('latex', '').strip()

    try:
        # Parse the LaTeX equation
        expr = from_latex(latex)

        # If it's an Eq object, extract left and right sides
        if hasattr(expr, 'lhs') and hasattr(expr, 'rhs'):
            equation = expr
        else:
            # Not an equation, can't solve
            return CellFunctionResult(
                visible_solutions=['Unable to solve: not an equation'],
                new_context=input_data.context
            )

        # Get the variable to solve for
        # Prefer variables that are NOT in the context
        variables = list(equation.free_symbols)
        if not variables:
            return CellFunctionResult(
                visible_solutions=['No variables to solve for'],
                new_context=input_data.context
            )

        # Get list of variables already in context
        context_var_names = {v.name for v in input_data.context.variables}

        # Try to find a variable not in context
        var = None
        for candidate in sorted(variables, key=str):
            if str(candidate) not in context_var_names:
                var = candidate
                break

        # If all variables are in context, we can't solve
        # (because we can substitute all of them, leaving nothing to solve for)
        if var is None:
            return CellFunctionResult(
                visible_solutions=['All variables already defined in context'],
                new_context=input_data.context
            )

        # Build list of substitution combinations
        # For each context variable, create substitution for each of its values
        context_vars_with_values = []
        for context_var in input_data.context.variables:
            var_symbol = symbols(context_var.name)
            if var_symbol != var and var_symbol in equation.free_symbols:
                context_vars_with_values.append((var_symbol, context_var.values))

        # Generate all combinations of substitutions
        from itertools import product

        all_solutions = set()  # Use set to avoid duplicates
        visible_solutions = []

        if context_vars_with_values:
            # Get all variable symbols and their value lists
            var_symbols = [v[0] for v in context_vars_with_values]
            value_lists = [v[1] for v in context_vars_with_values]

            # Generate all combinations
            for value_combo in product(*value_lists):
                # Create substitution dictionary
                subs_dict = dict(zip(var_symbols, [sympify(v) for v in value_combo]))

                # Substitute and solve
                substituted_eq = equation.subs(subs_dict)
                solutions = solve(substituted_eq, var)

                # Collect solutions
                for solution in solutions:
                    all_solutions.add(solution)
        else:
            # No context variables to substitute, solve directly
            solutions = solve(equation, var)
            all_solutions.update(solutions)

        # Format the solutions
        new_variables = list(input_data.context.variables)

        if all_solutions:
            # Convert solutions to list and format
            solution_strings = []
            for solution in all_solutions:
                solution_eq = Eq(var, solution)
                visible_solutions.append(to_latex(solution_eq))
                solution_strings.append(str(solution))

            # Add or update the variable in context with all solutions
            new_var = Variable.create_analytical(str(var), solution_strings)

            # Remove old variable with same name if exists
            new_variables = [v for v in new_variables if v.name != str(var)]
            new_variables.append(new_var)
        else:
            visible_solutions.append(f"No solution found for {var}")

        # Create new context with updated variables
        new_context = Context(variables=new_variables)

        return CellFunctionResult(
            visible_solutions=visible_solutions,
            new_context=new_context
        )

    except Exception as e:
        # If solving fails, return error message
        return CellFunctionResult(
            visible_solutions=[f"Error solving equation: {str(e)}"],
            new_context=input_data.context
        )