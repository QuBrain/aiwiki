import os
from urllib.parse import urlparse

raw = os.getenv("AIWIKI_DATABASE_URL", "")
if not raw:
    raw = os.getenv("DATABASE_URL", "sqlite:///./aiwiki.db")

# Guard against empty or placeholder values
if not raw or raw.startswith("${{") or "DATABASE_URL" in raw:
    raw = "sqlite:///./aiwiki.db"

DATABASE_URL = raw
LLM_PROVIDER = os.getenv("AIWIKI_LLM_PROVIDER", "simulated")
OPENAI_API_KEY = os.getenv("AIWIKI_OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("AIWIKI_ANTHROPIC_API_KEY", "")
LLM_MODEL = os.getenv("AIWIKI_LLM_MODEL", "gpt-4o")
AGENT_CYCLE_INTERVAL = int(os.getenv("AIWIKI_AGENT_CYCLE_INTERVAL", "300"))
EXTERNAL_RATE_LIMIT = int(os.getenv("AIWIKI_EXTERNAL_RATE_LIMIT", "10"))


def is_postgres() -> bool:
    return DATABASE_URL.startswith("postgresql://") or DATABASE_URL.startswith("postgres://")


def get_postgres_config() -> dict:
    result = urlparse(DATABASE_URL)
    return {
        "dbname": result.path[1:],
        "user": result.username,
        "password": result.password,
        "host": result.hostname,
        "port": result.port or 5432,
    }
