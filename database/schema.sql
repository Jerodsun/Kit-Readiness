-- Kits table
CREATE TABLE
    kits (
        kit_id INTEGER PRIMARY KEY AUTOINCREMENT,
        kit_name TEXT NOT NULL,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

-- Components table
CREATE TABLE
    components (
        component_id INTEGER PRIMARY KEY AUTOINCREMENT,
        component_name TEXT NOT NULL,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

-- KitComponents table (junction table)
CREATE TABLE
    kit_components (
        kit_id INTEGER,
        component_id INTEGER,
        quantity INTEGER NOT NULL,
        FOREIGN KEY (kit_id) REFERENCES kits (kit_id),
        FOREIGN KEY (component_id) REFERENCES components (component_id),
        PRIMARY KEY (kit_id, component_id)
    );

-- Warehouses table
CREATE TABLE
    warehouses (
        warehouse_id INTEGER PRIMARY KEY AUTOINCREMENT,
        warehouse_name TEXT NOT NULL,
        location TEXT,
        latitude REAL,
        longitude REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

-- WarehouseInventory table
CREATE TABLE
    warehouse_inventory (
        warehouse_id INTEGER,
        component_id INTEGER,
        quantity INTEGER NOT NULL DEFAULT 0,
        min_stock INTEGER DEFAULT 0,
        max_stock INTEGER,
        FOREIGN KEY (warehouse_id) REFERENCES warehouses (warehouse_id),
        FOREIGN KEY (component_id) REFERENCES components (component_id),
        PRIMARY KEY (warehouse_id, component_id)
    );

-- CompletedKits table
CREATE TABLE
    completed_kits (
        warehouse_id INTEGER,
        kit_id INTEGER,
        quantity INTEGER NOT NULL DEFAULT 0,
        completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (warehouse_id) REFERENCES warehouses (warehouse_id),
        FOREIGN KEY (kit_id) REFERENCES kits (kit_id),
        PRIMARY KEY (warehouse_id, kit_id, completed_at)
    );

-- Destinations table
CREATE TABLE
    destinations (
        destination_id INTEGER PRIMARY KEY AUTOINCREMENT,
        destination_name TEXT NOT NULL,
        latitude REAL,
        longitude REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

-- Create separate tables for transfers and shipments
CREATE TABLE
    warehouse_transfers (
        transfer_id INTEGER PRIMARY KEY AUTOINCREMENT,
        transfer_date DATE NOT NULL,
        source_warehouse_id INTEGER NOT NULL,
        destination_warehouse_id INTEGER NOT NULL,
        component_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        scheduled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (source_warehouse_id) REFERENCES warehouses (warehouse_id),
        FOREIGN KEY (destination_warehouse_id) REFERENCES warehouses (warehouse_id),
        FOREIGN KEY (component_id) REFERENCES components (component_id)
    );

CREATE TABLE
    end_shipments (
        shipment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        shipment_date DATE NOT NULL,
        scheduled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        warehouse_id INTEGER,
        destination_id INTEGER,
        kit_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        FOREIGN KEY (warehouse_id) REFERENCES warehouses (warehouse_id),
        FOREIGN KEY (destination_id) REFERENCES destinations (destination_id),
        FOREIGN KEY (kit_id) REFERENCES kits (kit_id)
    );