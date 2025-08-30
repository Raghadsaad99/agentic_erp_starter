# Agent-driven ERP System

A modular, agent-driven ERP system powered by OpenAI's language models.

## Features

- Natural language interface for ERP operations
- Specialized agents for Sales, Finance, Inventory, and Analytics
- Router agent for intent classification
- SQLite database with ERP schema
- FastAPI backend
- Streamlit frontend
- Docker containerization

## Setup

1. Place your `erp_v2.db` file in the `db/` directory
2. Set your OpenAI API key in the `.env` file
3. Install dependencies: `pip install -r requirements.txt`
4. Run the backend: `uvicorn backend.app:app --reload`
5. Run the frontend: `streamlit run frontend/streamlit_app.py`

## Docker Deployment

1. Build the image: `docker build -t agentic-erp .`
2. Run the container: `docker run -p 8000:8000 -p 8501:8501 -e OPENAI_API_KEY=your_key_here agentic-erp`

## Usage

1. Open http://localhost:8501
2. Enter your OpenAI API key in the sidebar
3. Start chatting with the ERP system# agentic_erp_starter
