"""
Simple DB checks to help verify tenant isolation and app.current_property behavior.

Usage:
    python check.py            # runs checks for all properties in seed/properties.json
    python check.py hotel_a    # run checks for a single property

Checks performed (read-only):
- verifies connection
- verifies set_config('app.current_property', ...) round-trip
- verifies that querying another tenant's rows is not possible (basic RLS check)

This tool is intentionally conservative and only issues SELECTs.
"""
import json
import os
import sys
from app.db import get_conn

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SEED_PROPERTIES_PATH = os.path.join(ROOT_DIR, "seed", "properties.json")


def load_seed_properties():
    if not os.path.exists(SEED_PROPERTIES_PATH):
        return []
    with open(SEED_PROPERTIES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def run_checks(property_id: str, other_property_id: str | None = None):
    print(f"\n== Checks for property: {property_id} ==")
    conn = get_conn()
    cur = conn.cursor()
    try:
        # verify connection
        cur.execute("SELECT 1")
        print("DB connection: OK")

        # set tenant
        cur.execute("SELECT set_config('app.current_property', %s, false)", (property_id,))
        cur.execute("SELECT current_setting('app.current_property', true)")
        current = cur.fetchone()
        print("app.current_property ->", current[0] if current else None)

        # verify properties row
        cur.execute("SELECT name FROM properties WHERE property_id = %s", (property_id,))
        row = cur.fetchone()
        if row:
            print("properties row found ->", row[0])
        else:
            print("properties row NOT found for", property_id)

        # basic RLS check: try to read other tenant bookings
        if other_property_id:
            cur.execute(
                "SELECT COUNT(*) FROM bookings WHERE property_id = %s",
                (other_property_id,)
            )
            other_count = cur.fetchone()[0]
            print(f"rows visible for other tenant ({other_property_id}): {other_count}")
            if other_count > 0:
                print("WARNING: Other tenant rows are visible — RLS may not be enforced.")
            else:
                print("Other tenant rows NOT visible (good).")

    finally:
        cur.close()
        conn.close()


def main():
    args = sys.argv[1:]
    seed = load_seed_properties()
    prop_ids = [p.get("property_id") for p in seed if p.get("property_id")]

    if args:
        targets = [args[0]]
    else:
        targets = prop_ids

    for pid in targets:
        # pick a different property for cross-tenant check
        other = next((p for p in prop_ids if p != pid), None)
        run_checks(pid, other_property_id=other)


if __name__ == "__main__":
    main()
import os

import psycopg2
from dotenv import load_dotenv


load_dotenv()


DATABASE_URL = os.getenv("DATABASE_URL")


def run_query(cur, title, query, params=None):
    print(title)
    cur.execute(query, params or ())
    rows = cur.fetchall()
    for row in rows:
        print(row)
    print()


def main():
    if not DATABASE_URL:
        raise SystemExit("DATABASE_URL is not set")

    conn = psycopg2.connect(DATABASE_URL)
    try:
        cur = conn.cursor()

        run_query(cur, "row_security", "SHOW row_security;")

        run_query(
            cur,
            "policies",
            """
            SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual, with_check
            FROM pg_policies
            WHERE tablename IN (
                'properties',
                'rooms',
                'rates',
                'bookings',
                'messages',
                'events',
                'workflow_jobs'
            )
            ORDER BY tablename, policyname;
            """,
        )

        cur.execute("SELECT set_config('app.current_property', %s, false);", ("hotel_a",))
        print("current_property hotel_a")
        run_query(cur, "booking scope hotel_a", "SELECT DISTINCT property_id FROM bookings ORDER BY property_id;")

        cur.execute("SELECT current_setting('app.current_property', true);")
        print("current_setting after hotel_a:")
        print(cur.fetchone())
        print()

        cur.execute("SELECT set_config('app.current_property', %s, false);", ("hotel_b",))
        print("current_property hotel_b")
        run_query(cur, "booking scope hotel_b", "SELECT DISTINCT property_id FROM bookings ORDER BY property_id;")

        cur.execute("SELECT current_setting('app.current_property', true);")
        print("current_setting after hotel_b:")
        print(cur.fetchone())
        print()

        cur.close()
    finally:
        conn.close()


if __name__ == "__main__":
    main()