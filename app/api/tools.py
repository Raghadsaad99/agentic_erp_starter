# app/api/tools.py

from fastapi          import APIRouter
from orchestrator.registry import REGISTRY

router = APIRouter()


@router.get("/")
def list_tools():
    """
    Returns the list of all registered MCP tools.
    """
    return REGISTRY.list_tools()
