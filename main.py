from sympy import solve


def meta_solve_simple(input_data: CellFunctionInput) -> MetaFunctionResult:
    """
    Check if the equation can be solved.
    Returns use_result=True only if:
    - Cell has LaTeX content
    - LaTeX contains an equals sign (=)
    - LaTeX can be parsed into a SymPy expression
    - Expression has at least one variable
    """
    try:
        latex = input_data.cell.get('latex', '').strip()

        # Check if there's any content
        if not latex:
            return MetaFunctionResult(index=100, name='Simple Solver', use_result=False)

        # Check if it's an equation (has =)
        if '=' not in latex:
            return MetaFunctionResult(index=100, name='Simple Solver', use_result=False)

        # Try to parse it
        expr = from_latex(latex)

        # Check if it has free symbols (variables)
        if not expr.free_symbols:
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

        # Get the variable to solve for (first free symbol)
        variables = list(equation.free_symbols)
        if not variables:
            return CellFunctionResult(
                visible_solutions=['No variables to solve for'],
                new_context=input_data.context
            )

        var = variables[0]

        # Solve the equation
        solutions = solve(equation, var)

        # Format the solutions
        visible_solutions = []
        new_variables = list(input_data.context.variables)

        if solutions:
            # Take the first solution
            solution = solutions[0]
            solution_str = f"{var} = {solution}"
            visible_solutions.append(solution_str)

            # Add or update the variable in context
            new_var = Variable.create_analytical(str(var), str(solution))

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