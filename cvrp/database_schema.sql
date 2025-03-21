-- Locations table (warehouses, destinations, refueling points)
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
CREATE INDEX idx_routes_destination ON routes(destination_id);