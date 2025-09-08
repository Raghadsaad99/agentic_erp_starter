# services/text_to_sql.py
from sqlite3 import OperationalError
from services.sql import execute_query
from services.llm import llm
from langchain.schema import AIMessage
import re

# Injected schema for LLM prompt
ERP_SCHEMA = """
customers(id, name, email, phone, created_at)
orders(id, customer_id, total, status, created_at)
order_items(order_id, product_id, quantity, price)
products(id, name, sku, price, description)
invoices(id, customer_id, invoice_number, total_amount, status, created_at)
invoice_lines(invoice_id, description, quantity, unit_price)
payments(id, customer_id, amount, method, received_at)
stock(product_id, qty_on_hand, reorder_point)
"""

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
        SELECT p.id AS product_id,
               p.name AS product_name,
               s.qty_on_hand,
               s.reorder_point
        FROM stock s
        JOIN products p ON p.id = s.product_id;
        """
        return _run_sql(sql, intent="inventory_read_stock")

    # Products below reorder point
    if "products below reorder point" in tl:
        sql = """
        SELECT p.id AS product_id,
               p.name AS product_name,
               s.qty_on_hand,
               s.reorder_point
        FROM stock s
        JOIN products p ON p.id = s.product_id
        WHERE s.qty_on_hand < s.reorder_point;
        """
        return _run_sql(sql, intent="inventory_read_stock")

    # Total revenue by product
    if "total revenue by product" in tl:
        sql = """
        SELECT p.id AS product_id,
               p.name AS product_name,
               SUM(oi.quantity * oi.price) AS total_revenue
        FROM order_items oi
        JOIN products p ON p.id = oi.product_id
        GROUP BY p.id, p.name
        ORDER BY total_revenue DESC;
        """
        return _run_sql(sql, intent="analytics_report")

    # Total sales by customer
    if "total sales by customer" in tl:
        sql = """
        SELECT c.id AS customer_id,
               c.name AS customer_name,
               SUM(oi.quantity * oi.price) AS total_sales
        FROM orders o
        JOIN customers c ON c.id = o.customer_id
        JOIN order_items oi ON oi.order_id = o.id
        GROUP BY c.id, c.name
        ORDER BY total_sales DESC;
        """
        return _run_sql(sql, intent="sales_by_customer")

    # Average order value this month
    if "average order value" in tl and "this month" in tl:
        sql = """
        SELECT ROUND(SUM(o.total) / COUNT(*), 2) AS avg_order_value
        FROM orders o
        WHERE o.created_at >= DATE('now', 'start of month');
        """
        return _run_sql(sql, intent="analytics_report")

    # Orders in last 30 days
    if "orders placed in the last 30 days" in tl:
        sql = """
        SELECT o.id AS order_id,
               c.name AS customer_name,
               o.total,
               o.status,
               o.created_at
        FROM orders o
        JOIN customers c ON c.id = o.customer_id
        WHERE o.created_at >= DATE('now', '-30 days');
        """
        return _run_sql(sql, intent="sales_read_orders")

    # Top N customers by revenue this quarter
    if "top" in tl and "customers" in tl and "revenue" in tl and "quarter" in tl:
        sql = """
        SELECT c.id AS customer_id,
               c.name AS customer_name,
               SUM(oi.quantity * oi.price) AS total_revenue
        FROM orders o
        JOIN customers c ON c.id = o.customer_id
        JOIN order_items oi ON oi.order_id = o.id
        WHERE strftime('%Y', o.created_at) = strftime('%Y', 'now')
          AND ((cast(strftime('%m', o.created_at) as integer)-1)/3 + 1) =
              ((cast(strftime('%m', 'now') as integer)-1)/3 + 1)
        GROUP BY c.id, c.name
        ORDER BY total_revenue DESC
        LIMIT 5;
        """
        return _run_sql(sql, intent="sales_by_customer")

    # Customers who haven't ordered in 6 months
    if "haven’t ordered" in tl or "haven't ordered" in tl:
        sql = """
        SELECT DISTINCT c.id AS customer_id,
               c.name AS customer_name
        FROM customers c
        WHERE c.id NOT IN (
            SELECT DISTINCT customer_id
            FROM orders o
            WHERE o.created_at >= DATE('now', '-6 months')
        );
        """
        return _run_sql(sql, intent="sales_read_customers")

    # Sales and finance data for a specific customer
    if "sales and finance data for customer" in tl:
        match = re.search(r"\d+", tl)
        if match:
            cid = match.group()
            sql = f"""
            SELECT c.id AS customer_id,
                   c.name AS customer_name,
                   o.id AS order_id,
                   o.total AS order_total,
                   i.invoice_number,
                   i.total_amount AS invoice_total,
                   i.status AS invoice_status
            FROM customers c
            LEFT JOIN orders o ON o.customer_id = c.id
            LEFT JOIN invoices i ON i.customer_id = c.id
            WHERE c.id = {cid};
            """
            return _run_sql(sql, intent="analytics_report")

    # Stubbed action queries for demo
    if "post a payment" in tl and "invoice" in tl:
        return {"type": "text", "content": "✅ Payment recorded (demo mode — no DB update performed)."}
    if "receive" in tl and "units" in tl and "product" in tl:
        return {"type": "text", "content": "✅ Stock receipt recorded (demo mode — no DB update performed)."}

    # Direct SQL passthrough
    if tl.startswith(("select ", "with ", "pragma ")):
        return _run_sql(text)

    # Fallback to schema-aware LLM
    try:
        prompt = (
            "You are an expert SQL generator for a SQLite ERP database. "
            "Here is the schema:\n"
            f"{ERP_SCHEMA}\n\n"
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

        # Deduplicate rows
        seen = set()
        rows = []
        for r in raw_rows:
            row_tuple = tuple(r.values()) if isinstance(r, dict) else tuple(r)
            if row_tuple not in seen:
                seen.add(row_tuple)
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
            headers = ["Invoice ID", "Customer Name", "Invoice #", "Amount", "Status"]
        elif intent == "inventory_read_stock":
            headers = ["Product ID", "Product Name", "Qty On Hand", "Reorder Point"]
        elif intent == "analytics_report":
            headers = ["Entity ID", "Entity Name", "Metric 1", "Metric 2"]
        elif intent == "sales_read_orders":
            headers = ["Order ID", "Customer Name", "Total", "Status", "Created At"]
        elif intent == "sales_by_customer":
            headers = ["Customer ID", "Customer Name", "Total Sales"]
        else:
            headers = [f"col_{i}" for i in range(len(rows[0]))] if rows else []

        return {"type": "table", "headers": headers, "rows": rows}

    except OperationalError as oe:
        return {"type": "error", "message": f"Database error: {oe}"}
    except Exception as e:
        return {"type": "error", "message": f"Error executing query: {e}"}

