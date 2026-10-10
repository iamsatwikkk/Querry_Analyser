import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from lexer import Lexer
from parser import Parser, ParseError
from ast_nodes import SelectStatement, Comparison, LogicalCondition, format_ast, ast_to_dict


def parse_query(query):
    tokens = Lexer(query).tokenize()
    return Parser(tokens).parse()


class ValidQueryParsingTests(unittest.TestCase):
    def test_simple_select_returns_ast(self):
        statement = parse_query("SELECT name FROM employee;")
        self.assertIsInstance(statement, SelectStatement)
        self.assertEqual([column.name for column in statement.columns], ["name"])
        self.assertEqual(statement.table.name, "employee")
        self.assertIsNone(statement.where)

    def test_multiple_columns(self):
        statement = parse_query("SELECT name, salary FROM employee;")
        self.assertEqual([column.name for column in statement.columns], ["name", "salary"])

    def test_long_column_list(self):
        columns = ", ".join(f"c{i}" for i in range(25))
        statement = parse_query(f"SELECT {columns} FROM employee;")
        self.assertEqual(len(statement.columns), 25)

    def test_where_with_comparison(self):
        statement = parse_query("SELECT name FROM employee WHERE salary > 50000;")
        self.assertIsInstance(statement.where.condition, Comparison)
        self.assertEqual(statement.where.condition.column.name, "salary")
        self.assertEqual(statement.where.condition.operator, ">")
        self.assertEqual(statement.where.condition.value.value, "50000")

    def test_where_with_string_comparison(self):
        statement = parse_query("SELECT name FROM employee WHERE department = 'IT';")
        self.assertEqual(statement.where.condition.value.literal_type, "STRING")

    def test_where_with_and(self):
        statement = parse_query(
            "SELECT name FROM employee WHERE salary >= 50000 AND department = 'IT';"
        )
        self.assertIsInstance(statement.where.condition, LogicalCondition)
        self.assertEqual(statement.where.condition.operator, "AND")

    def test_where_with_or(self):
        statement = parse_query(
            "SELECT name FROM employee WHERE department = 'IT' OR department = 'HR';"
        )
        self.assertIsInstance(statement.where.condition, LogicalCondition)
        self.assertEqual(statement.where.condition.operator, "OR")

    def test_multiple_conditions(self):
        statement = parse_query(
            "SELECT name FROM employee WHERE salary > 1 AND salary < 2 OR department = 'IT';"
        )
        self.assertIsInstance(statement.where.condition, LogicalCondition)

    def test_minimum_valid_query(self):
        statement = parse_query("SELECT id FROM employee;")
        self.assertEqual(len(statement.columns), 1)
        self.assertIsNone(statement.where)

    def test_ast_display_structure(self):
        statement = parse_query("SELECT name FROM employee WHERE salary > 50000;")
        tree_text = format_ast(statement)
        self.assertIn("SELECT", tree_text)
        self.assertIn("COLUMNS", tree_text)
        self.assertIn("WHERE", tree_text)
        self.assertIn("salary", tree_text)

    def test_ast_to_dict_structure(self):
        statement = parse_query("SELECT name FROM employee WHERE salary > 50000;")
        tree = ast_to_dict(statement)
        self.assertEqual(tree["label"], "SELECT")
        labels = [child["label"] for child in tree["children"]]
        self.assertEqual(labels, ["COLUMNS", "FROM", "WHERE"])


class InvalidQuerySyntaxTests(unittest.TestCase):
    def test_missing_column(self):
        with self.assertRaises(ParseError):
            parse_query("SELECT FROM employee;")

    def test_missing_from(self):
        with self.assertRaises(ParseError):
            parse_query("SELECT name employee;")

    def test_missing_table_name(self):
        with self.assertRaises(ParseError):
            parse_query("SELECT name FROM;")

    def test_incomplete_where(self):
        with self.assertRaises(ParseError):
            parse_query("SELECT name FROM employee WHERE;")

    def test_malformed_operator(self):
        with self.assertRaises(ParseError):
            parse_query("SELECT name FROM employee WHERE salary >;")

    def test_trailing_tokens_after_semicolon(self):
        with self.assertRaises(ParseError):
            parse_query("SELECT name FROM employee; EXTRA")


if __name__ == "__main__":
    unittest.main()
