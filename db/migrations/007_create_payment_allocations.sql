PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS payment_allocations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  payment_id INTEGER NOT NULL,
  invoice_id INTEGER NOT NULL,
  amount REAL NOT NULL,
  FOREIGN KEY(payment_id) REFERENCES payments(id),
  FOREIGN KEY(invoice_id) REFERENCES invoices(id)
);
