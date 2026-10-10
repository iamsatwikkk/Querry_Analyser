from dataclasses import dataclass
from ast_nodes import SelectStatement, collect_condition_columns


class SemanticError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(message)


@dataclass
class SemanticCheck:
    category: str
    name: str
    table: str
    clause: str = "from"


class SemanticAnalyzer:
    def __init__(self, schema):
        self.schema = schema

    def analyze(self, statement: SelectStatement):
        table_name = statement.table.name
        if not self.schema.table_exists(table_name):
            raise SemanticError(f"Table '{table_name}' does not exist")

        checks = [SemanticCheck("table", table_name, table_name, "from")]

        for column in statement.columns:
            self._check_column(table_name, column.name, "select", checks)

        if statement.where is not None:
            for column_name in collect_condition_columns(statement.where.condition):
                self._check_column(table_name, column_name, "where", checks)

        return checks

    def _check_column(self, table_name, column_name, clause, checks):
        if not self.schema.column_exists(table_name, column_name):
            raise SemanticError(f"Column '{column_name}' does not exist in table '{table_name}'")
        checks.append(SemanticCheck("column", column_name, table_name, clause))
