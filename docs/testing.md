# Testing

Run everything:

```bash
python3 -m unittest discover -s tests -v
```

The suite has 79 tests. API tests need `httpx2` (`pip install -r requirements-dev.txt`).

| File | Covers |
|---|---|
| `test_lexer.py` | token classification, numbers, decimals, strings, empty strings, operators, line/column tracking, long identifiers, long column lists, unsupported characters, unterminated strings, error positions |
| `test_parser.py` | AST for simple/multi-column/WHERE/AND/OR/multiple conditions, long column lists, minimum query, AST display and dict, missing column/FROM/table, incomplete WHERE, malformed operator, trailing tokens |
| `test_semantic.py` | valid table and columns, clause tracking, unknown table, unknown SELECT column, unknown WHERE column, error message content, custom schema |
| `test_ir.py` | IR shape with and without WHERE, columns, table, rendering, list form |
| `test_optimizer.py` | each rule applied and not applied, duplicate columns, non-canonical literals, with and without WHERE, execution plan order and optimized columns |
| `test_execution.py` | successful execution, string comparison, AND, OR, no matching rows, second table |
| `test_api.py` | health, schema, analyze (valid, lexical, syntax, semantic, empty), per-stage status, tokens, AST, optimizer rules, result, performance timings, execute endpoint, invalid query not executed, frontend served |

Timing tests check that timings are present and non-negative; they deliberately do not assert specific values because real measurements vary between runs.
