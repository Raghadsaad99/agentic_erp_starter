# app/api/chat.py

from typing import Dict
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from orchestrator.router_agent import RouterAgent

router = APIRouter()
agents_by_user: Dict[str, RouterAgent] = {}


class ChatRequest(BaseModel):
    user_id: str = "anon"
    message: str


@router.post("/chat")
def chat(req: ChatRequest):
    """
    Main chat endpoint. Delegates to RouterAgent.route_request(),
    which will call process_request() on the appropriate domain agent.
    """
    uid = req.user_id or "anon"
    agent = agents_by_user.setdefault(uid, RouterAgent())

    try:
        # route_request returns a dict like {"type": "text", "content": ...}
        # or {"type": "table", ...}
        return agent.route_request(req.message, uid)
    except Exception as exc:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error processing request: {exc}")
