import pytest
from datetime import date
from logistics_solver import haversine_distance

from logistics_solver import (
    InventoryManager,
    LogisticsSolver,
    Warehouse,
    Component,
    Kit,
    InventoryItem,
    TransferRequest,
    RouteSegment,
    DeliveryRoute,
)

@pytest.fixture
def inventory_manager():
    manager = InventoryManager()
    manager.warehouses = {
        1: Warehouse(id=1, name="Warehouse 1", location="Location 1", latitude=40.7128, longitude=-74.0060),
        2: Warehouse(id=2, name="Warehouse 2", location="Location 2", latitude=34.0522, longitude=-118.2437),
    }
    manager.components = {
        1: Component(id=1, name="Component A", description="Description A"),
        2: Component(id=2, name="Component B", description="Description B"),
    }
    manager.inventory = {
        (1, 1): InventoryItem(component_id=1, warehouse_id=1, quantity=100, min_stock=50, max_stock=200),
        (1, 2): InventoryItem(component_id=2, warehouse_id=1, quantity=75, min_stock=25, max_stock=150),
        (2, 1): InventoryItem(component_id=1, warehouse_id=2, quantity=50, min_stock=20, max_stock=100),
    }
    return manager

@pytest.fixture
def logistics_solver(inventory_manager):
    return LogisticsSolver(inventory_manager)

def test_haversine_distance():
    distance = haversine_distance(40.7128, -74.0060, 34.0522, -118.2437)
    assert round(distance, 2) == 2445.56

def test_get_warehouse_inventory(inventory_manager):
    inventory = inventory_manager.get_warehouse_inventory(1)
    assert len(inventory) == 2
    assert inventory[0].quantity == 100
    assert inventory[1].quantity == 75

def test_create_transfer_request(inventory_manager):
    transfer = inventory_manager.create_transfer_request(
        source_id=1,
        dest_id=2,
        component_id=1,
        quantity=30,
        transfer_date=date.today()
    )
    assert transfer is not None
    assert transfer.source_warehouse_id == 1
    assert transfer.destination_warehouse_id == 2
    assert transfer.component_id == 1
    assert transfer.quantity == 30

def test_execute_transfer(inventory_manager):
    transfer = TransferRequest(
        source_warehouse_id=1,
        destination_warehouse_id=2,
        component_id=1,
        quantity=30,
        priority=5,
        request_date=date.today(),
        transfer_date=date.today()
    )
    success = inventory_manager.execute_transfer(transfer)
    assert success is True
    assert inventory_manager.inventory[(1, 1)].quantity == 70
    assert inventory_manager.inventory[(2, 1)].quantity == 80

def test_find_path(logistics_solver):
    path = logistics_solver.find_path(1, 2)
    assert path == [1, 2]

def test_find_all_paths(logistics_solver):
    paths = logistics_solver.find_all_paths(1, 2)
    assert len(paths) > 0
    assert paths[0] == [1, 2]

def test_delivery_route():
    route = DeliveryRoute(starting_warehouse_id=1)
    segment = RouteSegment.calculate(
        origin=Warehouse(id=1, name="Warehouse 1", location="Location 1", latitude=40.7128, longitude=-74.0060),
        destination=Warehouse(id=2, name="Warehouse 2", location="Location 2", latitude=34.0522, longitude=-118.2437)
    )
    route.add_segment(destination_id=2, segment=segment)
    assert route.total_distance > 0
    assert route.total_time > 0
    assert route.path == [1, 2]