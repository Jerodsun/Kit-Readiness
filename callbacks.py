from dash import Input, Output, html, dash_table
import dash_bootstrap_components as dbc
from database.connector import get_all_warehouses, get_warehouse_inventory
from dash.exceptions import PreventUpdate
import logging

# Get logger
logger = logging.getLogger(__name__)


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

        elif active_tab == "tab-3":
            return html.Div("Dashboard content for Tab 3"), inventory_style

        return html.Div("Select a tab to see dashboard content"), inventory_style

    @app.callback(Output("warehouse-selector", "options"), Input("tabs", "active_tab"))
    def populate_warehouse_dropdown(active_tab):
        if active_tab == "warehouse-inventory":
            try:
                warehouses = get_all_warehouses()
                if not warehouses:
                    raise ValueError("No warehouses found")
                return [
                    {"label": w["warehouse_name"], "value": w["warehouse_id"]}
                    for w in warehouses
                ]
            except Exception as e:
                logger.error(f"Error fetching warehouses: {e}")
                return []
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
                {"name": "Min Stock", "id": "min_stock"},
                {"name": "Max Stock", "id": "max_stock"},
            ],
            style_table={"overflowX": "auto"},
            style_cell={"textAlign": "left", "padding": "10px"},
            style_header={
                "backgroundColor": "rgb(230, 230, 230)",
                "fontWeight": "bold",
            },
        )
