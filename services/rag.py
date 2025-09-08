# services/rag.py
from typing import List, Dict
import sqlite3
from core.config import DB_PATH

def _conn():
    return sqlite3.connect(DB_PATH)

def rag_definition_tool(query: str, module_filter: str = "") -> List[Dict[str, str]]:
    tl = query.lower()
    sql = "SELECT term, definition, module FROM glossary"
    params = []
    clauses = []
    if module_filter:
        clauses.append("module = ?")
        params.append(module_filter)
    if tl:
        clauses.append("LOWER(term) LIKE ? OR LOWER(definition) LIKE ?")
        params.extend([f"%{tl}%", f"%{tl}%"])
    if clauses:
        sql += " WHERE " + " AND ".join(["(" + " OR ".join(clauses[-2:]) + ")"] if len(clauses) > 1 else clauses)
    sql += " LIMIT 5"
    with _conn() as conn:
        rows = conn.execute(sql, params).fetchall()
        return [{"term": r[0], "definition": r[1], "module": r[2]} for r in rows]

def policy_rag_tool(query: str) -> List[Dict[str, str]]:
    # Simple search over documents tagged 'policy'
    with _conn() as conn:
        rows = conn.execute(
            "SELECT module, path, tags FROM documents WHERE LOWER(tags) LIKE '%policy%' ORDER BY created_at DESC LIMIT 10"
        ).fetchall()
    return [{"module": r[0], "path": r[1], "tags": r[2]} for r in rows]
