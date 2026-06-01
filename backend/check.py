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