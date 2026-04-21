import psycopg2
from core.config import DB_CONN_STRING

def get_db_connection():
    """Returns a new database connection."""
    return psycopg2.connect(DB_CONN_STRING)