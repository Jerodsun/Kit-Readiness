import numpy as np
import random
import math
from deap import base, creator, tools, algorithms
import matplotlib.pyplot as plt


# Notional data setup
class Warehouse:
    def __init__(self, name, lat, lon, capacity):
        self.name = name
        self.lat = lat
        self.lon = lon
        self.capacity = capacity  # Maximum transfer capacity
        self.available = capacity  # Current available capacity

    def __str__(self):
        return f"{self.name} ({self.lat}, {self.lon})"


class ResourceRequest:
    def __init__(self, warehouse, priority, amount, timestamp):
        self.warehouse = warehouse
        self.priority = priority  # 1-10 scale, 10 being highest
        self.amount = amount  # Amount of resources needed
        self.timestamp = timestamp  # When the request was made
        self.fulfilled = False
        self.assigned_to = None

    def __str__(self):
        return f"Request for {self.amount} units at {self.warehouse.name} (Priority: {self.priority})"


class ResourceDistributor:
    def __init__(self, name, lat, lon, capacity):
        self.name = name
        self.lat = lat
        self.lon = lon
        self.capacity = capacity
        self.available = capacity

    def __str__(self):
        return f"{self.name} ({self.lat}, {self.lon})"


# Helper functions
def haversine(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in kilometers"""
    R = 6371  # Earth radius in kilometers
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat / 2) * math.sin(dLat / 2) + math.cos(
        math.radians(lat1)
    ) * math.cos(math.radians(lat2)) * math.sin(dLon / 2) * math.sin(dLon / 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def calculate_travel_time(dist_km, speed_kmh=80):
    """Convert distance to travel time in hours"""
    return dist_km / speed_kmh


def calculate_distance_matrix(warehouses, distributors):
    """Calculate distance and time matrix between warehouses and distributors"""
    distances = {}
    times = {}
    for w in warehouses:
        distances[w.name] = {}
        times[w.name] = {}
        for d in distributors:
            dist = haversine(w.lat, w.lon, d.lat, d.lon)
            distances[w.name][d.name] = dist
            times[w.name][d.name] = calculate_travel_time(dist)
    return distances, times


# Create sample data
def create_sample_data():
    # Create warehouses across the US
    warehouses = [
        Warehouse("Seattle", 47.6062, -122.3321, 1000),
        Warehouse("Los Angeles", 34.0522, -118.2437, 1500),
        Warehouse("Denver", 39.7392, -104.9903, 800),
        Warehouse("Chicago", 41.8781, -87.6298, 1200),
        Warehouse("New York", 40.7128, -74.0060, 2000),
        Warehouse("Miami", 25.7617, -80.1918, 900),
        Warehouse("Dallas", 32.7767, -96.7970, 1100),
    ]

    # Create resource distributors
    distributors = [
        ResourceDistributor("Dist-A", 39.9526, -75.1652, 500),  # Philadelphia
        ResourceDistributor("Dist-B", 37.7749, -122.4194, 700),  # San Francisco
        ResourceDistributor("Dist-C", 29.7604, -95.3698, 600),  # Houston
    ]

    # Create sample resource requests
    requests = []
    for i in range(15):
        w = random.choice(warehouses)
        priority = random.randint(1, 10)
        amount = random.randint(50, 300)
        # Simulate requests coming in over a 24-hour period
        timestamp = random.randint(0, 1440)  # minutes in a day
        requests.append(ResourceRequest(w, priority, amount, timestamp))

    return warehouses, distributors, requests


# Greedy Algorithm
def greedy_algorithm(requests, distributors, time_matrix):
    """
    Greedy algorithm to distribute resources based on a combined score of
    priority, time to arrival, and available capacity.
    """
    results = []
    unassigned = []

    # Reset distributor capacities
    for d in distributors:
        d.available = d.capacity

    # Sort requests by a combined score
    for request in sorted(requests, key=lambda r: r.priority, reverse=True):
        best_dist = None
        best_score = -float("inf")

        for dist in distributors:
            if dist.available < request.amount:
                continue

            # Calculate time to arrival
            time_to_arrival = time_matrix[request.warehouse.name][dist.name]

            # Calculate score based on priority and time to arrival
            # Higher priority and lower time is better
            score = (request.priority * 10) - (time_to_arrival * 5)

            if score > best_score:
                best_score = score
                best_dist = dist

        if best_dist:
            # Assign the distributor to the request
            request.assigned_to = best_dist
            request.fulfilled = True
            best_dist.available -= request.amount
            results.append((request, best_dist))
        else:
            unassigned.append(request)

    return results, unassigned


# Genetic Algorithm Setup
def setup_genetic_algorithm(requests, distributors, time_matrix):
    """Setup for genetic algorithm"""
    creator.create(
        "FitnessMax", base.Fitness, weights=(1.0, -1.0)
    )  # Maximize priority, minimize time
    creator.create("Individual", list, fitness=creator.FitnessMax)

    toolbox = base.Toolbox()

    # Define genes as distributor indices
    toolbox.register("attr_dist", random.randint, 0, len(distributors) - 1)

    # Create individual and population
    toolbox.register(
        "individual",
        tools.initRepeat,
        creator.Individual,
        toolbox.attr_dist,
        n=len(requests),
    )
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)

    def evaluate(individual):
        total_priority = 0
        total_time = 0
        request_fulfillment = [0] * len(distributors)  # Track distributor load

        for i, dist_idx in enumerate(individual):
            request = requests[i]
            distributor = distributors[dist_idx]

            # Check if distributor has capacity
            if request_fulfillment[dist_idx] + request.amount > distributor.capacity:
                # Penalize invalid solutions
                return -1000, 1000

            request_fulfillment[dist_idx] += request.amount
            total_priority += request.priority
            total_time += time_matrix[request.warehouse.name][distributor.name]

        return total_priority, total_time

    toolbox.register("evaluate", evaluate)
    toolbox.register("mate", tools.cxTwoPoint)
    toolbox.register(
        "mutate", tools.mutUniformInt, low=0, up=len(distributors) - 1, indpb=0.1
    )
    toolbox.register("select", tools.selTournament, tournsize=3)

    return toolbox


def run_genetic_algorithm(requests, distributors, time_matrix):
    """Run genetic algorithm and return results"""
    toolbox = setup_genetic_algorithm(requests, distributors, time_matrix)

    # Create initial population
    pop = toolbox.population(n=100)
    hof = tools.HallOfFame(1)
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("avg", np.mean)
    stats.register("std", np.std)
    stats.register("min", np.min)
    stats.register("max", np.max)

    # Run algorithm
    pop, log = algorithms.eaSimple(
        pop,
        toolbox,
        cxpb=0.5,
        mutpb=0.2,
        ngen=40,
        stats=stats,
        halloffame=hof,
        verbose=False,
    )

    # Get the best solution
    best_solution = hof[0]
    results = []

    # Reset distributor capacities
    for d in distributors:
        d.available = d.capacity

    # Apply the solution
    for i, dist_idx in enumerate(best_solution):
        request = requests[i]
        distributor = distributors[dist_idx]
        request.assigned_to = distributor
        request.fulfilled = True
        distributor.available -= request.amount
        results.append((request, distributor))

    return results


def visualize_results(greedy_results, genetic_results, requests, distributors):
    """Visualize and compare results of both algorithms"""
    # Calculate total priority and time for greedy algorithm
    greedy_priority = sum(r.priority for r, _ in greedy_results)
    greedy_time = sum(time_matrix[r.warehouse.name][d.name] for r, d in greedy_results)
    greedy_unfulfilled = len(requests) - len(greedy_results)

    # Calculate total priority and time for genetic algorithm
    genetic_priority = sum(r.priority for r, _ in genetic_results)
    genetic_time = sum(
        time_matrix[r.warehouse.name][d.name] for r, d in genetic_results
    )
    genetic_unfulfilled = len(requests) - len(genetic_results)

    # Print summary
    print("=== Results Summary ===")
    print(
        f"Greedy Algorithm: Priority: {greedy_priority}, Time: {greedy_time:.2f}h, Unfulfilled: {greedy_unfulfilled}"
    )
    print(
        f"Genetic Algorithm: Priority: {genetic_priority}, Time: {genetic_time:.2f}h, Unfulfilled: {genetic_unfulfilled}"
    )

    # Plot distributor usage
    labels = [d.name for d in distributors]
    greedy_usage = [d.capacity - d.available for d in distributors]

    # Reset distributor capacities for genetic calculation
    for d in distributors:
        d.available = d.capacity
    for _, d in genetic_results:
        d.available -= 1  # Just for counting purposes

    genetic_usage = [d.capacity - d.available for d in distributors]

    x = np.arange(len(labels))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(x - width / 2, greedy_usage, width, label="Greedy")
    ax.bar(x + width / 2, genetic_usage, width, label="Genetic")

    ax.set_ylabel("Usage")
    ax.set_title("Distributor Usage by Algorithm")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend()

    plt.tight_layout()
    plt.show()


# Main execution
if __name__ == "__main__":
    warehouses, distributors, requests = create_sample_data()
    distances, time_matrix = calculate_distance_matrix(warehouses, distributors)

    print("Running greedy algorithm...")
    greedy_results, unassigned = greedy_algorithm(
        requests.copy(), distributors.copy(), time_matrix
    )

    print("Running genetic algorithm...")
    genetic_results = run_genetic_algorithm(
        requests.copy(), distributors.copy(), time_matrix
    )

    visualize_results(greedy_results, genetic_results, requests, distributors)
