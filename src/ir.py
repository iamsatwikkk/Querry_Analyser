from dataclasses import dataclass
from typing import Optional
from ast_nodes import SelectStatement, Condition, Comparison, literal_display


@dataclass
class ScanNode:
    table: str
    child: Optional["IRNode"] = None

    def describe(self) -> str:
        return f"SCAN({self.table})"


@dataclass
class FilterNode:
    condition: Condition
    child: "IRNode" = None

    def describe(self) -> str:
        return f"FILTER({condition_to_text(self.condition)})"


@dataclass
class ProjectNode:
    columns: list
    child: "IRNode" = None

    def describe(self) -> str:
        return f"PROJECT({', '.join(self.columns)})"


IRNode = object


def condition_to_text(condition: Condition) -> str:
    if isinstance(condition, Comparison):
        return f"{condition.column.name} {condition.operator} {literal_display(condition.value)}"
    return f"{condition_to_text(condition.left)} {condition.operator} {condition_to_text(condition.right)}"


def build_ir(statement: SelectStatement) -> ProjectNode:
    node = ScanNode(statement.table.name)
    if statement.where is not None:
        node = FilterNode(statement.where.condition, node)
    node = ProjectNode([column.name for column in statement.columns], node)
    return node


def chain_nodes(root):
    nodes = []
    current = root
    while current is not None:
        nodes.append(current)
        current = getattr(current, "child", None)
    return nodes


def render_ir(root) -> str:
    return "\n    ↓\n".join(node.describe() for node in chain_nodes(root))


def ir_to_list(root):
    return [node.describe() for node in chain_nodes(root)]


def find_node(root, node_type):
    for node in chain_nodes(root):
        if isinstance(node, node_type):
            return node
    return None
