import sqlite3


SAMPLE_SCHEMA = {
    "employee": ["id", "name", "salary", "department"],
    "department": ["dept_id", "dept_name"],
}

SAMPLE_ROWS = {
    "employee": [
        (1, "Alice", 60000, "IT"),
        (2, "Bob", 45000, "HR"),
        (3, "Charlie", 72000, "IT"),
        (4, "Diana", 50000, "Finance"),
    ],
    "department": [
        (1, "IT"),
        (2, "HR"),
        (3, "Finance"),
    ],
}


class Schema:
    def __init__(self, tables=None):
        self.tables = tables if tables is not None else SAMPLE_SCHEMA

    def table_exists(self, table_name):
        return table_name in self.tables

    def column_exists(self, table_name, column_name):
        return column_name in self.tables.get(table_name, [])

    def columns_for(self, table_name):
        return list(self.tables.get(table_name, []))

    def as_dict(self):
        return {table: list(columns) for table, columns in self.tables.items()}


def create_sample_database(schema=None):
    schema = schema or Schema()
    connection = sqlite3.connect(":memory:")
    cursor = connection.cursor()
    for table_name, columns in schema.tables.items():
        column_definitions = ", ".join(columns)
        cursor.execute(f"CREATE TABLE {table_name} ({column_definitions})")
        rows = SAMPLE_ROWS.get(table_name, [])
        if rows:
            placeholders = ", ".join("?" for _ in columns)
            cursor.executemany(f"INSERT INTO {table_name} VALUES ({placeholders})", rows)
    connection.commit()
    return connection
