def solve_simple(input_data):
    return CellFunctionResult(
        visible_solutions=['1'],
        new_context=input_data.context
    )


def meta_solve_simple(input_data):
    return MetaFunctionResult(
        index=100,
        name='Simple Solver',
        use_result=True
    )