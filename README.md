# Agent-driven ERP System

A comprehensive, AI-powered Enterprise Resource Planning (ERP) system built with specialized agents for sales, finance, inventory, and analytics operations. This system provides a natural language interface for complex ERP operations, leveraging OpenAI's language models and a modular, agent-driven architecture.

## Table of Contents

- [Overview](#overview)
- [System Architecture](#system-architecture)
- [Agent Responsibilities](#agent-responsibilities)
- [Tool Integration and MCP Compliance](#tool-integration-and-mcp-compliance)
- [Memory Management](#memory-management)
- [Database Usage](#database-usage)
- [Installation and Setup](#installation-and-setup)
- [Running the System](#running-the-system)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

Overview
The Agentic ERP System enables AI-driven management of core business operations using specialized agents. Users interact through plain English commands or queries, which the system routes to the correct agent.
Core Principles:
Agent Specialization – Sales, finance, inventory, analytics.
Natural Language Interface – Easy for non-technical users.
Multi-Capability Protocol (MCP) Compliance – Tools standardized and dynamically discoverable.
Persistent Memory – Conversation history and agent state retained across sessions.
System Architecture
Modular, agent-driven design ensures scalability and maintainability.
Architecture Overview
Frontend (Streamlit UI / React UI)
        |
FastAPI Backend (/api/chat, /api/tools)
        |
Router / Orchestrator
  - Intent Classification
  - Agent Routing
  - Pending Approvals
  |-----> Sales Agent
  |-----> Finance Agent
  |-----> Inventory Agent
  |-----> Analytics Agent
        |
Tool Layer
  - SQLite DB read/write
  - RAG / Vector search
  - ML / Prediction
        |
SQLite Database
  - Customers, Orders, Invoices, Payments, Stock, Ledger, etc.
User Request Flow
User Prompt – Entered via frontend.
Router / Orchestrator – Classifies intent, checks approvals, routes to the correct agent.
Agent Execution – Executes tasks using tools, database access, and ML models.
Router Merges Outputs – Combines responses if multiple agents are involved.
User Response – Final coherent reply delivered.
Agent Responsibilities
Sales Agent
Manages the customer lifecycle and sales operations.
Responsibilities:
Customer info CRUD operations
Order creation and tracking
Sales pipeline and opportunities
Support ticket handling
Sales reporting
Tools:
list_customers, get_customer_details, search_customers
create_order, get_order_details, list_customer_orders
get_order_items, update_order_status
Finance Agent
Handles accounting, payments, and financial reporting.
Responsibilities:
Invoice lifecycle and payments
Accounts receivable
Anomaly detection
Financial reporting
Cash flow analysis
Tools:
list_invoices_by_status, get_invoice_details, search_invoices_by_customer
process_payment, allocate_payment_to_invoice, detect_invoice_anomaly
get_financial_summary
Inventory Agent
Manages stock levels and procurement.
Responsibilities:
Real-time inventory tracking
Reorder and purchase management
Receiving and put-away operations
Stock movement tracking
Supplier management
Tools:
get_stock_levels, get_product_inventory, receive_inventory
update_stock_level, get_stock_movements, get_inventory_report
Analytics Agent
Provides BI and insights.
Responsibilities:
KPI tracking
Revenue & profitability analysis
Customer segmentation
Predictive analytics
Executive dashboards
Tools:
generate_analytics_report, get_revenue_by_product, get_top_customers_by_revenue
generate_custom_report, get_business_metrics, generate_executive_summary
Tool Integration and MCP Compliance
MCP Registry standardizes tool access.
Implementation: core/mcp.py
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
Highlights:
Centralized tool registry
Dynamic discovery for agents
Input schema enforcement via Pydantic
Error handling for resilient execution
Memory Management
Conversation Sessions: Unique IDs for multi-user support
Message Threading: Chronological message storage
Sliding Window: Recent messages retained; older summarized
Agent State Persistence: Retained across sessions
Storage: SQLite (conversations, messages, agent_state)
Optimization: Indexes, caching, lazy loading, semantic compression
Database Usage
SQLite database contains:
Customer Management: customers, customer_kv, leads
Product & Inventory: products, stock, stock_movements, suppliers, supplier_products
Orders: orders, order_items, tickets
Finance: invoices, invoice_lines, invoice_orders, payments, payment_allocations
Accounting: chart_of_accounts, ledger_entries, ledger_lines
Analytics: conversations, agent_state, analytics_data
Installation and Setup
git clone https://github.com/Raghadsaad99/agentic_erp_starter.git
cd agentic_erp_starter
pip install -r requirements.txt
Create .env with OpenAI API key and DB path.
Running the System
Backend (FastAPI)
uvicorn app.main:app --host 0.0.0.0 --port 8000
Frontend (Streamlit)
streamlit run ui/streamlit_app.py --server.port=8501 --server.address=0.0.0.0
Docker
docker-compose up --build
Ports: Backend 8000, UI 8501
API Documentation
POST /api/chat – Process natural language requests
GET /api/tools – List all registered tools
Testing
Unit tests: agent logic, database, tools
Integration tests: end-to-end workflows using pytest
Deployment
Dockerized for easy deployment
Unified DB path in .env and Docker volumes
Scalable via additional agents/tools
Troubleshooting
DB errors: Verify DATABASE_PATH and Docker volumes
API errors: Check FastAPI logs
Memory issues: Check conversation pruning settings
Contributing
Fork the repo
Add new agents/tools
Register tools in REGISTRY
Submit PRs with tests and documentation


uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
streamlit run ui/streamlit_app.py
docker-compose up --build

