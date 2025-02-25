from dash import Input, Output, html, State, dcc, ctx
import dash_bootstrap_components as dbc
from database.connector import (
    create_warehouse_transfer,
)

import logging

# Get logger
logger = logging.getLogger(__name__)


def register_transfer_callbacks(app):

    @app.callback(
        [
            Output("transfer-modal", "is_open"),
            Output("transfer-kit-selector", "children"),
            Output("transfer-quantity-input", "children"),
            Output("transfer-message", "children"),
        ],
        [
            Input("schedule-transfers", "n_clicks"),
            Input("cancel-transfer", "n_clicks"),
            Input("confirm-transfer", "n_clicks"),
        ],
        [
            State("transfer-modal", "is_open"),
            State("source-warehouse", "value"),
            State("destination-warehouse", "value"),
            State("shipment-date", "date"),
            State("transfer-component-selector", "value"),
            State("transfer-quantity", "value"),
            State("suggestions-store", "data"),
        ],
    )
    def handle_transfer_modal(
        schedule_n,
        cancel_n,
        confirm_n,
        is_open,
        source_id,
        dest_id,
        transfer_date,
        selected_component,
        quantity,
        suggestions,
    ):
        triggered_id = ctx.triggered_id if ctx.triggered_id else None

        # Create component selector using suggestions from store
        component_selector = dbc.Row(
            [
                dbc.Col(
                    [
                        html.Label("Select Component to Transfer:"),
                        dcc.Dropdown(
                            id="transfer-component-selector",
                            options=[
                                {
                                    "label": row["component"],
                                    "value": row["component_id"],
                                }
                                for row in (suggestions or [])
                            ],
                            className="mb-3",
                        ),
                    ]
                )
            ]
        )

        quantity_input = dbc.Row(
            [
                dbc.Col(
                    [
                        html.Label("Transfer Quantity:"),
                        dbc.Input(
                            type="number",
                            id="transfer-quantity",
                            min=1,
                            className="mb-3",
                        ),
                    ]
                )
            ]
        )

        message = ""

        if triggered_id == "schedule-transfers" and schedule_n:
            return True, component_selector, quantity_input, message

        elif triggered_id == "cancel-transfer":
            return False, component_selector, quantity_input, message

        elif triggered_id == "confirm-transfer":
            if not all(
                [source_id, dest_id, transfer_date, selected_component, quantity]
            ):
                message = html.Div("Please fill in all fields", className="text-danger")
                return True, component_selector, quantity_input, message

            # Create transfer record using correct function
            success = create_warehouse_transfer(
                source_id=source_id,
                dest_id=dest_id,
                component_id=selected_component,
                quantity=quantity,
                transfer_date=transfer_date,
            )

            if success:
                return False, component_selector, quantity_input, message
            else:
                message = html.Div("Error scheduling transfer", className="text-danger")
                return True, component_selector, quantity_input, message

        return is_open, component_selector, quantity_input, message
