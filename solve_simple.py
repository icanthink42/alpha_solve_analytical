from sympy import solve, symbols, sympify, Eq
from sympy.core.relational import Equality
from alpha_solve import CellFunctionInput, CellFunctionResult, MetaFunctionResult, Variable, Context
from sympy_tools import from_latex, to_latex


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

