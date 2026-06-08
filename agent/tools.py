import json

from pathlib import Path
from typing import Any

import duckdb
from openrouter.components import ChatToolCall

DUCKDB_PATH = Path(__file__).resolve().parents[1] / "warehouse" / "data.duckdb"
DUCKDB_TOOL = {
    "type": "function",
    "function": {
        "name": "query_duckdb",
        "description": (
            "Run a read-only SQL query against the local DuckDB GTM warehouse. "
            "Use this to discover schemas/tables and retrieve internal account or "
            "prospect context such as deal history, product usage, call intelligence, "
            "and marketing engagement. Prefer small, targeted queries and include "
            "LIMIT clauses when exploring data."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "A single read-only DuckDB SQL statement. Supported statement "
                        "types include SELECT, WITH, SHOW, DESCRIBE/DESC, EXPLAIN, and SUMMARIZE."
                    ),
                },
                "max_rows": {
                    "type": "integer",
                    "description": "Maximum rows to return. Defaults to 100 and is capped at 500.",
                    "minimum": 1,
                    "maximum": 500,
                },
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    },
}


def run_duckdb_query(query: str, max_rows: int = 100) -> str:
    """Run a read-only DuckDB query and return a JSON string for an LLM tool message."""
    query = query.strip()

    if not query:
        return json.dumps({"error": "query must not be empty"})

    max_rows = max(1, min(int(max_rows), 500))

    try:
        with duckdb.connect(DUCKDB_PATH, read_only=True) as connection:
            result = connection.execute(query)
            columns = [column[0] for column in result.description or []]
            rows = result.fetchmany(max_rows + 1)
    except Exception as exc:
        return json.dumps({"error": str(exc)})

    limited_rows = rows[:max_rows]

    return json.dumps(
        {
            "columns": columns,
            "rows": [row for row in limited_rows],
            "row_count": len(limited_rows),
            "truncated": len(rows) > max_rows,
        },
        default=str,
    )


def execute_duckdb_tool_call(tool_call: ChatToolCall) -> dict[str, str]:
    """Execute an OpenRouter DuckDB tool call and return a tool-message dict."""
    try:
        arguments = json.loads(tool_call.function.arguments or "{}")
    except json.JSONDecodeError as exc:
        content = json.dumps({"error": f"Invalid JSON arguments: {exc}"})
    else:
        content = run_duckdb_query(
            query=arguments.get("query", ""),
            max_rows=arguments.get("max_rows", 100),
        )

    return {"role": "tool", "tool_call_id": tool_call.id, "content": content}
