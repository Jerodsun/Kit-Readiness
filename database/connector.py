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
        result = cursor.execute(
            """
            SELECT * FROM warehouses
        """
        ).fetchall()

        return result


def get_warehouse_inventory(warehouse_id):
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
        return result


def get_kit_details():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        result = cursor.execute(
            """
            SELECT * FROM kits
        """
        ).fetchall()

        return result


def get_warehouse_health_metrics():
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

        return result


def get_kit_components(warehouse_id=None):
    """Fetches kit component mappings with current inventory if warehouse specified"""

    with get_db_connection() as conn:
        cursor = conn.cursor()
        if warehouse_id:
            result = cursor.execute(
                """
                SELECT 
                    k.kit_id,
                    k.kit_name,
                    k.description as kit_description,
                    c.component_id,
                    c.component_name,
                    kc.quantity as required_quantity,
                    COALESCE(wi.quantity, 0) as current_inventory,
                    FLOOR(CAST(COALESCE(wi.quantity, 0) AS FLOAT) / kc.quantity) as possible_completions
                FROM kits k
                JOIN kit_components kc ON k.kit_id = kc.kit_id
                JOIN components c ON kc.component_id = c.component_id
                LEFT JOIN warehouse_inventory wi ON c.component_id = wi.component_id 
                    AND wi.warehouse_id = ?
                ORDER BY k.kit_name, c.component_name
                """,
                (warehouse_id,),
            ).fetchall()
        else:
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
                            "impact": (
                                "High"
                                if impact_score > 2
                                else "Medium"
                                if impact_score > 1
                                else "Low"
                            ),
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

            return True
        except Exception as e:
            conn.rollback()
            return False


def create_warehouse_transfer(
    source_id, dest_id, component_id, quantity, transfer_date
):
    """Creates a new warehouse transfer record"""

    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO warehouse_transfers (
                    transfer_date, source_warehouse_id, destination_warehouse_id,
                    component_id, quantity
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (transfer_date, source_id, dest_id, component_id, quantity),
            )
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            return False


def create_end_shipment(warehouse_id, destination_id, kit_id, quantity, shipment_date):
    """Creates a new end-user shipment record"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO end_shipments (
                    shipment_date, warehouse_id, destination_id,
                    kit_id, quantity
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (shipment_date, warehouse_id, destination_id, kit_id, quantity),
            )
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            return False


def get_warehouse_transfers():
    """Fetches all transfers between warehouses"""

    with get_db_connection() as conn:
        cursor = conn.cursor()
        result = cursor.execute(
            """
            SELECT 
                t.transfer_id,
                t.transfer_date,
                w_source.warehouse_name as source_warehouse,
                w_dest.warehouse_name as destination_warehouse,
                c.component_name,
                t.quantity
            FROM warehouse_transfers t
            JOIN warehouses w_source ON t.source_warehouse_id = w_source.warehouse_id
            JOIN warehouses w_dest ON t.destination_warehouse_id = w_dest.warehouse_id
            JOIN components c ON t.component_id = c.component_id
            ORDER BY t.transfer_date DESC
            """
        ).fetchall()
        return result


def get_end_user_shipments():
    """Fetches all shipments to end users"""

    with get_db_connection() as conn:
        cursor = conn.cursor()
        result = cursor.execute(
            """
            SELECT 
                s.shipment_id,
                s.shipment_date,
                w.warehouse_name as source_warehouse,
                d.destination_name,
                k.kit_name,
                s.quantity
            FROM end_shipments s
            JOIN warehouses w ON s.warehouse_id = w.warehouse_id
            JOIN destinations d ON s.destination_id = d.destination_id
            JOIN kits k ON s.kit_id = k.kit_id
            ORDER BY s.shipment_date DESC
            """
        ).fetchall()
        return result


def get_all_destinations():
    """Fetches all destination locations"""

    with get_db_connection() as conn:
        cursor = conn.cursor()
        result = cursor.execute(
            """
            SELECT * FROM destinations
            ORDER BY destination_name
            """
        ).fetchall()

        return result
