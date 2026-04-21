from sentence_transformers import SentenceTransformer
from core.config import EMBEDDING_MODEL

print(f"Loading embedding model: {EMBEDDING_MODEL}...")
model = SentenceTransformer(EMBEDDING_MODEL)

def get_vector_for_db(text: str) -> list:
    """Use the 'passage:' prefix when saving items TO the database."""
    formatted_text = f"passage: {text}"
    return model.encode(formatted_text).tolist()

def get_vector_for_search(text: str) -> list:
    """Use the 'query:' prefix when SEARCHING the database."""
    formatted_text = f"query: {text}"
    return model.encode(formatted_text).tolist()
    
def get_vector(text: str) -> list:
    """Backward-compatible default helper for existing callers."""
    return get_vector_for_db(text)