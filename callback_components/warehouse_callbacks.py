from dash import Input, Output, State
from database.connector import (
    get_all_warehouses,
)
from dash.exceptions import PreventUpdate
import logging

# Get logger
logger = logging.getLogger(__name__)


def register_warehouse_callbacks(app):
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
        [Output("source-warehouse", "value"), Output("destination-warehouse", "value")],
        [Input("swap-warehouses-button", "n_clicks")],
        [State("source-warehouse", "value"), State("destination-warehouse", "value")],
        prevent_initial_call=True,
    )
    def swap_warehouses(n_clicks, source_id, dest_id):
        if not source_id or not dest_id:
            raise PreventUpdate
        return dest_id, source_id

    @app.callback(
        [
            Output("common-warehouse-selector", "options"),
            Output("common-warehouse-selector", "value"),
        ],
        [Input("tabs", "active_tab")],
        [State("common-warehouse-selector", "value")],
    )
    def populate_warehouse_dropdown(active_tab, current_value):
        try:
            warehouses = get_all_warehouses()
            if not warehouses:
                raise ValueError("No warehouses found")
            options = [
                {"label": w["warehouse_name"], "value": w["warehouse_id"]}
                for w in warehouses
            ]
            # Only set default value if there isn't one already
            default_value = (
                current_value if current_value else warehouses[0]["warehouse_id"]
            )
            return options, default_value
        except Exception as e:
            logger.error(f"Error fetching warehouses: {e}")
            return [], None
        return [], None
