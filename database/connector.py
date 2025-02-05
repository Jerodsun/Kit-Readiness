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


def get_warehouse_health_metrics():
    logger.info("Fetching warehouse health metrics.")
    with get_db_connection() as conn:
        cursor = conn.cursor()
        result = cursor.execute(
            """
            WITH StockLevels AS (
                SELECT 
                    w.warehouse_id,
                    w.warehouse_name,
                    COUNT(CASE WHEN wi.quantity <= wi.min_stock THEN 1 END) as low_stock_items,
                    COUNT(wi.component_id) as total_items,
                    SUM(wi.quantity) as total_inventory,
                    AVG(CAST(wi.quantity as FLOAT) / NULLIF(wi.max_stock, 0)) * 100 as stock_level_percentage
                FROM warehouses w
                LEFT JOIN warehouse_inventory wi ON w.warehouse_id = wi.warehouse_id
                GROUP BY w.warehouse_id, w.warehouse_name
            )
            SELECT 
                *,
                CASE 
                    WHEN stock_level_percentage >= 80 THEN 'Healthy'
                    WHEN stock_level_percentage >= 50 THEN 'Warning'
                    ELSE 'Critical'
                END as health_status
            FROM StockLevels
            ORDER BY stock_level_percentage DESC
            """
        ).fetchall()
        logger.info(f"Retrieved health metrics for {len(result)} warehouses.")
        return result


def get_kit_components():
    logger.info("Fetching kit component mappings")
    with get_db_connection() as conn:
        cursor = conn.cursor()
        result = cursor.execute(
            """
            SELECT 
                k.kit_id,
                k.kit_name,
                k.description as kit_description,
                c.component_id,
                c.component_name,
                kc.quantity as required_quantity
            FROM kits k
            JOIN kit_components kc ON k.kit_id = kc.kit_id
            JOIN components c ON kc.component_id = c.component_id
            ORDER BY k.kit_name, c.component_name
        """
        ).fetchall()
        return result


def calculate_possible_kits(warehouse_id):
    logger.info(f"Calculating possible kits for warehouse {warehouse_id}")
    with get_db_connection() as conn:
        cursor = conn.cursor()
        result = cursor.execute(
            """
            WITH KitLimits AS (
                SELECT 
                    k.kit_id,
                    k.kit_name,
                    MIN(FLOOR(CAST(wi.quantity AS FLOAT) / kc.quantity)) as possible_kits
                FROM kits k
                JOIN kit_components kc ON k.kit_id = kc.kit_id
                JOIN warehouse_inventory wi ON kc.component_id = wi.component_id
                WHERE wi.warehouse_id = ?
                GROUP BY k.kit_id, k.kit_name
            )
            SELECT 
                kit_id,
                kit_name,
                possible_kits
            FROM KitLimits
            ORDER BY kit_name
        """,
            (warehouse_id,),
        ).fetchall()
        return result


def calculate_rebalance_suggestions(
    source_id, dest_id, min_transfers=1, max_transfers=100
):
    logger.info(
        f"Calculating rebalance suggestions between warehouses {source_id} and {dest_id}"
    )
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Get current kit completion possibilities for both warehouses
        current_source_kits = cursor.execute(
            """
            WITH KitLimits AS (
                SELECT 
                    k.kit_id,
                    MIN(FLOOR(CAST(wi.quantity AS FLOAT) / kc.quantity)) as possible_kits
                FROM kits k
                JOIN kit_components kc ON k.kit_id = kc.kit_id
                JOIN warehouse_inventory wi ON kc.component_id = wi.component_id
                WHERE wi.warehouse_id = ?
                GROUP BY k.kit_id
            )
            SELECT COALESCE(SUM(possible_kits), 0) as total_possible_kits
            FROM KitLimits
        """,
            (source_id,),
        ).fetchone()["total_possible_kits"]

        current_dest_kits = cursor.execute(
            """
            WITH KitLimits AS (
                SELECT 
                    k.kit_id,
                    MIN(FLOOR(CAST(wi.quantity AS FLOAT) / kc.quantity)) as possible_kits
                FROM kits k
                JOIN kit_components kc ON k.kit_id = kc.kit_id
                JOIN warehouse_inventory wi ON kc.component_id = wi.component_id
                WHERE wi.warehouse_id = ?
                GROUP BY k.kit_id
            )
            SELECT COALESCE(SUM(possible_kits), 0) as total_possible_kits
            FROM KitLimits
        """,
            (dest_id,),
        ).fetchone()["total_possible_kits"]

        # Get component inventories and requirements
        source_inventory = cursor.execute(
            """
            SELECT 
                c.component_id,
                c.component_name,
                wi.quantity as available_quantity,
                wi.min_stock,
                wi.max_stock
            FROM warehouse_inventory wi
            JOIN components c ON wi.component_id = c.component_id
            WHERE wi.warehouse_id = ?
        """,
            (source_id,),
        ).fetchall()

        dest_inventory = {
            row["component_id"]: row["quantity"]
            for row in cursor.execute(
                """
            SELECT component_id, quantity
            FROM warehouse_inventory
            WHERE warehouse_id = ?
        """,
                (dest_id,),
            ).fetchall()
        }

        # Calculate potential transfers
        suggestions = []
        for component in source_inventory:
            # Calculate excess inventory (keeping minimum stock level)
            excess = max(0, component["available_quantity"] - component["min_stock"])

            if excess > 0:
                # Calculate how much the destination warehouse needs
                dest_current = dest_inventory.get(component["component_id"], 0)
                dest_max = component["max_stock"]
                dest_capacity = max(0, dest_max - dest_current)

                # Calculate transfer amount within constraints
                transfer_amount = min(excess, dest_capacity, max_transfers)

                if transfer_amount >= min_transfers:
                    # Calculate impact score based on kit completion potential
                    impact_score = cursor.execute(
                        """
                        SELECT COUNT(*) as kit_count
                        FROM kit_components
                        WHERE component_id = ?
                    """,
                        (component["component_id"],),
                    ).fetchone()["kit_count"]

                    suggestions.append(
                        {
                            "component_id": component["component_id"],
                            "component": component["component_name"],
                            "quantity": transfer_amount,
                            "impact": "High"
                            if impact_score > 2
                            else "Medium"
                            if impact_score > 1
                            else "Low",
                            "source_remaining": component["available_quantity"]
                            - transfer_amount,
                            "dest_new_total": dest_current + transfer_amount,
                        }
                    )

        # Sort suggestions by impact
        impact_values = {"High": 3, "Medium": 2, "Low": 1}
        suggestions.sort(
            key=lambda x: (impact_values[x["impact"]], x["quantity"]), reverse=True
        )

        return {
            "suggestions": suggestions,
            "current_metrics": {
                "source_kits": current_source_kits,
                "dest_kits": current_dest_kits,
            },
        }


def update_warehouse_inventory(warehouse_id, updates):
    """
    Updates inventory quantities for a warehouse
    updates: list of dicts with component_id and new quantity
    """
    logger.info(f"Updating inventory for warehouse {warehouse_id}")
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            for update in updates:
                cursor.execute(
                    """
                    UPDATE warehouse_inventory
                    SET quantity = ?
                    WHERE warehouse_id = ? AND component_id = ?
                    """,
                    (update["quantity"], warehouse_id, update["component_id"]),
                )
            conn.commit()
            logger.info(f"Successfully updated {len(updates)} inventory items")
            return True
        except Exception as e:
            logger.error(f"Error updating inventory: {e}")
            conn.rollback()
            return False
