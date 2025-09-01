# domain/analytics/tools.py
from services.text_to_sql import text_to_sql_tool
from services.rag import rag_definition_tool

def analytics_text_to_sql(nl_query: str):
    """
    Run analytics/reporting questions via text-to-SQL.
    Returns a dict with type/table or type/text.
    """
    return text_to_sql_tool(nl_query)

def analytics_rag_definition(query: str):
    """
    Search analytics-related definitions in the glossary.
    """
    return rag_definition_tool(query, module_filter="analytics")
