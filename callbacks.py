from dash import Input, Output, html, dash_table, State, callback, dcc
import dash_bootstrap_components as dbc
from database.connector import (
    get_all_warehouses,
    get_warehouse_inventory,
    get_warehouse_health_metrics,
    calculate_possible_kits,
    get_kit_components,
)
from dash.exceptions import PreventUpdate
import logging

# Get logger
logger = logging.getLogger(__name__)


def create_health_card(title, value, color="success"):
    return dbc.Card(
        dbc.CardBody(
            [
                html.H4(title, className="card-title"),
                html.H2(value, className=f"text-{color}"),
            ]
        ),
        className="mb-4",
    )


def register_callbacks(app):
    @app.callback(
        [
            Output("dashboard-content", "children"),
            Output("inventory-management", "style"),
        ],
        [Input("tabs", "active_tab")],
    )
    def update_dashboard(active_tab):
        # Default style (hidden)
        inventory_style = {"display": "none"}

        if active_tab == "home":
            return (
                html.Div(
                    [
                        html.Br(),
                        html.Br(),
                        dbc.Card(
                            [
                                dbc.CardBody(
                                    [
                                        html.H4("About", className="card-title"),
                                        html.P(
                                            """
                            The Kit Readiness Dashboard helps you monitor and manage kit assembly 
                            across multiple warehouses. Track component availability, calculate potential 
                            kit completions, and optimize inventory distribution.
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
                        "format": {"specifier": ".1f"},
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
                        html.Br(),
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
            )

        elif active_tab == "warehouse-inventory":
            # Show inventory management section
            inventory_style = {"display": "block"}
            return (
                html.Div(
                    [
                        html.Br(),
                        html.H3("Warehouse Inventory Management", className="mb-4"),
                        html.P("Select a warehouse to view and manage its inventory."),
                    ]
                ),
                inventory_style,
            )

        elif active_tab == "kit-calculator":
            return (
                html.Div(
                    [
                        html.Br(),
                        html.H3("Kit Calculator", className="mb-4"),
                        html.P(
                            "Calculate possible kit completions based on current inventory."
                        ),
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.Label("Select Warehouse:"),
                                        dcc.Dropdown(
                                            id="kit-calculator-warehouse",
                                            options=[
                                                {
                                                    "label": w["warehouse_name"],
                                                    "value": w["warehouse_id"],
                                                }
                                                for w in get_all_warehouses()
                                            ],
                                            className="mb-4",
                                        ),
                                    ],
                                    width=6,
                                ),
                            ]
                        ),
                        html.Div(id="kit-calculation-results"),
                        html.Div(id="kit-components-detail"),
                    ]
                ),
                inventory_style,
            )

        return html.Div("Select a tab to see dashboard content"), inventory_style

    @app.callback(
        [
            Output("warehouse-selector", "options"),
            Output("warehouse-selector", "value"),
        ],
        Input("tabs", "active_tab"),
    )
    def populate_warehouse_dropdown(active_tab):
        if active_tab == "warehouse-inventory":
            try:
                warehouses = get_all_warehouses()
                if not warehouses:
                    raise ValueError("No warehouses found")
                options = [
                    {"label": w["warehouse_name"], "value": w["warehouse_id"]}
                    for w in warehouses
                ]
                # Set default value to first warehouse's ID if available
                default_value = warehouses[0]["warehouse_id"] if warehouses else None
                return options, default_value
            except Exception as e:
                logger.error(f"Error fetching warehouses: {e}")
                return [], None
        raise PreventUpdate

    @app.callback(
        Output("inventory-table-container", "children"),
        [Input("warehouse-selector", "value")],
    )
    def update_inventory_table(warehouse_id):
        if not warehouse_id:
            return html.Div("Please select a warehouse to view inventory.")

        inventory = get_warehouse_inventory(warehouse_id)
        if not inventory:
            return html.Div("No inventory data available for this warehouse.")

        return dash_table.DataTable(
            data=[dict(row) for row in inventory],
            columns=[
                {"name": "Component", "id": "component_name"},
                {"name": "Description", "id": "description"},
                {"name": "Quantity", "id": "quantity"},
                {"name": "Minimum Healthy Stock", "id": "min_stock"},
                {"name": "Maximum Warehouse Capacity", "id": "max_stock"},
            ],
            style_table={"overflowX": "auto"},
            style_cell={"textAlign": "left", "padding": "10px"},
            style_header={
                "backgroundColor": "rgb(230, 230, 230)",
                "fontWeight": "bold",
            },
            style_data_conditional=[
                {
                    "if": {
                        "filter_query": "{quantity} < {min_stock}",
                        "column_id": "quantity",
                    },
                    "backgroundColor": "#ffebee",
                    "color": "#c62828",
                },
                {
                    "if": {
                        "filter_query": "{quantity} >= {min_stock} && {quantity} < {max_stock}",
                        "column_id": "quantity",
                    },
                    "backgroundColor": "#fff3e0",
                    "color": "#ef6c00",
                },
                {
                    "if": {
                        "filter_query": "{quantity} >= {max_stock}",
                        "column_id": "quantity",
                    },
                    "backgroundColor": "#e8f5e9",
                    "color": "#2e7d32",
                },
            ],
        )

    @app.callback(
        [
            Output("kit-calculation-results", "children"),
            Output("kit-components-detail", "children"),
            Output("kit-calculation-results", "style"),
            Output("kit-components-detail", "style"),
        ],
        [Input("kit-calculator-warehouse", "value")],
    )
    def update_kit_calculations(warehouse_id):
        if not warehouse_id:
            return (
                html.Div("Please select a warehouse."),
                None,
                {"display": "none"},
                {"display": "none"},
            )

        # Get possible kits calculation
        possible_kits = calculate_possible_kits(warehouse_id)
        kit_components = get_kit_components()

        # Create results table
        results_table = dash_table.DataTable(
            data=[dict(row) for row in possible_kits],
            columns=[
                {"name": "Kit Name", "id": "kit_name"},
                {"name": "Possible Completions", "id": "possible_kits"},
            ],
            style_table={"overflowX": "auto"},
            style_cell={"textAlign": "left", "padding": "10px"},
            style_header={
                "backgroundColor": "rgb(230, 230, 230)",
                "fontWeight": "bold",
            },
        )

        # Create components breakdown table
        components_table = dash_table.DataTable(
            data=[dict(row) for row in kit_components],
            columns=[
                {"name": "Kit", "id": "kit_name"},
                {"name": "Component", "id": "component_name"},
                {"name": "Required Quantity", "id": "required_quantity"},
            ],
            style_table={"overflowX": "auto"},
            style_cell={"textAlign": "left", "padding": "10px"},
            style_header={
                "backgroundColor": "rgb(230, 230, 230)",
                "fontWeight": "bold",
            },
        )

        return (
            dbc.Card(
                [
                    dbc.CardHeader("Possible Kit Completions"),
                    dbc.CardBody(results_table),
                ]
            ),
            dbc.Card(
                [
                    dbc.CardHeader("Kit Component Requirements"),
                    dbc.CardBody(components_table),
                ],
                className="mt-4",
            ),
            {"display": "block"},
            {"display": "block"},
        )
