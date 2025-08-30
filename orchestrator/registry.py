# orchestrator/registry.py
from core.tooling import ToolRegistry

REGISTRY = ToolRegistry()

# Importing registers tools
from domain.sales import tools as sales_tools
from domain.finance import tools as finance_tools
from domain.inventory import tools as inventory_tools
