import matplotlib.pyplot as plt
import numpy as np
import sqlite3
import json
from matplotlib.patches import Circle
import matplotlib.colors as mcolors
import folium
from folium.plugins import MarkerCluster
import pandas as pd
import random


class CVRPVisualizer:
    """Visualization tools for CVRP solutions."""

    def __init__(self, db_path):
        """Initialize with database connection."""
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

        # Load base data
        self.locations = self._load_locations()
        self.deliveries = self._load_deliveries()
        self.delivery_items = self._load_delivery_items()
        self.inventory_types = self._load_inventory_types()

    def _load_locations(self):
        """Load locations from database."""
        self.cursor.execute("SELECT * FROM locations")
        return {row["location_id"]: dict(row) for row in self.cursor.fetchall()}

    def _load_deliveries(self):
        """Load deliveries from database."""
        self.cursor.execute("SELECT * FROM deliveries")
        deliveries = []
        for row in self.cursor.fetchall():
            delivery = dict(row)
            # Parse JSON path
            delivery["route_path"] = json.loads(delivery["route_path"])
            deliveries.append(delivery)
        return deliveries

    def _load_delivery_items(self):
        """Load delivery items from database."""
        self.cursor.execute("SELECT * FROM delivery_items")
        items = {}
        for row in self.cursor.fetchall():
            delivery_id = row["delivery_id"]
            if delivery_id not in items:
                items[delivery_id] = []
            items[delivery_id].append(dict(row))
        return items

    def _load_inventory_types(self):
        """Load inventory types from database."""
        self.cursor.execute("SELECT * FROM inventory_types")
        return {row["inventory_id"]: dict(row) for row in self.cursor.fetchall()}

    def plot_network(self):
        """Plot the network of locations."""
        # Extract location data
        locs = list(self.locations.values())

        # Group by type
        warehouses = [loc for loc in locs if "WAREHOUSE" in loc["type"]]
        refuel_points = [loc for loc in locs if "REFUEL_POINT" in loc["type"]]
        destinations = [loc for loc in locs if "DESTINATION" in loc["type"]]

        # Create figure
        plt.figure(figsize=(14, 10))

        # Plot warehouses
        plt.scatter(
            [w["longitude"] for w in warehouses],
            [w["latitude"] for w in warehouses],
            c="blue",
            s=100,
            edgecolor="black",
            label="Warehouses",
        )

        # Plot refuel points
        plt.scatter(
            [r["longitude"] for r in refuel_points],
            [r["latitude"] for r in refuel_points],
            c="green",
            s=80,
            marker="^",
            edgecolor="black",
            label="Refuel Points",
        )

        # Plot destinations
        plt.scatter(
            [d["longitude"] for d in destinations],
            [d["latitude"] for d in destinations],
            c="red",
            s=60,
            marker="o",
            alpha=0.7,
            edgecolor="black",
            label="Destinations",
        )

        # Plot routes
        self.cursor.execute("SELECT * FROM routes")
        for route in self.cursor.fetchall():
            origin = self.locations[route["origin_id"]]
            dest = self.locations[route["destination_id"]]
            plt.plot(
                [origin["longitude"], dest["longitude"]],
                [origin["latitude"], dest["latitude"]],
                "gray",
                alpha=0.1,
                linewidth=0.5,
            )

        # Add labels for warehouses and refuel points
        for w in warehouses:
            plt.annotate(
                w["name"],
                (w["longitude"], w["latitude"]),
                textcoords="offset points",
                xytext=(0, 10),
                ha="center",
            )

        for r in refuel_points:
            plt.annotate(
                r["name"],
                (r["longitude"], r["latitude"]),
                textcoords="offset points",
                xytext=(0, 10),
                ha="center",
            )

        plt.legend()
        plt.title("CVRP Network")
        plt.xlabel("Longitude")
        plt.ylabel("Latitude")
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        return plt.gcf()

    def plot_solution(self, max_routes=10):
        """
        Plot the solution routes.

        Args:
            max_routes: Maximum number of routes to plot (to avoid clutter)
        """
        # Create figure
        plt.figure(figsize=(14, 10))

        # Extract location data
        locs = list(self.locations.values())

        # Group by type
        warehouses = [loc for loc in locs if "WAREHOUSE" in loc["type"]]
        refuel_points = [loc for loc in locs if "REFUEL_POINT" in loc["type"]]
        destinations = [loc for loc in locs if "DESTINATION" in loc["type"]]

        # Plot warehouses
        plt.scatter(
            [w["longitude"] for w in warehouses],
            [w["latitude"] for w in warehouses],
            c="blue",
            s=100,
            edgecolor="black",
            label="Warehouses",
        )

        # Plot refuel points
        plt.scatter(
            [r["longitude"] for r in refuel_points],
            [r["latitude"] for r in refuel_points],
            c="green",
            s=80,
            marker="^",
            edgecolor="black",
            label="Refuel Points",
        )

        # Plot destinations
        plt.scatter(
            [d["longitude"] for d in destinations],
            [d["latitude"] for d in destinations],
            c="red",
            s=60,
            marker="o",
            alpha=0.7,
            edgecolor="black",
            label="Destinations",
        )

        # Limit number of routes to plot
        routes_to_plot = self.deliveries[:max_routes]

        # Generate colors for routes
        colors = list(mcolors.TABLEAU_COLORS)
        random.shuffle(colors)

        # Plot each delivery route
        for i, delivery in enumerate(routes_to_plot):
            path = delivery["route_path"]

            # Get coordinates for each location in the path
            lons = [self.locations[loc_id]["longitude"] for loc_id in path]
            lats = [self.locations[loc_id]["latitude"] for loc_id in path]

            # Plot route
            color = colors[i % len(colors)]
            plt.plot(
                lons,
                lats,
                "-",
                color=color,
                linewidth=2,
                label=f"Route {i+1}: {self.locations[path[0]]['name']} to {self.locations[path[-1]]['name']}",
            )

            # Add arrows to show direction
            for j in range(len(path) - 1):
                # Midpoint for arrow
                mid_lon = (lons[j] + lons[j + 1]) / 2
                mid_lat = (lats[j] + lats[j + 1]) / 2

                # Direction vector
                dir_lon = lons[j + 1] - lons[j]
                dir_lat = lats[j + 1] - lats[j]

                # Normalize
                length = np.sqrt(dir_lon**2 + dir_lat**2)
                dir_lon /= length
                dir_lat /= length

                # Plot arrow
                plt.arrow(
                    mid_lon - dir_lon * 0.2,
                    mid_lat - dir_lat * 0.2,
                    dir_lon * 0.4,
                    dir_lat * 0.4,
                    head_width=0.1,
                    head_length=0.1,
                    fc=color,
                    ec=color,
                )

        plt.legend(loc="upper left", bbox_to_anchor=(1, 1))
        plt.title("CVRP Solution Routes")
        plt.xlabel("Longitude")
        plt.ylabel("Latitude")
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        return plt.gcf()

    def create_interactive_map(self, output_file="cvrp_solution.html"):
        """
        Create an interactive map visualization of the solution using Folium.

        Args:
            output_file: File path to save the HTML map
        """
        # Calculate center of map
        locs = list(self.locations.values())
        center_lat = sum(loc["latitude"] for loc in locs) / len(locs)
        center_lon = sum(loc["longitude"] for loc in locs) / len(locs)

        # Create map
        m = folium.Map(location=[center_lat, center_lon], zoom_start=5)

        # Create marker clusters for each type of location
        warehouse_cluster = MarkerCluster(name="Warehouses")
        refuel_cluster = MarkerCluster(name="Refuel Points")
        destination_cluster = MarkerCluster(name="Destinations")

        # Add locations to appropriate clusters
        for loc_id, loc in self.locations.items():
            if "WAREHOUSE" in loc["type"]:
                folium.Marker(
                    [loc["latitude"], loc["longitude"]],
                    popup=f"<b>{loc['name']}</b><br>Type: Warehouse",
                    icon=folium.Icon(color="blue", icon="home"),
                ).add_to(warehouse_cluster)

            elif "REFUEL_POINT" in loc["type"]:
                folium.Marker(
                    [loc["latitude"], loc["longitude"]],
                    popup=f"<b>{loc['name']}</b><br>Type: Refuel Point",
                    icon=folium.Icon(color="green", icon="gas-pump", prefix="fa"),
                ).add_to(refuel_cluster)

            else:  # Destination
                folium.Marker(
                    [loc["latitude"], loc["longitude"]],
                    popup=f"<b>{loc['name']}</b><br>Type: Destination",
                    icon=folium.Icon(color="red", icon="flag"),
                ).add_to(destination_cluster)

        # Add clusters to map
        warehouse_cluster.add_to(m)
        refuel_cluster.add_to(m)
        destination_cluster.add_to(m)

        # Add routes
        for i, delivery in enumerate(self.deliveries):
            path = delivery["route_path"]

            # Get coordinates for each location in the path
            route_points = [
                [
                    self.locations[loc_id]["latitude"],
                    self.locations[loc_id]["longitude"],
                ]
                for loc_id in path
            ]

            # Create popup text
            origin = self.locations[path[0]]
            destination = self.locations[path[-1]]
            vehicle_id = delivery["vehicle_id"]

            # Get vehicle details
            self.cursor.execute(
                "SELECT * FROM vehicles WHERE vehicle_id = ?", (vehicle_id,)
            )
            vehicle = dict(self.cursor.fetchone())

            # Get delivery items
            items_text = ""
            if delivery["delivery_id"] in self.delivery_items:
                items = self.delivery_items[delivery["delivery_id"]]
                items_text = "<br><b>Items:</b><br>"
                for item in items:
                    inv_id = item["inventory_id"]
                    inv_name = self.inventory_types[inv_id]["name"]
                    items_text += f"- {item['quantity']} {inv_name}<br>"

            popup_text = f"""
            <b>Route {i+1}</b><br>
            <b>From:</b> {origin['name']}<br>
            <b>To:</b> {destination['name']}<br>
            <b>Vehicle:</b> {vehicle['name']}<br>
            <b>Distance:</b> {delivery['total_distance_km']:.2f} km<br>
            <b>Time:</b> {delivery['total_distance_km'] / vehicle['speed_kmh']:.2f} hours
            {items_text}
            """

            # Generate a random color for the route
            color = "#{:02x}{:02x}{:02x}".format(
                random.randint(0, 200), random.randint(0, 200), random.randint(100, 255)
            )

            # Add the route to the map
            folium.PolyLine(
                route_points,
                color=color,
                weight=3,
                opacity=0.8,
                popup=folium.Popup(popup_text, max_width=300),
            ).add_to(m)

        # Add layer control
        folium.LayerControl().add_to(m)

        # Save map to file
        m.save(output_file)
        print(f"Interactive map saved to {output_file}")

        return m

    def generate_statistics_report(self):
        """Generate a detailed statistics report about the solution."""
        # Basic delivery statistics
        total_deliveries = len(self.deliveries)
        total_distance = sum(
            delivery["total_distance_km"] for delivery in self.deliveries
        )

        # Calculate total time based on vehicle speed
        total_time = 0
        for delivery in self.deliveries:
            vehicle_id = delivery["vehicle_id"]
            self.cursor.execute(
                "SELECT speed_kmh FROM vehicles WHERE vehicle_id = ?", (vehicle_id,)
            )
            speed = self.cursor.fetchone()["speed_kmh"]
            total_time += delivery["total_distance_km"] / speed

        # Count deliveries by vehicle type
        vehicle_usage = {}
        for delivery in self.deliveries:
            vehicle_id = delivery["vehicle_id"]
            self.cursor.execute(
                "SELECT name FROM vehicles WHERE vehicle_id = ?", (vehicle_id,)
            )
            vehicle_name = self.cursor.fetchone()["name"]

            if vehicle_name not in vehicle_usage:
                vehicle_usage[vehicle_name] = 0
            vehicle_usage[vehicle_name] += a

        # Count deliveries by warehouse (origin)
        warehouse_usage = {}
        for delivery in self.deliveries:
            origin_id = delivery["start_location_id"]
            origin_name = self.locations[origin_id]["name"]

            if origin_name not in warehouse_usage:
                warehouse_usage[origin_name] = 0
            warehouse_usage[origin_name] += 1

        # Calculate inventory statistics
        inventory_delivered = {}
        for delivery_id, items in self.delivery_items.items():
            for item in items:
                inv_id = item["inventory_id"]
                inv_name = self.inventory_types[inv_id]["name"]

                if inv_name not in inventory_delivered:
                    inventory_delivered[inv_name] = 0
                inventory_delivered[inv_name] += item["quantity"]

        # Create statistics DataFrame
        stats = {
            "Total Deliveries": [total_deliveries],
            "Total Distance (km)": [total_distance],
            "Total Time (hours)": [total_time],
            "Average Distance per Delivery (km)": [
                total_distance / total_deliveries if total_deliveries > 0 else 0
            ],
            "Average Time per Delivery (hours)": [
                total_time / total_deliveries if total_deliveries > 0 else 0
            ],
        }

        stats_df = pd.DataFrame(stats)

        # Create vehicle usage DataFrame
        vehicle_df = pd.DataFrame(
            {
                "Vehicle Type": list(vehicle_usage.keys()),
                "Count": list(vehicle_usage.values()),
            }
        )

        # Create warehouse usage DataFrame
        warehouse_df = pd.DataFrame(
            {
                "Warehouse": list(warehouse_usage.keys()),
                "Count": list(warehouse_usage.values()),
            }
        )

        # Create inventory DataFrame
        inventory_df = pd.DataFrame(
            {
                "Inventory Type": list(inventory_delivered.keys()),
                "Quantity Delivered": list(inventory_delivered.values()),
            }
        )

        return {
            "summary": stats_df,
            "vehicle_usage": vehicle_df,
            "warehouse_usage": warehouse_df,
            "inventory_delivered": inventory_df,
        }

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()


# Example usage
if __name__ == "__main__":
    visualizer = CVRPVisualizer("cvrp.db")

    try:
        # Plot network
        network_fig = visualizer.plot_network()
        network_fig.savefig("cvrp_network.png")

        # Plot solution
        solution_fig = visualizer.plot_solution(max_routes=15)
        solution_fig.savefig("cvrp_solution.png")

        # Create interactive map
        visualizer.create_interactive_map()

        # Generate statistics report
        stats = visualizer.generate_statistics_report()
        print("Solution Statistics:")
        print(stats["summary"])
        print("\nVehicle Usage:")
        print(stats["vehicle_usage"])
        print("\nWarehouse Usage:")
        print(stats["warehouse_usage"])
        print("\nInventory Delivered:")
        print(stats["inventory_delivered"])

    finally:
        visualizer.close()
