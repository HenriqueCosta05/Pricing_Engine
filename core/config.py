import os
from dotenv import load_dotenv

load_dotenv()

DB_NAME = os.getenv("DB_NAME", "")
DB_USER = os.getenv("DB_USER", "")
DB_PASS = os.getenv("DB_PASS", "")
DB_HOST = os.getenv("DB_HOST", "")

DB_CONN_STRING = f"dbname={DB_NAME} user={DB_USER} password={DB_PASS} host={DB_HOST}"

# Global AI Settings
SIMILARITY_THRESHOLD = 0.4

# Embedding model for vector storage (used by SentenceTransformer)
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-small")

# LLM provider for schema generation (used by crawl4ai/litellm)
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini/gemini-1.5-flash")

# Fallback LLM providers if primary model fails
LLM_PROVIDER_FALLBACKS = [
    "gemini/gemini-pro",
    "gemini/gemini-1.5-pro",
    "gpt-4o-mini",
]