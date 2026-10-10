# Optimization

The optimizer is rule-based and transparent. It is not cost-based and makes no performance claims.

Initial IR for `SELECT name FROM employee WHERE salary > 50000;`:

```
PROJECT(name) -> FILTER(salary > 50000) -> SCAN(employee)
```

Rules run in this order, and each returns a record with `applied`, `before`, `after` and `reason`.

## 1. Predicate Pushdown
**Applies when** the root is a Project directly above a Filter (a WHERE clause exists).
**Effect** reorders the logical plan to `FILTER -> PROJECT -> SCAN`.
**Not applied** when there is no WHERE clause.

Honest scope: the grammar supports one table and no joins, so no real data movement is being optimized. Rule 1 illustrates the pushdown idea in the logical representation. Because a filter above a projection is only valid when the projection keeps the filtered columns, the final execution plan does not trust this ordering: `execution_plan.py` always produces SCAN, FILTER, PROJECT. Pushdown becomes genuinely meaningful once joins are added.

## 2. Projection Reduction
**Applies when** the SELECT list contains duplicates, for example `SELECT name, name FROM employee;`.
**Effect** removes duplicates, keeping first occurrences in order: `PROJECT(name)`.

## 3. Constant Literal Simplification
**Applies when** a numeric literal in the WHERE condition is not in canonical form, for example `050000` or `50000.00`.
**Effect** rewrites it to `50000`. String literals are never changed.

## Demonstration queries

| Query | Rule that applies |
|---|---|
| `SELECT name FROM employee WHERE salary > 50000;` | Predicate Pushdown |
| `SELECT name, name FROM employee WHERE department = 'IT';` | Predicate Pushdown, Projection Reduction |
| `SELECT name FROM employee WHERE salary > 050000;` | Predicate Pushdown, Constant Literal Simplification |
| `SELECT name FROM employee;` | none |
