from sentence_transformers import SentenceTransformer
from core.config import MODEL_NAME

print("Loading E5 Multilingual model...")
model = SentenceTransformer('intfloat/multilingual-e5-small')

def get_vector_for_db(text: str) -> list:
    """Use the 'passage:' prefix when saving items TO the database."""
    formatted_text = f"passage: {text}"
    return model.encode(formatted_text).tolist()

def get_vector_for_search(text: str) -> list:
    """Use the 'query:' prefix when SEARCHING the database."""
    formatted_text = f"query: {text}"
    return model.encode(formatted_text).tolist()