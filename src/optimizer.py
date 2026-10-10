from dataclasses import dataclass
from ast_nodes import Comparison
from ir import ProjectNode, FilterNode, build_ir, render_ir, find_node


@dataclass
class OptimizationStep:
    rule: str
    applied: bool
    before: str
    after: str
    reason: str


def canonical_number(value: str) -> str:
    if "." in value:
        as_float = float(value)
        if as_float == int(as_float):
            return str(int(as_float))
        return str(as_float)
    return str(int(value))


def simplify_condition_literals(condition, changed):
    if isinstance(condition, Comparison):
        if condition.value.literal_type == "NUMBER":
            canonical = canonical_number(condition.value.value)
            if canonical != condition.value.value:
                condition.value.value = canonical
                changed.append(True)
        return
    simplify_condition_literals(condition.left, changed)
    simplify_condition_literals(condition.right, changed)


def apply_predicate_pushdown(root):
    before = render_ir(root)
    if isinstance(root, ProjectNode) and isinstance(root.child, FilterNode):
        filter_node = root.child
        scan_node = filter_node.child
        pushed_root = FilterNode(filter_node.condition, ProjectNode(root.columns, scan_node))
        return pushed_root, OptimizationStep(
            "Predicate Pushdown",
            True,
            before,
            render_ir(pushed_root),
            "The filter is moved ahead of the projection so it runs closer to the scan.",
        )
    return root, OptimizationStep(
        "Predicate Pushdown",
        False,
        before,
        before,
        "There is no WHERE clause to push earlier, or the plan is already in pushdown form.",
    )


def apply_constant_simplification(root):
    before = render_ir(root)
    filter_node = find_node(root, FilterNode)
    if filter_node is None:
        return root, OptimizationStep(
            "Constant Literal Simplification",
            False,
            before,
            before,
            "There is no filter condition to simplify.",
        )
    changed = []
    simplify_condition_literals(filter_node.condition, changed)
    if not changed:
        return root, OptimizationStep(
            "Constant Literal Simplification",
            False,
            before,
            before,
            "Numeric literals in the condition are already in canonical form.",
        )
    return root, OptimizationStep(
        "Constant Literal Simplification",
        True,
        before,
        render_ir(root),
        "Numeric literals were normalized (leading zeros or redundant decimals removed).",
    )


def apply_projection_reduction(root):
    before = render_ir(root)
    project_node = find_node(root, ProjectNode)
    if project_node is None:
        return root, OptimizationStep(
            "Projection Reduction", False, before, before, "No projection stage was found."
        )
    deduplicated = list(dict.fromkeys(project_node.columns))
    if len(deduplicated) == len(project_node.columns):
        return root, OptimizationStep(
            "Projection Reduction",
            False,
            before,
            before,
            "The column list has no redundant or duplicate columns.",
        )
    project_node.columns = deduplicated
    return root, OptimizationStep(
        "Projection Reduction",
        True,
        before,
        render_ir(root),
        "Duplicate columns were removed from the projection list.",
    )


def optimize(statement):
    root = build_ir(statement)
    steps = []

    root, step = apply_predicate_pushdown(root)
    steps.append(step)

    root, step = apply_constant_simplification(root)
    steps.append(step)

    root, step = apply_projection_reduction(root)
    steps.append(step)

    return root, steps
