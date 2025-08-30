# services/sql.py
import sqlite3
import os

DB_PATH = os.getenv("ERP_DB_PATH", "db/erp_v2.db")

def execute_query(query: str, params: tuple = ()):
    """
    Execute raw SQL against the ERP database.

    Returns:
        list of tuples for SELECT queries,
        None for non-SELECT queries.

    Raises:
        sqlite3.Error (or subclass) if the query fails.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        if query.strip().lower().startswith("select"):
            return cursor.fetchall()
        conn.commit()
        return None
    except Exception:
        # Let the caller (_run_sql) handle the error
        raise
    finally:
        conn.close()
