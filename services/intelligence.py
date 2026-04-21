from core.database import get_db_connection
from services.embedding import get_vector_for_search
from core.config import SIMILARITY_THRESHOLD

def get_pricing_intelligence(target_product_name: str, threshold: float = SIMILARITY_THRESHOLD):
    conn = get_db_connection()
    cur = conn.cursor()

    query_vector = get_vector_for_search(target_product_name)

    cur.execute("""
        SELECT title, price_numeric, url 
        FROM product_listings
        WHERE price_numeric > 0 AND title_vector <=> %s::vector < %s
    """, (query_vector, threshold))
    
    matches = cur.fetchall()
    cur.close()
    conn.close()

    if not matches:
        return {"error": "No similar products found."}

    prices = [match[1] for match in matches]
    
    return {
        "target": target_product_name,
        "total_matches_found": len(prices),
        "lowest_price": float(min(prices)),
        "highest_price": float(max(prices)),
        "average_price": round(float(sum(prices) / len(prices)), 2),
    }