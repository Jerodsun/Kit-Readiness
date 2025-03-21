import sqlite3
import numpy as np
import pandas as pd
from datetime import datetime, date
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass
from datetime import date, timedelta
import heapq
import logging
from contextlib import contextmanager
from math import radians, cos, sin, asin, sqrt
from collections import defaultdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("logistics_solver")

# Database path
DATABASE_PATH = "database/kit_readiness.db"

# Define Constants
ARRIVAL_DELAY = 0.5  # time in hours for each additional stop
DEFAULT_DISTANCE_WEIGHT = 1.0
DEFAULT_TIME_WEIGHT = 1.0
DEFAULT_BALANCE_WEIGHT = 1.0
DEFAULT_HOP_WEIGHT = 1.0


@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    logger.info("Connecting to the database.")
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
        logger.info("Database connection closed.")


def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(float, [lat1, lon1, lat2, lon2])
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    r = 3958.8  # Radius of earth in miles
    return c * r


@dataclass
class Warehouse:
    """Represents a warehouse location"""

    id: int
    name: str
    location: str
    latitude: float
    longitude: float
    capacity: float = 0
    refuel_capable: bool = (
        True  # Indicates if this location can serve as a refueling point
    )

    def __str__(self):
        return f"Warehouse({self.id}: {self.name} at {self.location})"


@dataclass
class Component:
    """Represents an inventory component"""

    id: int
    name: str
    description: str
    pallets_per_unit: float = 1.0  # Space required per unit

    def __str__(self):
        return f"Component({self.id}: {self.name})"


@dataclass
class Kit:
    """Represents a kit composed of multiple components"""

    id: int
    name: str
    description: str
    components: Dict[int, int] = None  # component_id -> quantity

    def __str__(self):
        return f"Kit({self.id}: {self.name})"


@dataclass
class InventoryItem:
    """Represents inventory of a component at a warehouse"""

    component_id: int
    warehouse_id: int
    quantity: int
    min_stock: int
    max_stock: int

    @property
    def is_low(self) -> bool:
        """Check if inventory is below minimum threshold"""
        return self.quantity <= self.min_stock

    @property
    def excess_quantity(self) -> int:
        """Calculate quantity available for transfer"""
        return max(0, self.quantity - self.min_stock)

    @property
    def capacity_available(self) -> int:
        """Calculate additional capacity available"""
        return max(0, self.max_stock - self.quantity)


@dataclass
class TransferRequest:
    """Represents a request to transfer components between warehouses"""

    source_warehouse_id: int
    destination_warehouse_id: int
    component_id: int
    quantity: int
    priority: int  # 1-10 scale, higher is more important
    request_date: date
    transfer_date: Optional[date] = None
    request_id: Optional[int] = None

    def __str__(self):
        return (
            f"Transfer {self.quantity} of component {self.component_id} from "
            f"warehouse {self.source_warehouse_id} to warehouse {self.destination_warehouse_id}"
        )


@dataclass
class RouteSegment:
    """Represents a segment of a delivery route"""

    origin_id: int
    destination_id: int
    distance: float  # in miles or kilometers
    estimated_time: float  # in hours

    @classmethod
    def calculate(cls, origin: Warehouse, destination: Warehouse, speed: float = 60.0):
        """Create a route segment with calculated distance and time"""
        distance = haversine_distance(
            origin.latitude,
            origin.longitude,
            destination.latitude,
            destination.longitude,
        )
        time = distance / speed
        return cls(origin.id, destination.id, distance, time)


class DeliveryRoute:
    """Represents an optimized delivery route with multiple stops"""

    def __init__(self, starting_warehouse_id: int, max_stops: int = 10):
        self.starting_warehouse_id = starting_warehouse_id
        self.max_stops = max_stops
        self.segments: List[RouteSegment] = []
        self.transfers: List[TransferRequest] = []
        self.current_location_id = starting_warehouse_id
        self.path = [
            starting_warehouse_id
        ]  # List of warehouse IDs in order of visitation

        # Metadata for reporting
        self.aircraft_type_id = None
        self.aircraft_name = ""
        self.origin_name = ""
        self.destination_name = ""
        self.pallets_delivered = 0
        self.total_distance = 0
        self.total_time = 0
        self.delivery_contents = {}  # {component_id: quantity}
        self.pickup_contents = {}  # {warehouse_id: {component_id: quantity}}

    def add_segment(
        self,
        destination_id: int,
        segment: RouteSegment,
        transfer: Optional[TransferRequest] = None,
    ):
        """Add a new segment to the route"""
        if len(self.segments) >= self.max_stops:
            raise ValueError(f"Maximum stops ({self.max_stops}) reached")

        self.segments.append(segment)
        self.path.append(destination_id)
        self.current_location_id = destination_id
        self.total_distance += segment.distance
        self.total_time += segment.estimated_time

        if transfer:
            self.transfers.append(transfer)

        return self

    @property
    def num_hops(self) -> int:
        """Calculate the number of intermediate stops"""
        return len(self.path) - 2 if len(self.path) > 1 else 0

    @property
    def final_destination_id(self) -> int:
        """Get the final destination warehouse ID"""
        return self.path[-1] if self.path else self.starting_warehouse_id

    @property
    def stops(self) -> List[int]:
        """Get the list of warehouse IDs along the route"""
        return self.path

    @property
    def has_cycle(self) -> bool:
        """Check if the route has any cycles (a warehouse appears more than once)"""
        seen = set()
        for warehouse_id in self.path:
            if warehouse_id in seen:
                return True
            seen.add(warehouse_id)
        return False

    def update_metadata(self, data_dict: Dict):
        """Update metadata about this route"""
        for key, value in data_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)
        return self

    def to_dict(self):
        """Convert route to dictionary for serialization"""
        return {
            "starting_warehouse_id": self.starting_warehouse_id,
            "path": self.path,
            "aircraft_type_id": self.aircraft_type_id,
            "aircraft_name": self.aircraft_name,
            "origin_name": self.origin_name,
            "destination_name": self.destination_name,
            "pallets_delivered": self.pallets_delivered,
            "total_distance": round(self.total_distance, 2),
            "total_time": round(self.total_time, 2),
            "num_hops": self.num_hops,
            "delivery_contents": self.delivery_contents,
            "transfers": [str(t) for t in self.transfers],
        }

    def __str__(self):
        """String representation of the route"""
        path_str = " -> ".join([str(w_id) for w_id in self.path])
        return (
            f"Route: {path_str} ({round(self.total_distance, 2)} miles, "
            f"{round(self.total_time, 2)} hours) "
            f"Pallets: {self.pallets_delivered}"
        )


class InventoryManager:
    """Manages inventory across warehouses and handles transfers"""

    def __init__(self):
        self.warehouses: Dict[int, Warehouse] = {}
        self.components: Dict[int, Component] = {}
        self.kits: Dict[int, Kit] = {}
        self.inventory: Dict[Tuple[int, int], InventoryItem] = (
            {}
        )  # (warehouse_id, component_id) -> InventoryItem
        self.pending_transfers: List[TransferRequest] = []

    def load_data_from_db(self):
        """Load all warehouse and inventory data from the database"""
        logger.info("Loading inventory data from database")

        with get_db_connection() as conn:
            # Load warehouses
            cursor = conn.cursor()
            warehouses_query = "SELECT * FROM warehouses"
            warehouses = cursor.execute(warehouses_query).fetchall()

            for w in warehouses:
                self.warehouses[w["warehouse_id"]] = Warehouse(
                    id=w["warehouse_id"],
                    name=w["warehouse_name"],
                    location=w["location"],
                    latitude=w["latitude"],
                    longitude=w["longitude"],
                )

            # Load components
            components_query = "SELECT * FROM components"
            components = cursor.execute(components_query).fetchall()

            for c in components:
                self.components[c["component_id"]] = Component(
                    id=c["component_id"],
                    name=c["component_name"],
                    description=c["description"],
                )

            # Load kits
            kits_query = "SELECT * FROM kits"
            kits = cursor.execute(kits_query).fetchall()

            for k in kits:
                # Get components for this kit
                kit_components_query = """
                    SELECT component_id, quantity 
                    FROM kit_components 
                    WHERE kit_id = ?
                """
                kit_components = cursor.execute(
                    kit_components_query, (k["kit_id"],)
                ).fetchall()

                components_dict = {
                    c["component_id"]: c["quantity"] for c in kit_components
                }

                self.kits[k["kit_id"]] = Kit(
                    id=k["kit_id"],
                    name=k["kit_name"],
                    description=k["description"],
                    components=components_dict,
                )

            # Load inventory
            inventory_query = """
                SELECT 
                    wi.warehouse_id, 
                    wi.component_id, 
                    wi.quantity, 
                    wi.min_stock, 
                    wi.max_stock
                FROM warehouse_inventory wi
            """
            inventory = cursor.execute(inventory_query).fetchall()

            for item in inventory:
                self.inventory[(item["warehouse_id"], item["component_id"])] = (
                    InventoryItem(
                        warehouse_id=item["warehouse_id"],
                        component_id=item["component_id"],
                        quantity=item["quantity"],
                        min_stock=item["min_stock"],
                        max_stock=item["max_stock"],
                    )
                )

            # Load pending transfers
            transfer_query = """
                SELECT 
                    t.transfer_id,
                    t.transfer_date,
                    t.source_warehouse_id,
                    t.destination_warehouse_id,
                    t.component_id,
                    t.quantity,
                    t.scheduled_at
                FROM warehouse_transfers t
                WHERE t.transfer_date >= date('now')
                ORDER BY t.transfer_date ASC
            """
            transfers = cursor.execute(transfer_query).fetchall()

            for t in transfers:
                # Skip if any referenced entity is not found
                if (
                    t["source_warehouse_id"] not in self.warehouses
                    or t["destination_warehouse_id"] not in self.warehouses
                    or t["component_id"] not in self.components
                ):
                    continue

                # Parse dates
                request_date = datetime.strptime(
                    t["scheduled_at"].split()[0], "%Y-%m-%d"
                ).date()
                transfer_date = datetime.strptime(t["transfer_date"], "%Y-%m-%d").date()

                transfer = TransferRequest(
                    source_warehouse_id=t["source_warehouse_id"],
                    destination_warehouse_id=t["destination_warehouse_id"],
                    component_id=t["component_id"],
                    quantity=t["quantity"],
                    priority=5,  # Default priority
                    request_date=request_date,
                    transfer_date=transfer_date,
                    request_id=t["transfer_id"],
                )
                self.pending_transfers.append(transfer)

        logger.info(
            f"Loaded {len(self.warehouses)} warehouses, {len(self.components)} components, "
            f"{len(self.kits)} kits, {len(self.inventory)} inventory items, and "
            f"{len(self.pending_transfers)} pending transfers"
        )

    def get_warehouse_inventory(self, warehouse_id: int) -> List[InventoryItem]:
        """Get all inventory items for a specific warehouse"""
        result = []
        for (wh_id, _), item in self.inventory.items():
            if wh_id == warehouse_id:
                result.append(item)
        return result

    def get_component_inventory(self, component_id: int) -> Dict[int, InventoryItem]:
        """Get inventory of a specific component across all warehouses"""
        result = {}
        for (wh_id, comp_id), item in self.inventory.items():
            if comp_id == component_id:
                result[wh_id] = item
        return result

    def get_inventory(self, warehouse_id: int, component_id: int) -> int:
        """Get the current inventory quantity for a component at a warehouse"""
        inventory_key = (warehouse_id, component_id)
        if inventory_key in self.inventory:
            return self.inventory[inventory_key].quantity
        return 0

    def has_sufficient_inventory(
        self, warehouse_id: int, component_id: int, quantity_needed: int
    ) -> bool:
        """Check if a warehouse has sufficient inventory"""
        available = self.get_inventory(warehouse_id, component_id)
        return available >= quantity_needed

    def create_transfer_request(
        self,
        source_id: int,
        dest_id: int,
        component_id: int,
        quantity: int,
        transfer_date: date,
        priority: int = 5,
    ) -> Optional[TransferRequest]:
        """Create a new transfer request and save it to the database"""
        # Validate warehouse and component exist
        if source_id not in self.warehouses or dest_id not in self.warehouses:
            logger.error(f"Invalid warehouse IDs: {source_id}, {dest_id}")
            return None

        if component_id not in self.components:
            logger.error(f"Invalid component ID: {component_id}")
            return None

        # Check if source has enough inventory
        if not self.has_sufficient_inventory(source_id, component_id, quantity):
            logger.error(f"Not enough inventory at source warehouse {source_id}")
            return None

        # Create the transfer request
        transfer = TransferRequest(
            source_warehouse_id=source_id,
            destination_warehouse_id=dest_id,
            component_id=component_id,
            quantity=quantity,
            priority=priority,
            request_date=date.today(),
            transfer_date=transfer_date,
        )

        # Save to database
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
                    (
                        transfer_date.isoformat(),
                        source_id,
                        dest_id,
                        component_id,
                        quantity,
                    ),
                )
                conn.commit()
                transfer.request_id = cursor.lastrowid
                self.pending_transfers.append(transfer)
                logger.info(f"Created transfer request: {transfer}")
                return transfer
            except Exception as e:
                logger.error(f"Error creating transfer: {e}")
                conn.rollback()
                return None

    def execute_transfer(self, transfer: TransferRequest) -> bool:
        """Execute a transfer request by updating inventory"""
        source_id = transfer.source_warehouse_id
        dest_id = transfer.destination_warehouse_id
        component_id = transfer.component_id
        quantity = transfer.quantity

        # Check if source has enough inventory
        if not self.has_sufficient_inventory(source_id, component_id, quantity):
            logger.error(
                f"Not enough inventory at source warehouse {source_id} for transfer"
            )
            return False

        # Remove from source
        source_key = (source_id, component_id)
        self.inventory[source_key].quantity -= quantity

        # Add to destination
        dest_key = (dest_id, component_id)
        if dest_key in self.inventory:
            self.inventory[dest_key].quantity += quantity
        else:
            # If destination doesn't have this component yet, create inventory record
            # Use same min/max stock as source for now
            source_item = self.inventory[source_key]
            self.inventory[dest_key] = InventoryItem(
                warehouse_id=dest_id,
                component_id=component_id,
                quantity=quantity,
                min_stock=source_item.min_stock,
                max_stock=source_item.max_stock,
            )

        # Update database with the new inventory
        with get_db_connection() as conn:
            cursor = conn.cursor()
            try:
                # Begin transaction
                cursor.execute("BEGIN TRANSACTION")

                # Update source inventory
                cursor.execute(
                    """
                    UPDATE warehouse_inventory
                    SET quantity = ?
                    WHERE warehouse_id = ? AND component_id = ?
                    """,
                    (self.inventory[source_key].quantity, source_id, component_id),
                )

                # Update or insert destination inventory
                dest_exists = cursor.execute(
                    """
                    SELECT 1 FROM warehouse_inventory
                    WHERE warehouse_id = ? AND component_id = ?
                    """,
                    (dest_id, component_id),
                ).fetchone()

                if dest_exists:
                    cursor.execute(
                        """
                        UPDATE warehouse_inventory
                        SET quantity = ?
                        WHERE warehouse_id = ? AND component_id = ?
                        """,
                        (self.inventory[dest_key].quantity, dest_id, component_id),
                    )
                else:
                    cursor.execute(
                        """
                        INSERT INTO warehouse_inventory
                        (warehouse_id, component_id, quantity, min_stock, max_stock)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            dest_id,
                            component_id,
                            quantity,
                            self.inventory[dest_key].min_stock,
                            self.inventory[dest_key].max_stock,
                        ),
                    )

                # Remove from pending transfers if it was there
                if transfer in self.pending_transfers:
                    self.pending_transfers.remove(transfer)

                    # Delete from database if it has a request_id
                    if transfer.request_id:
                        cursor.execute(
                            """
                            DELETE FROM warehouse_transfers
                            WHERE transfer_id = ?
                            """,
                            (transfer.request_id,),
                        )

                # Commit changes
                conn.commit()
                logger.info(f"Successfully executed transfer: {transfer}")
                return True

            except Exception as e:
                conn.rollback()
                logger.error(f"Error executing transfer: {e}")
                return False

    def batch_execute_transfers(self, transfers: List[TransferRequest]) -> bool:
        """Execute multiple transfers in a batch"""
        success = True
        for transfer in transfers:
            if not self.execute_transfer(transfer):
                success = False
        return success

    def calculate_rebalance_suggestions(
        self,
        source_id: int,
        dest_id: int,
        min_transfer_qty: int = 1,
        max_transfer_qty: int = 100,
    ) -> List[Dict]:
        """
        Generate suggestions for rebalancing inventory between two warehouses

        Args:
            source_id: Source warehouse ID
            dest_id: Destination warehouse ID
            min_transfer_qty: Minimum transfer quantity to consider
            max_transfer_qty: Maximum transfer quantity to consider

        Returns:
            List of dictionaries containing transfer suggestions
        """
        suggestions = []

        # Get source and destination inventory
        source_inventory = {
            item.component_id: item
            for item in self.inventory_manager.get_warehouse_inventory(source_id)
        }
        dest_inventory = {
            item.component_id: item
            for item in self.inventory_manager.get_warehouse_inventory(dest_id)
        }

        # Check each component in source inventory
        for component_id, src_item in source_inventory.items():
            # Calculate excess inventory (keeping minimum stock level)
            excess = src_item.excess_quantity

            if excess <= 0:
                continue

            # Calculate how much the destination warehouse needs
            dest_capacity = 0
            if component_id in dest_inventory:
                dest_capacity = dest_inventory[component_id].capacity_available
                dest_current = dest_inventory[component_id].quantity
            else:
                # If component doesn't exist at destination, use source's max_stock as capacity
                dest_capacity = src_item.max_stock
                dest_current = 0

            # Calculate transfer amount within constraints
            transfer_amount = min(excess, dest_capacity, max_transfer_qty)

            if transfer_amount >= min_transfer_qty:
                # Get component info
                component = self.inventory_manager.components.get(component_id)
                component_name = (
                    component.name if component else f"Component {component_id}"
                )

                # Calculate impact (how many kits this could complete)
                impact_score = self.calculate_transfer_impact(
                    component_id, dest_id, transfer_amount
                )

                # Determine impact level based on score
                if impact_score > 5:
                    impact = "High"
                elif impact_score > 2:
                    impact = "Medium"
                else:
                    impact = "Low"

                suggestions.append(
                    {
                        "component_id": component_id,
                        "component": component_name,
                        "quantity": transfer_amount,
                        "impact": impact,
                        "impact_score": impact_score,
                        "source_remaining": src_item.quantity - transfer_amount,
                        "dest_new_total": dest_current + transfer_amount,
                    }
                )

        # Sort suggestions by impact then quantity
        suggestions.sort(key=lambda x: (x["impact_score"], x["quantity"]), reverse=True)

        return suggestions

    def reset_to_initial_state(self):
        """Reset inventory to initial database state"""
        # Reload from database
        self.inventory = {}
        with get_db_connection() as conn:
            cursor = conn.cursor()
            inventory_query = """
                SELECT 
                    wi.warehouse_id, 
                    wi.component_id, 
                    wi.quantity, 
                    wi.min_stock, 
                    wi.max_stock
                FROM warehouse_inventory wi
            """
            inventory = cursor.execute(inventory_query).fetchall()

            for item in inventory:
                self.inventory[(item["warehouse_id"], item["component_id"])] = (
                    InventoryItem(
                        warehouse_id=item["warehouse_id"],
                        component_id=item["component_id"],
                        quantity=item["quantity"],
                        min_stock=item["min_stock"],
                        max_stock=item["max_stock"],
                    )
                )


class LogisticsSolver:
    """Solves logistics problems to find optimal routes for transfers and optimize delivery schedules"""

    def __init__(self, inventory_manager: InventoryManager):
        self.inventory_manager = inventory_manager
        self.arrival_delay = ARRIVAL_DELAY  # Time delay at each stop (hours)
        self.vehicle_speed = 60.0  # Default vehicle speed in miles/hour
        self.max_vehicle_range = 500.0  # Default vehicle range in miles
        self.vehicle_capacity = 10  # Default vehicle capacity in pallets

        # Generate distance matrix for all warehouses
        self.distances = {}
        self.generate_distance_matrix()

        # Default scoring weights
        self.default_weights = {
            "distance": DEFAULT_DISTANCE_WEIGHT,
            "time": DEFAULT_TIME_WEIGHT,
            "balance": DEFAULT_BALANCE_WEIGHT,
            "hops": DEFAULT_HOP_WEIGHT,
        }

    def generate_distance_matrix(self):
        """Calculate distances between all pairs of warehouses"""
        logger.info("Generating distance matrix...")
        for w1_id, w1 in self.inventory_manager.warehouses.items():
            for w2_id, w2 in self.inventory_manager.warehouses.items():
                if w1_id == w2_id:
                    continue
                distance = haversine_distance(
                    w1.latitude, w1.longitude, w2.latitude, w2.longitude
                )
                self.distances[(w1_id, w2_id)] = distance
                # Debug log for extreme distances
                if distance > 1000:
                    logger.debug(
                        f"Long distance {distance:.2f} miles between warehouses {w1_id} and {w2_id}"
                    )
        logger.info(f"Distance matrix generated with {len(self.distances)} entries")

    def get_distance(self, origin_id: int, destination_id: int) -> float:
        """Get distance between two warehouses"""
        if origin_id == destination_id:
            return 0.0
        if (origin_id, destination_id) not in self.distances:
            logger.warning(
                f"No distance found between {origin_id} and {destination_id}"
            )
            # Try to calculate on the fly if warehouses exist
            if (
                origin_id in self.inventory_manager.warehouses
                and destination_id in self.inventory_manager.warehouses
            ):
                w1 = self.inventory_manager.warehouses[origin_id]
                w2 = self.inventory_manager.warehouses[destination_id]
                distance = haversine_distance(
                    w1.latitude, w1.longitude, w2.latitude, w2.longitude
                )
                self.distances[(origin_id, destination_id)] = distance
                return distance
            return float("inf")
        return self.distances.get((origin_id, destination_id), float("inf"))

    def is_direct_route_possible(
        self, origin_id: int, destination_id: int, max_range: float
    ) -> bool:
        """Check if a direct route is possible given the range constraint"""
        distance = self.get_distance(origin_id, destination_id)
        return distance <= max_range

    def find_path(
        self,
        origin_id: int,
        destination_id: int,
        max_range: float = None,
        max_hops: int = 2,
    ) -> List[int]:
        """
        Find a path from origin to destination respecting range constraints
        Uses breadth-first search to find the shortest valid path

        Args:
            origin_id: Starting warehouse ID
            destination_id: Destination warehouse ID
            max_range: Maximum range allowed for each segment (defaults to solver's max_vehicle_range)
            max_hops: Maximum number of intermediate stops allowed

        Returns:
            List of warehouse IDs representing the path, or None if no path found
        """
        # Use class default if max_range not specified
        if max_range is None:
            max_range = self.max_vehicle_range

        # Check if origin and destination exist
        if origin_id not in self.inventory_manager.warehouses:
            logger.error(f"Origin warehouse {origin_id} not found")
            return None
        if destination_id not in self.inventory_manager.warehouses:
            logger.error(f"Destination warehouse {destination_id} not found")
            return None

        # Log the distance and range constraint
        distance = self.get_distance(origin_id, destination_id)
        logger.info(
            f"Distance between warehouses {origin_id} and {destination_id}: {distance:.2f} miles"
        )
        logger.info(f"Maximum range constraint: {max_range:.2f} miles")

        # If direct path is possible, return it
        if self.is_direct_route_possible(origin_id, destination_id, max_range):
            logger.info(
                f"Direct route is possible between {origin_id} and {destination_id}"
            )
            return [origin_id, destination_id]
        else:
            logger.info(
                f"Direct route not possible, searching for path with max {max_hops} hops"
            )

        # Use BFS to find the shortest path
        queue = [(origin_id, [origin_id])]
        visited = set([origin_id])

        while queue:
            (current_id, path) = queue.pop(0)

            # If we've reached the maximum number of hops, skip further exploration
            if len(path) > max_hops + 1:
                continue

            # Check if we can reach the destination from here
            if self.is_direct_route_possible(current_id, destination_id, max_range):
                logger.info(
                    f"Found path with {len(path)} stops: {path + [destination_id]}"
                )
                return path + [destination_id]

            # Try all possible next stops
            for next_id in self.inventory_manager.warehouses:
                # Skip if we've visited this warehouse already
                if next_id in visited:
                    continue

                # Check if this segment is within range
                if self.is_direct_route_possible(current_id, next_id, max_range):
                    visited.add(next_id)
                    queue.append((next_id, path + [next_id]))

        # No path found, log available warehouses for debugging
        logger.error("No path found. Available warehouses:")
        for wh_id, wh in self.inventory_manager.warehouses.items():
            logger.error(
                f"  Warehouse {wh_id}: {wh.name} at ({wh.latitude}, {wh.longitude})"
            )

        # If max_range is less than the direct distance, suggest increasing it
        if distance > max_range:
            logger.error(
                f"Distance ({distance:.2f}) exceeds max range ({max_range:.2f}). Try increasing max_range."
            )

        return None

    def find_all_paths(
        self,
        origin_id: int,
        destination_id: int,
        max_range: float = None,
        max_hops: int = 2,
        max_paths: int = 10,
    ) -> List[List[int]]:
        """
        Find all valid paths from origin to destination respecting range constraints

        Args:
            origin_id: Starting warehouse ID
            destination_id: Destination warehouse ID
            max_range: Maximum range allowed for each segment (defaults to solver's max_vehicle_range)
            max_hops: Maximum number of intermediate stops allowed
            max_paths: Maximum number of paths to return

        Returns:
            List of paths, where each path is a list of warehouse IDs
        """
        # Use class default if max_range not specified
        if max_range is None:
            max_range = self.max_vehicle_range

        # Skip if origin or destination don't exist
        if (
            origin_id not in self.inventory_manager.warehouses
            or destination_id not in self.inventory_manager.warehouses
        ):
            return []
        all_paths = []

        # Use DFS with backtracking
        def dfs(current_id, path, hops_used):
            # If we've found enough paths, stop searching
            if len(all_paths) >= max_paths:
                return

            # If we reached the destination, add the path to results
            if current_id == destination_id:
                all_paths.append(path.copy())
                return

            # If we've used all allowed hops, we can only go to destination
            if hops_used >= max_hops:
                if self.is_direct_route_possible(current_id, destination_id, max_range):
                    all_paths.append(path.copy() + [destination_id])
                return

            # Try all possible next warehouses
            for next_id in self.inventory_manager.warehouses:
                # Skip if already in path (avoid cycles)
                if next_id in path:
                    continue

                # Check if segment is within range
                if self.is_direct_route_possible(current_id, next_id, max_range):
                    # Add to path and continue exploration
                    dfs(next_id, path + [next_id], hops_used + 1)

        # Start DFS from origin
        dfs(origin_id, [origin_id], 0)
        return all_paths


if __name__ == "__main__":
    # Initialize InventoryManager and load data
    inventory_manager = InventoryManager()
    inventory_manager.load_data_from_db()

    # Initialize LogisticsSolver with the inventory manager
    solver = LogisticsSolver(inventory_manager)

    # Show available warehouses
    logger.info("Available warehouses:")
    for wh_id, wh in inventory_manager.warehouses.items():
        logger.info(
            f"  Warehouse {wh_id}: {wh.name} at ({wh.latitude}, {wh.longitude})"
        )

    # Define sample warehouses and components for the test
    source_warehouse_id = 1
    destination_warehouse_id = 2
    component_id = 1
    transfer_quantity = 10
    transfer_date = date.today() + timedelta(days=1)

    # Create a transfer request
    transfer_request = inventory_manager.create_transfer_request(
        source_id=source_warehouse_id,
        dest_id=destination_warehouse_id,
        component_id=component_id,
        quantity=transfer_quantity,
        transfer_date=transfer_date,
    )

    if transfer_request:
        logger.info(f"Transfer request created: {transfer_request}")

        # Execute the transfer
        success = inventory_manager.execute_transfer(transfer_request)
        if success:
            logger.info("Transfer executed successfully.")
        else:
            logger.error("Failed to execute transfer.")
    else:
        logger.error("Failed to create transfer request.")

    # Try to find a path
    path = solver.find_path(
        origin_id=source_warehouse_id,
        destination_id=destination_warehouse_id,
        max_range=5000.0,  # Much larger range
        max_hops=3,
    )

    if path:
        logger.info(f"Found path: {path}")
    else:
        logger.error("No path found even with increased range. Check warehouse data.")
