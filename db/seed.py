import sqlite3
from core.config import DB_PATH

def seed_invoices():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Ensure at least one customer and one product exist
    cur.execute("SELECT id FROM customers LIMIT 1")
    row_c = cur.fetchone()
    if not row_c:
        cur.execute("INSERT INTO customers (name, email, phone, created_at) VALUES ('Acme Corp', 'acme@example.com', '123456789', datetime('now'))")
        conn.commit()
        cur.execute("SELECT id FROM customers LIMIT 1")
        row_c = cur.fetchone()
    customer_id = row_c[0]

    cur.execute("SELECT id FROM products LIMIT 1")
    row_p = cur.fetchone()
    if not row_p:
        cur.execute("INSERT INTO products (sku, name, price, description) VALUES ('SKU001', 'Widget A', 10.5, 'Standard widget')")
        conn.commit()
        cur.execute("SELECT id FROM products LIMIT 1")
        row_p = cur.fetchone()
    product_id = row_p[0]

    # Only insert invoice if INV-001 doesn't exist
    cur.execute("SELECT 1 FROM invoices WHERE invoice_number = 'INV-001'")
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO invoices (customer_id, invoice_number, issue_date, due_date, total_amount, status, created_at)
            VALUES (?, 'INV-001', date('now'), date('now','+30 day'), 100.0, 'unpaid', datetime('now'))
        """, (customer_id,))
        invoice_id = cur.lastrowid

        cur.execute("""
            INSERT INTO invoice_lines (invoice_id, description, quantity, unit_price)
            VALUES (?, 'Widget A', 2, 50.0)
        """, (invoice_id,))

    # Ensure stock rows for the product
    cur.execute("SELECT 1 FROM stock WHERE product_id = ?", (product_id,))
    if not cur.fetchone():
        cur.execute("INSERT INTO stock (product_id, qty_on_hand, reorder_point) VALUES (?, 100, 20)", (product_id,))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    # existing seed() call…
    seed_invoices()
    print("Invoices and stock seeded.")
