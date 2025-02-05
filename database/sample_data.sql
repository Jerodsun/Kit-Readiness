-- Sample Kits
INSERT INTO
    kits (kit_name, description)
VALUES
    (
        'Basic Tool Kit',
        'Essential tools for home maintenance'
    ),
    ('Emergency Kit', 'Basic emergency supplies'),
    ('First Aid Kit', 'Standard medical supplies');

-- Sample Components
INSERT INTO
    components (component_name, description)
VALUES
    ('Hammer', 'Standard claw hammer'),
    (
        'Screwdriver Set',
        'Phillips and flathead screwdrivers'
    ),
    ('Wrench Set', 'Adjustable wrenches'),
    ('Flashlight', 'LED emergency flashlight'),
    ('Batteries', 'AA batteries'),
    ('Bandages', 'Adhesive bandages'),
    ('Antiseptic Wipes', 'Medical wipes'),
    ('Gauze Rolls', 'Medical gauze');

-- Kit Components Relationships
INSERT INTO
    kit_components (kit_id, component_id, quantity)
VALUES
    (1, 1, 1), -- Tool Kit: 1 Hammer
    (1, 2, 1), -- Tool Kit: 1 Screwdriver Set
    (1, 3, 1), -- Tool Kit: 1 Wrench Set
    (2, 4, 2), -- Emergency Kit: 2 Flashlights
    (2, 5, 4), -- Emergency Kit: 4 Batteries
    (3, 6, 5), -- First Aid Kit: 5 Bandages
    (3, 7, 10), -- First Aid Kit: 10 Antiseptic Wipes
    (3, 8, 2);

-- First Aid Kit: 2 Gauze Rolls
-- Sample Warehouses
INSERT INTO
    warehouses (warehouse_name, location, latitude, longitude)
VALUES
    (
        'East Coast Facility',
        'New York, NY',
        40.7128,
        -74.0060
    ),
    (
        'West Coast Facility',
        'Los Angeles, CA',
        34.0522,
        -118.2437
    ),
    (
        'Central Facility',
        'Chicago, IL',
        41.8781,
        -87.6298
    ),
    (
        'Southern Facility',
        'Houston, TX',
        29.7604,
        -95.3698
    ),
    (
        'Mountain Facility',
        'Denver, CO',
        39.7392,
        -104.9903
    ),
    (
        'Pacific Northwest Facility',
        'Seattle, WA',
        47.6062,
        -122.3321
    ),
    (
        'Southwest Facility',
        'Phoenix, AZ',
        33.4484,
        -112.0740
    ),
    (
        'Midwest Facility',
        'Kansas City, MO',
        39.0997,
        -94.5786
    ),
    (
        'Northeast Facility',
        'Boston, MA',
        42.3601,
        -71.0589
    ),
    (
        'Southeast Facility',
        'Miami, FL',
        25.7617,
        -80.1918
    ),
    (
        'Great Lakes Facility',
        'Cleveland, OH',
        41.4993,
        -81.6944
    ),
    (
        'Northern Facility',
        'Minneapolis, MN',
        44.9778,
        -93.2650
    ),
    ('Plains Facility', 'Omaha, NE', 41.2565, -95.9345);

-- Sample Warehouse Inventory
INSERT INTO
    warehouse_inventory (
        warehouse_id,
        component_id,
        quantity,
        min_stock,
        max_stock
    )
VALUES
    (1, 1, 50, 20, 100), -- NY: 50 Hammers
    (1, 2, 75, 30, 150), -- NY: 75 Screwdriver Sets
    (1, 3, 40, 20, 100), -- NY: 40 Wrench Sets
    (2, 4, 100, 40, 200), -- LA: 100 Flashlights
    (2, 5, 200, 100, 500), -- LA: 200 Batteries
    (3, 6, 150, 50, 300), -- Chicago: 150 Bandages
    (3, 7, 300, 100, 500), -- Chicago: 300 Antiseptic Wipes
    (3, 8, 80, 40, 200);

-- Chicago: 80 Gauze Rolls
-- Sample Completed Kits
INSERT INTO
    completed_kits (warehouse_id, kit_id, quantity)
VALUES
    (1, 1, 10), -- NY: 10 Tool Kits
    (2, 2, 15), -- LA: 15 Emergency Kits
    (3, 3, 20);

-- Chicago: 20 First Aid Kits