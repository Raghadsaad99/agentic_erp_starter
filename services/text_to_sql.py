# services/text_to_sql.py
from sqlite3 import OperationalError
from services.sql import execute_query
from services.llm import llm
from langchain.schema import AIMessage

def text_to_sql_tool(user_input):
    text = user_input.content if isinstance(user_input, AIMessage) else str(user_input)
    tl = text.strip().lower()

    # Greetings
    if tl in {"hi", "hello", "hey"} or any(tl.startswith(g + " ") for g in ["hi", "hello", "hey"]):
        return {"type": "text", "content": "👋 Hello! How can I help with your ERP data today?"}

    # Customers
    if ("list" in tl or "show" in tl or "get" in tl) and "customers" in tl:
        sql = "SELECT id, name, email FROM customers;" if "email" in tl else "SELECT id, name FROM customers;"
        return _run_sql(sql, intent="sales_read_customers")

    # Invoices
    if ("list" in tl or "show" in tl) and "invoices" in tl:
        sql = """
        SELECT i.id, c.name AS customer_name,
               i.invoice_number, i.total_amount, i.status
        FROM invoices i
        JOIN customers c ON c.id = i.customer_id;
        """
        return _run_sql(sql, intent="finance_read_invoices")

    # Stock levels
    if "check" in tl and ("stock" in tl or "inventory" in tl):
        sql = """
        SELECT p.id   AS product_id,
               p.name AS product_name,
               s.qty_on_hand,
               s.reorder_point
        FROM stock s
        JOIN products p ON p.id = s.product_id;
        """
        return _run_sql(sql, intent="inventory_read_stock")

    # Analytics report — now more specific
    if ("analytics" in tl and "report" in tl) or "analytics report" in tl:
        sql = """
        SELECT p.id AS product_id,
               p.name AS product_name,
               SUM(oi.quantity) AS total_sold,
               SUM(oi.quantity * oi.price) AS total_revenue
        FROM order_items oi
        JOIN products p ON p.id = oi.product_id
        GROUP BY p.id, p.name;
        """
        result = _run_sql(sql, intent="analytics_report")
        if not result["rows"]:
            return {"type": "text", "content": "No analytics data found for the requested period."}
        return result

    # Direct SQL passthrough
    if tl.startswith(("select ", "with ", "pragma ")):
        return _run_sql(text)

    # Fallback to LLM
    try:
        prompt = (
            "You are an expert SQL generator for a SQLite ERP database. "
            "Return ONLY a syntactically correct SQLite SELECT query without explanations:\n"
            f"{text}\n"
        )
        sql = llm.invoke(prompt)
        if isinstance(sql, AIMessage):
            sql = sql.content
        sql = sql.strip().strip("```").strip("sql").strip()
        return _run_sql(sql)
    except Exception as e:
        return {"type": "error", "message": f"Error generating SQL: {e}"}


def _run_sql(sql: str, intent: str = ""):
    try:
        raw_rows = execute_query(sql) or []

        # Normalise to list-of-lists
        rows = []
        for r in raw_rows:
            if isinstance(r, dict):
                rows.append(list(r.values()))
            elif isinstance(r, (list, tuple)):
                rows.append(list(r))
            else:
                try:
                    rows.append(list(r))
                except Exception:
                    rows.append([str(r)])

        # Headers by intent
        if intent == "sales_read_customers":
            headers = ["Customer ID", "Name", "Email"] if rows and len(rows[0]) >= 3 else ["Customer ID", "Name"]
        elif intent == "finance_read_invoices":
            headers = ["Invoice ID", "customer_name", "Invoice #", "Amount", "Status"]
        elif intent == "inventory_read_stock":
            headers = ["Product ID", "Product Name", "Qty On Hand", "Reorder Point"]
        elif intent == "analytics_report":
            headers = ["Product ID", "Product Name", "Total Sold", "Total Revenue"]
        else:
            headers = [f"col_{i}" for i in range(len(rows[0]))] if rows else []

        return {"type": "table", "headers": headers, "rows": rows}

    except OperationalError as oe:
        return {"type": "error", "message": f"Database error: {oe}"}
    except Exception as e:
        return {"type": "error", "message": f"Error executing query: {e}"}
