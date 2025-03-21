import sqlite3
import math
import json
import heapq
from collections import defaultdict, namedtuple
import time
from datetime import datetime, timedelta

# Define data structures
Vehicle = namedtuple(
    "Vehicle",
    [
        "id",
        "name",
        "capacity",
        "range_km",
        "speed_kmh",
        "refuel_time",
        "loading_time",
        "unloading_time",
    ],
)
Location = namedtuple(
    "Location",
    [
        "id",
        "name",
        "type",
        "latitude",
        "longitude",
        "refuel_capable",
        "warehouse_capacity",
    ],
)
InventoryType = namedtuple(
    "InventoryType", ["id", "name", "description", "volume_per_unit", "weight_per_unit"]
)
Demand = namedtuple(
    "Demand", ["location_id", "inventory_id", "quantity", "priority", "due_date"]
)
Route = namedtuple(
    "Route",
    [
        "id",
        "origin_id",
        "destination_id",
        "distance_km",
        "estimated_time_hours",
        "restricted_vehicle_types",
    ],
)


class CVRPSolver:
    """Capacitated Vehicle Routing Problem Solver with multiple constraints."""

    def __init__(self, db_path):
        """Initialize the solver with database connection."""
        self.db_path = db_path
        self.conn = None
        self.cursor = None

        # Data structures
        self.locations = {}  # location_id -> Location
        self.vehicles = {}  # vehicle_id -> Vehicle
        self.inventory_types = {}  # inventory_id -> InventoryType
        self.inventory = defaultdict(dict)  # location_id -> {inventory_id -> quantity}
        self.demand = defaultdict(dict)  # location_id -> {inventory_id -> Demand}
        self.routes = {}  # (origin_id, destination_id) -> Route
        self.distances = {}  # (origin_id, destination_id) -> distance
        self.vehicle_locations = defaultdict(
            dict
        )  # location_id -> {vehicle_id -> quantity}

        # Solution state
        self.available_vehicles = defaultdict(
            dict
        )  # Copy of vehicle_locations for tracking
        self.available_inventory = defaultdict(dict)  # Copy of inventory for tracking
        self.route_graph = defaultdict(list)  # adjacency list for path finding

        # Load all data
        self._connect_db()
        self._load_data()

    def _connect_db(self):
        """Connect to the SQLite database."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # Use row factory for named columns
        self.cursor = self.conn.cursor()

    def _load_data(self):
        """Load all necessary data from the database."""
        # Load locations
        self.cursor.execute("SELECT * FROM locations")
        for row in self.cursor.fetchall():
            self.locations[row["location_id"]] = Location(
                id=row["location_id"],
                name=row["name"],
                type=row["type"],
                latitude=row["latitude"],
                longitude=row["longitude"],
                refuel_capable=bool(row["refuel_capable"]),
                warehouse_capacity=row["warehouse_capacity"],
            )

        # Load vehicles
        self.cursor.execute("SELECT * FROM vehicles")
        for row in self.cursor.fetchall():
            self.vehicles[row["vehicle_id"]] = Vehicle(
                id=row["vehicle_id"],
                name=row["name"],
                capacity=row["capacity"],
                range_km=row["range_km"],
                speed_kmh=row["speed_kmh"],
                refuel_time=row["refuel_time_hours"],
                loading_time=row["loading_time_hours"],
                unloading_time=row["unloading_time_hours"],
            )

        # Load inventory types
        self.cursor.execute("SELECT * FROM inventory_types")
        for row in self.cursor.fetchall():
            self.inventory_types[row["inventory_id"]] = InventoryType(
                id=row["inventory_id"],
                name=row["name"],
                description=row["description"],
                volume_per_unit=row["volume_per_unit"],
                weight_per_unit=row["weight_per_unit"],
            )

        # Load inventory data
        self.cursor.execute("SELECT * FROM inventory")
        for row in self.cursor.fetchall():
            self.inventory[row["location_id"]][row["inventory_id"]] = row["quantity"]

        # Load demand data
        self.cursor.execute("SELECT * FROM demand")
        for row in self.cursor.fetchall():
            self.demand[row["location_id"]][row["inventory_id"]] = Demand(
                location_id=row["location_id"],
                inventory_id=row["inventory_id"],
                quantity=row["quantity"],
                priority=row["priority"],
                due_date=row["due_date"],
            )

        # Load routes
        self.cursor.execute("SELECT * FROM routes")
        for row in self.cursor.fetchall():
            route = Route(
                id=row["route_id"],
                origin_id=row["origin_id"],
                destination_id=row["destination_id"],
                distance_km=row["distance_km"],
                estimated_time_hours=row["estimated_time_hours"],
                restricted_vehicle_types=row["restricted_vehicle_types"],
            )
            self.routes[(row["origin_id"], row["destination_id"])] = route

            # Also save to distances for quick lookup
            self.distances[(row["origin_id"], row["destination_id"])] = row[
                "distance_km"
            ]

            # Build adjacency list for routing
            self.route_graph[row["origin_id"]].append(row["destination_id"])

        # Load vehicle locations
        self.cursor.execute("SELECT * FROM vehicle_locations")
        for row in self.cursor.fetchall():
            self.vehicle_locations[row["location_id"]][row["vehicle_type_id"]] = row[
                "quantity"
            ]

        # Initialize solution state
        self.reset_solution_state()

        print(
            f"Loaded {len(self.locations)} locations, {len(self.vehicles)} vehicle types"
        )
        print(
            f"Loaded {sum(len(inv) for inv in self.inventory.values())} inventory records"
        )
        print(f"Loaded {sum(len(dem) for dem in self.demand.values())} demand records")
        print(f"Loaded {len(self.routes)} routes")

    def reset_solution_state(self):
        """Reset the solution state to initial conditions."""
        # Deep copy of inventory and vehicle locations
        self.available_inventory = defaultdict(dict)
        for loc_id, inv_dict in self.inventory.items():
            for inv_id, qty in inv_dict.items():
                self.available_inventory[loc_id][inv_id] = qty

        self.available_vehicles = defaultdict(dict)
        for loc_id, veh_dict in self.vehicle_locations.items():
            for veh_id, qty in veh_dict.items():
                self.available_vehicles[loc_id][veh_id] = qty

    def haversine_distance(self, lat1, lon1, lat2, lon2):
        """Calculate the great circle distance between two points in kilometers."""
        # Convert decimal degrees to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

        # Haversine formula
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.asin(math.sqrt(a))
        r = 6371  # Radius of earth in kilometers
        return c * r

    def get_distance(self, origin_id, destination_id):
        """Get the distance between two locations."""
        # Check if we have a direct route
        if (origin_id, destination_id) in self.distances:
            return self.distances[(origin_id, destination_id)]

        # If not, calculate using coordinates
        origin = self.locations[origin_id]
        destination = self.locations[destination_id]
        return self.haversine_distance(
            origin.latitude,
            origin.longitude,
            destination.latitude,
            destination.longitude,
        )

    def find_path(self, origin_id, destination_id, max_range, max_hops=2):
        """
        Find a path from origin to destination respecting range constraints.
        Uses Dijkstra's algorithm with a limit on the number of hops.

        Args:
            origin_id: Starting location ID
            destination_id: Target location ID
            max_range: Maximum range of the vehicle in kilometers
            max_hops: Maximum number of intermediate stops allowed

        Returns:
            List of location IDs representing the path, or None if no path found
        """
        # Priority queue for Dijkstra's algorithm
        pq = [
            (0, origin_id, [origin_id], 0)
        ]  # (total_distance, current_id, path, hops)
        visited = set()  # Track visited locations for each hop count

        while pq:
            total_dist, current_id, path, hops = heapq.heappop(pq)

            # If we've reached the destination, return the path
            if current_id == destination_id:
                return path

            # Skip if we've visited this node with the same or fewer hops
            state = (current_id, hops)
            if state in visited:
                continue
            visited.add(state)

            # If we've reached the maximum number of hops, only try to go directly to destination
            if hops >= max_hops:
                if destination_id in self.route_graph[current_id]:
                    next_dist = self.get_distance(current_id, destination_id)
                    if next_dist <= max_range:
                        new_path = path + [destination_id]
                        heapq.heappush(
                            pq,
                            (
                                total_dist + next_dist,
                                destination_id,
                                new_path,
                                hops + 1,
                            ),
                        )
                continue

            # Try all neighbors
            for next_id in self.route_graph[current_id]:
                # Skip if already in path (avoid cycles)
                if next_id in path:
                    continue

                # Calculate distance to next node
                next_dist = self.get_distance(current_id, next_id)

                # Skip if beyond range
                if next_dist > max_range:
                    continue

                # Skip if not a refuel point and not the destination
                if (
                    next_id != destination_id
                    and not self.locations[next_id].refuel_capable
                ):
                    continue

                # Add to queue
                new_path = path + [next_id]
                heapq.heappush(
                    pq, (total_dist + next_dist, next_id, new_path, hops + 1)
                )

        # No path found
        return None

    def find_all_paths(
        self, origin_id, destination_id, max_range, max_hops=2, max_paths=10
    ):
        """
        Find multiple paths from origin to destination.
        Returns paths sorted by total distance.

        Args:
            origin_id: Starting location ID
            destination_id: Target location ID
            max_range: Maximum range of the vehicle in kilometers
            max_hops: Maximum number of intermediate stops allowed
            max_paths: Maximum number of paths to return

        Returns:
            List of paths, where each path is a list of location IDs
        """
        # Use Dijkstra's for the first path
        first_path = self.find_path(origin_id, destination_id, max_range, max_hops)
        if not first_path:
            return []

        all_paths = [first_path]

        # Use a modified k-shortest paths approach
        # We'll find alternative paths by temporarily removing edges from the best path
        original_graph = dict(self.route_graph)  # Save original graph

        for _ in range(1, max_paths):
            if not all_paths:
                break

            # Get the last best path
            prev_path = all_paths[-1]

            # Try removing one edge at a time from the previous best path
            found_alternative = False

            for i in range(len(prev_path) - 1):
                u, v = prev_path[i], prev_path[i + 1]

                # Temporarily remove this edge
                self.route_graph[u] = [x for x in self.route_graph[u] if x != v]

                # Find a new path
                new_path = self.find_path(
                    origin_id, destination_id, max_range, max_hops
                )

                # Restore the edge
                self.route_graph[u] = original_graph[u]

                if new_path and new_path not in all_paths:
                    all_paths.append(new_path)
                    found_alternative = True
                    break

            if not found_alternative:
                break

        # Restore original graph (just to be safe)
        self.route_graph = original_graph

        # Sort paths by total distance
        return sorted(all_paths, key=lambda path: self.calculate_path_distance(path))

    def calculate_path_distance(self, path):
        """Calculate the total distance of a path."""
        if not path or len(path) < 2:
            return float("inf")

        total_distance = 0
        for i in range(len(path) - 1):
            total_distance += self.get_distance(path[i], path[i + 1])

        return total_distance

    def calculate_path_time(self, path, vehicle):
        """
        Calculate the total time of a path including travel, refueling, and loading/unloading.

        Args:
            path: List of location IDs
            vehicle: Vehicle namedtuple

        Returns:
            Total time in hours
        """
        if not path or len(path) < 2:
            return float("inf")

        total_time = 0

        # Loading time at origin
        total_time += vehicle.loading_time

        for i in range(len(path) - 1):
            # Travel time
            distance = self.get_distance(path[i], path[i + 1])
            travel_time = distance / vehicle.speed_kmh
            total_time += travel_time

            # Add refueling time at intermediate stops (except destination)
            if i < len(path) - 2 and self.locations[path[i + 1]].refuel_capable:
                total_time += vehicle.refuel_time

        # Unloading time at destination
        total_time += vehicle.unloading_time

        return total_time

    def find_vehicle_for_delivery(self, origin_id, inventory_needs, max_hops=2):
        """
        Find the best vehicle and route for a delivery.

        Args:
            origin_id: Starting warehouse ID
            inventory_needs: Dictionary mapping inventory_id to quantity needed
            max_hops: Maximum number of intermediate stops

        Returns:
            Tuple of (vehicle, path, loading_plan) or (None, None, None) if no solution
            where loading_plan is a dictionary mapping inventory_id to quantity to load
        """
        best_vehicle = None
        best_path = None
        best_loading_plan = None
        best_score = float("-inf")

        # Calculate total volume needed
        total_volume_needed = sum(
            qty * self.inventory_types[inv_id].volume_per_unit
            for inv_id, qty in inventory_needs.items()
        )

        # Get available vehicles at this origin
        available_vehicles_at_origin = self.available_vehicles.get(origin_id, {})

        for vehicle_id, count in available_vehicles_at_origin.items():
            if count <= 0:
                continue

            vehicle = self.vehicles[vehicle_id]

            # Skip if vehicle capacity is insufficient
            if vehicle.capacity < total_volume_needed:
                continue

            # Check inventory availability at origin
            inventory_at_origin = self.available_inventory.get(origin_id, {})
            loading_plan = {}
            can_fulfill = True

            for inv_id, qty_needed in inventory_needs.items():
                available = inventory_at_origin.get(inv_id, 0)
                if available < qty_needed:
                    can_fulfill = False
                    break
                loading_plan[inv_id] = qty_needed

            if not can_fulfill:
                continue

            # Find all possible destinations
            destinations = list(self.demand.keys())

            for destination_id in destinations:
                if destination_id == origin_id:
                    continue

                # Find paths from origin to destination
                paths = self.find_all_paths(
                    origin_id,
                    destination_id,
                    vehicle.range_km,
                    max_hops,
                    max_paths=3,  # Limit to top 3 paths
                )

                for path in paths:
                    # Calculate metrics for this path
                    distance = self.calculate_path_distance(path)
                    time = self.calculate_path_time(path, vehicle)

                    # Calculate how much of the demand can be fulfilled
                    destination_demand = self.demand.get(destination_id, {})
                    fulfilled_demand = {}

                    for inv_id, qty_loaded in loading_plan.items():
                        if inv_id in destination_demand:
                            fulfilled_demand[inv_id] = min(
                                qty_loaded, destination_demand[inv_id].quantity
                            )

                    total_fulfilled = sum(fulfilled_demand.values())
                    if total_fulfilled == 0:
                        continue

                    # Calculate score based on multiple factors
                    # - Higher priority demand is better
                    # - Shorter distance is better
                    # - Shorter time is better
                    # - More fulfilled demand is better
                    # - Fewer hops is better

                    priority_score = sum(
                        fulfilled_demand.get(inv_id, 0)
                        * self.demand[destination_id][inv_id].priority
                        for inv_id in fulfilled_demand
                    )

                    distance_score = 1000 / (distance + 1)  # Lower distance is better
                    time_score = 100 / (time + 1)  # Lower time is better
                    demand_score = (
                        total_fulfilled * 10
                    )  # More fulfilled demand is better
                    hop_score = 50 / (len(path) - 1)  # Fewer hops is better

                    # Weight the different factors
                    score = (
                        priority_score * 2.0
                        + distance_score * 0.5
                        + time_score * 0.5
                        + demand_score * 1.0
                        + hop_score * 0.5
                    )

                    if score > best_score:
                        best_score = score
                        best_vehicle = vehicle
                        best_path = path
                        best_loading_plan = loading_plan

        return best_vehicle, best_path, best_loading_plan

    def solve(self, max_hops=2, max_vehicles=None):
        """
        Solve the CVRP problem.

        Args:
            max_hops: Maximum number of intermediate stops
            max_vehicles: Maximum number of vehicles to use (None for unlimited)

        Returns:
            List of delivery routes and solution statistics
        """
        # Reset solution state
        self.reset_solution_state()

        # Track solution
        deliveries = []
        vehicle_count = 0

        # Track unfulfilled demand
        unfulfilled = {}
        for loc_id, demand_dict in self.demand.items():
            for inv_id, demand in demand_dict.items():
                if loc_id not in unfulfilled:
                    unfulfilled[loc_id] = {}
                unfulfilled[loc_id][inv_id] = demand.quantity

        # Process demand by priority and location
        # First, sort locations by maximum priority of any demand item
        locations_by_priority = []
        for loc_id, demand_dict in self.demand.items():
            max_priority = max(demand.priority for demand in demand_dict.values())
            locations_by_priority.append((loc_id, max_priority))

        # Sort by priority (descending)
        locations_by_priority.sort(key=lambda x: x[1], reverse=True)

        # Process each location
        for loc_id, _ in locations_by_priority:
            while loc_id in unfulfilled and any(unfulfilled[loc_id].values()):
                # Check if we've reached the vehicle limit
                if max_vehicles is not None and vehicle_count >= max_vehicles:
                    break

                # Get current demand for this location
                current_demand = {
                    inv_id: qty
                    for inv_id, qty in unfulfilled[loc_id].items()
                    if qty > 0
                }

                if not current_demand:
                    break

                # Try each warehouse as a source
                best_delivery = None
                best_origin = None
                best_vehicle = None
                best_path = None
                best_loading = None

                for warehouse_id in self.locations:
                    # Skip if not a warehouse
                    if "WAREHOUSE" not in self.locations[warehouse_id].type:
                        continue

                    # Try to find a vehicle for this delivery
                    vehicle, path, loading = self.find_vehicle_for_delivery(
                        warehouse_id, current_demand, max_hops
                    )

                    if vehicle and path and loading:
                        # Check if this is the first solution or better than current best
                        if not best_delivery or (
                            sum(loading.values()) > sum(best_loading.values())
                        ):
                            best_origin = warehouse_id
                            best_vehicle = vehicle
                            best_path = path
                            best_loading = loading

                # If we found a solution, add it to deliveries
                if best_vehicle and best_path and best_loading:
                    # Update available vehicles
                    self.available_vehicles[best_origin][best_vehicle.id] -= 1
                    vehicle_count += 1

                    # Update available inventory
                    for inv_id, qty in best_loading.items():
                        self.available_inventory[best_origin][inv_id] -= qty

                        # Update unfulfilled demand
                        unfulfilled[loc_id][inv_id] -= qty
                        if unfulfilled[loc_id][inv_id] <= 0:
                            del unfulfilled[loc_id][inv_id]

                    # Calculate metrics for this delivery
                    distance = self.calculate_path_distance(best_path)
                    time = self.calculate_path_time(best_path, best_vehicle)

                    # Create delivery record
                    delivery = {
                        "vehicle": best_vehicle._asdict(),
                        "origin": self.locations[best_origin]._asdict(),
                        "destination": self.locations[best_path[-1]]._asdict(),
                        "path": [
                            self.locations[loc_id]._asdict() for loc_id in best_path
                        ],
                        "distance": distance,
                        "time": time,
                        "loading": best_loading,
                        "inventory_types": {
                            inv_id: self.inventory_types[inv_id]._asdict()
                            for inv_id in best_loading.keys()
                        },
                    }

                    deliveries.append(delivery)
                else:
                    # No solution for this location, move to next
                    break

        # Calculate statistics
        stats = self._calculate_statistics(deliveries, unfulfilled)

        return deliveries, stats

    def _calculate_statistics(self, deliveries, unfulfilled):
        """Calculate statistics for the solution."""
        total_vehicles = len(deliveries)
        total_distance = sum(d["distance"] for d in deliveries)
        total_time = sum(d["time"] for d in deliveries)

        # Calculate fulfilled demand
        total_demand = 0
        fulfilled_demand = 0

        for loc_id, demand_dict in self.demand.items():
            for inv_id, demand in demand_dict.items():
                total_demand += demand.quantity

                # Calculate how much is still unfulfilled
                unfulfilled_qty = unfulfilled.get(loc_id, {}).get(inv_id, 0)
                fulfilled_demand += demand.quantity - unfulfilled_qty

        fulfillment_rate = fulfilled_demand / total_demand if total_demand > 0 else 0

        # Analyze warehouse usage
        warehouse_usage = defaultdict(int)
        for delivery in deliveries:
            origin_id = next(
                loc_id
                for loc_id, loc in self.locations.items()
                if loc.name == delivery["origin"]["name"]
            )
            warehouse_usage[origin_id] += 1

        # Calculate balance metrics (how evenly warehouses are used)
        if warehouse_usage:
            usage_values = list(warehouse_usage.values())
            avg_usage = sum(usage_values) / len(usage_values)
            max_usage = max(usage_values)
            min_usage = min(usage_values)
            balance_score = min_usage / max_usage if max_usage > 0 else 1.0
        else:
            avg_usage = 0
            max_usage = 0
            min_usage = 0
            balance_score = 0

        stats = {
            "total_vehicles": total_vehicles,
            "total_distance": total_distance,
            "total_time": total_time,
            "total_demand": total_demand,
            "fulfilled_demand": fulfilled_demand,
            "fulfillment_rate": fulfillment_rate,
            "warehouse_usage": {
                self.locations[wh_id].name: count
                for wh_id, count in warehouse_usage.items()
            },
            "avg_warehouse_usage": avg_usage,
            "max_warehouse_usage": max_usage,
            "min_warehouse_usage": min_usage,
            "balance_score": balance_score,
        }

        return stats

    def save_solution(self, deliveries):
        """Save the solution to the database."""
        cursor = self.conn.cursor()

        # Insert each delivery
        for i, delivery in enumerate(deliveries):
            # Generate delivery ID
            delivery_id = i + 1

            # Get location IDs
            origin_id = next(
                loc_id
                for loc_id, loc in self.locations.items()
                if loc.name == delivery["origin"]["name"]
            )

            destination_id = next(
                loc_id
                for loc_id, loc in self.locations.items()
                if loc.name == delivery["destination"]["name"]
            )

            # Generate timestamps
            start_time = datetime.now().isoformat()
            end_time = (datetime.now() + timedelta(hours=delivery["time"])).isoformat()

            # Serialize path
            path_ids = [
                next(
                    loc_id
                    for loc_id, loc in self.locations.items()
                    if loc.name == path_loc["name"]
                )
                for path_loc in delivery["path"]
            ]

            path_json = json.dumps(path_ids)

            # Insert delivery record
            cursor.execute(
                """
                INSERT INTO deliveries 
                (delivery_id, vehicle_id, start_location_id, end_location_id, 
                 start_time, end_time, total_distance_km, route_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    delivery_id,
                    delivery["vehicle"]["id"],
                    origin_id,
                    destination_id,
                    start_time,
                    end_time,
                    delivery["distance"],
                    path_json,
                ),
            )

            # Insert delivery items
            for inv_id, qty in delivery["loading"].items():
                cursor.execute(
                    """
                    INSERT INTO delivery_items
                    (delivery_id, inventory_id, quantity)
                    VALUES (?, ?, ?)
                    """,
                    (delivery_id, inv_id, qty),
                )

        self.conn.commit()
        print(f"Saved {len(deliveries)} deliveries to database")

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None


# Example usage
if __name__ == "__main__":
    # Create an instance of the CVRP solver
    solver = CVRPSolver("cvrp.db")

    # Solve the problem
    print("Solving CVRP...")
    start_time = time.time()
    deliveries, stats = solver.solve(max_hops=2)
    end_time = time.time()

    # Print solution statistics
    print(f"Solution found in {end_time - start_time:.2f} seconds")
    print(f"Total vehicles used: {stats['total_vehicles']}")
    print(f"Total distance: {stats['total_distance']:.2f} km")
    print(f"Total time: {stats['total_time']:.2f} hours")
    print(f"Demand fulfillment rate: {stats['fulfillment_rate'] * 100:.2f}%")
    print("Warehouse usage:")
    for wh_name, count in stats["warehouse_usage"].items():
        print(f"  {wh_name}: {count} vehicles")

    # Save solution to database
    solver.save_solution(deliveries)

    # Close database connection
    solver.close()
