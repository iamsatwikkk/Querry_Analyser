import os
import sys
import time
import sqlite3

SRC_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from lexer import Lexer, LexicalError
from parser import Parser, ParseError
from ast_nodes import format_ast, ast_to_dict
from schema import Schema, create_sample_database
from semantic import SemanticAnalyzer, SemanticError
from ir import build_ir, render_ir, ir_to_list
from optimizer import optimize
from execution_plan import render_execution_plan, render_execution_summary, execution_plan_to_list


STAGE_ORDER = [
    "lexical",
    "syntax",
    "ast",
    "semantic",
    "ir",
    "optimization",
    "execution_plan",
    "execution",
]

PERFORMANCE_NOTE = (
    "Timings are local wall-clock measurements taken with time.perf_counter() "
    "around each real pipeline stage during this request. They are intended "
    "for comparative demonstration, not a formal benchmark."
)


def elapsed_ms(start):
    return round((time.perf_counter() - start) * 1000, 4)


def token_to_dict(token):
    return {
        "lexeme": token.value,
        "type": token.type.name,
        "line": token.line,
        "column": token.column,
    }


def check_to_dict(check):
    return {
        "category": check.category,
        "clause": check.clause,
        "name": check.name,
        "table": check.table,
        "status": "valid",
    }


def step_to_dict(step):
    return {
        "rule": step.rule,
        "applied": step.applied,
        "status": "Applied" if step.applied else "Not Applied",
        "before": step.before,
        "after": step.after,
        "reason": step.reason,
    }


def empty_result():
    return {
        "query": "",
        "valid": False,
        "stages": {name: "skipped" for name in STAGE_ORDER},
        "tokens": None,
        "syntax": None,
        "ast": None,
        "semantic": None,
        "ir": None,
        "optimization": None,
        "execution_plan": None,
        "result": None,
        "performance": {"note": PERFORMANCE_NOTE, "timings_ms": {}, "total_ms": 0},
        "error": None,
    }


def run_analysis(query, schema=None):
    schema = schema or Schema()
    result = empty_result()
    result["query"] = query
    timings = {}

    if not query or not query.strip():
        result["error"] = {
            "stage": "lexical",
            "type": "Lexical Error",
            "message": "Query is empty.",
        }
        return result

    start = time.perf_counter()
    try:
        tokens = Lexer(query).tokenize()
    except LexicalError as error:
        timings["lexical_analysis_ms"] = elapsed_ms(start)
        result["stages"]["lexical"] = "failed"
        result["error"] = {
            "stage": "lexical",
            "type": "Lexical Error",
            "message": f"{error.message} at line {error.line}, column {error.column}.",
        }
        result["performance"]["timings_ms"] = timings
        result["performance"]["total_ms"] = round(sum(timings.values()), 4)
        return result
    timings["lexical_analysis_ms"] = elapsed_ms(start)
    result["stages"]["lexical"] = "passed"
    result["tokens"] = [token_to_dict(token) for token in tokens]

    start = time.perf_counter()
    try:
        statement = Parser(tokens).parse()
    except ParseError as error:
        timings["syntax_analysis_ms"] = elapsed_ms(start)
        result["stages"]["syntax"] = "failed"
        result["syntax"] = {"status": "invalid", "message": None}
        result["error"] = {
            "stage": "syntax",
            "type": "Syntax Error",
            "message": f"{error.message} at line {error.line}, column {error.column}.",
        }
        result["performance"]["timings_ms"] = timings
        result["performance"]["total_ms"] = round(sum(timings.values()), 4)
        return result
    timings["syntax_analysis_ms"] = elapsed_ms(start)
    result["stages"]["syntax"] = "passed"
    result["syntax"] = {"status": "valid", "message": "Valid SELECT statement"}

    start = time.perf_counter()
    tree_text = format_ast(statement)
    tree_dict = ast_to_dict(statement)
    timings["ast_construction_ms"] = elapsed_ms(start)
    result["stages"]["ast"] = "passed"
    result["ast"] = {"text": tree_text, "tree": tree_dict}

    start = time.perf_counter()
    try:
        checks = SemanticAnalyzer(schema).analyze(statement)
    except SemanticError as error:
        timings["semantic_analysis_ms"] = elapsed_ms(start)
        result["stages"]["semantic"] = "failed"
        result["semantic"] = {"checks": [], "schema": schema.as_dict()}
        result["error"] = {
            "stage": "semantic",
            "type": "Semantic Error",
            "message": f"{error.message}.",
        }
        result["performance"]["timings_ms"] = timings
        result["performance"]["total_ms"] = round(sum(timings.values()), 4)
        return result
    timings["semantic_analysis_ms"] = elapsed_ms(start)
    result["stages"]["semantic"] = "passed"
    result["semantic"] = {
        "checks": [check_to_dict(check) for check in checks],
        "schema": schema.as_dict(),
    }

    start = time.perf_counter()
    ir_root = build_ir(statement)
    timings["ir_generation_ms"] = elapsed_ms(start)
    result["stages"]["ir"] = "passed"
    result["ir"] = {"lines": ir_to_list(ir_root), "text": render_ir(ir_root)}

    start = time.perf_counter()
    optimized_ir, steps = optimize(statement)
    timings["optimization_ms"] = elapsed_ms(start)
    result["stages"]["optimization"] = "passed"
    result["optimization"] = {"rules": [step_to_dict(step) for step in steps]}

    result["stages"]["execution_plan"] = "passed"
    result["execution_plan"] = {
        "lines": execution_plan_to_list(optimized_ir),
        "text": render_execution_plan(optimized_ir),
        "flow": render_execution_summary(optimized_ir),
    }

    start = time.perf_counter()
    connection = create_sample_database(schema)
    try:
        cursor = connection.execute(query)
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        timings["execution_ms"] = elapsed_ms(start)
        result["stages"]["execution"] = "passed"
        result["result"] = {
            "columns": columns,
            "rows": [list(row) for row in rows],
            "row_count": len(rows),
        }
        result["valid"] = True
    except sqlite3.Error as error:
        timings["execution_ms"] = elapsed_ms(start)
        result["stages"]["execution"] = "failed"
        result["error"] = {
            "stage": "execution",
            "type": "Execution Error",
            "message": str(error),
        }
    finally:
        connection.close()

    result["performance"]["timings_ms"] = timings
    result["performance"]["total_ms"] = round(sum(timings.values()), 4)
    return result


def run_execution_only(query, schema=None):
    schema = schema or Schema()
    if not query or not query.strip():
        return {"valid": False, "stage": "lexical", "error": "Query is empty."}

    try:
        tokens = Lexer(query).tokenize()
    except LexicalError as error:
        return {
            "valid": False,
            "stage": "lexical",
            "error": f"{error.message} at line {error.line}, column {error.column}.",
        }

    try:
        statement = Parser(tokens).parse()
    except ParseError as error:
        return {
            "valid": False,
            "stage": "syntax",
            "error": f"{error.message} at line {error.line}, column {error.column}.",
        }

    try:
        SemanticAnalyzer(schema).analyze(statement)
    except SemanticError as error:
        return {"valid": False, "stage": "semantic", "error": f"{error.message}."}

    connection = create_sample_database(schema)
    try:
        cursor = connection.execute(query)
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        return {
            "valid": True,
            "columns": columns,
            "rows": [list(row) for row in rows],
            "row_count": len(rows),
        }
    except sqlite3.Error as error:
        return {"valid": False, "stage": "execution", "error": str(error)}
    finally:
        connection.close()
