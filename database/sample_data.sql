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
    (3, 8, 80, 40, 200), -- Chicago: 80 Gauze Rolls
    (4, 1, 85, 20, 100), -- Houston: 85 Hammers
    (4, 2, 130, 30, 150), -- Houston: 130 Screwdriver Sets
    (5, 3, 85, 20, 100), -- Denver: 85 Wrench Sets
    (5, 4, 170, 40, 200), -- Denver: 170 Flashlights
    (6, 5, 425, 100, 500), -- Seattle: 425 Batteries
    (6, 6, 255, 50, 300), -- Seattle: 255 Bandages
    (7, 7, 425, 100, 500), -- Phoenix: 425 Antiseptic Wipes
    (7, 8, 170, 40, 200), -- Phoenix: 170 Gauze Rolls
    (8, 1, 85, 20, 100), -- Kansas City: 85 Hammers
    (8, 2, 130, 30, 150), -- Kansas City: 130 Screwdriver Sets
    (9, 3, 85, 20, 100), -- Boston: 85 Wrench Sets
    (9, 4, 170, 40, 200), -- Boston: 170 Flashlights
    (10, 5, 425, 100, 500), -- Miami: 425 Batteries
    (10, 6, 155, 50, 300), -- Miami: 155 Bandages
    (11, 7, 310, 100, 500), -- Cleveland: 310 Antiseptic Wipes
    (11, 8, 85, 40, 200), -- Cleveland: 85 Gauze Rolls
    (12, 1, 65, 20, 100), -- Minneapolis: 65 Hammers
    (12, 2, 85, 30, 150), -- Minneapolis: 85 Screwdriver Sets
    (13, 3, 55, 20, 100), -- Omaha: 55 Wrench Sets
    (13, 4, 110, 40, 200), -- Omaha: 110 Flashlights
    (13, 5, 220, 100, 500), -- Omaha: 220 Batteries
    (14, 6, 130, 50, 300), -- Plains: 130 Bandages
    (14, 7, 260, 100, 500), -- Plains: 260 Antiseptic Wipes
    (14, 8, 100, 40, 200) -- Plains: 100 Gauze Rolls
;

-- Chicago: 80 Gauze Rolls
-- Sample Completed Kits
INSERT INTO
    completed_kits (warehouse_id, kit_id, quantity)
VALUES
    (1, 1, 10), -- NY: 10 Tool Kits
    (2, 2, 15), -- LA: 15 Emergency Kits
    (3, 3, 20), -- Chicago: 20 First Aid Kits
    (4, 1, 12), -- Houston: 12 Tool Kits
    (5, 2, 18), -- Denver: 18 Emergency Kits
    (6, 3, 25), -- Seattle: 25 First Aid Kits
    (7, 1, 14), -- Phoenix: 14 Tool Kits
    (8, 2, 20), -- Kansas City: 20 Emergency Kits
    (9, 3, 22), -- Boston: 22 First Aid Kits
    (10, 1, 16), -- Miami: 16 Tool Kits
    (11, 2, 19), -- Cleveland: 19 Emergency Kits
    (12, 3, 24), -- Minneapolis: 24 First Aid Kits
    (13, 1, 11) -- Omaha: 11 Tool Kits
;

-- Sample Destinations in Mexico
INSERT INTO
    destinations (destination_name, latitude, longitude)
VALUES
    ('Mexico City', 19.4326, -99.1332),
    ('Guadalajara', 20.6597, -103.3496),
    ('Monterrey', 25.6866, -100.3161),
    ('Cancun', 21.1619, -86.8515),
    ('Tijuana', 32.5149, -117.0382),
    ('Puebla', 19.0414, -98.2063),
    ('Merida', 20.9674, -89.5926),
    ('Toluca', 19.2826, -99.6557),
    ('Leon', 21.1619, -101.6868),
    ('San Luis Potosi', 22.1565, -100.9855),
    ('Queretaro', 20.5888, -100.3899),
    ('Chihuahua', 28.6320, -106.0691),
    ('Morelia', 19.7008, -101.1844),
    ('Aguascalientes', 21.8853, -102.2916),
    ('Acapulco', 16.8531, -99.8237);

-- Sample Shipments
INSERT INTO
    shipments (
        shipment_date,
        warehouse_id,
        destination_id,
        kit_id,
        quantity
    )
VALUES
    ('2023-01-15', 1, 1, 1, 5) --, -- NY to Mexico City: 5 Tool Kits
    -- ('2023-01-20', 2, 2, 2, 10), -- LA to Guadalajara: 10 Emergency Kits
    -- ('2023-01-25', 3, 3, 3, 15), -- Chicago to Monterrey: 15 First Aid Kits
    -- ('2023-02-01', 4, 4, 1, 8), -- Houston to Cancun: 8 Tool Kits
    -- ('2023-02-05', 5, 5, 2, 12), -- Denver to Tijuana: 12 Emergency Kits
    -- ('2023-02-10', 6, 6, 3, 20), -- Seattle to Puebla: 20 First Aid Kits
    -- ('2023-02-15', 7, 7, 1, 10), -- Phoenix to Merida: 10 Tool Kits
    -- ('2023-02-20', 8, 8, 2, 14), -- Kansas City to Toluca: 14 Emergency Kits
    -- ('2023-02-25', 9, 9, 3, 18), -- Boston to Leon: 18 First Aid Kits
    -- ('2023-03-01', 10, 10, 1, 12), -- Miami to San Luis Potosi: 12 Tool Kits
    -- ('2023-03-05', 11, 11, 2, 16), -- Cleveland to Queretaro: 16 Emergency Kits
    -- ('2023-03-10', 12, 12, 3, 22), -- Minneapolis to Chihuahua: 22 First Aid Kits
    -- ('2023-03-15', 13, 13, 1, 9), -- Omaha to Morelia: 9 Tool Kits
    -- ('2023-03-20', 14, 14, 2, 11), -- Plains to Aguascalientes: 11 Emergency Kits
    -- ('2023-03-25', 1, 15, 3, 13) -- NY to Acapulco: 13 First Aid Kits
;