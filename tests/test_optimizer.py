import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from lexer import Lexer
from parser import Parser
from optimizer import optimize
from execution_plan import render_execution_plan, render_execution_summary, execution_plan_to_list


def optimize_query(query):
    tokens = Lexer(query).tokenize()
    statement = Parser(tokens).parse()
    return optimize(statement)


def step_by_rule(steps, rule_name):
    return next(step for step in steps if step.rule == rule_name)


class PredicatePushdownTests(unittest.TestCase):
    def test_applied_when_where_clause_present(self):
        _, steps = optimize_query("SELECT name FROM employee WHERE salary > 50000;")
        step = step_by_rule(steps, "Predicate Pushdown")
        self.assertTrue(step.applied)

    def test_not_applied_without_where_clause(self):
        _, steps = optimize_query("SELECT name FROM employee;")
        step = step_by_rule(steps, "Predicate Pushdown")
        self.assertFalse(step.applied)


class ConstantLiteralSimplificationTests(unittest.TestCase):
    def test_applied_for_non_canonical_numeric_literal(self):
        _, steps = optimize_query("SELECT name FROM employee WHERE salary > 050000;")
        step = step_by_rule(steps, "Constant Literal Simplification")
        self.assertTrue(step.applied)
        self.assertIn("50000", step.after)

    def test_not_applied_for_canonical_numeric_literal(self):
        _, steps = optimize_query("SELECT name FROM employee WHERE salary > 50000;")
        step = step_by_rule(steps, "Constant Literal Simplification")
        self.assertFalse(step.applied)

    def test_not_applied_without_where_clause(self):
        _, steps = optimize_query("SELECT name FROM employee;")
        step = step_by_rule(steps, "Constant Literal Simplification")
        self.assertFalse(step.applied)


class ProjectionReductionTests(unittest.TestCase):
    def test_applied_for_duplicate_columns(self):
        _, steps = optimize_query("SELECT name, name FROM employee;")
        step = step_by_rule(steps, "Projection Reduction")
        self.assertTrue(step.applied)

    def test_not_applied_without_duplicate_columns(self):
        _, steps = optimize_query("SELECT name, salary FROM employee;")
        step = step_by_rule(steps, "Projection Reduction")
        self.assertFalse(step.applied)


class ExecutionPlanTests(unittest.TestCase):
    def test_execution_order_is_scan_filter_project(self):
        optimized_ir, _ = optimize_query("SELECT name FROM employee WHERE salary > 50000;")
        self.assertEqual(render_execution_summary(optimized_ir), "SCAN → FILTER → PROJECT")

    def test_execution_order_without_filter(self):
        optimized_ir, _ = optimize_query("SELECT name FROM employee;")
        self.assertEqual(render_execution_summary(optimized_ir), "SCAN → PROJECT")

    def test_execution_plan_reflects_optimized_columns(self):
        optimized_ir, _ = optimize_query("SELECT name, name FROM employee;")
        plan_text = render_execution_plan(optimized_ir)
        self.assertIn("PROJECT name", plan_text)
        self.assertNotIn("PROJECT name, name", plan_text)

    def test_execution_plan_to_list(self):
        optimized_ir, _ = optimize_query("SELECT name FROM employee WHERE salary > 50000;")
        steps = execution_plan_to_list(optimized_ir)
        self.assertEqual(steps, ["SCAN employee", "FILTER salary > 50000", "PROJECT name"])


if __name__ == "__main__":
    unittest.main()
