from services.text_to_sql import text_to_sql_tool
from langchain.schema import AIMessage

queries = [
    # Sales
    "List all customers",
    "Show me orders placed in the last 30 days",
    "Who are our top 5 customers by revenue this quarter",
    "What’s our average order value this month",

    # Finance
    "List all unpaid invoices",
    "Post a payment of 5,000 AED to invoice INV-2025-003",
    "Show me the aging report for receivables",

    # Inventory
    "Check stock levels for product P-102",
    "List all products below their reorder point",
    "Receive 50 units of product P-204 from supplier S-11",

    # Analytics
    "What is the total revenue by product",
    "Total sales by customer",
    "Generate a KPI report for August",

    # Edge cases
    "Which customers haven’t ordered in 6 months",
    "Show me sales and finance data for customer ID 102",
    "List all invoices for customers who ordered inventory last week",
]

for q in queries:
    print(f"\n🧠 Query: {q}")
    result = text_to_sql_tool(AIMessage(content=q))
    print("📊 Result:", result)
