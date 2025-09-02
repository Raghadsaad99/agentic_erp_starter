# domain/sales/agent.py
from langchain.agents import initialize_agent, Tool
from langchain.prompts import ChatPromptTemplate
from services.llm import llm
from services.sql import execute_query
from services.text_to_sql import text_to_sql_tool
from domain.finance import tools as finance_tools
from core.logging import logger

# Tool wrappers for Sales-specific queries
def list_all_customers(_):
    rows = execute_query("SELECT id, name, email, phone FROM customers")
    return {"type": "table", "headers": ["id", "name", "email", "phone"], "rows": rows}

def count_customers(_):
    rows = execute_query("SELECT COUNT(*) FROM customers")
    count = rows[0][0] if rows else 0
    return {"type": "text", "content": f"We have {count} customers."}

def order_items_for_order(order_id: str):
    sql = "SELECT id, product_id, quantity, price FROM order_items WHERE order_id = ?"
    rows = execute_query(sql, (order_id,))
    return {"type": "table", "headers": ["id", "product_id", "quantity", "price"], "rows": rows}

# Wrap functions as LangChain Tools
sales_tool_list = [
    Tool(name="List All Customers Tool", func=list_all_customers,
         description="List all customers with their ID, name, email, and phone."),
    Tool(name="Count Customers Tool", func=count_customers,
         description="Count the total number of customers."),
    Tool(name="Order Items For Order Tool", func=order_items_for_order,
         description="List all items for a given order ID."),
    Tool(name="Unpaid Invoices Tool", func=lambda _: finance_tools.get_unpaid_invoices(),
         description="List all unpaid invoices."),
    Tool(name="Paid Invoices Tool", func=lambda _: finance_tools.get_paid_invoices(),
         description="List all paid invoices."),
    Tool(name="Cancelled Invoices Tool", func=lambda _: finance_tools.get_cancelled_invoices(),
         description="List all cancelled invoices."),
    Tool(name="All Invoices Tool", func=lambda _: finance_tools.get_all_invoices(),
         description="List all invoices."),
    Tool(name="Invoices By Customer Tool", func=finance_tools.get_invoices_by_customer,
         description="List all invoices for a given customer name."),
    Tool(name="Sales SQL Tool", func=text_to_sql_tool,
         description="Run SQL for sales-related questions not covered by other tools.")
]

# Prompt for the Sales Agent
sales_prompt = ChatPromptTemplate.from_template("""
You are the Sales Agent for the ERP system.
You can answer questions about customers, orders, and invoices.
Use the provided tools to get the correct data.
If the question is about customers, use the customer tools.
If it's about orders, use the order tools.
If it's about invoices, use the invoice tools.
If it's a custom sales query, use the Sales SQL Tool.
Always return results in the structured dict format:
{{"type": "table", "headers": [...], "rows": [...]}} or {{"type": "text", "content": "..."}}
""")

# Initialize the LangChain agent
sales_agent_executor = initialize_agent(
    tools=sales_tool_list,
    llm=llm,
    agent="zero-shot-react-description",
    verbose=True
)

class SalesAgent:
    def process_request(self, prompt: str):
        logger.info(f"[SalesAgent] Received prompt: {prompt}")
        try:
            result = sales_agent_executor.run(prompt)
            if isinstance(result, dict):
                return result
            return {"type": "text", "content": str(result)}
        except Exception as e:
            logger.error(f"[SalesAgent] Error: {e}")
            return {"type": "text", "content": "Sorry, there was an error processing your sales query."}
