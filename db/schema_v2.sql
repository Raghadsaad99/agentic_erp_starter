# db/schema_v2.sql
CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  email TEXT UNIQUE,
  role TEXT DEFAULT 'user',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
, department TEXT);
CREATE TABLE sqlite_sequence(name,seq);
CREATE TABLE approvals (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  module TEXT,
  payload_json TEXT,
  status TEXT DEFAULT 'pending',
  requested_by TEXT,
  decided_by TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  decided_at DATETIME
);
CREATE TABLE tool_calls (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  agent TEXT,
  tool_name TEXT,
  input_json TEXT,
  output_json TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE conversations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER,
  started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(user_id) REFERENCES users(id)
);
CREATE TABLE messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  conversation_id INTEGER,
  sender TEXT,
  content TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(conversation_id) REFERENCES conversations(id)
);
CREATE TABLE customers (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  email TEXT,
  phone TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE customer_kv (
  customer_id INTEGER,
  key TEXT,
  value TEXT,
  PRIMARY KEY (customer_id, key),
  FOREIGN KEY(customer_id) REFERENCES customers(id)
);
CREATE TABLE leads (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  customer_name TEXT,
  contact_email TEXT,
  message TEXT,
  score REAL,
  status TEXT DEFAULT 'new',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE products (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  sku TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  price REAL NOT NULL,
  description TEXT
);
CREATE TABLE orders (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  customer_id INTEGER NOT NULL,
  total REAL NOT NULL,
  status TEXT DEFAULT 'pending',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP, customer VARCHAR(255),
  FOREIGN KEY(customer_id) REFERENCES customers(id)
);
CREATE TABLE order_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  order_id INTEGER NOT NULL,
  product_id INTEGER NOT NULL,
  quantity INTEGER NOT NULL,
  price REAL NOT NULL,
  FOREIGN KEY(order_id) REFERENCES orders(id) ON DELETE CASCADE,
  FOREIGN KEY(product_id) REFERENCES products(id)
);
CREATE TABLE tickets (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  customer_id INTEGER,
  subject TEXT,
  body TEXT,
  status TEXT DEFAULT 'open',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(customer_id) REFERENCES customers(id)
);
CREATE TABLE invoices (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  customer_id INTEGER,
  invoice_number TEXT,
  issue_date DATE,
  due_date DATE,
  total_amount REAL,
  status TEXT DEFAULT 'unpaid',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(customer_id) REFERENCES customers(id)
);
CREATE TABLE invoice_lines (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  invoice_id INTEGER NOT NULL,
  description TEXT,
  quantity INTEGER,
  unit_price REAL,
  FOREIGN KEY(invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
);
CREATE TABLE invoice_orders (
  invoice_id INTEGER,
  order_id INTEGER,
  PRIMARY KEY (invoice_id, order_id),
  FOREIGN KEY(invoice_id) REFERENCES invoices(id),
  FOREIGN KEY(order_id) REFERENCES orders(id)
);
CREATE TABLE payments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  customer_id INTEGER,
  amount REAL,
  method TEXT,
  received_at DATETIME,
  FOREIGN KEY(customer_id) REFERENCES customers(id)
);
CREATE TABLE payment_allocations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  payment_id INTEGER,
  invoice_id INTEGER,
  amount REAL,
  FOREIGN KEY(payment_id) REFERENCES payments(id),
  FOREIGN KEY(invoice_id) REFERENCES invoices(id)
);
CREATE TABLE chart_of_accounts (
  account TEXT PRIMARY KEY,
  description TEXT
);
CREATE TABLE ledger_entries (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  entry_date DATE NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE ledger_lines (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  entry_id INTEGER NOT NULL,
  account TEXT NOT NULL,
  debit REAL DEFAULT 0,
  credit REAL DEFAULT 0,
  FOREIGN KEY(entry_id) REFERENCES ledger_entries(id) ON DELETE CASCADE,
  FOREIGN KEY(account) REFERENCES chart_of_accounts(account)
);
CREATE TABLE stock (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  product_id INTEGER NOT NULL,
  qty_on_hand INTEGER NOT NULL DEFAULT 0,
  reorder_point INTEGER NOT NULL DEFAULT 0,
  FOREIGN KEY(product_id) REFERENCES products(id)
);
CREATE TABLE stock_movements (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  product_id INTEGER NOT NULL,
  change_qty INTEGER NOT NULL,
  reason TEXT,
  ref_id INTEGER,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(product_id) REFERENCES products(id)
);
CREATE TABLE suppliers (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  email TEXT,
  phone TEXT
);
CREATE TABLE supplier_products (
  supplier_id INTEGER,
  product_id INTEGER,
  lead_time_days INTEGER,
  default_cost REAL,
  PRIMARY KEY (supplier_id, product_id),
  FOREIGN KEY(supplier_id) REFERENCES suppliers(id),
  FOREIGN KEY(product_id) REFERENCES products(id)
);
CREATE TABLE purchase_orders (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  supplier_id INTEGER NOT NULL,
  status TEXT DEFAULT 'draft',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(supplier_id) REFERENCES suppliers(id)
);
CREATE TABLE po_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  po_id INTEGER NOT NULL,
  product_id INTEGER NOT NULL,
  quantity INTEGER NOT NULL,
  unit_cost REAL NOT NULL,
  FOREIGN KEY(po_id) REFERENCES purchase_orders(id) ON DELETE CASCADE,
  FOREIGN KEY(product_id) REFERENCES products(id)
);
CREATE TABLE po_receipts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  po_id INTEGER,
  product_id INTEGER,
  received_qty INTEGER,
  received_at DATETIME,
  FOREIGN KEY(po_id) REFERENCES purchase_orders(id),
  FOREIGN KEY(product_id) REFERENCES products(id)
);
CREATE TABLE saved_reports (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  sql TEXT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE glossary (
  term TEXT PRIMARY KEY,
  definition TEXT,
  module TEXT
);
CREATE TABLE documents (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  module TEXT,
  path TEXT,
  tags TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE model_registry (
  name TEXT,
  version TEXT,
  path TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (name, version)
);
CREATE TABLE ml_features_cache (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  entity_type TEXT,
  entity_id INTEGER,
  feature_json TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_invoice_customer ON invoices(customer_id);
CREATE INDEX idx_stock_product ON stock(product_id);
CREATE INDEX idx_movements_product ON stock_movements(product_id);
CREATE INDEX idx_po_supplier ON purchase_orders(supplier_id);
CREATE INDEX idx_messages_conv ON messages(conversation_id);
CREATE INDEX idx_tool_calls_agent ON tool_calls(agent);
CREATE TABLE sales_data (date TEXT, product TEXT, quantity INTEGER, price REAL);
CREATE TABLE inventory (product TEXT, stock_level INTEGER);
