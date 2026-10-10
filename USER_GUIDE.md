# User Guide

## Entering and analyzing a query

Type a SQL query into the dark **SQL Editor** panel, or choose one from **Example queries**. Click **Analyze Query** (or press Ctrl/Cmd + Enter). **Clear** empties the editor and **Copy Query** copies its contents.

Supported queries have the form `SELECT columns FROM table [WHERE conditions];` and must end with a semicolon. The **Schema** panel lists the tables and columns you may use.

The status pill in the header shows Idle, Analyzing, Valid or Invalid for the last run.

## Tabs

**Overview** - Query status (VALID or INVALID) and a tick or cross for each pipeline stage. A dash means the stage was skipped because an earlier stage failed. Any error is shown here with its type and message.

**Tokens** - The lexer's output: lexeme, token type (KEYWORD, IDENTIFIER, NUMBER, STRING, OPERATOR, COMMA, SEMICOLON, EOF), and the line and column where it starts.

**Syntax / AST** - Whether the query matches the grammar, and the abstract syntax tree. `SELECT` is the root; `COLUMNS`, `FROM` and `WHERE` are its children. Comparisons appear as an operator node with the column and the value beneath it; AND/OR combine comparisons.

**Semantic** - Checks the AST against the schema: the table, the SELECT columns and the WHERE columns, each marked VALID. If a name does not exist, you see a SEMANTIC ERROR such as `Column 'age' does not exist in table 'employee'.`

**IR** - The intermediate representation, read top to bottom: `PROJECT` takes the output of `FILTER`, which takes the output of `SCAN`.

**Optimization** - One card per rule with status (Applied or Not Applied), the reason, and the plan Before and After. A rule that does not apply shows identical Before and After.

**Execution Plan** - The ordered steps actually executed: SCAN, then FILTER (if there is a WHERE clause), then PROJECT, plus a one-line Flow summary.

**Result** - The rows returned by executing the query on the sample SQLite database. If nothing matches, it says so. Invalid queries are never executed; the tab explains which stage stopped them.

**Performance** - Time spent in each stage in milliseconds, measured on the server with `time.perf_counter()`, plus the total. These are local measurements for comparison, not a formal benchmark, and they vary between runs.

## Errors

| Error | Meaning | Example |
|---|---|---|
| Lexical Error | A character the lexer does not recognize, or an unterminated string | `salary @ 50000` |
| Syntax Error | Tokens are valid but not in the allowed order | `SELECT FROM employee;` |
| Semantic Error | Valid syntax, but a table or column is not in the schema | `SELECT age FROM employee;` |
| Execution Error | SQLite itself failed (rare, since the query already passed validation) | - |

Errors include the line and column where the problem was found (lexical and syntax errors). When a query fails, the app switches to the Overview tab so the error is visible.

## Suggested walkthrough

1. Analyze `SELECT name, salary FROM employee WHERE salary > 50000;` and visit each tab in order.
2. Analyze `SELECT age FROM employee;` to see a semantic error.
3. Analyze `SELECT FROM employee;` to see a syntax error.
4. Return to the valid query.
