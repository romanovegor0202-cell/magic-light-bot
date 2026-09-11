import json
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parent / "products.json"

with DATA_FILE.open("r", encoding="utf-8") as f:
    PRODUCTS = json.load(f)

BY_ID = {p["id"]: p for p in PRODUCTS}
CATEGORIES = []
for p in PRODUCTS:
    if p["category"] not in CATEGORIES:
        CATEGORIES.append(p["category"])


def get_product(product_id: str):
    return BY_ID.get(product_id)


def get_products_by_category(category: str):
    return [p for p in PRODUCTS if p["category"] == category]


def price_for_quantity(product: dict, quantity: int):
    pricing = product["pricing"]
    if pricing["type"] == "fixed":
        value = pricing["price"] * quantity
        return value, value
    if pricing["type"] == "tiered":
        value = pricing["first"] + max(0, quantity - 1) * pricing["additional"]
        return value, value
    if pricing["type"] == "range":
        return pricing["min"] * quantity, pricing["max"] * quantity
    raise ValueError(f"Unknown pricing type: {pricing['type']}")


def money(value: int) -> str:
    return f"{value:,}".replace(",", " ") + " ₽"


def price_label(product: dict):
    pricing = product["pricing"]
    if pricing["type"] == "fixed":
        return money(pricing["price"])
    if pricing["type"] == "tiered":
        return f"1-й запуск — {money(pricing['first'])}\nДоп. запуск — {money(pricing['additional'])}"
    return f"От {money(pricing['min'])} до {money(pricing['max'])}"
