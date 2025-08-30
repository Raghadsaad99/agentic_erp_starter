# services/ml.py
from typing import Dict, Any

def lead_score_tool(text: str) -> float:
    # Super simple heuristic; replace with real model later
    tl = text.lower()
    score = 0.5
    if "budget" in tl or "buy" in tl or "quote" in tl:
        score += 0.3
    if "just curious" in tl or "later" in tl:
        score -= 0.2
    return max(0.0, min(1.0, score))

def anomaly_detector_tool(invoice_payload: Dict[str, Any]) -> float:
    # Heuristic based on amount and description length
    amt = float(invoice_payload.get("total_amount", 0) or 0)
    desc_len = sum(len(str(l.get("description",""))) for l in invoice_payload.get("lines", []))
    score = 0.0
    if amt > 10000: score += 0.6
    if desc_len < 10: score += 0.2
    return max(0.0, min(1.0, score))

def forecast_tool(history: list) -> float:
    # Simple mean forecast
    if not history:
        return 0.0
    return sum(history) / len(history)
 