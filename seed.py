"""CLI to seed and manage the product catalog.

Run it INSIDE the running stack (recommended), so it targets the compose Postgres:

    docker compose exec api python seed.py                       # seed defaults (idempotent)
    docker compose exec api python seed.py --list
    docker compose exec api python seed.py --add gorra 120 40 "Gorra deportiva"
    docker compose exec api python seed.py --file seed_data.json # add/update many from JSON
    docker compose exec api python seed.py --reset               # wipe products, reseed defaults

Locally (without Docker) it uses DATABASE_URL from your environment/.env — make sure that
points at the right database before running.
"""
import argparse
import json

from sqlalchemy import delete, select

from bot.db import models  # noqa: F401  (registers ORM models on Base)
from bot.db.database import Base, SessionLocal, engine
from bot.db.models import Product
from bot.db.seed import seed_products, upsert_product


def print_catalog(db) -> None:
    products = db.scalars(select(Product).order_by(Product.name)).all()
    if not products:
        print("(catálogo vacío)")
        return
    print(f"{'NOMBRE':<14}{'PRECIO':>10}{'STOCK':>8}  DESCRIPCIÓN")
    print("-" * 60)
    for p in products:
        print(f"{p.name:<14}{float(p.price):>10.2f}{p.stock_quantity:>8}  {p.description}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed/manage the product catalog.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--list", action="store_true", help="List the current catalog.")
    parser.add_argument(
        "--add",
        nargs="+",
        metavar="ARG",
        help="Add/update one product: NAME PRICE STOCK [DESCRIPTION...].",
    )
    parser.add_argument("--file", help="Add/update many products from a JSON file (list of objects).")
    parser.add_argument(
        "--reset", action="store_true", help="Delete ALL products, then reseed the defaults."
    )
    args = parser.parse_args()

    # Make sure tables exist, and show where we're writing (password hidden).
    Base.metadata.create_all(bind=engine)
    print(f"→ Base de datos: {engine.url.render_as_string(hide_password=True)}\n")

    did_something = False
    with SessionLocal() as db:
        if args.reset:
            db.execute(delete(Product))
            db.commit()
            n = seed_products(db)
            print(f"Catálogo reiniciado: {n} productos por defecto insertados.")
            did_something = True

        if args.add:
            if len(args.add) < 3:
                parser.error("--add requiere al menos: NAME PRICE STOCK [DESCRIPTION...]")
            name, price, stock = args.add[0], float(args.add[1]), int(args.add[2])
            description = " ".join(args.add[3:])
            action = upsert_product(db, name, price, stock, description)
            db.commit()
            print(f"Producto '{name}' {action}.")
            did_something = True

        if args.file:
            with open(args.file, encoding="utf-8") as fh:
                items = json.load(fh)
            for item in items:
                action = upsert_product(
                    db,
                    item["name"],
                    item["price"],
                    int(item.get("stock_quantity", 0)),
                    item.get("description", ""),
                )
                print(f"  {item['name']}: {action}")
            db.commit()
            print(f"{len(items)} productos procesados desde {args.file}.")
            did_something = True

        # No mutation flag given -> behave like startup seeding (insert missing defaults).
        if not did_something and not args.list:
            n = seed_products(db)
            print(f"Seed por defecto: {n} productos insertados (los existentes se conservan).")

        if args.list:
            print()
            print_catalog(db)


if __name__ == "__main__":
    main()
