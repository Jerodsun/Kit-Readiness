from dash import Input, Output, html, dash_table
import dash_bootstrap_components as dbc
from database.connector import (
    get_warehouse_health_metrics,
    get_warehouse_transfers,
    get_end_user_shipments,
)

from .utils import create_health_card


def register_dashboard_callbacks(app):
    @app.callback(
        [
            Output("dashboard-content", "children"),
            Output("inventory-management", "style"),
            Output("rebalance-container", "style"),
            Output("kit-calculator-container", "style"),
        ],
        [Input("tabs", "active_tab")],
    )
    def update_dashboard(active_tab):
        # Default styles (hidden)
        inventory_style = {"display": "none"}
        rebalance_style = {"display": "none"}
        calculator_style = {"display": "none"}

        if active_tab == "home":
            return (
                html.Div(
                    [
                        dbc.Card(
                            [
                                dbc.CardBody(
                                    [
                                        html.H4("About", className="card-title"),
                                        html.P(
                                            """
                            The Kit Readiness Dashboard helps you monitor and manage component assembly 
                            across multiple warehouses. Track component availability, calculate potential 
                            completions, and optimize inventory distribution.
                        """
                                        ),
                                    ]
                                )
                            ],
                            className="mb-4",
                        ),
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        dbc.Card(
                                            [
                                                dbc.CardBody(
                                                    [
                                                        html.H5(
                                                            "Key Features",
                                                            className="card-title",
                                                        ),
                                                        html.Ul(
                                                            [
                                                                html.Li(
                                                                    "Real-time kit completion calculations"
                                                                ),
                                                                html.Li(
                                                                    "Interactive warehouse map visualization"
                                                                ),
                                                                html.Li(
                                                                    "Inventory rebalancing suggestions"
                                                                ),
                                                                html.Li(
                                                                    "Component transfer management"
                                                                ),
                                                                html.Li(
                                                                    "Warehouse performance metrics"
                                                                ),
                                                            ]
                                                        ),
                                                    ]
                                                )
                                            ]
                                        )
                                    ],
                                    width=6,
                                ),
                                dbc.Col(
                                    [
                                        dbc.Card(
                                            [
                                                dbc.CardBody(
                                                    [
                                                        html.H5(
                                                            "Getting Started",
                                                            className="card-title",
                                                        ),
                                                        html.P(
                                                            """
                                    Use the tabs above to navigate between different features. 
                                    The map on the right shows all warehouse locations - click 
                                    on any location to view detailed inventory information.
                                """
                                                        ),
                                                    ]
                                                )
                                            ]
                                        )
                                    ],
                                    width=6,
                                ),
                            ]
                        ),
                    ]
                ),
                inventory_style,
                rebalance_style,
                calculator_style,
            )

        elif active_tab == "warehouse-health":
            # Moved health metrics content
            health_metrics = get_warehouse_health_metrics()

            # Calculate overall statistics
            total_warehouses = len(health_metrics)
            healthy_warehouses = sum(
                1 for w in health_metrics if w["health_status"] == "Healthy"
            )
            critical_warehouses = sum(
                1 for w in health_metrics if w["health_status"] == "Critical"
            )

            # Create overview cards
            overview_stats = dbc.Row(
                [
                    dbc.Col(
                        create_health_card(
                            "Total Warehouses", total_warehouses, "primary"
                        )
                    ),
                    dbc.Col(
                        create_health_card(
                            "Healthy Warehouses", healthy_warehouses, "success"
                        )
                    ),
                    dbc.Col(
                        create_health_card(
                            "Critical Warehouses", critical_warehouses, "danger"
                        )
                    ),
                ]
            )

            # Create warehouse health table
            health_table = dash_table.DataTable(
                data=[dict(row) for row in health_metrics],
                columns=[
                    {"name": "Warehouse", "id": "warehouse_name"},
                    {
                        "name": "Stock Level %",
                        "id": "stock_level_percentage",
                        "format": {"specifier": ".2f"},
                    },
                    {"name": "Low Stock Items", "id": "low_stock_items"},
                    {"name": "Total Items", "id": "total_items"},
                    {"name": "Status", "id": "health_status"},
                ],
                style_data_conditional=[
                    {
                        "if": {"filter_query": '{health_status} = "Critical"'},
                        "backgroundColor": "#ffebee",
                        "color": "#c62828",
                    },
                    {
                        "if": {"filter_query": '{health_status} = "Warning"'},
                        "backgroundColor": "#fff3e0",
                        "color": "#ef6c00",
                    },
                    {
                        "if": {"filter_query": '{health_status} = "Healthy"'},
                        "backgroundColor": "#e8f5e9",
                        "color": "#2e7d32",
                    },
                ],
                style_table={"overflowX": "auto"},
                style_cell={"textAlign": "left", "padding": "10px"},
                style_header={
                    "backgroundColor": "rgb(230, 230, 230)",
                    "fontWeight": "bold",
                },
            )

            return (
                html.Div(
                    [
                        overview_stats,
                        html.Br(),
                        dbc.Card(
                            [
                                dbc.CardHeader("Warehouse Health Status"),
                                dbc.CardBody(health_table),
                            ]
                        ),
                    ]
                ),
                inventory_style,
                rebalance_style,
                calculator_style,
            )

        elif active_tab == "warehouse-inventory":
            # Show inventory management section
            inventory_style = {"display": "block"}
            return (
                html.Div(
                    [
                        html.H3("Warehouse Inventory Management", className="mb-4"),
                        dbc.Card(
                            [
                                dbc.CardHeader(
                                    [
                                        html.H5(
                                            "Manage Component Inventory",
                                            className="mb-0",
                                        ),
                                    ]
                                ),
                                dbc.CardBody(
                                    [
                                        html.P(
                                            """
                                            View and update component quantities for the selected warehouse. 
                                            Components below minimum stock are highlighted in red, 
                                            healthy levels in green.
                                            """
                                        ),
                                    ]
                                ),
                            ],
                            className="mb-4",
                        ),
                    ]
                ),
                inventory_style,
                rebalance_style,
                calculator_style,
            )

        elif active_tab == "kit-calculator":
            calculator_style = {"display": "block"}
            return (
                html.Div(
                    [
                        html.H3("Kit Calculator", className="mb-4"),
                        html.P(
                            "Calculate possible kit completions based on current inventory."
                        ),
                    ]
                ),
                inventory_style,
                rebalance_style,
                calculator_style,
            )

        elif active_tab == "rebalance-warehouses":
            rebalance_style = {"display": "block"}
            return (
                html.Div(
                    [
                        html.H3("Warehouse Rebalancing", className="mb-4"),
                        html.P(
                            """
                            Optimize component distribution across warehouses to maximize
                            kit completion potential. Select source and destination warehouses
                            to view suggested transfers.
                            """
                        ),
                    ]
                ),
                inventory_style,
                rebalance_style,
                calculator_style,
            )

        elif active_tab == "scheduled-transfers":
            transfers = get_warehouse_transfers()

            transfers_table = dash_table.DataTable(
                data=[dict(row) for row in transfers],
                columns=[
                    {
                        "name": "Transfer Date",
                        "id": "transfer_date",
                    },
                    {"name": "From", "id": "source_warehouse"},
                    {"name": "To", "id": "destination_warehouse"},
                    {"name": "Component", "id": "component_name"},
                    {"name": "Quantity", "id": "quantity"},
                ],
                style_table={"overflowX": "auto"},
                style_cell={"textAlign": "left", "padding": "10px"},
                style_header={
                    "backgroundColor": "rgb(230, 230, 230)",
                    "fontWeight": "bold",
                },
                sort_action="native",
                sort_mode="multi",
            )

            return (
                html.Div(
                    [
                        html.H3("Warehouse Transfers", className="mb-4"),
                        dbc.Card(
                            [
                                dbc.CardHeader("Component Transfers"),
                                dbc.CardBody(transfers_table),
                            ]
                        ),
                    ]
                ),
                inventory_style,
                rebalance_style,
                calculator_style,
            )

        elif active_tab == "scheduled-shipments":
            shipments = get_end_user_shipments()

            shipments_table = dash_table.DataTable(
                data=[dict(row) for row in shipments],
                columns=[
                    {"name": "Shipment Date", "id": "shipment_date"},
                    {"name": "Warehouse", "id": "source_warehouse"},
                    {"name": "Destination", "id": "destination_name"},
                    {"name": "Kit", "id": "kit_name"},
                    {"name": "Quantity", "id": "quantity"},
                ],
                style_table={"overflowX": "auto"},
                style_cell={"textAlign": "left", "padding": "10px"},
                style_header={
                    "backgroundColor": "rgb(230, 230, 230)",
                    "fontWeight": "bold",
                },
                sort_action="native",
                sort_mode="multi",
            )

            return (
                html.Div(
                    [
                        html.H3("Shipments to Endpoints", className="mb-4"),
                        dbc.Button(
                            "Create Shipment",
                            id="create-shipment-button",
                            color="primary",
                            className="mb-3",
                        ),
                        dbc.Card(
                            [
                                dbc.CardHeader("Kit Shipments"),
                                dbc.CardBody(shipments_table),
                            ]
                        ),
                    ]
                ),
                inventory_style,
                rebalance_style,
                calculator_style,
            )

        return (
            html.Div("Select a tab to see dashboard content"),
            inventory_style,
            rebalance_style,
            calculator_style,
        )
