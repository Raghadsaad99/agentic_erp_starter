# core/db.py
import os
import sqlite3

# Same env‑driven path as app/db.py
DB_PATH = os.getenv("DATABASE_PATH", "/app/db/erp_v2.db")

def execute_query(query):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(query)
        if query.strip().lower().startswith("select"):
            result = cursor.fetchall()
        else:
            conn.commit()
            result = "Query executed successfully"
        return result
    except Exception as e:
        return f"Error executing query: {str(e)}"
    finally:
        conn.close()
