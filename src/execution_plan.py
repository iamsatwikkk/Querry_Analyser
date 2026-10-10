from ir import ScanNode, FilterNode, ProjectNode, find_node, condition_to_text


def build_execution_plan(root):
    steps = []
    scan_node = find_node(root, ScanNode)
    filter_node = find_node(root, FilterNode)
    project_node = find_node(root, ProjectNode)
    if scan_node is not None:
        steps.append(scan_node)
    if filter_node is not None:
        steps.append(filter_node)
    if project_node is not None:
        steps.append(project_node)
    return steps


def execution_step_text(node) -> str:
    if isinstance(node, ScanNode):
        return f"SCAN {node.table}"
    if isinstance(node, FilterNode):
        return f"FILTER {condition_to_text(node.condition)}"
    if isinstance(node, ProjectNode):
        return f"PROJECT {', '.join(node.columns)}"
    raise TypeError(f"Unsupported IR node: {type(node).__name__}")


def render_execution_plan(root) -> str:
    steps = build_execution_plan(root)
    return "\n    ↓\n".join(execution_step_text(step) for step in steps)


def execution_plan_to_list(root):
    return [execution_step_text(step) for step in build_execution_plan(root)]


def render_execution_summary(root) -> str:
    labels = {ScanNode: "SCAN", FilterNode: "FILTER", ProjectNode: "PROJECT"}
    steps = build_execution_plan(root)
    return " → ".join(labels[type(step)] for step in steps)
