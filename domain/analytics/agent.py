# domain/analytics/agent.py
from langchain.agents import initialize_agent, Tool
from langchain.prompts import ChatPromptTemplate
from services.llm import llm
from domain.analytics.tools import analytics_text_to_sql, analytics_rag_definition
from core.logging import logger

# Define Tools
analytics_tools = [
    Tool(
        name="Analytics SQL Tool",
        func=analytics_text_to_sql,
        description="Run SQL queries for analytics and reporting. Use for metrics, trends, and aggregations."
    ),
    Tool(
        name="Analytics Glossary Tool",
        func=analytics_rag_definition,
        description="Look up definitions of analytics-related terms in the glossary."
    )
]

# Optional: a dedicated cash flow tool
def cash_flow_report_tool(_):
    from services.sql import execute_query
    sql = """
        SELECT date(created_at) AS Date,
               SUM(CASE WHEN LOWER(status)='unpaid' THEN total_amount ELSE 0 END) AS total_invoiced,
               SUM(CASE WHEN LOWER(status)='paid' THEN total_amount ELSE 0 END)   AS total_paid
        FROM invoices
        WHERE date(created_at) >= date('now','-7 days')
        GROUP BY date(created_at)
    """
    rows = execute_query(sql)
    return {"type": "table", "headers": ["Date", "total_invoiced", "total_paid"], "rows": rows}

analytics_tools.append(
    Tool(
        name="Cash Flow Report Tool",
        func=cash_flow_report_tool,
        description="Generate a 7-day cash flow report from invoices."
    )
)

# Prompt for the Analytics Agent
analytics_prompt = ChatPromptTemplate.from_template("""
You are the Analytics Agent for the ERP system.
You can answer questions about metrics, reports, KPIs, and definitions.
Use the provided tools to get data or definitions.
If a question is about cash flow, use the Cash Flow Report Tool.
If it's about definitions, use the Analytics Glossary Tool.
Otherwise, use the Analytics SQL Tool.
""")

# Initialize the LangChain agent
analytics_agent_executor = initialize_agent(
    tools=analytics_tools,
    llm=llm,
    agent="zero-shot-react-description",
    verbose=True
)

class AnalyticsAgent:
    def process_request(self, prompt: str):
        logger.info(f"[AnalyticsAgent] Received prompt: {prompt}")
        try:
            return analytics_agent_executor.run(prompt)
        except Exception as e:
            logger.error(f"[AnalyticsAgent] Error: {e}")
            return {"type": "text", "content": "Sorry, there was an error processing your analytics query."}
