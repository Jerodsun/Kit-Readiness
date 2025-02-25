from dash import Input, Output, html, dash_table
import dash_bootstrap_components as dbc
from database.connector import (
    calculate_possible_kits,
    get_kit_components,
    calculate_rebalance_suggestions,

)

import logging
from .utils import create_health_card

# Get logger
logger = logging.getLogger(__name__)


def register_rebalance_callbacks(app):

    @app.callback(
        [
            Output("rebalance-suggestions", "children"),
            Output("suggestions-store", "data"),  # Add output for store
        ],
        [
            Input("source-warehouse", "value"),
            Input("destination-warehouse", "value"),
            Input("min-transfers", "value"),
            Input("max-transfers", "value"),
        ],
    )
    def update_rebalance_suggestions(source_id, dest_id, min_transfers, max_transfers):
        if not source_id or not dest_id or source_id == dest_id:
            return (
                html.Div(
                    "Select different source and destination warehouses to view suggestions.",
                    className="text-muted",
                ),
                [],
            )  # Return empty list for store

        try:
            # Use safe default values if not provided
            min_transfers = max(1, min_transfers or 1)
            max_transfers = max(min_transfers, max_transfers or 100)

            results = calculate_rebalance_suggestions(
                source_id, dest_id, min_transfers, max_transfers
            )

            if not results["suggestions"]:
                return (
                    html.Div(
                        "No viable transfers found with current parameters.",
                        className="text-warning",
                    ),
                    [],
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

            return (
                html.Div(
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
                                                "Schedule Transfer",
                                                id="schedule-transfers",
                                                color="primary",
                                                className="mt-3",
                                                n_clicks=0,  # Initialize with 0 clicks
                                            ),
                                            className="text-end",
                                        ),
                                    ]
                                ),
                            ]
                        ),
                    ]
                ),
                results["suggestions"],
            )

        except Exception as e:
            logger.error(f"Error generating rebalance suggestions: {e}")
            return (
                html.Div(
                    "Error generating suggestions. Please try again.",
                    className="text-danger",
                ),
                [],
            )

    @app.callback(
        [
            Output("kit-calculation-results", "children"),
            Output("kit-components-detail", "children"),
            Output("kit-calculation-results", "style"),
            Output("kit-components-detail", "style"),
        ],
        [Input("common-warehouse-selector", "value")],
    )
    def update_kit_calculations(warehouse_id):
        possible_kits = calculate_possible_kits(warehouse_id)
        kit_components = get_kit_components(warehouse_id)

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
                {"name": "Current Inventory", "id": "current_inventory"},
                {
                    "name": "Possible Completions",
                    "id": "possible_completions",
                    "type": "numeric",
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
                        "filter_query": "{possible_completions} > 0",
                        "column_id": "possible_completions",
                    },
                    "backgroundColor": "#e8f5e9",
                    "color": "#2e7d32",
                },
            ],
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
