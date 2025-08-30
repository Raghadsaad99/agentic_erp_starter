# orchestrator/classifier.py
def classify_intent(text: str) -> str:
    """
    Simple keyword-based intent classifier that maps text to a domain label.
    """
    text_lower = text.lower()
    if any(word in text_lower for word in ["sale", "customer", "lead", "order"]):
        return "sales"
    if any(word in text_lower for word in ["invoice", "payment", "finance", "ledger"]):
        return "finance"
    if any(word in text_lower for word in ["inventory", "stock", "supplier", "purchase"]):
        return "inventory"
    if any(word in text_lower for word in ["report", "analytics", "kpi", "metric"]):
        return "analytics"
    return "general"
