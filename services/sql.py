# services/sql.py
import sqlite3
import os

# Resolve DB path to an absolute location inside the project by default
DB_PATH = os.getenv(
    "ERP_DB_PATH",
    os.path.join(os.path.dirname(__file__), "..", "db", "erp_v2.db")
)
DB_PATH = os.path.abspath(DB_PATH)



def execute_query(query: str, params: tuple = ()):
    """
    Execute raw SQL against the ERP database.

    Args:
        query (str): SQL query to execute.
        params (tuple): Optional parameters for the query.

    Returns:
        list of tuples for SELECT queries,
        None for non-SELECT queries.

    Raises:
        sqlite3.Error (or subclass) if the query fails.
    """
    print(f"[DEBUG] Using DB path: {DB_PATH}")
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)

            if query.strip().lower().startswith("select"):
                rows = cursor.fetchall()
                print(f"[DEBUG] Query returned {len(rows)} row(s)")
                return rows

            # Non-SELECT queries are automatically committed by the context manager
            print("[DEBUG] Non-SELECT query executed successfully")
            return None

    except sqlite3.Error as e:
        print(f"[DEBUG] SQL execution error: {e}")
        raise
