import sqlite3
import logging
from contextlib import contextmanager

DATABASE_PATH = "database/kit_readiness.db"

# Get logger
logger = logging.getLogger(__name__)


@contextmanager
def get_db_connection():
    logger.info("Connecting to the database.")
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
        logger.info("Database connection closed.")


def get_all_warehouses():
    logger.info("Fetching all warehouses.")
    with get_db_connection() as conn:
        cursor = conn.cursor()
        result = cursor.execute(
            """
            SELECT * FROM warehouses
        """
        ).fetchall()
        logger.info(f"Retrieved {len(result)} warehouses.")
        return result


def get_warehouse_inventory(warehouse_id):
    logger.info(f"Fetching inventory for warehouse ID: {warehouse_id}.")
    with get_db_connection() as conn:
        cursor = conn.cursor()
        result = cursor.execute(
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
        logger.info(
            f"Retrieved {len(result)} inventory items for warehouse ID: {warehouse_id}."
        )
        return result


def get_kit_details():
    logger.info("Fetching all kit details.")
    with get_db_connection() as conn:
        cursor = conn.cursor()
        result = cursor.execute(
            """
            SELECT * FROM kits
        """
        ).fetchall()
        logger.info(f"Retrieved {len(result)} kits.")
        return result
