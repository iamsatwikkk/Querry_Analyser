# Architecture

## Layers

1. **Frontend** (`frontend/`) - static HTML, CSS and JavaScript. It calls the API with relative URLs (`/api/analyze`, `/api/schema`), so it works on localhost and on Vercel without configuration.
2. **API** (`api/index.py`) - a FastAPI app exposing `/api/health`, `/api/schema`, `/api/analyze`, `/api/execute`. It also serves the frontend files, so one deployment contains everything.
3. **Pipeline** (`api/pipeline.py`) - runs the compiler stages in order, times each with `time.perf_counter()`, converts results to JSON, and stops at the first failing stage.
4. **Compiler modules** (`src/`) - independent of the web layer and usable from any Python code.

## Pipeline

```
SQL text
 -> Lexer.tokenize()            -> tokens
 -> Parser.parse()              -> SelectStatement (AST)
 -> format_ast / ast_to_dict    -> displayable tree
 -> SemanticAnalyzer.analyze()  -> checks (table, select columns, where columns)
 -> build_ir()                  -> Project -> Filter -> Scan
 -> optimize()                  -> optimized IR + rule records
 -> build_execution_plan()      -> Scan, Filter, Project
 -> SQLite execution            -> columns and rows
```

## Error model

Each stage raises its own exception (`LexicalError`, `ParseError`, `SemanticError`). The pipeline catches them, marks that stage `failed`, marks later stages `skipped`, and returns a structured `error` object with `stage`, `type` and `message`. SQLite errors are reported separately as Execution Errors.

## Path handling

`api/index.py` and `api/pipeline.py` add `src/` to `sys.path` using paths computed from `__file__`, and the frontend directory is also resolved from `__file__`. No working-directory assumptions, absolute paths or port numbers appear in the code.

## Data

The schema (`employee`, `department`) and its sample rows live in `src/schema.py`. A fresh in-memory SQLite database is created for every request, so requests cannot affect each other and nothing is persisted.
