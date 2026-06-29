"""Catalog tools: look up prices and search the provider's products."""
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from bot.db.models import Product


def get_price(db: Session, product_name: str) -> dict:
    """Return the provider price for a product (case-insensitive exact match)."""
    product = db.scalar(
        select(Product).where(func.lower(Product.name) == product_name.strip().lower())
    )
    if product is None:
        return {"found": False, "product_name": product_name}
    return {
        "found": True,
        "product_name": product.name,
        "price": float(product.price),
        "currency": "MXN",
    }


def _serialize(products) -> dict:
    return {
        "count": len(products),
        "results": [
            {
                "product_name": p.name,
                "price": float(p.price),
                "stock_quantity": p.stock_quantity,
                "description": p.description,
            }
            for p in products
        ],
    }


def list_products(db: Session) -> dict:
    """Return the entire catalog. Use this to answer '¿qué productos venden?'."""
    products = db.scalars(select(Product).order_by(Product.name)).all()
    return _serialize(products)


def search_products(db: Session, query: str = "") -> dict:
    """Search the catalog by name or description (substring, case-insensitive).

    A blank query lists the whole catalog, so the model can enumerate products
    even when the customer doesn't name a specific one.
    """
    query = (query or "").strip()
    if not query:
        return list_products(db)
    pattern = f"%{query}%"
    products = db.scalars(
        select(Product)
        .where(or_(Product.name.ilike(pattern), Product.description.ilike(pattern)))
        .order_by(Product.name)
    ).all()
    return _serialize(products)
