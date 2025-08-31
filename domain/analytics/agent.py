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
                       SUM(CASE WHEN LOWER(status)='unpaid' THEN total_amount ELSE 0 END) AS total_invoiced,
                       SUM(CASE WHEN LOWER(status)='paid' THEN total_amount ELSE 0 END)   AS total_paid
                  FROM invoices
                 WHERE date(created_at) >= date('now','-7 days')
              GROUP BY date(created_at)
            """
            rows = execute_query(sql)
            return {
                "type": "table",
                "headers": ["Date", "total_invoiced", "total_paid"],
                "rows": rows
            }

        # 2️⃣ Analytics report (broadened match, guaranteed early return)
        if "analytics" in clean_prompt and "report" in clean_prompt:
            logger.info("[AnalyticsAgent] Matched 'analytics report'")
            sql = """
                SELECT customer_id,
                       SUM(total_amount) AS total_spent
                  FROM invoices
              GROUP BY customer_id
              ORDER BY total_spent DESC
            """
            rows = execute_query(sql)
            if not rows:
                return {
                    "type": "text",
                    "content": "No analytics data found for the requested period."
                }
            return {
                "type": "table",
                "headers": ["customer_id", "total_spent"],
                "rows": rows
            }

        # 3️⃣ Fallback to text-to-SQL
        try:
            logger.info(f"[AnalyticsAgent] Fallback query: {prompt}")
            result = text_to_sql_tool(prompt)
            return result if isinstance(result, dict) else {
                "type": "text",
                "content": str(result)
            }
        except Exception as e:
            logger.error(f"[AnalyticsAgent] Error in fallback: {e}")
            return {
                "type": "text",
                "content": "Sorry, there was an error processing your analytics query."
            }
