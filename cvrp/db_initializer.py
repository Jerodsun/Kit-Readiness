import sqlite3
import random
import math
import json
from datetime import datetime


def create_database(db_path="cvrp.db"):
    """Create and initialize the CVRP database with sample data."""
    # Connect to database (will be created if it doesn't exist)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create tables
    with open("database_schema.sql", "r") as f:
        schema_sql = f.read()
        cursor.executescript(schema_sql)

    # Generate sample data
    generate_sample_data(conn)

    # Commit changes and close connection
    conn.commit()
    conn.close()

    print(f"Database created at {db_path}")


def haversine_distance(lat1, lon1, lat2, lon2):
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


def generate_sample_data(conn):
    """Generate and insert sample data into the database."""
    cursor = conn.cursor()

    # Sample locations - mix of warehouses, destinations, and refueling points
    # Using real coordinates for major US cities for realism
    warehouses = [
        (1, "New York Warehouse", "WAREHOUSE", 40.7128, -74.0060, 1, 10000),
        (2, "Los Angeles Warehouse", "WAREHOUSE", 34.0522, -118.2437, 1, 12000),
        (3, "Chicago Warehouse", "WAREHOUSE", 41.8781, -87.6298, 1, 8000),
        (4, "Houston Warehouse", "WAREHOUSE", 29.7604, -95.3698, 1, 9000),
        (5, "Phoenix Warehouse", "WAREHOUSE", 33.4484, -112.0740, 1, 7500),
    ]

    refuel_points = [
        (6, "Denver Refuel Point", "REFUEL_POINT", 39.7392, -104.9903, 1, None),
        (7, "Dallas Refuel Point", "REFUEL_POINT", 32.7767, -96.7970, 1, None),
        (8, "Atlanta Refuel Point", "REFUEL_POINT", 33.7490, -84.3880, 1, None),
        (9, "St Louis Refuel Point", "REFUEL_POINT", 38.6270, -90.1994, 1, None),
        (
            10,
            "Salt Lake City Refuel Point",
            "REFUEL_POINT",
            40.7608,
            -111.8910,
            1,
            None,
        ),
    ]

    # Generate 40 destinations based on smaller US cities
    destinations = [
        (11, "Portland, ME", "DESTINATION", 43.6591, -70.2568, 0, None),
        (12, "Burlington, VT", "DESTINATION", 44.4759, -73.2121, 0, None),
        (13, "Manchester, NH", "DESTINATION", 42.9956, -71.4548, 0, None),
        (14, "Providence, RI", "DESTINATION", 41.8240, -71.4128, 0, None),
        (15, "Hartford, CT", "DESTINATION", 41.7658, -72.6734, 0, None),
        (16, "Buffalo, NY", "DESTINATION", 42.8864, -78.8784, 0, None),
        (17, "Pittsburgh, PA", "DESTINATION", 40.4406, -79.9959, 0, None),
        (18, "Columbus, OH", "DESTINATION", 39.9612, -82.9988, 0, None),
        (19, "Indianapolis, IN", "DESTINATION", 39.7684, -86.1581, 0, None),
        (20, "Louisville, KY", "DESTINATION", 38.2527, -85.7585, 0, None),
        (21, "Nashville, TN", "DESTINATION", 36.1627, -86.7816, 0, None),
        (22, "Birmingham, AL", "DESTINATION", 33.5186, -86.8104, 0, None),
        (23, "Jacksonville, FL", "DESTINATION", 30.3322, -81.6557, 0, None),
        (24, "New Orleans, LA", "DESTINATION", 29.9511, -90.0715, 0, None),
        (25, "Oklahoma City, OK", "DESTINATION", 35.4676, -97.5164, 0, None),
        (26, "Albuquerque, NM", "DESTINATION", 35.0844, -106.6504, 0, None),
        (27, "Tucson, AZ", "DESTINATION", 32.2226, -110.9747, 0, None),
        (28, "Las Vegas, NV", "DESTINATION", 36.1699, -115.1398, 0, None),
        (29, "Sacramento, CA", "DESTINATION", 38.5816, -121.4944, 0, None),
        (30, "San Diego, CA", "DESTINATION", 32.7157, -117.1611, 0, None),
        (31, "Portland, OR", "DESTINATION", 45.5051, -122.6750, 0, None),
        (32, "Seattle, WA", "DESTINATION", 47.6062, -122.3321, 0, None),
        (33, "Boise, ID", "DESTINATION", 43.6150, -116.2023, 0, None),
        (34, "Helena, MT", "DESTINATION", 46.5891, -112.0391, 0, None),
        (35, "Cheyenne, WY", "DESTINATION", 41.1400, -104.8202, 0, None),
        (36, "Rapid City, SD", "DESTINATION", 44.0805, -103.2310, 0, None),
        (37, "Fargo, ND", "DESTINATION", 46.8772, -96.7898, 0, None),
        (38, "Minneapolis, MN", "DESTINATION", 44.9778, -93.2650, 0, None),
        (39, "Milwaukee, WI", "DESTINATION", 43.0389, -87.9065, 0, None),
        (40, "Des Moines, IA", "DESTINATION", 41.5868, -93.6250, 0, None),
        (41, "Kansas City, MO", "DESTINATION", 39.0997, -94.5786, 0, None),
        (42, "Little Rock, AR", "DESTINATION", 34.7465, -92.2896, 0, None),
        (43, "Jackson, MS", "DESTINATION", 32.2988, -90.1848, 0, None),
        (44, "Richmond, VA", "DESTINATION", 37.5407, -77.4360, 0, None),
        (45, "Charlotte, NC", "DESTINATION", 35.2271, -80.8431, 0, None),
        (46, "Charleston, SC", "DESTINATION", 32.7765, -79.9311, 0, None),
        (47, "Omaha, NE", "DESTINATION", 41.2565, -95.9345, 0, None),
        (48, "Wichita, KS", "DESTINATION", 37.6872, -97.3301, 0, None),
        (49, "El Paso, TX", "DESTINATION", 31.7619, -106.4850, 0, None),
        (50, "Baton Rouge, LA", "DESTINATION", 30.4515, -91.1871, 0, None),
    ]

    # Insert all locations
    locations = warehouses + refuel_points + destinations
    cursor.executemany(
        "INSERT INTO locations (location_id, name, type, latitude, longitude, refuel_capable, warehouse_capacity) VALUES (?, ?, ?, ?, ?, ?, ?)",
        locations,
    )

    # Sample vehicles
    vehicles = [
        (1, "Standard Truck", 200, 600, 80, 0.5, 1.0, 0.8),  # 200 capacity, 600km range
        (
            2,
            "Heavy Duty Truck",
            350,
            500,
            70,
            0.6,
            1.5,
            1.0,
        ),  # 350 capacity, 500km range
        (3, "Light Truck", 100, 800, 90, 0.4, 0.7, 0.5),  # 100 capacity, 800km range
    ]

    cursor.executemany(
        "INSERT INTO vehicles (vehicle_id, name, capacity, range_km, speed_kmh, refuel_time_hours, loading_time_hours, unloading_time_hours) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        vehicles,
    )

    # Vehicle locations (place them at warehouses)
    vehicle_locations = []

    # Add standard trucks to all warehouses
    for warehouse_id, _, _, _, _, _, _ in warehouses:
        vehicle_locations.append(
            (1, warehouse_id, random.randint(3, 6))
        )  # 3-6 standard trucks

    # Add heavy duty trucks to some warehouses
    for warehouse_id in [1, 2, 3]:
        vehicle_locations.append(
            (2, warehouse_id, random.randint(2, 4))
        )  # 2-4 heavy duty trucks

    # Add light trucks to all warehouses
    for warehouse_id, _, _, _, _, _, _ in warehouses:
        vehicle_locations.append(
            (3, warehouse_id, random.randint(4, 8))
        )  # 4-8 light trucks

    cursor.executemany(
        "INSERT INTO vehicle_locations (vehicle_type_id, location_id, quantity) VALUES (?, ?, ?)",
        vehicle_locations,
    )

    # Inventory types
    inventory_types = [
        (1, "Food Supplies", "Non-perishable food items", 1.0, 1.0),
        (2, "Medical Supplies", "Basic medical supplies", 0.8, 0.7),
        (3, "Water", "Bottled water", 1.2, 1.5),
        (4, "Clothing", "Basic clothing items", 0.5, 0.3),
        (5, "Shelter", "Tents and temporary shelters", 2.0, 1.0),
        (6, "Tools", "Basic tools and equipment", 1.5, 2.0),
        (7, "Hygiene Products", "Soap, sanitizer, etc.", 0.6, 0.5),
        (8, "Blankets", "Thermal blankets", 0.7, 0.4),
    ]

    cursor.executemany(
        "INSERT INTO inventory_types (inventory_id, name, description, volume_per_unit, weight_per_unit) VALUES (?, ?, ?, ?, ?)",
        inventory_types,
    )

    # Populate warehouses with inventory
    inventory_data = []

    for warehouse_id, _, _, _, _, _, _ in warehouses:
        for inventory_id, _, _, _, _ in inventory_types:
            # Generate random inventory quantities - larger warehouses have more inventory
            if warehouse_id == 1 or warehouse_id == 2:  # Larger warehouses
                quantity = random.randint(500, 1000)
            else:  # Smaller warehouses
                quantity = random.randint(200, 500)

            inventory_data.append((warehouse_id, inventory_id, quantity))

    cursor.executemany(
        "INSERT INTO inventory (location_id, inventory_id, quantity) VALUES (?, ?, ?)",
        inventory_data,
    )

    # Generate demand at destinations
    demand_data = []

    for dest_id, _, _, _, _, _, _ in destinations:
        # Each destination needs 2-4 different types of inventory
        num_inventory_types = random.randint(2, 4)
        selected_inventory = random.sample(
            [i[0] for i in inventory_types], num_inventory_types
        )

        for inventory_id in selected_inventory:
            quantity = random.randint(10, 50)  # Random demand between 10-50 units
            priority = random.randint(1, 3)  # Priority 1-3 (3 being highest)
            demand_data.append((dest_id, inventory_id, quantity, priority, None))

    cursor.executemany(
        "INSERT INTO demand (location_id, inventory_id, quantity, priority, due_date) VALUES (?, ?, ?, ?, ?)",
        demand_data,
    )

    # Generate routes between locations
    # First, convert location list to a lookup format
    location_lookup = {loc[0]: (loc[3], loc[4]) for loc in locations}  # id: (lat, lon)

    routes_data = []
    route_id = 1

    # Function to determine if a route should exist between two locations
    def should_have_route(loc1_type, loc2_type, distance):
        # All warehouses connect to all refuel points
        if (loc1_type == "WAREHOUSE" and loc2_type == "REFUEL_POINT") or (
            loc1_type == "REFUEL_POINT" and loc2_type == "WAREHOUSE"
        ):
            return True

        # All warehouses connect to all destinations within 1000km
        if (loc1_type == "WAREHOUSE" and loc2_type == "DESTINATION") or (
            loc1_type == "DESTINATION" and loc2_type == "WAREHOUSE"
        ):
            return distance <= 1000

        # Refuel points connect to destinations within 800km
        if (loc1_type == "REFUEL_POINT" and loc2_type == "DESTINATION") or (
            loc1_type == "DESTINATION" and loc2_type == "REFUEL_POINT"
        ):
            return distance <= 800

        # Refuel points connect to other refuel points within 600km
        if loc1_type == "REFUEL_POINT" and loc2_type == "REFUEL_POINT":
            return distance <= 600

        # Warehouses connect to other warehouses
        if loc1_type == "WAREHOUSE" and loc2_type == "WAREHOUSE":
            return True

        # Destinations don't connect to other destinations
        if loc1_type == "DESTINATION" and loc2_type == "DESTINATION":
            return False

        return False

    # Generate routes between locations if they meet criteria
    for i, loc1 in enumerate(locations):
        for loc2 in locations[i + 1 :]:  # Avoid duplicate routes
            loc1_id, _, loc1_type, _, _, _, _ = loc1
            loc2_id, _, loc2_type, _, _, _, _ = loc2

            # Calculate distance
            lat1, lon1 = location_lookup[loc1_id]
            lat2, lon2 = location_lookup[loc2_id]
            distance = haversine_distance(lat1, lon1, lat2, lon2)

            # Check if route should exist
            if should_have_route(loc1_type, loc2_type, distance):
                # Bidirectional routes (both directions)
                # Forward direction
                travel_time = distance / 80  # Approximate average speed of 80 km/h
                routes_data.append(
                    (route_id, loc1_id, loc2_id, distance, travel_time, None)
                )
                route_id += 1

                # Backward direction
                routes_data.append(
                    (route_id, loc2_id, loc1_id, distance, travel_time, None)
                )
                route_id += 1

    cursor.executemany(
        "INSERT INTO routes (route_id, origin_id, destination_id, distance_km, estimated_time_hours, restricted_vehicle_types) VALUES (?, ?, ?, ?, ?, ?)",
        routes_data,
    )

    print(
        f"Sample data generated: {len(locations)} locations, {len(vehicles)} vehicle types, {len(inventory_types)} inventory types"
    )
    print(f"Generated {len(routes_data)} routes between locations")


if __name__ == "__main__":
    create_database()
