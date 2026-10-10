# SQL Query Analyzer and Optimizer Using Compiler Design Techniques

**Student:** Satwik Som | **Register Number:** 24BCE2822
**Course:** Compiler Design Laboratory | **Milestone:** Final (Phase 3)
**Repository:** SQL_QUERRY_ANALYSER

A web-based tool that processes a SQL `SELECT` query the way a compiler processes source code, and shows every internal stage instead of only the final database result.

## Overview

A query goes through lexical analysis, syntax analysis, AST construction, semantic analysis against a schema, translation into a relational intermediate representation, rule-based optimization, execution-plan generation, and finally execution against an in-memory SQLite sample database. The web interface exposes each stage in its own tab, with real per-stage timings.

## Problem Statement

Database engines report SQL mistakes with engine-specific messages, and their optimizers are opaque. This project applies classical compiler techniques to a SQL subset to give position-aware diagnostics and a transparent, explainable optimization process.

## Compiler Design Relevance

| Stage | Module | Concept |
|---|---|---|
| Lexical analysis | `src/lexer.py` | Character-by-character scanning, token classification, lexical errors |
| Syntax analysis | `src/parser.py` | Recursive-descent parsing of an explicit grammar |
| AST | `src/ast_nodes.py` | Tree construction and traversal |
| Semantic analysis | `src/semantic.py`, `src/schema.py` | Symbol-table lookups, semantic errors |
| Intermediate representation | `src/ir.py` | Relational IR (Scan / Filter / Project) |
| Optimization | `src/optimizer.py` | Rule-based IR rewriting |
| Execution plan | `src/execution_plan.py` | Lowering the optimized IR into ordered steps |

## Architecture

```
Browser (frontend/: HTML, CSS, JavaScript)
        |  relative URLs: /api/...
FastAPI app (api/index.py)  ->  api/pipeline.py (orchestration, timing, JSON)
        |
Compiler modules (src/): tokens, lexer, parser, ast_nodes, schema,
semantic, ir, optimizer, execution_plan
        |
SQLite in-memory sample database (schema.py)
```

The compiler modules know nothing about the web layer. `api/pipeline.py` calls them in order, measures each stage with `time.perf_counter()`, and serializes the results to JSON. One FastAPI app serves both the API and the frontend, so a single Vercel deployment is enough.

## Currently Implemented

- Lexical analysis with line/column tracking, number (including decimal), string and operator tokens
- Recursive-descent syntax analysis with position-aware errors and trailing-token detection
- AST construction, with both a text tree and a JSON tree
- Semantic analysis (table and column existence, tracked per clause)
- Relational IR, three rule-based optimizer rules, execution plan
- Execution on an in-memory SQLite sample database
- Per-stage performance measurements
- FastAPI backend, lightweight HTML/CSS/JS frontend
- 79 automated tests

## Supported SQL Subset

```
select_stmt      -> SELECT column_list FROM table_name [WHERE condition] ;
column_list      -> identifier | identifier , column_list
condition        -> identifier operator literal
                  | identifier operator literal logical_op condition
logical_op       -> AND | OR
operator         -> = | > | < | >= | <=
literal          -> NUMBER | 'STRING'
```

Single table only. Keywords are case-insensitive. Identifiers are case-sensitive and must match the schema exactly.

## Optimization Rules

1. **Predicate Pushdown** - reorders Filter ahead of Project in the logical representation when a WHERE clause exists.
2. **Projection Reduction** - removes duplicate columns from the projection list.
3. **Constant Literal Simplification** - normalizes numeric literals such as `050000` to `50000`.

These are rule-based only. There is no cost model. See `docs/optimization.md` for the honest scope of Rule 1.

## Project Structure

```
sql-query-analyzer-optimizer/
├── src/        compiler modules
├── api/        FastAPI app (index.py) and pipeline.py
├── frontend/   index.html, styles.css, app.js
├── tests/      module-wise tests
├── docs/       architecture, compiler concepts, optimization, testing
├── README.md  DEPLOYMENT.md  USER_GUIDE.md
├── requirements.txt  requirements-dev.txt  vercel.json
```

## API Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health` | Liveness check, returns `{"status": "ok"}` |
| GET | `/api/schema` | Sample schema (tables and columns) |
| POST | `/api/analyze` | Full pipeline; body `{"query": "..."}` |
| POST | `/api/execute` | Validates (lex, parse, semantic) then executes only; returns rows |

`/api/analyze` returns `query`, `valid`, `stages`, `tokens`, `syntax`, `ast`, `semantic`, `ir`, `optimization`, `execution_plan`, `result`, `performance` and `error`.

## Local Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
python3 -m uvicorn api.index:app --reload --port 8000
```

Open http://127.0.0.1:8000 in a browser (the same server serves the UI and the API).

Test the API:

```bash
curl http://127.0.0.1:8000/api/health
curl -X POST http://127.0.0.1:8000/api/analyze -H "Content-Type: application/json" -d '{"query": "SELECT name FROM employee WHERE salary > 50000;"}'
```

## Testing

```bash
python3 -m unittest discover -s tests -v
```

## Deployment to Vercel

See [DEPLOYMENT.md](DEPLOYMENT.md).

## User Instructions

See [USER_GUIDE.md](USER_GUIDE.md).

## Examples

```sql
SELECT name FROM employee;
SELECT name, salary FROM employee WHERE salary > 50000;
SELECT name FROM employee WHERE department = 'IT' OR department = 'HR';
SELECT name, name FROM employee;
SELECT name FROM employee WHERE salary > 050000;
SELECT age FROM employee;
```

## Known Limitations

- Single table, `SELECT` only. No joins, subqueries, `SELECT *`, `GROUP BY`, `ORDER BY`, aggregates, or parentheses in conditions.
- Chained AND/OR conditions are parsed right-recursively with no operator precedence handling in the AST; the query is still executed by SQLite, which applies standard SQL precedence.
- The sample database is a small fixed in-memory dataset recreated for every request.
- Predicate Pushdown is a logical-plan illustration; with one table there is nothing real to push below.
- Timings are local measurements for comparison, not a formal benchmark.
- `/api/execute` and `/api/analyze` run the query text through SQLite only after it passes the compiler's lexer, parser and semantic checks.

## Future Enhancements

- Joins across tables, where predicate pushdown becomes genuinely meaningful
- Parenthesized conditions with proper precedence in the AST
- `ORDER BY`, `GROUP BY`, aggregates
- Cost-based optimization using table statistics
- User-defined schemas
