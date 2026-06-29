"""Catalog seeding helpers.
`seed_products` runs on startup and only inserts what's missing (idempotent).
`upsert_product` is used by the seed CLI (seed.py) to add or overwrite entries.
"""
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from bot.db.models import Product

# Default catalog, seeded on first startup.
SEED_PRODUCTS = [
    {"name": "camisa", "price": 100, "stock_quantity": 50,
        "description": "Camisa de vestir"},
    {"name": "pantalón", "price": 250, "stock_quantity": 30,
        "description": "Pantalón de vestir"},
    {"name": "corbata", "price": 75, "stock_quantity": 80,
        "description": "Corbata clásica"},
]


def seed_products(db: Session, products: list[dict] | None = None) -> int:
    """Insert any missing products (matched by name). Safe to run repeatedly.
    Existing products are left untouched. Returns the number inserted.
    """
    products = products or SEED_PRODUCTS
    existing = {name.lower()
                for name in db.scalars(select(Product.name)).all()}
    created = 0
    for item in products:
        if item["name"].lower() not in existing:
            db.add(Product(**item))
            created += 1
    if created:
        db.commit()
    return created


def upsert_product(
    db: Session, name: str, price: float, stock_quantity: int = 0, description: str = ""
) -> str:
    """Insert a product or overwrite the existing one (by name). Does NOT commit.
    Returns "created" or "updated" so callers can report what happened.
    """
    name = name.strip()
    product = db.scalar(select(Product).where(
        func.lower(Product.name) == name.lower()))
    if product is None:
        product = Product(name=name)
        db.add(product)
        action = "created"
    else:
        action = "updated"
    product.price = price
    product.stock_quantity = stock_quantity
    product.description = description
    return action
