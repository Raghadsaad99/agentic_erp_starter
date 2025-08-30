# app/main.py

import os
import sys
import logging
from fastapi import FastAPI
from dotenv import load_dotenv

# 1) Configure logging to stdout so Docker sees it
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s'
)

# 2) Load environment
load_dotenv()

# 3) Create all tables
from app.db import engine, Base
import app.models.customer
import app.models.order
import app.models.order_item
import app.models.invoice
import app.models.invoice_line
import app.models.payment
import app.models.payment_allocation

Base.metadata.create_all(bind=engine)

# 4) Create app and mount your routers
from app.api.chat      import router as chat_router
from app.api.approvals import router as approvals_router
from app.api.tools     import router as tools_router

app = FastAPI(title="ERP Agents API")

# Mount your routers under /api
app.include_router(chat_router,      prefix="/api", tags=["chat"])
app.include_router(approvals_router, prefix="/api/approvals", tags=["approvals"])
app.include_router(tools_router,     prefix="/api/tools", tags=["tools"])

# 5) Health-check
@app.get("/health")
async def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
