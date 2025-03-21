import os
import argparse
import time
from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd

# Import our modules
# Make sure the database_schema.sql file exists before running
with open("database_schema.sql", "w") as f:
    f.write(
        """-- Locations table (warehouses, destinations, refueling points)
CREATE TABLE locations (
    location_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL, -- 'WAREHOUSE', 'DESTINATION', 'REFUEL_POINT', or combination
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    refuel_capable BOOLEAN DEFAULT 0,
    warehouse_capacity INTEGER -- Max storage capacity (NULL if not a warehouse)
);

-- Vehicles table
CREATE TABLE vehicles (
    vehicle_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    capacity INTEGER NOT NULL, -- Pallet or volume capacity
    range_km REAL NOT NULL, -- Maximum range in kilometers
    speed_kmh REAL NOT NULL, -- Speed in kilometers per hour
    refuel_time_hours REAL DEFAULT 0.5, -- Time needed for refueling
    loading_time_hours REAL DEFAULT 0.5, -- Time needed for loading
    unloading_time_hours REAL DEFAULT 0.5 -- Time needed for unloading
);

-- Vehicle locations (where vehicles are based)
CREATE TABLE vehicle_locations (
    vehicle_type_id INTEGER NOT NULL,
    location_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    PRIMARY KEY (vehicle_type_id, location_id),
    FOREIGN KEY (vehicle_type_id) REFERENCES vehicles(vehicle_id),
    FOREIGN KEY (location_id) REFERENCES locations(location_id)
);

-- Inventory types table
CREATE TABLE inventory_types (
    inventory_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    volume_per_unit REAL NOT NULL, -- Volume/space required per unit
    weight_per_unit REAL -- Weight per unit (if weight constraints apply)
);

-- Current inventory at locations
CREATE TABLE inventory (
    location_id INTEGER NOT NULL,
    inventory_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (location_id, inventory_id),
    FOREIGN KEY (location_id) REFERENCES locations(location_id),
    FOREIGN KEY (inventory_id) REFERENCES inventory_types(inventory_id)
);

-- Demand requirements at destinations
CREATE TABLE demand (
    location_id INTEGER NOT NULL,
    inventory_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    priority INTEGER DEFAULT 1, -- Higher number = higher priority
    due_date TEXT, -- Optional due date in ISO format
    PRIMARY KEY (location_id, inventory_id),
    FOREIGN KEY (location_id) REFERENCES locations(location_id),
    FOREIGN KEY (inventory_id) REFERENCES inventory_types(inventory_id)
);

-- Valid routes between locations
CREATE TABLE routes (
    route_id INTEGER PRIMARY KEY,
    origin_id INTEGER NOT NULL,
    destination_id INTEGER NOT NULL,
    distance_km REAL NOT NULL,
    estimated_time_hours REAL, -- Estimated travel time (if different from distance/speed)
    restricted_vehicle_types TEXT, -- Comma-separated list of vehicle IDs that cannot use this route
    FOREIGN KEY (origin_id) REFERENCES locations(location_id),
    FOREIGN KEY (destination_id) REFERENCES locations(location_id),
    UNIQUE (origin_id, destination_id)
);

-- Routes can be one-way, so we need to define both directions if applicable

-- Completed deliveries (for historical tracking)
CREATE TABLE deliveries (
    delivery_id INTEGER PRIMARY KEY,
    vehicle_id INTEGER NOT NULL,
    start_location_id INTEGER NOT NULL,
    end_location_id INTEGER NOT NULL,
    start_time TEXT NOT NULL, -- ISO format
    end_time TEXT NOT NULL, -- ISO format
    total_distance_km REAL NOT NULL,
    route_path TEXT NOT NULL, -- JSON array of location_ids in order of visit
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(vehicle_id),
    FOREIGN KEY (start_location_id) REFERENCES locations(location_id),
    FOREIGN KEY (end_location_id) REFERENCES locations(location_id)
);

-- Delivery items (what was delivered)
CREATE TABLE delivery_items (
    delivery_id INTEGER NOT NULL,
    inventory_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    PRIMARY KEY (delivery_id, inventory_id),
    FOREIGN KEY (delivery_id) REFERENCES deliveries(delivery_id),
    FOREIGN KEY (inventory_id) REFERENCES inventory_types(inventory_id)
);

-- Index for faster queries
CREATE INDEX idx_inventory_location ON inventory(location_id);
CREATE INDEX idx_inventory_type ON inventory(inventory_id);
CREATE INDEX idx_demand_location ON demand(location_id);
CREATE INDEX idx_routes_origin ON routes(origin_id);
CREATE INDEX idx_routes_destination ON routes(destination_id);"""
    )

from db_initializer import create_database
from cvrp_solver import CVRPSolver
from solution_visualizer import CVRPVisualizer


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="CVRP Solver")

    parser.add_argument(
        "--db",
        type=str,
        default="cvrp.db",
        help="Path to SQLite database (default: cvrp.db)",
    )

    parser.add_argument(
        "--init", action="store_true", help="Initialize the database with sample data"
    )

    parser.add_argument(
        "--max-hops",
        type=int,
        default=2,
        help="Maximum number of intermediate stops (default: 2)",
    )

    parser.add_argument(
        "--max-vehicles",
        type=int,
        default=None,
        help="Maximum number of vehicles to use (default: unlimited)",
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default="output",
        help="Directory to save output files (default: output)",
    )

    return parser.parse_args()


def ensure_output_dir(output_dir):
    """Ensure output directory exists."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    return output_dir


def save_solution_summary(deliveries, stats, output_dir):
    """Save solution summary to CSV."""
    # Create summary DataFrame
    summary = pd.DataFrame(
        {
            "Total Vehicles": [stats["total_vehicles"]],
            "Total Distance (km)": [stats["total_distance"]],
            "Total Time (hours)": [stats["total_time"]],
            "Total Demand": [stats["total_demand"]],
            "Fulfilled Demand": [stats["fulfilled_demand"]],
            "Fulfillment Rate (%)": [stats["fulfillment_rate"] * 100],
            "Balance Score": [stats["balance_score"]],
        }
    )

    # Save summary
    summary_path = os.path.join(output_dir, "solution_summary.csv")
    summary.to_csv(summary_path, index=False)

    # Create warehouse usage DataFrame
    warehouse_usage = pd.DataFrame(
        {
            "Warehouse": list(stats["warehouse_usage"].keys()),
            "Vehicles Used": list(stats["warehouse_usage"].values()),
        }
    )

    # Save warehouse usage
    usage_path = os.path.join(output_dir, "warehouse_usage.csv")
    warehouse_usage.to_csv(usage_path, index=False)

    # Save delivery details
    delivery_details = []
    for i, delivery in enumerate(deliveries):
        detail = {
            "Delivery ID": i + 1,
            "Origin": delivery["origin"]["name"],
            "Destination": delivery["destination"]["name"],
            "Vehicle": delivery["vehicle"]["name"],
            "Distance (km)": delivery["distance"],
            "Time (hours)": delivery["time"],
            "Path": " -> ".join([loc["name"] for loc in delivery["path"]]),
            "Items": ", ".join(
                [
                    f"{qty} {delivery['inventory_types'][inv_id]['name']}"
                    for inv_id, qty in delivery["loading"].items()
                ]
            ),
        }
        delivery_details.append(detail)

    details_df = pd.DataFrame(delivery_details)
    details_path = os.path.join(output_dir, "delivery_details.csv")
    details_df.to_csv(details_path, index=False)

    print(f"Solution summary saved to {summary_path}")
    print(f"Warehouse usage saved to {usage_path}")
    print(f"Delivery details saved to {details_path}")


def main():
    """Main function."""
    args = parse_arguments()
    output_dir = ensure_output_dir(args.output_dir)

    # Initialize database if requested
    if args.init:
        print("Initializing database...")
        create_database(args.db)

    # Solve CVRP
    print("Solving CVRP...")
    start_time = time.time()

    solver = CVRPSolver(args.db)
    deliveries, stats = solver.solve(
        max_hops=args.max_hops, max_vehicles=args.max_vehicles
    )

    # Save solution to database
    solver.save_solution(deliveries)
    solver.close()

    end_time = time.time()
    print(f"Solution found in {end_time - start_time:.2f} seconds")

    # Print solution statistics
    print(f"Total vehicles used: {stats['total_vehicles']}")
    print(f"Total distance: {stats['total_distance']:.2f} km")
    print(f"Total time: {stats['total_time']:.2f} hours")
    print(f"Demand fulfillment rate: {stats['fulfillment_rate'] * 100:.2f}%")
    print(f"Balance score: {stats['balance_score']:.2f}")
    print("Warehouse usage:")
    for wh_name, count in stats["warehouse_usage"].items():
        print(f"  {wh_name}: {count} vehicles")

    # Save solution summary
    save_solution_summary(deliveries, stats, output_dir)

    # Create visualizations
    print("Creating visualizations...")
    visualizer = CVRPVisualizer(args.db)

    # Network visualization
    network_fig = visualizer.plot_network()
    network_path = os.path.join(output_dir, "network.png")
    network_fig.savefig(network_path, dpi=300, bbox_inches="tight")

    # Solution visualization
    solution_fig = visualizer.plot_solution(max_routes=min(15, len(deliveries)))
    solution_path = os.path.join(output_dir, "solution.png")
    solution_fig.savefig(solution_path, dpi=300, bbox_inches="tight")

    # Interactive map
    map_path = os.path.join(output_dir, "interactive_map.html")
    visualizer.create_interactive_map(output_file=map_path)

    visualizer.close()

    print(f"Network visualization saved to {network_path}")
    print(f"Solution visualization saved to {solution_path}")
    print(f"Interactive map saved to {map_path}")
    print(f"All output saved to {output_dir} directory")


if __name__ == "__main__":
    main()
