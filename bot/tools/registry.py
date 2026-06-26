"""Tool schemas (Groq/OpenAI function-calling format) and the dispatch table.

The agent loop sends ``TOOL_SCHEMAS`` to the model; when the model emits a tool call
we route it through ``dispatch`` to the matching Python function.
"""
import json

from sqlalchemy.orm import Session

from bot.tools import catalog, inventory, orders

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_price",
            "description": "Obtiene el precio del proveedor para un producto del catálogo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_name": {"type": "string", "description": "Nombre del producto, ej. 'camisa'."}
                },
                "required": ["product_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_products",
            "description": "Busca productos del catálogo por nombre o descripción.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Texto a buscar, ej. 'vestir'."}
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_stock",
            "description": "Consulta las existencias disponibles de un producto.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_name": {"type": "string", "description": "Nombre del producto."}
                },
                "required": ["product_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_order",
            "description": (
                "Registra un pedido tras validar productos, precios y existencias. "
                "Úsalo solo cuando el cliente confirme la compra."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "items": {
                        "type": "array",
                        "description": "Productos a pedir.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "product_name": {"type": "string"},
                                "quantity": {"type": "integer", "minimum": 1},
                            },
                            "required": ["product_name", "quantity"],
                        },
                    }
                },
                "required": ["items"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_order_status",
            "description": "Consulta el estado y los productos de un pedido por su id.",
            "parameters": {
                "type": "object",
                "properties": {"order_id": {"type": "integer"}},
                "required": ["order_id"],
            },
        },
    },
]


def dispatch(name: str, arguments: str | dict, db: Session, session_id: str) -> dict:
    """Run a tool by name. ``arguments`` is the JSON string/dict from the model."""
    args = json.loads(arguments) if isinstance(arguments, str) else (arguments or {})

    if name == "get_price":
        return catalog.get_price(db, args["product_name"])
    if name == "search_products":
        return catalog.search_products(db, args["query"])
    if name == "check_stock":
        return inventory.check_stock(db, args["product_name"])
    if name == "create_order":
        return orders.create_order(db, session_id, args.get("items", []))
    if name == "get_order_status":
        return orders.get_order_status(db, int(args["order_id"]))
    return {"error": f"Herramienta desconocida: {name}"}
