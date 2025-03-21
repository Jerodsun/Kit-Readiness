# Capacitated Vehicle Routing Problem (CVRP) Solver

A comprehensive implementation of a CVRP solver that handles complex logistics constraints including range limitations, inventory management, refueling capabilities, and multi-destination routing.

## Features

- **Range-Constrained Routing**: Vehicles have limited range and require refueling points
- **Inventory Management**: Tracks warehouse inventory and fulfills specific demand requirements
- **Multi-Hop Planning**: Supports intermediate stops for refueling and complex routing
- **Priority-Based Allocation**: Processes destinations by priority to maximize service level
- **Vehicle Capacity Constraints**: Ensures vehicle loading respects capacity limitations
- **Resource Optimization**: Balances vehicle usage across warehouses
- **Visualization Tools**: Interactive maps and static visualizations of networks and routes
- **Detailed Analytics**: Comprehensive statistics and solution metrics

## Installation

### Setup

1. pip install required packages
2. Initialize database with sample data:

```bash
python main.py --init
```

## Components

The implementation consists of several key components:

1. **Database Schema** (`database_schema.sql`): SQLite database structure for storing all logistics data
2. **Database Initializer** (`db_initializer.py`): Creates and populates the database with sample data
3. **CVRP Solver** (`cvrp_solver.py`): Core algorithm that computes optimal routes
4. **Solution Visualizer** (`solution_visualizer.py`): Visualization tools for the solution
5. **Main Script** (`main.py`): Integrates all components with a CLI

## Usage

Run the solver with default settings:

```bash
python main.py
```

### Command-line Options

- `--db PATH`: Path to SQLite database (default: cvrp.db)
- `--init`: Initialize the database with sample data
- `--max-hops N`: Maximum number of intermediate stops (default: 2)
- `--max-vehicles N`: Maximum number of vehicles to use (default: unlimited)
- `--output-dir DIR`: Directory to save output files (default: output)

### Example

```bash
# Initialize database with sample data
python main.py --init

# Run solver with a maximum of 3 intermediate stops
python main.py --max-hops 3 --output-dir results
```

## Output

The solver generates several types of output:

1. **Solution Summary**: CSV files with solution statistics

   - `solution_summary.csv`: Overall solution metrics
   - `warehouse_usage.csv`: Vehicle usage by warehouse
   - `delivery_details.csv`: Detailed information about each delivery

2. **Visualizations**:

   - `network.png`: Map of all locations and routes
   - `solution.png`: Visualization of the solution routes
   - `interactive_map.html`: Interactive web map of the solution

3. **Database Records**: Deliveries and delivery items are stored in the database

## Algorithm Details

The CVRP solver implements a heuristic algorithm with several key components:

1. **Path Finding**: Modified Dijkstra's algorithm with hop constraints to find valid routes respecting vehicle range limitations

2. **Route Selection**: Routes are scored based on weighted factors:

   - Distance efficiency
   - Time efficiency
   - Vehicle distribution balance
   - Demand priority
   - Number of hops

3. **Demand Fulfillment**: Processes demand locations in priority order, allocating vehicles and inventory to maximize fulfillment

4. **Resource Optimization**: Tracks and manages vehicle and inventory resources throughout the solution process

## Database Schema

The SQLite database includes the following tables:

- `locations`: Warehouses, destinations, and refueling points
- `vehicles`: Vehicle types and specifications
- `vehicle_locations`: Distribution of vehicles across warehouses
- `inventory_types`: Types of inventory items
- `inventory`: Current inventory levels at each location
- `demand`: Demand requirements at destinations
- `routes`: Valid routes between locations
- `deliveries`: Completed delivery routes
- `delivery_items`: Items included in each delivery

## Extending the Solution

The solution can be extended in several ways:

1. **Custom Data**: Replace the sample data with specific scenarios
2. **Additional Constraints**: Add time windows, driver scheduling, etc.
3. **Advanced Algorithms**: Implement meta-heuristics for larger problems
4. **Real-time Updates**: Add capabilities for dynamic routing

## Performance Considerations

The solution is optimized for medium-sized problems (~40 destinations). For larger problems:

- Implement pruning techniques in the path finding algorithm
- Use distributed computing approaches
- Consider implementing a progressive solver

## License

This project is released under the MIT License.

## Acknowledgments

This implementation was inspired by real-world logistics challenges and academic research in vehicle routing problems.
