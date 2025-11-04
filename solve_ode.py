from sympy import dsolve, symbols, Function, Derivative, Eq
from sympy.core.relational import Equality
from alpha_solve import CellFunctionInput, CellFunctionResult, MetaFunctionResult, Variable, Context
from sympy_tools import from_latex, to_latex


def meta_solve_ode(input_data: CellFunctionInput) -> MetaFunctionResult:
    """
    Check if the equation is a differential equation that can be solved.
    Returns use_result=True only if:
    - Cell has LaTeX content
    - LaTeX can be parsed into a SymPy expression
    - Expression is an equation (Equality type)
    - Expression contains at least one Derivative
    """
    try:
        latex = input_data.cell.get('latex', '').strip()

        # Check if there's any content
        if not latex:
            return MetaFunctionResult(index=90, name='ODE Solver', use_result=False)

        # Try to parse it
        expr = from_latex(latex)

        # Check if it's an equation (Equality type)
        if not isinstance(expr, Equality):
            return MetaFunctionResult(index=90, name='ODE Solver', use_result=False)

        # Check if it contains any derivatives
        has_derivative = any(isinstance(arg, Derivative) for arg in expr.atoms(Derivative))

        if not has_derivative:
            return MetaFunctionResult(index=90, name='ODE Solver', use_result=False)

        # It's an ODE!
        return MetaFunctionResult(index=90, name='ODE Solver', use_result=True)
    except Exception as e:
        # If anything fails, don't use this solver
        return MetaFunctionResult(index=90, name='ODE Solver', use_result=False)


def solve_ode(input_data: CellFunctionInput) -> CellFunctionResult:
    """
    Solve an ordinary differential equation (ODE) using SymPy's dsolve.
    """
    latex = input_data.cell.get('latex', '').strip()

    try:
        # Parse the LaTeX equation
        expr = from_latex(latex)

        # Check if it's an equation
        if not isinstance(expr, Equality):
            return CellFunctionResult(
                visible_solutions=['Unable to solve: not an equation'],
                new_context=input_data.context
            )

        # Find all derivatives in the equation
        derivatives = expr.atoms(Derivative)

        if not derivatives:
            return CellFunctionResult(
                visible_solutions=['No derivatives found in equation'],
                new_context=input_data.context
            )

        # Get the function being differentiated
        # Assume all derivatives are of the same function
        first_deriv = list(derivatives)[0]
        func_expr = first_deriv.expr

        # Get the independent variable (what we're differentiating with respect to)
        diff_var = first_deriv.variables[0] if first_deriv.variables else symbols('t')

        # If func_expr is a symbol, we need to convert it to a function
        if func_expr.is_Symbol:
            func_name = str(func_expr)

            # Create a function symbol: f(t) where f is the function name
            func = Function(func_name)(diff_var)

            # Build replacement dictionary
            # Replace the symbol with the function
            replacements = {func_expr: func}

            # Replace each derivative with the proper functional derivative
            for deriv in derivatives:
                if deriv.expr == func_expr:
                    # Get the order of the derivative
                    order = sum(1 for v in deriv.variables if v == diff_var)

                    # Create new derivative with the function
                    if order == 1:
                        new_deriv = Derivative(func, diff_var)
                    else:
                        new_deriv = Derivative(func, (diff_var, order))

                    replacements[deriv] = new_deriv

            # Apply all replacements to the equation
            equation = expr.subs(replacements)
        else:
            # Already a function
            equation = expr
            func = func_expr

        # Try to solve the ODE
        try:
            solutions = dsolve(equation, func)

            # dsolve can return a single solution or a list
            if not isinstance(solutions, list):
                solutions = [solutions]

            visible_solutions = []
            for solution in solutions:
                visible_solutions.append(to_latex(solution))

            # For ODEs, we don't typically add to context since the solution
            # is a function, not a simple variable value

            return CellFunctionResult(
                visible_solutions=visible_solutions,
                new_context=input_data.context
            )

        except Exception as solve_error:
            return CellFunctionResult(
                visible_solutions=[f"Could not solve ODE: {str(solve_error)}"],
                new_context=input_data.context
            )

    except Exception as e:
        # If solving fails, return error message
        return CellFunctionResult(
            visible_solutions=[f"Error solving differential equation: {str(e)}"],
            new_context=input_data.context
        )

