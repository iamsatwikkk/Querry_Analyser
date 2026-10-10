import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from schema import Schema, create_sample_database


def execute(query, schema=None):
    connection = create_sample_database(schema or Schema())
    try:
        cursor = connection.execute(query)
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        return columns, rows
    finally:
        connection.close()


class SuccessfulExecutionTests(unittest.TestCase):
    def test_simple_select_returns_rows(self):
        columns, rows = execute("SELECT name FROM employee;")
        self.assertEqual(columns, ["name"])
        self.assertEqual(len(rows), 4)

    def test_where_filters_rows(self):
        columns, rows = execute("SELECT name FROM employee WHERE salary > 50000;")
        names = [row[0] for row in rows]
        self.assertIn("Alice", names)
        self.assertIn("Charlie", names)
        self.assertNotIn("Bob", names)

    def test_string_comparison(self):
        columns, rows = execute("SELECT name FROM employee WHERE department = 'IT';")
        names = [row[0] for row in rows]
        self.assertEqual(sorted(names), ["Alice", "Charlie"])

    def test_and_condition(self):
        columns, rows = execute(
            "SELECT name FROM employee WHERE salary >= 50000 AND department = 'IT';"
        )
        names = [row[0] for row in rows]
        self.assertEqual(sorted(names), ["Alice", "Charlie"])

    def test_or_condition(self):
        columns, rows = execute(
            "SELECT name FROM employee WHERE department = 'HR' OR department = 'Finance';"
        )
        names = [row[0] for row in rows]
        self.assertEqual(sorted(names), ["Bob", "Diana"])


class NoMatchingRowsTests(unittest.TestCase):
    def test_no_matching_rows_returns_empty_list(self):
        columns, rows = execute("SELECT name FROM employee WHERE salary > 1000000;")
        self.assertEqual(rows, [])


class CustomSchemaExecutionTests(unittest.TestCase):
    def test_department_table_has_sample_rows(self):
        columns, rows = execute("SELECT dept_name FROM department;")
        self.assertEqual(len(rows), 3)


if __name__ == "__main__":
    unittest.main()
