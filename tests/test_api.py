import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "api"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from fastapi.testclient import TestClient
import index

client = TestClient(index.app)


class HealthEndpointTests(unittest.TestCase):
    def test_health_returns_ok(self):
        response = client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})


class SchemaEndpointTests(unittest.TestCase):
    def test_schema_contains_employee_and_department(self):
        response = client.get("/api/schema")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("employee", data)
        self.assertIn("department", data)


class AnalyzeEndpointValidTests(unittest.TestCase):
    def test_valid_query_has_all_stages_passed(self):
        response = client.post(
            "/api/analyze",
            json={"query": "SELECT name, salary FROM employee WHERE salary > 50000;"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["valid"])
        self.assertTrue(all(status == "passed" for status in data["stages"].values()))
        self.assertIsNone(data["error"])

    def test_valid_query_has_tokens(self):
        response = client.post("/api/analyze", json={"query": "SELECT name FROM employee;"})
        data = response.json()
        self.assertGreater(len(data["tokens"]), 0)
        self.assertEqual(data["tokens"][0]["lexeme"], "SELECT")
        self.assertEqual(data["tokens"][0]["type"], "KEYWORD")

    def test_valid_query_has_ast_tree(self):
        response = client.post("/api/analyze", json={"query": "SELECT name FROM employee;"})
        data = response.json()
        self.assertEqual(data["ast"]["tree"]["label"], "SELECT")

    def test_valid_query_has_optimization_rules(self):
        response = client.post(
            "/api/analyze",
            json={"query": "SELECT name FROM employee WHERE salary > 50000;"},
        )
        data = response.json()
        rule_names = [rule["rule"] for rule in data["optimization"]["rules"]]
        self.assertIn("Predicate Pushdown", rule_names)
        self.assertIn("Constant Literal Simplification", rule_names)
        self.assertIn("Projection Reduction", rule_names)

    def test_valid_query_has_execution_result(self):
        response = client.post(
            "/api/analyze",
            json={"query": "SELECT name FROM employee WHERE salary > 50000;"},
        )
        data = response.json()
        self.assertIn("name", data["result"]["columns"])
        self.assertGreater(data["result"]["row_count"], 0)

    def test_valid_query_has_performance_timings(self):
        response = client.post("/api/analyze", json={"query": "SELECT name FROM employee;"})
        data = response.json()
        self.assertIn("lexical_analysis_ms", data["performance"]["timings_ms"])
        self.assertGreaterEqual(data["performance"]["total_ms"], 0)


class PerformanceCorrectnessTests(unittest.TestCase):
    def test_timings_do_not_change_results(self):
        query = "SELECT name FROM employee WHERE department = 'IT';"
        analyzed = client.post("/api/analyze", json={"query": query}).json()
        executed = client.post("/api/execute", json={"query": query}).json()
        self.assertEqual(analyzed["result"]["rows"], executed["rows"])
        timings = analyzed["performance"]["timings_ms"]
        self.assertTrue(all(value >= 0 for value in timings.values()))
        self.assertAlmostEqual(
            analyzed["performance"]["total_ms"], sum(timings.values()), places=2
        )


class AnalyzeEndpointInvalidTests(unittest.TestCase):
    def test_lexical_error_stops_pipeline_early(self):
        response = client.post(
            "/api/analyze",
            json={"query": "SELECT name FROM employee WHERE salary @ 50000;"},
        )
        data = response.json()
        self.assertFalse(data["valid"])
        self.assertEqual(data["error"]["stage"], "lexical")
        self.assertEqual(data["stages"]["syntax"], "skipped")

    def test_syntax_error_reported(self):
        response = client.post("/api/analyze", json={"query": "SELECT FROM employee;"})
        data = response.json()
        self.assertFalse(data["valid"])
        self.assertEqual(data["error"]["stage"], "syntax")

    def test_semantic_error_reported(self):
        response = client.post("/api/analyze", json={"query": "SELECT age FROM employee;"})
        data = response.json()
        self.assertFalse(data["valid"])
        self.assertEqual(data["error"]["stage"], "semantic")
        self.assertIn("age", data["error"]["message"])

    def test_empty_query_reported(self):
        response = client.post("/api/analyze", json={"query": ""})
        data = response.json()
        self.assertFalse(data["valid"])
        self.assertEqual(data["error"]["stage"], "lexical")


class ExecuteEndpointTests(unittest.TestCase):
    def test_execute_valid_query(self):
        response = client.post(
            "/api/execute", json={"query": "SELECT name FROM employee WHERE department = 'IT';"}
        )
        data = response.json()
        self.assertTrue(data["valid"])
        self.assertEqual(data["row_count"], 2)

    def test_execute_invalid_query_not_run(self):
        response = client.post("/api/execute", json={"query": "SELECT age FROM employee;"})
        data = response.json()
        self.assertFalse(data["valid"])
        self.assertEqual(data["stage"], "semantic")

    def test_execute_no_matching_rows(self):
        response = client.post(
            "/api/execute",
            json={"query": "SELECT name FROM employee WHERE salary > 1000000;"},
        )
        data = response.json()
        self.assertTrue(data["valid"])
        self.assertEqual(data["row_count"], 0)


class FrontendServingTests(unittest.TestCase):
    def test_index_served_at_root(self):
        response = client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("SQL Query Analyzer", response.text)

    def test_static_assets_served(self):
        response = client.get("/static/styles.css")
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
