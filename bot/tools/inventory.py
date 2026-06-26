"""Inventory tool: check available stock for a product."""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from bot.db.models import Product


def check_stock(db: Session, product_name: str) -> dict:
    """Return how many units of a product are currently available."""
    product = db.scalar(
        select(Product).where(func.lower(Product.name) == product_name.strip().lower())
    )
    if product is None:
        return {"found": False, "product_name": product_name}
    return {
        "found": True,
        "product_name": product.name,
        "stock_quantity": product.stock_quantity,
        "in_stock": product.stock_quantity > 0,
    }
