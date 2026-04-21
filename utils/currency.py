import re

def clean_brazilian_price(price_str: str) -> float:
    """Converts a string like 'R$ 1.500,99' to a float 1500.99"""
    if not price_str:
        return 0.0
    clean_str = re.sub(r'[^\d,]', '', price_str)
    clean_str = clean_str.replace(',', '.')
    try:
        return float(clean_str)
    except ValueError:
        return 0.0