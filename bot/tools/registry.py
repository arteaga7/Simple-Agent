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
            "name": "list_products",
            "description": (
                "Lista TODO el catálogo de productos disponibles. Úsalo cuando el cliente "
                "pregunte qué productos/artículos venden o pida ver el catálogo. Sin parámetros."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_products",
            "description": (
                "Busca productos del catálogo por nombre o descripción. "
                "Deja 'query' vacío para listar todo el catálogo."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Texto a buscar, ej. 'vestir'. Vacío = todo."}
                },
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
    """Run a tool by name. ``arguments`` is the JSON string/dict from the model.

    Argument problems (malformed JSON, missing or wrong-typed params) are returned
    as structured ``{"error": ...}`` dicts so the model can read them and retry,
    rather than raised — the model often emits imperfect arguments.
    """
    if isinstance(arguments, str):
        try:
            args = json.loads(arguments) if arguments.strip() else {}
        except json.JSONDecodeError:
            return {"error": f"Argumentos inválidos (JSON) para '{name}': {arguments!r}"}
    else:
        args = arguments or {}
    if not isinstance(args, dict):
        return {"error": f"Los argumentos de '{name}' deben ser un objeto."}

    def _require_str(key: str) -> str:
        value = args.get(key)
        if not isinstance(value, str) or not value.strip():
            raise _ArgError(f"Falta el parámetro de texto '{key}' para '{name}'.")
        return value

    try:
        if name == "get_price":
            return catalog.get_price(db, _require_str("product_name"))
        if name == "list_products":
            return catalog.list_products(db)
        if name == "search_products":
            return catalog.search_products(db, str(args.get("query") or ""))
        if name == "check_stock":
            return inventory.check_stock(db, _require_str("product_name"))
        if name == "create_order":
            items = args.get("items")
            if not isinstance(items, list):
                return {"error": "El parámetro 'items' debe ser una lista de productos."}
            return orders.create_order(db, session_id, items)
        if name == "get_order_status":
            try:
                order_id = int(args["order_id"])
            except (KeyError, TypeError, ValueError):
                return {"error": "Falta un 'order_id' numérico para 'get_order_status'."}
            return orders.get_order_status(db, order_id)
    except _ArgError as exc:
        return {"error": str(exc)}
    return {"error": f"Herramienta desconocida: {name}"}


class _ArgError(Exception):
    """Internal signal for a missing/invalid required argument."""
