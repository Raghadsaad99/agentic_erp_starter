# orchestrator/router_agent.py
import re
import json
import ast
from typing import Any, Dict, Tuple

from services.governance import (
    log_tool_call,
    requires_approval,
    request_approval,
    ensure_conversation,
    save_message,
)
from services.llm import llm
from services.rag import rag_definition_tool, policy_rag_tool
from services.ml import lead_score_tool as _lead_score_tool, anomaly_detector_tool as _anomaly_detector_tool

from domain.finance.tools import (
    get_unpaid_invoices,
    get_paid_invoices,
    get_cancelled_invoices,
    get_all_invoices,
    get_invoices_by_customer,
    finance_sql_read as _finance_sql_read,
    finance_sql_write as _finance_sql_write,
)
from domain.sales.tools import (
    sales_sql_read as _sales_sql_read,
    sales_sql_write as _sales_sql_write,
)
from domain.inventory.tools import (
    inventory_sql_read as _inventory_sql_read,
    inventory_sql_write as _inventory_sql_write,
    get_stock_levels as _get_stock_levels,
)
from services.text_to_sql import text_to_sql_tool as _text_to_sql

from langchain.tools import Tool
from langchain.agents import initialize_agent, AgentType
from langchain.memory import ConversationBufferWindowMemory


def classify_intent(text: str) -> Tuple[str, str, str]:
    tl = text.lower().strip()
    if any(g in tl for g in ["hi", "hello", "hey", "thanks", "thank you"]):
        return "general", "none", "greeting"
    if any(k in tl for k in ["customer", "lead", "order", "ticket", "crm", "sales"]):
        if any(k in tl for k in ["create", "add", "open", "insert", "update", "new"]):
            return "sales", "write", "sales_write"
        return "sales", "read", "sales_read"
    if (
        any(k in tl for k in ["invoice", "ledger", "payment", "account", "policy", "finance"])
        or re.search(r"\b(cash[- ]flow|aging|aging report|aging buckets)\b", tl)
    ):
        if any(k in tl for k in ["create", "add", "post", "allocate", "update", "record"]):
            return "finance", "write", "finance_write"
        return "finance", "read", "finance_read"
    if any(k in tl for k in [
        "stock", "inventory", "supplier", "purchase order", "po", "reorder",
        "product", "products", "quantity"
    ]):
        if any(k in tl for k in ["create", "add", "receive", "update"]):
            return "inventory", "write", "inventory_write"
        return "inventory", "read", "inventory_read"
    if any(k in tl for k in ["report", "kpi", "analytics", "chart", "trend", "glossary"]):
        return "analytics", "read", "analytics_read"
    return "unknown", "none", "fallback"


def _json_dumps(obj: Any) -> str:
    try:
        return json.dumps(obj, ensure_ascii=False, default=str)
    except Exception:
        return json.dumps({"type": "text", "content": str(obj)}, ensure_ascii=False)


def _parse_possible_json(s: str) -> Dict[str, Any]:
    try:
        obj = json.loads(s)
        if isinstance(obj, dict):
            return obj
        if isinstance(obj, list) and all(isinstance(r, (list, tuple, dict)) for r in obj):
            return {"type": "table", "headers": [], "rows": obj}
    except Exception:
        pass
    try:
        obj = ast.literal_eval(s)
        if isinstance(obj, dict):
            return obj
        if isinstance(obj, list) and all(isinstance(r, (list, tuple, dict)) for r in obj):
            return {"type": "table", "headers": [], "rows": obj}
    except Exception:
        pass
    return {"type": "text", "content": s}


def text_payload(text: str) -> Dict[str, Any]:
    return {"type": "text", "content": text}


def _build_finance_tools():
    return [
        Tool.from_function(func=lambda input: _json_dumps(get_unpaid_invoices()), name="finance_get_unpaid_invoices", description="List unpaid invoices", return_direct=True),
        Tool.from_function(func=lambda input: _json_dumps(get_paid_invoices()), name="finance_get_paid_invoices", description="List paid invoices", return_direct=True),
        Tool.from_function(func=lambda input: _json_dumps(get_cancelled_invoices()), name="finance_get_cancelled_invoices", description="List cancelled invoices", return_direct=True),
        Tool.from_function(func=lambda input: _json_dumps(get_all_invoices()), name="finance_get_all_invoices", description="List all invoices", return_direct=True),
        Tool.from_function(func=lambda input: _json_dumps(get_invoices_by_customer(str(input))), name="finance_get_invoices_by_customer", description="Invoices for a customer", return_direct=True),
        Tool.from_function(func=lambda input: _json_dumps(_finance_sql_read(str(input))), name="finance_sql_read", description="Finance read via text-to-SQL", return_direct=True),
        Tool.from_function(func=lambda input: _json_dumps(_finance_sql_write(**(input if isinstance(input, dict) else json.loads(input)))), name="finance_sql_write", description="Finance write actions", return_direct=True),
        Tool.from_function(func=lambda input: _json_dumps(policy_rag_tool(str(input))), name="policy_rag_tool", description="Search finance policy docs", return_direct=True),
        Tool.from_function(func=lambda input: _json_dumps({"type": "text", "content": str(_anomaly_detector_tool(input if isinstance(input, dict) else json.loads(input)))}), name="finance_anomaly_detector_tool", description="Anomaly risk score", return_direct=True),
    ]


def _build_sales_tools():
    return [
        Tool.from_function(func=lambda input: _json_dumps(_sales_sql_read(str(input))), name="sales_sql_read", description="Sales read via text-to-SQL", return_direct=True),
        Tool.from_function(func=lambda input: _json_dumps(_sales_sql_write(**(input if isinstance(input, dict) else json.loads(input)))), name="sales_sql_write", description="Sales write actions", return_direct=True),
        Tool.from_function(func=lambda input: _json_dumps({"type": "text", "content": str(_lead_score_tool(str(input)))}), name="lead_score_tool", description="Score a lead 0..1", return_direct=True),
        Tool.from_function(func=lambda input: _json_dumps(rag_definition_tool(str(input), module_filter="sales")), name="glossary_rag_definition_tool", description="Search sales glossary", return_direct=True),
    ]


def _build_inventory_tools():
    return [
        Tool.from_function(func=lambda input: _json_dumps(_inventory_sql_read(str(input))), name="inventory_sql_read", description="Inventory read via text-to-SQL", return_direct=True),
        Tool.from_function(func=lambda input: _json_dumps(_inventory_sql_write(**(input if isinstance(input, dict) else json.loads(input)))), name="inventory_sql_write", description="Inventory write actions", return_direct=True),
        Tool.from_function(func=lambda input: _json_dumps({"type": "table", "headers": ["product_id", "qty_on_hand", "reorder_point"], "rows": _get_stock_levels()}), name="inventory_get_stock_levels", description="Current stock levels", return_direct=True),
    ]


def _build_analytics_tools():
    return [
        Tool.from_function(func=lambda input: _json_dumps(_text_to_sql(str(input))), name="analytics_text_to_sql", description="Analytics/reporting via text-to-SQL", return_direct=True),
        Tool.from_function(func=lambda input: _json_dumps(rag_definition_tool(str(input), module_filter="analytics")), name="glossary_rag_definition_tool", description="Search analytics glossary", return_direct=True),
    ]


def _make_agent(tools):
    memory = ConversationBufferWindowMemory(k=5, memory_key="chat_history", return_messages=True)
    return initialize_agent(tools=tools, llm=llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, memory=memory, verbose=False, handle_parsing_errors=True)


class RouterAgent:
    def __init__(self):
        self._per_user_agents = {}

    def _ensure_user_agents(self, user_id: str):
        if user_id not in self._per_user_agents:
            self._per_user_agents[user_id] = {
                "sales": _make_agent(_build_sales_tools()),
                "finance": _make_agent(_build_finance_tools()),
                "inventory": _make_agent(_build_inventory_tools()),
                "analytics": _make_agent(_build_analytics_tools()),
            }

    def process_request(self, user_id: str, user_input: str) -> Dict[str, Any]:
        module, access, action = classify_intent(user_input)
        conversation_id = ensure_conversation(user_id)
        save_message(conversation_id, sender="user", content=user_input)

        if module == "general":
            return text_payload("Hello! How can I help you today?")
        if module == "unknown":
            return text_payload("Sorry, I’m not sure which module to use for that request.")

        if access == "write":
            needs_approval, reason = requires_
        # Approval check for write actions
        if access == "write":
            needs_approval, reason = requires_approval(module, action, {"raw_input": user_input})
            if needs_approval:
                approval_id = request_approval(module, {"raw_input": user_input}, requested_by=user_id)
                return text_payload(f"⚠️ {reason} Approval request #{approval_id} has been created.")

        # Ensure we have LC agents for this user
        self._ensure_user_agents(user_id)
        agent = self._per_user_agents[user_id].get(module)

        if not agent:
            result = text_payload("Module not implemented yet.")
            log_tool_call(agent=module, tool_name=action, inputs={"query": user_input}, outputs=result)
            save_message(conversation_id, sender=module, content=str(result))
            return result

        # Direct handling for specific sales queries that SalesAgent can handle directly
        if module == "sales" and action == "sales_read" and "how many customers" in user_input.lower():

            from domain.sales.agent import SalesAgent
            return SalesAgent().process_request(user_input)
            sales_agent = SalesAgent()
            result = sales_agent.process_request(user_input)
        else:
            # Run the LC agent — it will decide which tool to call
            try:
                raw = agent.run(user_input)
                result = _parse_possible_json(raw if isinstance(raw, str) else str(raw))
            except Exception as e:
                result = text_payload(f"Error processing with agent: {e}")

        # Log the tool call
        log_tool_call(agent=module, tool_name=action, inputs={"query": user_input}, outputs=result)

        # Save bot response to conversation
        save_message(conversation_id, sender=module, content=_json_dumps(result))

        return result

    def route_request(self, message: str, user_id: str) -> Dict[str, Any]:
        """
        Alias for process_request to match API expectations in app/api/chat.py.
        """
        return self.process_request(user_id, message)
