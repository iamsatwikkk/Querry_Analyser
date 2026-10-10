# Compiler Concepts in This Project

## Lexical analysis (`src/lexer.py`)
The lexer reads the source one character at a time, groups characters into lexemes, and classifies each as a token: keyword, identifier, number, string, operator, comma or semicolon. It tracks line and column, so errors point at an exact position. Keywords are matched case-insensitively against a fixed set. An unrecognized character or an unterminated string raises `LexicalError`.

## Syntax analysis (`src/parser.py`)
A hand-written recursive-descent parser: one method per grammar rule (`_parse_select_statement`, `_parse_column_list`, `_parse_table_name`, `_parse_condition`). It uses one token of lookahead. Errors state what was expected and where. After the semicolon the next token must be EOF, otherwise the parser reports a trailing token.

## Abstract syntax tree (`src/ast_nodes.py`)
The parser builds `SelectStatement`, `Identifier`, `Literal`, `Comparison`, `LogicalCondition`, `TableReference` and `WhereClause` nodes. The tree is parsed in a single pass, so syntax validation and AST construction happen together; the displayed tree is derived from the real nodes.

## Symbol table and semantic analysis (`src/schema.py`, `src/semantic.py`)
`Schema` is the symbol table: it answers whether a table exists, whether a column exists in a table, and which columns a table has. `SemanticAnalyzer` walks the AST (not the raw text) and checks the table, the SELECT columns and the WHERE columns, recording which clause each check came from.

## Intermediate representation (`src/ir.py`)
A relational IR with `ScanNode`, `FilterNode` and `ProjectNode`, linked by `child`. It is built from the validated AST. A relational IR suits SQL better than three-address code because queries describe set operations, not sequential instructions.

## Optimization (`src/optimizer.py`)
Each rule inspects the IR, decides whether it applies, rewrites it, and returns a record (rule, applied, before, after, reason). See `optimization.md`.

## Code generation analogue (`src/execution_plan.py`)
The execution plan lowers the optimized IR into an ordered list of steps. It is derived by locating the Scan, Filter and Project nodes, so the order is always Scan, Filter, Project regardless of how the optimizer arranged the logical display.

## Execution
The original, already-validated query text is run on an in-memory SQLite database. The project does not implement its own execution engine.
