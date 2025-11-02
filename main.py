import sympy as sp

def solve_simple(input_data):
    x = sp.symbols('x')
    equation = sp.Eq(x**2 - 4, 0)
    solution = sp.solve(equation, x)
    return CellFunctionResult(
        visible_solutions=[str(solution)],
        new_context=input_data.context
    )


def meta_solve_simple(input_data):
    return MetaFunctionResult(
        index=100,
        name='Simple Solver',
        use_result=True
    )