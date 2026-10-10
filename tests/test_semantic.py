import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from lexer import Lexer
from parser import Parser
from schema import Schema
from semantic import SemanticAnalyzer, SemanticError


def analyze_query(query, schema=None):
    tokens = Lexer(query).tokenize()
    statement = Parser(tokens).parse()
    return SemanticAnalyzer(schema or Schema()).analyze(statement)


class ValidSemanticTests(unittest.TestCase):
    def test_valid_table_and_columns(self):
        checks = analyze_query("SELECT name, salary FROM employee;")
        names = [check.name for check in checks]
        self.assertIn("employee", names)
        self.assertIn("name", names)
        self.assertIn("salary", names)

    def test_valid_condition_column(self):
        checks = analyze_query("SELECT name FROM employee WHERE salary > 50000;")
        names = [check.name for check in checks]
        self.assertIn("salary", names)


class ClauseTrackingTests(unittest.TestCase):
    def test_checks_record_originating_clause(self):
        checks = analyze_query("SELECT name FROM employee WHERE salary > 50000;")
        clauses = {(check.name, check.clause) for check in checks}
        self.assertIn(("employee", "from"), clauses)
        self.assertIn(("name", "select"), clauses)
        self.assertIn(("salary", "where"), clauses)


class InvalidSemanticTests(unittest.TestCase):
    def test_unknown_table(self):
        with self.assertRaises(SemanticError):
            analyze_query("SELECT name FROM customers;")

    def test_unknown_column_in_select(self):
        with self.assertRaises(SemanticError):
            analyze_query("SELECT age FROM employee;")

    def test_unknown_column_in_where(self):
        with self.assertRaises(SemanticError):
            analyze_query("SELECT name FROM employee WHERE bonus > 1000;")

    def test_error_message_mentions_table_and_column(self):
        try:
            analyze_query("SELECT age FROM employee;")
            self.fail("Expected a SemanticError to be raised")
        except SemanticError as error:
            self.assertIn("age", error.message)
            self.assertIn("employee", error.message)


class CustomSchemaTests(unittest.TestCase):
    def test_custom_schema_is_respected(self):
        schema = Schema({"orders": ["order_id", "amount"]})
        checks = analyze_query("SELECT amount FROM orders;", schema)
        self.assertTrue(any(check.name == "orders" for check in checks))

    def test_schema_as_dict(self):
        schema = Schema()
        data = schema.as_dict()
        self.assertIn("employee", data)
        self.assertIn("name", data["employee"])


if __name__ == "__main__":
    unittest.main()
