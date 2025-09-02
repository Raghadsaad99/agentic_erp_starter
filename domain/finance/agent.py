# domain/finance/agent.py
from langchain.agents import initialize_agent, Tool
from langchain.prompts import ChatPromptTemplate
from services.llm import llm
from domain.finance import tools as finance_tools
from core.logging import logger

# LangChain Tools
finance_tool_list = [
    Tool(
        name="Unpaid Invoices Tool",
        func=lambda _: finance_tools.get_unpaid_invoices(),
        description="List all unpaid invoices with customer, amount, and status."
    ),
    Tool(
        name="Paid Invoices Tool",
        func=lambda _: finance_tools.get_paid_invoices(),
        description="List all paid invoices with customer, amount, and status."
    ),
    Tool(
        name="Cancelled Invoices Tool",
        func=lambda _: finance_tools.get_cancelled_invoices(),
        description="List all cancelled invoices with customer, amount, and status."
    ),
    Tool(
        name="All Invoices Tool",
        func=lambda _: finance_tools.get_all_invoices(),
        description="List all invoices with customer, amount, and status."
    ),
    Tool(
        name="Invoices By Customer Tool",
        func=finance_tools.get_invoices_by_customer,
        description="List all invoices for a given customer name."
    ),
    Tool(
        name="Finance SQL Tool",
        func=finance_tools.finance_sql_read,
        description="Run SQL for finance-related questions not covered by other tools."
    ),
    Tool(
        name="Finance Write Tool",
        func=finance_tools.finance_sql_write,
        description="Perform finance write actions like creating invoices or posting payments."
    )
]

# Prompt for the Finance Agent
finance_prompt = ChatPromptTemplate.from_template("""
You are the Finance Agent for the ERP system.
You can answer questions about invoices, payments, and finance reports.
Use the provided tools to get the correct data or perform write actions.
If the question is about unpaid, paid, cancelled, or all invoices, use the matching tool.
If it's about invoices for a specific customer, use the Invoices By Customer Tool.
If it's a custom finance query, use the Finance SQL Tool.
If it's a write action like creating an invoice or posting a payment, use the Finance Write Tool.
Always return results in the structured dict format: 
{{"type": "table", "headers": [...], "rows": [...]}} or {{"type": "text", "content": "..."}}
""")

# Initialize the LangChain agent
finance_agent_executor = initialize_agent(
    tools=finance_tool_list,
    llm=llm,
    agent="zero-shot-react-description",
    verbose=True
)

class FinanceAgent:
    def process_request(self, prompt: str):
        logger.info(f"[FinanceAgent] Received prompt: {prompt}")
        try:
            result = finance_agent_executor.run(prompt)
            # Ensure result is a dict for UI compatibility
            if isinstance(result, dict):
                return result
            return {"type": "text", "content": str(result)}
        except Exception as e:
            logger.error(f"[FinanceAgent] Error: {e}")
            return {"type": "text", "content": "Sorry, there was an error processing your finance query."}
