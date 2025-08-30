import json
import sqlite3
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from core.config import DB_PATH

def _conn():
    return sqlite3.connect(DB_PATH)

def log_tool_call(agent: str, tool_name: str, inputs: Dict[str, Any], outputs: Any, status: str = "ok"):
    try:
        with _conn() as conn:
            conn.execute(
                """
                INSERT INTO tool_calls (agent, tool_name, input_json, output_json, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    agent,
                    tool_name,
                    json.dumps(inputs, ensure_ascii=False),
                    json.dumps(outputs, ensure_ascii=False, default=str),
                    datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                ),
            )
    except Exception:
        # Auditing must never crash the app
        pass

def requires_approval(module: str, action: str, payload: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    # Example policies; tune thresholds to your needs
    if module == "finance" and action in {"create_invoice", "post_payment"}:
        amount = float(payload.get("total_amount", payload.get("amount", 0)) or 0)
        if amount >= 10000:
            return True, f"Finance action '{action}' over threshold requires approval."
    if module == "inventory" and action in {"create_po"}:
        total = float(payload.get("total", 0) or 0)
        if total >= 20000:
            return True, "Large purchase order requires approval."
    return False, None

def request_approval(module: str, payload: Dict[str, Any], requested_by: str) -> int:
    with _conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO approvals (module, payload_json, status, requested_by, created_at)
            VALUES (?, ?, 'pending', ?, ?)
            """,
            (
                module,
                json.dumps(payload, ensure_ascii=False),
                requested_by,
                datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            ),
        )
        return cur.lastrowid

def save_message(conversation_id: int, sender: str, content: str):
    with _conn() as conn:
        conn.execute(
            """
            INSERT INTO messages (conversation_id, sender, content, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                conversation_id,
                sender,
                content,
                datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            ),
        )

def ensure_conversation(user_id: str) -> int:
    with _conn() as conn:
        cur = conn.execute(
            "SELECT id FROM conversations WHERE user_id = ? ORDER BY started_at DESC LIMIT 1",
            (user_id,),
        )
        row = cur.fetchone()
        if row:
            return row[0]
        cur = conn.execute(
            "INSERT INTO conversations (user_id, started_at) VALUES (?, ?)",
            (user_id, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")),
        )
        return cur.lastrowid
