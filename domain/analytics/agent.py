# domain/analytics/agent.py

from services.sql import execute_query
from services.text_to_sql import text_to_sql_tool
from core.logging import logger

class AnalyticsAgent:
    def process_request(self, prompt: str):
        clean_prompt = " ".join(prompt.lower().split())
        logger.info(f"[AnalyticsAgent] Received prompt: {prompt}")
        logger.info(f"[AnalyticsAgent] Clean prompt: {clean_prompt}")

        # 1️⃣ Cash flow report
        if "cash flow" in clean_prompt:
            logger.info("[AnalyticsAgent] Matched 'cash flow'")
            sql = """
                SELECT date(created_at) AS Date,
                       SUM(CASE WHEN status='unpaid' THEN total_amount ELSE 0 END) AS total_invoiced,
                       SUM(CASE WHEN status='paid' THEN total_amount ELSE 0 END)   AS total_paid
                  FROM invoices
                 WHERE created_at >= date('now','-7 days')
              GROUP BY date(created_at)
            """
            rows = execute_query(sql)
            return {
                "type": "table",
                "headers": ["Date", "total_invoiced", "total_paid"],
                "rows": rows
            }

        # 2️⃣ Analytics report
        if "analytics report" in clean_prompt or "show analytics report" in clean_prompt:
            logger.info("[AnalyticsAgent] Matched 'analytics report'")
            sql = """
                SELECT customer_id,
                       SUM(total_amount) AS total_spent
                  FROM invoices
              GROUP BY customer_id
              ORDER BY total_spent DESC
            """
            rows = execute_query(sql)
            return {
                "type": "table",
                "headers": ["customer_id", "total_spent"],
                "rows": rows
            }

        # 3️⃣ Fallback
        try:
            logger.info(f"[AnalyticsAgent] Fallback query: {prompt}")
            result = text_to_sql_tool(prompt)

            # Intercept inventory misfires
            def is_inventory_misfire(text):
                return any(kw in text.lower() for kw in [
                    "inventory request", "stock", "product qty", "could not process inventory"
                ])

            if isinstance(result, dict):
                content = result.get("content", "")
                if is_inventory_misfire(content):
                    logger.warning("[AnalyticsAgent] Inventory fallback detected—overriding")
                    return {
                        "type": "text",
                        "content": "Sorry, that query seems unrelated to analytics. Try asking about cash flow, customer spend, or KPIs."
                    }
                return result

            if isinstance(result, str):
                if is_inventory_misfire(result):
                    logger.warning("[AnalyticsAgent] Inventory fallback string detected—overriding")
                    return {
                        "type": "text",
                        "content": "Sorry, that query seems unrelated to analytics. Try asking about cash flow, customer spend, or KPIs."
                    }
                return {
                    "type": "text",
                    "content": result
                }

            return {
                "type": "text",
                "content": "Analytics query not recognized. Try asking about cash flow, customer spend, or KPIs."
            }

        except Exception as e:
            logger.error(f"[AnalyticsAgent] Error in fallback: {e}")
            return {
                "type": "error",
                "message": f"Error processing analytics query: {e}"
            }
