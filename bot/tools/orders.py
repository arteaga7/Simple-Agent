"""Order tools: create an order (with validation) and look up an order's status."""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from bot.db.models import Order, OrderItem, Product


def create_order(db: Session, session_id: str, items: list[dict]) -> dict:
    """Validate items against the catalog and stock, then persist the order.

    Each item is ``{"product_name": str, "quantity": int}``. The whole order is
    rejected (nothing persisted) if any product is unknown or has insufficient stock.
    """
    if not items:
        return {"success": False, "error": "No se especificaron productos."}

    resolved: list[tuple[Product, int]] = []
    for item in items:
        name = str(item.get("product_name", "")).strip()
        try:
            qty = int(item.get("quantity", 0))
        except (TypeError, ValueError):
            return {"success": False, "error": f"Cantidad inválida para '{name}'."}
        if qty <= 0:
            return {"success": False, "error": f"La cantidad de '{name}' debe ser mayor a 0."}

        product = db.scalar(select(Product).where(func.lower(Product.name) == name.lower()))
        if product is None:
            return {"success": False, "error": f"El producto '{name}' no está en el catálogo."}
        if product.stock_quantity < qty:
            return {
                "success": False,
                "error": (
                    f"Stock insuficiente de '{product.name}': "
                    f"disponibles {product.stock_quantity}, solicitados {qty}."
                ),
            }
        resolved.append((product, qty))

    order = Order(session_id=session_id, status="confirmed", total=0)
    db.add(order)
    db.flush()  # assign order.id before adding items

    total = 0.0
    lines = []
    for product, qty in resolved:
        unit_price = float(product.price)
        line_total = unit_price * qty
        total += line_total
        product.stock_quantity -= qty
        db.add(
            OrderItem(
                order_id=order.id,
                product_name=product.name,
                quantity=qty,
                unit_price=unit_price,
                line_total=line_total,
            )
        )
        lines.append(
            {"product_name": product.name, "quantity": qty, "unit_price": unit_price, "line_total": line_total}
        )

    order.total = total
    db.commit()

    return {"success": True, "order_id": order.id, "status": order.status, "total": total, "items": lines}


def get_order_status(db: Session, order_id: int) -> dict:
    """Fetch an order and its line items by id."""
    order = db.get(Order, order_id)
    if order is None:
        return {"found": False, "order_id": order_id}
    return {
        "found": True,
        "order_id": order.id,
        "status": order.status,
        "total": float(order.total),
        "items": [
            {"product_name": i.product_name, "quantity": i.quantity, "line_total": float(i.line_total)}
            for i in order.items
        ],
    }
