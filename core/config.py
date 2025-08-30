import os
from dotenv import load_dotenv

load_dotenv()  # read from .env if present

DB_PATH = os.getenv("ERP_DB_PATH", "db/erp_v2.db")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0"))
