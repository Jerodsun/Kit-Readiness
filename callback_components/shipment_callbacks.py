from dash import Input, Output, html, State, ctx
from database.connector import (
    get_all_warehouses,

    get_all_destinations,
    get_kit_details,
    create_end_shipment,
)

import logging

# Get logger
logger = logging.getLogger(__name__)


def register_shipment_callbacks(app):

    @app.callback(
        [
            Output("shipment-modal", "is_open"),
            Output("shipment-warehouse", "options"),
            Output("shipment-destination", "options"),
            Output("shipment-kit", "options"),
            Output("shipment-message", "children"),
        ],
        [
            Input("create-shipment-button", "n_clicks"),
            Input("cancel-shipment", "n_clicks"),
            Input("confirm-shipment", "n_clicks"),
        ],
        [
            State("shipment-modal", "is_open"),
            State("shipment-warehouse", "value"),
            State("shipment-destination", "value"),
            State("shipment-kit", "value"),
            State("shipment-quantity", "value"),
            State("new-shipment-date", "date"),
        ],
    )
    def handle_shipment_modal(
        create_n,
        cancel_n,
        confirm_n,
        is_open,
        warehouse_id,
        destination_id,
        kit_id,
        quantity,
        shipment_date,
    ):
        triggered_id = ctx.triggered_id if ctx.triggered_id else None

        # Get data for dropdowns
        warehouses = get_all_warehouses()
        destinations = get_all_destinations()
        kits = get_kit_details()

        warehouse_options = [
            {"label": w["warehouse_name"], "value": w["warehouse_id"]}
            for w in warehouses
        ]
        destination_options = [
            {"label": d["destination_name"], "value": d["destination_id"]}
            for d in destinations
        ]
        kit_options = [{"label": k["kit_name"], "value": k["kit_id"]} for k in kits]

        message = ""

        if triggered_id == "create-shipment-button" and create_n:
            return True, warehouse_options, destination_options, kit_options, message

        elif triggered_id == "cancel-shipment":
            return False, warehouse_options, destination_options, kit_options, message

        elif triggered_id == "confirm-shipment":
            if not all([warehouse_id, destination_id, kit_id, quantity, shipment_date]):
                message = html.Div("Please fill in all fields", className="text-danger")
                return (
                    True,
                    warehouse_options,
                    destination_options,
                    kit_options,
                    message,
                )

            # Create shipment record
            success = create_end_shipment(
                warehouse_id=warehouse_id,
                destination_id=destination_id,
                kit_id=kit_id,
                quantity=quantity,
                shipment_date=shipment_date,
            )

            if success:
                return (
                    False,
                    warehouse_options,
                    destination_options,
                    kit_options,
                    message,
                )
            else:
                message = html.Div("Error creating shipment", className="text-danger")
                return (
                    True,
                    warehouse_options,
                    destination_options,
                    kit_options,
                    message,
                )

        return (
            is_open,
            warehouse_options,
            destination_options,
            kit_options,
            message,
        )
