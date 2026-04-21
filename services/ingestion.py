import json
from pathlib import Path
from core.database import get_db_connection
from services.embedding import get_vector
from utils.currency import clean_brazilian_price

def ingest_scraped_data():
    """Reads all JSON files in the data_buffer and pushes them to pgvector."""
    data_dir = Path("data_buffer")
    if not data_dir.exists():
        return {"status": "No data buffer found."}
        
    conn = get_db_connection()
    cur = conn.cursor()
    total_inserted = 0

    for json_file in data_dir.glob("*.json"):
        domain_name = json_file.stem
        
        with open(json_file, 'r') as f:
            data = json.load(f)
            
        for item in data:
            clean_price = clean_brazilian_price(item.get('price'))
            title = item.get('title', '')
            vector = get_vector(title)
            
            cur.execute("""
                INSERT INTO product_listings (domain, title, price_numeric, url, seller, title_vector)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (domain_name, title, clean_price, item.get('url'), item.get('seller'), vector))
            total_inserted += 1
            
        # Optional: Delete or move the JSON file after successful ingestion
        # json_file.unlink() 

    conn.commit()
    cur.close()
    conn.close()
    
    return {"status": "success", "inserted": total_inserted}