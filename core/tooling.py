# tooling.py
import json

class MCPServer:
    def __init__(self):
        self.tools = {}
    
    def register_tool(self, agent_name, tool_name, tool_function, description=""):
        unique_name = f"{agent_name}_{tool_name}"
        self.tools[unique_name] = {
            "function": tool_function,
            "description": description
        }
    
    def registry_tool(self, query=None):
        if query and "detail" in query.lower():
            tool_list = "\n".join([f"- {name}: {info['description']}" for name, info in self.tools.items()])
        else:
            tool_list = "\n".join([f"- {name}" for name in self.tools.keys()])
        return f"Available tools:\n{tool_list}"
    
    def call_tool(self, tool_name, arguments):
        if tool_name in self.tools:
            try:
                if isinstance(arguments, dict):
                    return self.tools[tool_name]["function"](**arguments)
                elif isinstance(arguments, str):
                    try:
                        args_dict = json.loads(arguments)
                        return self.tools[tool_name]["function"](**args_dict)
                    except:
                        return self.tools[tool_name]["function"](arguments)
                else:
                    return self.tools[tool_name]["function"](arguments)
            except Exception as e:
                return f"Error calling tool {tool_name}: {str(e)}"
        return f"Tool {tool_name} not found."

# single MCP server instance
mcp_server = MCPServer()
class ToolRegistry:
    def __init__(self):
        self._factories = {}
        self._instances = {}

    def register_tool(self, name: str, factory, description: str):
        self._factories[name] = {"factory": factory, "description": description}

    def get_tool(self, name: str):
        if name not in self._instances:
            self._instances[name] = self._factories[name]["factory"]()
        return self._instances[name]

    def list_tools(self):
        return [{"name": n, "description": f["description"]} for n, f in self._factories.items()]

# Global registry
REGISTRY = ToolRegistry()
