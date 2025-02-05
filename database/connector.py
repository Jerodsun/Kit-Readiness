import sqlite3
from contextlib import contextmanager

DATABASE_PATH = "database/kit_readiness.db"


@contextmanager
def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def get_all_warehouses():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        return cursor.execute(
            """
            SELECT * FROM warehouses
        """
        ).fetchall()


def get_warehouse_inventory(warehouse_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        return cursor.execute(
            """
            SELECT 
                wi.*, 
                c.component_name,
                c.description
            FROM warehouse_inventory wi
            JOIN components c ON wi.component_id = c.component_id
            WHERE wi.warehouse_id = ?
        """,
            (warehouse_id,),
        ).fetchall()


def get_kit_details():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        return cursor.execute(
            """
            SELECT * FROM kits
        """
        ).fetchall()
