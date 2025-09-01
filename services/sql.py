# services/sql.py
import sqlite3
from core.config import DB_PATH  # single source of truth

def execute_query(query: str, params: tuple = ()):
    """
    Execute raw SQL against the ERP database.

    Args:
        query (str): SQL query to execute.
        params (tuple): Optional parameters for the query.

    Returns:
        list of tuples for SELECT queries,
        None for non-SELECT queries.
    """
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)

            if query.strip().lower().startswith("select"):
                return cursor.fetchall()

            # Non-SELECT queries are auto-committed by the context manager
            return None

    except sqlite3.Error as e:
        # Bubble up to callers so they can render a useful error payload
        raise
