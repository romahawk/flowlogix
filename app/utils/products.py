import os
from pathlib import Path

PRODUCTS_FILE = Path(__file__).resolve().parents[2] / "data" / "products.txt"

def load_products():
    if not PRODUCTS_FILE.exists():
        return []
    with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
        return sorted(set(line.strip() for line in f if line.strip()))

def add_product_if_new(product_name):
    name = product_name.strip()
    if not name:
        return
    products = load_products()
    if name not in products:
        with open(PRODUCTS_FILE, "a", encoding="utf-8") as f:
            f.write(name + "\n")
