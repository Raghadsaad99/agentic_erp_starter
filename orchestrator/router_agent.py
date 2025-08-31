# orchestrator/router_agent.py
import re
from typing import Any, Dict, Tuple

from services.governance import (
    log_tool_call,
    requires_approval,
    request_approval,
    ensure_conversation,
    save_message,
)
from domain.sales.agent import SalesAgent
from domain.finance.agent import FinanceAgent
from domain.inventory.agent import InventoryAgent
from domain.analytics.agent import AnalyticsAgent


def classify_intent(text: str) -> Tuple[str, str, str]:
    tl = text.lower().strip()

    # 1) Greetings
    if any(g in tl for g in ["hi", "hello", "hey", "thanks", "thank you"]):
        return "general", "none", "greeting"

    # 2) Sales / CRM intents
    if any(k in tl for k in ["customer", "lead", "order", "ticket", "crm", "sales"]):
        if any(k in tl for k in ["create", "add", "open", "insert", "update", "new"]):
            return "sales", "write", "sales_write"
        return "sales", "read", "sales_read"

    # 3) Finance intents
    if (
        any(k in tl for k in ["invoice", "ledger", "payment", "account", "policy", "finance"])
        or re.search(r"\b(cash[- ]flow|aging|aging report|aging buckets)\b", tl)
    ):
        if any(k in tl for k in ["create", "add", "post", "allocate", "update", "record"]):
            return "finance", "write", "finance_write"
        return "finance", "read", "finance_read"

    # 4) Inventory intents — expanded keywords to catch "product" + "quantity"
    if any(k in tl for k in [
        "stock", "inventory", "supplier", "purchase order", "po", "reorder",
        "product", "products", "quantity"
    ]):
        if any(k in tl for k in ["create", "add", "receive", "update"]):
            return "inventory", "write", "inventory_write"
        return "inventory", "read", "inventory_read"

    # 5) Analytics / Reports intents
    if any(k in tl for k in ["report", "kpi", "analytics", "chart", "trend", "glossary"]):
        return "analytics", "read", "analytics_read"

    # 6) Fallback
    return "unknown", "none", "fallback"


def text_payload(text: str) -> Dict[str, Any]:
    return {"type": "text", "content": text}


class RouterAgent:
    def __init__(self):
        self.sales_agent = SalesAgent()
        self.finance_agent = FinanceAgent()
        self.inventory_agent = InventoryAgent()
        self.analytics_agent = AnalyticsAgent()

    def process_request(self, user_id: str, user_input: str) -> Dict[str, Any]:
        """
        Main entry point for routing user input to the correct domain agent.
        """
        module, access, action = classify_intent(user_input)

        # Ensure conversation exists
        conversation_id = ensure_conversation(user_id)
        save_message(conversation_id, sender="user", content=user_input)

        # Handle greetings or unknowns
        if module == "general":
            return text_payload("Hello! How can I help you today?")
        if module == "unknown":
            return text_payload("Sorry, I’m not sure which module to use for that request.")

        # Approval check for write actions
        if access == "write":
            needs_approval, reason = requires_approval(module, action, {"raw_input": user_input})
            if needs_approval:
                approval_id = request_approval(module, {"raw_input": user_input}, requested_by=user_id)
                return text_payload(f"⚠️ {reason} Approval request #{approval_id} has been created.")

        # Route to the correct agent
        if module == "sales":
            result = self.sales_agent.process_request(user_input)
        elif module == "finance":
            result = self.finance_agent.process_request(user_input)
        elif module == "inventory":
            result = self.inventory_agent.process_request(user_input)
        elif module == "analytics":
            result = self.analytics_agent.process_request(user_input)
        else:
            result = text_payload("Module not implemented yet.")

        # Log the tool call
        log_tool_call(agent=module, tool_name=action, inputs={"query": user_input}, outputs=result)

        # Save bot response to conversation
        save_message(conversation_id, sender=module, content=str(result))

        return result

    def route_request(self, message: str, user_id: str) -> Dict[str, Any]:
        """
        Alias for process_request to match API expectations in app/api/chat.py.
        """
        return self.process_request(user_id, message)
