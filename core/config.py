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
MODEL_NAME = os.getenv("MODEL_NAME", "")