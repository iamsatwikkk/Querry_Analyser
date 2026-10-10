import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from lexer import Lexer
from parser import Parser
from ir import build_ir, render_ir, ir_to_list, ScanNode, FilterNode, ProjectNode, find_node


def build_ir_for(query):
    tokens = Lexer(query).tokenize()
    statement = Parser(tokens).parse()
    return build_ir(statement)


class IRConstructionTests(unittest.TestCase):
    def test_select_without_where_has_no_filter(self):
        root = build_ir_for("SELECT name FROM employee;")
        self.assertIsInstance(root, ProjectNode)
        self.assertIsInstance(root.child, ScanNode)
        self.assertIsNone(find_node(root, FilterNode))

    def test_select_with_where_has_filter_between_project_and_scan(self):
        root = build_ir_for("SELECT name FROM employee WHERE salary > 50000;")
        self.assertIsInstance(root, ProjectNode)
        self.assertIsInstance(root.child, FilterNode)
        self.assertIsInstance(root.child.child, ScanNode)

    def test_project_columns_match_select_list(self):
        root = build_ir_for("SELECT name, salary FROM employee;")
        self.assertEqual(root.columns, ["name", "salary"])

    def test_scan_table_matches_from_clause(self):
        root = build_ir_for("SELECT name FROM employee;")
        scan_node = find_node(root, ScanNode)
        self.assertEqual(scan_node.table, "employee")

    def test_render_ir_contains_all_stages(self):
        root = build_ir_for("SELECT name FROM employee WHERE salary > 50000;")
        text = render_ir(root)
        self.assertIn("PROJECT(name)", text)
        self.assertIn("FILTER(salary > 50000)", text)
        self.assertIn("SCAN(employee)", text)

    def test_ir_to_list(self):
        root = build_ir_for("SELECT name FROM employee WHERE salary > 50000;")
        steps = ir_to_list(root)
        self.assertEqual(steps, ["PROJECT(name)", "FILTER(salary > 50000)", "SCAN(employee)"])


if __name__ == "__main__":
    unittest.main()
