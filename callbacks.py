from dash import Input, Output, html, dash_table, State, callback, dcc
import dash_bootstrap_components as dbc
from database.connector import (
    get_all_warehouses,
    get_warehouse_inventory,
    get_warehouse_health_metrics,
    calculate_possible_kits,
    get_kit_components,
    calculate_rebalance_suggestions,
)
from dash.exceptions import PreventUpdate
import plotly.express as px
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
            Output("rebalance-container", "style"),
        ],
        [Input("tabs", "active_tab")],
    )
    def update_dashboard(active_tab):
        # Default styles (hidden)
        inventory_style = {"display": "none"}
        rebalance_style = {"display": "none"}

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
            )

        elif active_tab == "warehouse-inventory":
            # Show inventory management section
            inventory_style = {"display": "block"}
            return (
                html.Div(
                    [
                        html.H3("Warehouse Inventory Management", className="mb-4"),
                        html.P("Select a warehouse to view and manage its inventory."),
                    ]
                ),
                inventory_style,
                rebalance_style,
            )

        elif active_tab == "kit-calculator":
            return (
                html.Div(
                    [
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
                rebalance_style,
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
            )

        return (
            html.Div("Select a tab to see dashboard content"),
            inventory_style,
            rebalance_style,
        )

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
        [
            Output("kit-calculator-warehouse", "options"),
            Output("kit-calculator-warehouse", "value"),
        ],
        Input("tabs", "active_tab"),
    )
    def populate_kit_calculator_dropdown(active_tab):
        if active_tab == "kit-calculator":
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
        [
            Output("source-warehouse", "options"),
            Output("destination-warehouse", "options"),
        ],
        [Input("tabs", "active_tab")],
    )
    def populate_warehouse_dropdowns(active_tab):
        if active_tab == "rebalance-warehouses":
            try:
                warehouses = get_all_warehouses()
                if not warehouses:
                    raise ValueError("No warehouses found")
                options = [
                    {"label": w["warehouse_name"], "value": w["warehouse_id"]}
                    for w in warehouses
                ]
                return options, options
            except Exception as e:
                logger.error(f"Error fetching warehouses: {e}")
                return [], []
        raise PreventUpdate

    @app.callback(
        Output("rebalance-suggestions", "children"),
        [
            Input("source-warehouse", "value"),
            Input("destination-warehouse", "value"),
            Input("min-transfers", "value"),
            Input("max-transfers", "value"),
        ],
    )
    def update_rebalance_suggestions(source_id, dest_id, min_transfers, max_transfers):
        if not source_id or not dest_id or source_id == dest_id:
            return html.Div(
                "Select different source and destination warehouses to view suggestions.",
                className="text-muted",
            )

        try:
            # Use safe default values if not provided
            min_transfers = max(1, min_transfers or 1)
            max_transfers = max(min_transfers, max_transfers or 100)

            results = calculate_rebalance_suggestions(
                source_id, dest_id, min_transfers, max_transfers
            )

            if not results["suggestions"]:
                return html.Div(
                    "No viable transfers found with current parameters.",
                    className="text-warning",
                )

            suggestions_table = dash_table.DataTable(
                data=results["suggestions"],
                columns=[
                    {"name": "Component", "id": "component"},
                    {"name": "Transfer Quantity", "id": "quantity"},
                    {"name": "Impact", "id": "impact"},
                    {"name": "Source Remaining", "id": "source_remaining"},
                    {"name": "Destination New Total", "id": "dest_new_total"},
                ],
                style_table={"overflowX": "auto"},
                style_cell={"textAlign": "left", "padding": "10px"},
                style_header={
                    "backgroundColor": "var(--light)",
                    "fontWeight": "bold",
                },
                style_data_conditional=[
                    {
                        "if": {"filter_query": '{impact} = "High"'},
                        "backgroundColor": "rgba(39, 174, 96, 0.1)",
                    },
                    {
                        "if": {"filter_query": '{impact} = "Medium"'},
                        "backgroundColor": "rgba(243, 156, 18, 0.1)",
                    },
                    {
                        "if": {"filter_query": '{impact} = "Low"'},
                        "backgroundColor": "rgba(231, 76, 60, 0.1)",
                    },
                ],
            )

            metrics_cards = dbc.Row(
                [
                    dbc.Col(
                        create_health_card(
                            "Current Source Kits",
                            results["current_metrics"]["source_kits"],
                            "primary",
                        )
                    ),
                    dbc.Col(
                        create_health_card(
                            "Current Destination Kits",
                            results["current_metrics"]["dest_kits"],
                            "primary",
                        )
                    ),
                ]
            )

            return html.Div(
                [
                    metrics_cards,
                    html.Br(),
                    dbc.Card(
                        [
                            dbc.CardHeader("Suggested Transfers"),
                            dbc.CardBody(
                                [
                                    suggestions_table,
                                    html.Div(
                                        dbc.Button(
                                            "Schedule Transfers",
                                            id="schedule-transfers",
                                            color="primary",
                                            className="mt-3",
                                        ),
                                        className="text-end",
                                    ),
                                ]
                            ),
                        ]
                    ),
                ]
            )

        except Exception as e:
            logger.error(f"Error generating rebalance suggestions: {e}")
            return html.Div(
                "Error generating suggestions. Please try again.",
                className="text-danger",
            )

    @app.callback(
        Output("inventory-table-container", "children"),
        [Input("warehouse-selector", "value")],
    )
    def update_inventory_table(warehouse_id):
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

    @app.callback(
        [
            Output("source-warehouse", "value"),
            Output("destination-warehouse", "value")
        ],
        [
            Input("swap-warehouses-button", "n_clicks")
        ],
        [
            State("source-warehouse", "value"),
            State("destination-warehouse", "value")
        ],
        prevent_initial_call=True
    )
    def swap_warehouses(n_clicks, source_id, dest_id):
        if not source_id or not dest_id:
            raise PreventUpdate
        return dest_id, source_id

    @app.callback(
        Output("map-content", "figure"),
        [
            Input("source-warehouse", "value"),
            Input("destination-warehouse", "value"),
            Input("warehouse-selector", "value")
        ]
    )
    def update_map_with_selections(source_id, dest_id, inventory_id):
        warehouses = get_all_warehouses()
        
        # Create base map
        fig = px.scatter_mapbox(
            lat=[w["latitude"] for w in warehouses],
            lon=[w["longitude"] for w in warehouses],
            hover_name=[w["warehouse_name"] for w in warehouses],
            zoom=3,
            mapbox_style="carto-positron",
        )

        fig.update_layout(
            mapbox=dict(
                bearing=0,
                pitch=0,
            ),
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
            showlegend=False,
            paper_bgcolor="white",
            plot_bgcolor="white",
        )

        # Handle rebalancing warehouse connections
        if source_id and dest_id:
            source = next((w for w in warehouses if w["warehouse_id"] == source_id), None)
            dest = next((w for w in warehouses if w["warehouse_id"] == dest_id), None)
            
            if source and dest:
                # Add connection line
                fig.add_trace(
                    dict(
                        type="scattermapbox",
                        lon=[source["longitude"], dest["longitude"]],
                        lat=[source["latitude"], dest["latitude"]],
                        mode="lines",
                        line=dict(
                            width=2,
                            color="#3072b4",
                        ),
                        hoverinfo="skip"
                    )
                )
                
                # Add source and destination markers
                fig.add_trace(
                    dict(
                        type="scattermapbox",
                        lon=[source["longitude"]],
                        lat=[source["latitude"]],
                        mode="markers",
                        marker=dict(size=12, color="#e74c3c"),
                        name="Source",
                        hovertext=f"Source: {source['warehouse_name']}"
                    )
                )
                
                fig.add_trace(
                    dict(
                        type="scattermapbox",
                        lon=[dest["longitude"]],
                        lat=[dest["latitude"]],
                        mode="markers",
                        marker=dict(size=12, color="#27ae60"),
                        name="Destination",
                        hovertext=f"Destination: {dest['warehouse_name']}"
                    )
                )

        # Handle inventory warehouse selection
        if inventory_id:
            selected = next((w for w in warehouses if w["warehouse_id"] == inventory_id), None)
            if selected:
                # Add circle around selected warehouse
                fig.add_trace(
                    dict(
                        type="scattermapbox",
                        lon=[selected["longitude"]],
                        lat=[selected["latitude"]],
                        mode="markers",
                        marker=dict(
                            size=25,
                            color="rgba(48, 114, 180, 0.3)",
                            symbol="circle"
                        ),
                        hoverinfo="skip"
                    )
                )
                # Add center point
                fig.add_trace(
                    dict(
                        type="scattermapbox",
                        lon=[selected["longitude"]],
                        lat=[selected["latitude"]],
                        mode="markers",
                        marker=dict(size=8, color="#3072b4"),
                        name="Selected Warehouse",
                        hovertext=f"Selected: {selected['warehouse_name']}"
                    )
                )

        return fig
