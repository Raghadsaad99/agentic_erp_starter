# core/mcp.py
from typing import Any, Dict, Optional, List
from pydantic import BaseModel

class Tool:
    name: str
    description: str
    input_schema: Optional[BaseModel] = None

    def run(self, **kwargs) -> Any:
        raise NotImplementedError

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool):
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    def list(self) -> List[Dict[str, Any]]:
        out = []
        for t in self._tools.values():
            out.append({
                "name": t.name,
                "description": t.description,
                "input_schema": t.input_schema.model_json_schema() if t.input_schema else None,
            })
        return out

REGISTRY = ToolRegistry()

def registry_tool() -> List[Dict[str, Any]]:
    return REGISTRY.list()
