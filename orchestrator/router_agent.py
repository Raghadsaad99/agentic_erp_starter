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

    # 3) Finance intents (invoices, payments, ledger, policy, cash flow, aging)
    if (
        any(k in tl for k in ["invoice", "ledger", "payment", "account", "policy", "finance"])
        or re.search(r"\b(cash[- ]flow|aging|aging report|aging buckets)\b", tl)
    ):
        if any(k in tl for k in ["create", "add", "post", "allocate", "update", "record"]):
            return "finance", "write", "finance_write"
        return "finance", "read", "finance_read"

    # 4) Inventory intents
    if any(k in tl for k in ["stock", "inventory", "supplier", "purchase order", "po", "reorder"]):
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
        self.sales     = SalesAgent()
        self.finance   = FinanceAgent()
        self.inventory = InventoryAgent()
        self.analytics = AnalyticsAgent()

    def route_request(self, message: str, user_id: str) -> Dict[str, Any]:
        # Persist the incoming message
        conv_id = ensure_conversation(user_id)
        save_message(conv_id, "user", message)

        # Classify the intent
        module, op_type, action = classify_intent(message)

        # Handle general/unknown
        if module == "general":
            greeting = (
                "👋 Hello! I can help with customers, invoices, stock levels, and reports.\n"
                "Try:\n"
                "- List all customers\n"
                "- Show unpaid invoices\n"
                "- Check stock levels\n"
                "- Show analytics report"
            )
            reply = text_payload(greeting)
            save_message(conv_id, "router", greeting)
            return reply

        if module == "unknown":
            apology = (
                "I couldn’t understand that. Try asking about sales, finance, inventory, or analytics."
            )
            reply = text_payload(apology)
            save_message(conv_id, "router", apology)
            return reply

        # Read flows
        if op_type == "read":
            try:
                if module == "sales":
                    result = self.sales.process_request(message)
                    log_tool_call("sales", "sales_sql_read", {"msg": message}, result)
                    save_message(conv_id, "sales", str(result))
                    return result

                if module == "finance":
                    result = self.finance.process_request(message)
                    log_tool_call("finance", "finance_sql_read", {"msg": message}, result)
                    save_message(conv_id, "finance", str(result))
                    return result

                if module == "inventory":
                    result = self.inventory.process_request(message)
                    log_tool_call("inventory", "inventory_sql_read", {"msg": message}, result)
                    save_message(conv_id, "inventory", str(result))
                    return result

                if module == "analytics":
                    result = self.analytics.process_request(message)
                    log_tool_call("analytics", "analytics_read", {"msg": message}, result)
                    save_message(conv_id, "analytics", str(result))
                    return result

            except Exception as e:
                err = text_payload(f"Error during read operation: {e}")
                log_tool_call(module, f"{module}_read_error", {"msg": message}, {"error": str(e)}, status="error")
                save_message(conv_id, "router", err["content"])
                return err

        # Write flows (with approval gating)
        need_ok, reason = requires_approval(module, action, {"message": message})
        if need_ok:
            appr_id = request_approval(module, {"message": message}, requested_by=user_id)
            pending = text_payload(f"Action queued for approval (id={appr_id}). Reason: {reason}")
            log_tool_call(module, "approval_requested", {"action": action, "msg": message},
                          {"approval_id": appr_id}, status="pending")
            save_message(conv_id, "router", pending["content"])
            return pending

        try:
            if module == "sales":
                result = self.sales.write(message)
                log_tool_call("sales", "sales_sql_write", {"msg": message}, result)
                save_message(conv_id, "sales", str(result))
                return result

            if module == "finance":
                result = self.finance.write(message)
                log_tool_call("finance", "finance_sql_write", {"msg": message}, result)
                save_message(conv_id, "finance", str(result))
                return result

            if module == "inventory":
                result = self.inventory.write(message)
                log_tool_call("inventory", "inventory_sql_write", {"msg": message}, result)
                save_message(conv_id, "inventory", str(result))
                return result

            # analytics has no write path yet
            reply = text_payload("Write operations are not supported for analytics.")
            save_message(conv_id, "router", reply["content"])
            return reply

        except Exception as e:
            err = text_payload(f"Something went wrong while processing your request: {e}")
            log_tool_call(module, "router_error", {"msg": message}, {"error": str(e)}, status="error")
            save_message(conv_id, "router", err["content"])
            return err
