from dash import Input, Output, html, dash_table, State
import dash_bootstrap_components as dbc
from database.connector import (
    get_warehouse_inventory,
    update_warehouse_inventory,
)
from dash.exceptions import PreventUpdate
import logging

# Get logger
logger = logging.getLogger(__name__)


def register_inventory_callbacks(app):
    @app.callback(
        Output("save-status", "children"),
        [
            Input("save-inventory", "n_clicks"),
        ],
        [
            State("inventory-table", "data"),
            State("common-warehouse-selector", "value"),
        ],
        prevent_initial_call=True,
    )
    def save_inventory_changes(n_clicks, table_data, warehouse_id):
        if not n_clicks or not table_data or not warehouse_id:
            raise PreventUpdate

        updates = [
            {"component_id": row["component_id"], "quantity": row["quantity"]}
            for row in table_data
        ]

        success = update_warehouse_inventory(warehouse_id, updates)

        if success:
            return html.Div("Changes saved successfully!", className="text-success")
        else:
            return html.Div(
                "Error saving changes. Please try again.", className="text-danger"
            )

    @app.callback(
        Output("inventory-table-container", "children"),
        [Input("common-warehouse-selector", "value")],
    )
    def update_inventory_table(warehouse_id):
        if not warehouse_id:
            return html.Div("Please select a warehouse.")

        inventory = get_warehouse_inventory(warehouse_id)
        if not inventory:
            return html.Div("No inventory data available for this warehouse.")

        return html.Div(
            [
                dash_table.DataTable(
                    id="inventory-table",
                    data=[
                        {
                            "component_id": row["component_id"],
                            "component_name": row["component_name"],
                            "description": row["description"],
                            "quantity": row["quantity"],
                            "min_stock": row["min_stock"],
                            "max_stock": row["max_stock"],
                        }
                        for row in inventory
                    ],
                    columns=[
                        {
                            "name": "Component",
                            "id": "component_name",
                            "editable": False,
                        },
                        {"name": "Description", "id": "description", "editable": False},
                        {
                            "name": "Quantity",
                            "id": "quantity",
                            "editable": True,
                            "type": "numeric",
                        },
                        {
                            "name": "Minimum Healthy Stock",
                            "id": "min_stock",
                            "editable": False,
                        },
                        {
                            "name": "Maximum Warehouse Capacity",
                            "id": "max_stock",
                            "editable": False,
                        },
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
                ),
                dbc.Button(
                    "Save Changes",
                    id="save-inventory",
                    color="primary",
                    className="mt-3",
                ),
                html.Div(id="save-status", className="mt-2"),
            ]
        )
