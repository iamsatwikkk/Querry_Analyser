from dataclasses import dataclass, field
from typing import List, Optional, Union


@dataclass
class Identifier:
    name: str


@dataclass
class Literal:
    value: str
    literal_type: str


@dataclass
class Comparison:
    column: Identifier
    operator: str
    value: Literal


@dataclass
class LogicalCondition:
    left: "Condition"
    operator: str
    right: "Condition"


Condition = Union[Comparison, LogicalCondition]


@dataclass
class TableReference:
    name: str


@dataclass
class WhereClause:
    condition: Condition


@dataclass
class SelectStatement:
    columns: List[Identifier]
    table: TableReference
    where: Optional[WhereClause] = None


@dataclass
class TreeNode:
    label: str
    children: List["TreeNode"] = field(default_factory=list)


def literal_display(literal: Literal) -> str:
    if literal.literal_type == "STRING":
        return f"'{literal.value}'"
    return literal.value


def condition_to_tree(condition: Condition) -> TreeNode:
    if isinstance(condition, Comparison):
        return TreeNode(
            condition.operator,
            [TreeNode(condition.column.name), TreeNode(literal_display(condition.value))],
        )
    return TreeNode(
        condition.operator,
        [condition_to_tree(condition.left), condition_to_tree(condition.right)],
    )


def select_statement_to_tree(statement: SelectStatement) -> TreeNode:
    root = TreeNode("SELECT")
    root.children.append(TreeNode("COLUMNS", [TreeNode(column.name) for column in statement.columns]))
    root.children.append(TreeNode("FROM", [TreeNode(statement.table.name)]))
    if statement.where is not None:
        root.children.append(TreeNode("WHERE", [condition_to_tree(statement.where.condition)]))
    return root


def render_tree(node: TreeNode, prefix: str = "", is_root: bool = True, is_last: bool = True) -> List[str]:
    lines = []
    if is_root:
        lines.append(node.label)
        child_prefix = ""
    else:
        connector = "└── " if is_last else "├── "
        lines.append(f"{prefix}{connector}{node.label}")
        child_prefix = prefix + ("    " if is_last else "│   ")
    for index, child in enumerate(node.children):
        lines.extend(render_tree(child, child_prefix, False, index == len(node.children) - 1))
    return lines


def format_ast(statement: SelectStatement) -> str:
    return "\n".join(render_tree(select_statement_to_tree(statement)))


def tree_to_dict(node: TreeNode) -> dict:
    return {"label": node.label, "children": [tree_to_dict(child) for child in node.children]}


def ast_to_dict(statement: SelectStatement) -> dict:
    return tree_to_dict(select_statement_to_tree(statement))


def collect_condition_columns(condition: Condition) -> List[str]:
    if isinstance(condition, Comparison):
        return [condition.column.name]
    return collect_condition_columns(condition.left) + collect_condition_columns(condition.right)
