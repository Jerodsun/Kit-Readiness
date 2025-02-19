import pytest
from unittest.mock import Mock, patch
from datetime import date
from database.connector import (
    get_all_warehouses,
    get_warehouse_inventory,
    get_kit_details,
    create_end_shipment,
    get_end_user_shipments,
    get_all_destinations,
)

# Mock data
MOCK_WAREHOUSES = [
    {
        "warehouse_id": 1,
        "warehouse_name": "Test Warehouse 1",
        "latitude": 40.7128,
        "longitude": -74.0060,
    },
    {
        "warehouse_id": 2,
        "warehouse_name": "Test Warehouse 2",
        "latitude": 34.0522,
        "longitude": -118.2437,
    },
]

MOCK_INVENTORY = [
    {
        "component_id": 1,
        "component_name": "Component A",
        "description": "Test Component A",
        "quantity": 100,
        "min_stock": 50,
        "max_stock": 200,
    },
    {
        "component_id": 2,
        "component_name": "Component B",
        "description": "Test Component B",
        "quantity": 75,
        "min_stock": 25,
        "max_stock": 150,
    },
]

MOCK_KITS = [
    {"kit_id": 1, "kit_name": "Test Kit 1", "description": "Description 1"},
    {"kit_id": 2, "kit_name": "Test Kit 2", "description": "Description 2"},
]

MOCK_DESTINATIONS = [
    {
        "destination_id": 1,
        "destination_name": "Test Destination 1",
        "latitude": 51.5074,
        "longitude": -0.1278,
    },
    {
        "destination_id": 2,
        "destination_name": "Test Destination 2",
        "latitude": 48.8566,
        "longitude": 2.3522,
    },
]

MOCK_SHIPMENTS = [
    {
        "shipment_id": 1,
        "shipment_date": "2024-01-01",
        "source_warehouse": "Test Warehouse 1",
        "destination_name": "Test Destination 1",
        "kit_name": "Test Kit 1",
        "quantity": 5,
    }
]


@pytest.fixture
def mock_cursor():
    cursor = Mock()
    cursor.fetchall = Mock()
    cursor.execute = Mock(return_value=cursor)
    return cursor


@pytest.fixture
def mock_db_connection(mock_cursor):
    conn = Mock()
    conn.cursor = Mock(return_value=mock_cursor)
    conn.commit = Mock()
    conn.close = Mock()
    return conn


def test_get_all_warehouses(mock_db_connection, mock_cursor):
    mock_cursor.fetchall.return_value = MOCK_WAREHOUSES

    with patch("database.connector.get_db_connection") as mock_get_conn:
        mock_get_conn.return_value.__enter__.return_value = mock_db_connection

        warehouses = get_all_warehouses()

        assert len(warehouses) == 2
        assert warehouses[0]["warehouse_name"] == "Test Warehouse 1"
        assert warehouses[1]["warehouse_name"] == "Test Warehouse 2"
        mock_cursor.execute.assert_called_once()


def test_get_warehouse_inventory(mock_db_connection, mock_cursor):
    mock_cursor.fetchall.return_value = MOCK_INVENTORY

    with patch("database.connector.get_db_connection") as mock_get_conn:
        mock_get_conn.return_value.__enter__.return_value = mock_db_connection

        inventory = get_warehouse_inventory(1)

        assert len(inventory) == 2
        assert inventory[0]["quantity"] == 100
        assert inventory[1]["quantity"] == 75
        mock_cursor.execute.assert_called_once()


def test_get_kit_details(mock_db_connection, mock_cursor):
    mock_cursor.fetchall.return_value = MOCK_KITS

    with patch("database.connector.get_db_connection") as mock_get_conn:
        mock_get_conn.return_value.__enter__.return_value = mock_db_connection

        kits = get_kit_details()

        assert len(kits) == 2
        assert kits[0]["kit_name"] == "Test Kit 1"
        assert kits[1]["kit_name"] == "Test Kit 2"
        mock_cursor.execute.assert_called_once()


def test_create_end_shipment(mock_db_connection, mock_cursor):
    with patch("database.connector.get_db_connection") as mock_get_conn:
        mock_get_conn.return_value.__enter__.return_value = mock_db_connection

        success = create_end_shipment(
            warehouse_id=1,
            destination_id=1,
            kit_id=1,
            quantity=5,
            shipment_date=date.today().isoformat(),
        )

        assert success is True
        mock_cursor.execute.assert_called_once()
        mock_db_connection.commit.assert_called_once()


def test_create_end_shipment_failure(mock_db_connection, mock_cursor):
    mock_cursor.execute.side_effect = Exception("Database error")

    with patch("database.connector.get_db_connection") as mock_get_conn:
        mock_get_conn.return_value.__enter__.return_value = mock_db_connection

        success = create_end_shipment(
            warehouse_id=1,
            destination_id=1,
            kit_id=1,
            quantity=5,
            shipment_date=date.today().isoformat(),
        )

        assert success is False
        mock_cursor.execute.assert_called_once()
        mock_db_connection.rollback.assert_called_once()


def test_get_end_user_shipments(mock_db_connection, mock_cursor):
    mock_cursor.fetchall.return_value = MOCK_SHIPMENTS

    with patch("database.connector.get_db_connection") as mock_get_conn:
        mock_get_conn.return_value.__enter__.return_value = mock_db_connection

        shipments = get_end_user_shipments()

        assert len(shipments) == 1
        assert shipments[0]["quantity"] == 5
        mock_cursor.execute.assert_called_once()


def test_get_all_destinations(mock_db_connection, mock_cursor):
    mock_cursor.fetchall.return_value = MOCK_DESTINATIONS

    with patch("database.connector.get_db_connection") as mock_get_conn:
        mock_get_conn.return_value.__enter__.return_value = mock_db_connection

        destinations = get_all_destinations()

        assert len(destinations) == 2
        assert destinations[0]["destination_name"] == "Test Destination 1"
        assert destinations[1]["destination_name"] == "Test Destination 2"
        mock_cursor.execute.assert_called_once()
