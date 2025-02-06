import dash_bootstrap_components as dbc
from dash import html, dcc, dash_table
import plotly.express as px
from database.connector import get_all_warehouses
from datetime import date


### This creates the initial layout
def create_layout():
    # Get warehouse data
    warehouses = get_all_warehouses()

    # Create map
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
        showlegend=True,
        paper_bgcolor="white",
        plot_bgcolor="white",
    )

    return html.Div(
        [
            html.Div(
                [
                    html.H1("Inventory Readiness Dashboard", className="header"),
                    html.A(
                        dbc.Button(
                            "Help 📖",
                            id="help-button",
                            color="secondary",
                            size="sm",
                            className="ms-2",
                        ),
                        href="/assets/documentation.pdf",
                        target="_blank",
                    ),
                ],
                className="header",
            ),
            html.Div(
                [
                    # Left column
                    html.Div(
                        [
                            dbc.Tabs(
                                [
                                    dbc.Tab(label="Home", tab_id="home"),
                                    dbc.Tab(
                                        label="Warehouse Health",
                                        tab_id="warehouse-health",
                                    ),
                                    dbc.Tab(
                                        label="Warehouse Inventory",
                                        tab_id="warehouse-inventory",
                                    ),
                                    dbc.Tab(
                                        label="Kit Calculator",
                                        tab_id="kit-calculator",
                                    ),
                                    dbc.Tab(
                                        label="Rebalance Warehouses",
                                        tab_id="rebalance-warehouses",
                                    ),
                                    dbc.Tab(
                                        label="Scheduled Transfers",
                                        tab_id="scheduled-transfers",
                                    ),
                                    dbc.Tab(
                                        label="Scheduled Shipments",
                                        tab_id="scheduled-shipments",
                                    ),
                                ],
                                id="tabs",
                                active_tab="home",
                            ),
                            html.Div(id="dashboard-content"),
                            # Add inventory management container to initial layout
                            html.Div(
                                [
                                    html.Div(
                                        dash_table.DataTable(
                                            id="inventory-table",
                                            columns=[
                                                {
                                                    "name": "Component",
                                                    "id": "component_name",
                                                    "editable": False,
                                                },
                                                {
                                                    "name": "Description",
                                                    "id": "description",
                                                    "editable": False,
                                                },
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
                                            data=[],
                                            style_table={"overflowX": "auto"},
                                        ),
                                        id="inventory-table-container",
                                    ),
                                    dbc.Button(
                                        "Save Changes",
                                        id="save-inventory",
                                        color="primary",
                                        className="mt-3",
                                        style={"display": "none"},  # Hidden by default
                                    ),
                                    html.Div(id="save-status", className="mt-2"),
                                ],
                                id="inventory-management",
                                style={"display": "none"},
                            ),  # Hidden by default
                            # Add kit calculator containers with display: none by default
                            html.Div(
                                [
                                    html.Div(id="kit-calculation-results"),
                                    html.Div(id="kit-components-detail"),
                                ],
                                id="kit-calculator-container",
                                style={"display": "none"},  # Hidden by default
                            ),
                            # Add rebalancing container
                            html.Div(
                                [
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                [
                                                    html.Label("Source Warehouse:"),
                                                    dcc.Dropdown(
                                                        id="source-warehouse",
                                                        className="mb-4",
                                                    ),
                                                ],
                                                width=5,
                                            ),
                                            dbc.Col(
                                                dbc.Button(
                                                    "⇄",
                                                    id="swap-warehouses-button",
                                                    color="primary",
                                                    className="mb-4",
                                                    style={"width": "50px"},
                                                ),
                                                width=2,
                                                className="d-flex align-items-end justify-content-center",
                                                style={"width": "80px"},
                                            ),
                                            dbc.Col(
                                                [
                                                    html.Label(
                                                        "Destination Warehouse:"
                                                    ),
                                                    dcc.Dropdown(
                                                        id="destination-warehouse",
                                                        className="mb-4",
                                                    ),
                                                ],
                                                width=5,
                                            ),
                                        ],
                                        className="d-flex align-items-end justify-content-center",
                                    ),
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                [
                                                    html.Label(
                                                        "Minimum Transfer Quantity:"
                                                    ),
                                                    dcc.Input(
                                                        id="min-transfers",
                                                        type="number",
                                                        min=1,
                                                        value=1,
                                                        className="form-control mb-4",
                                                    ),
                                                ],
                                                width=2,
                                            ),
                                            dbc.Col(
                                                [
                                                    html.Label(
                                                        "Maximum Transfer Quantity:"
                                                    ),
                                                    dcc.Input(
                                                        id="max-transfers",
                                                        type="number",
                                                        min=1,
                                                        value=100,
                                                        className="form-control mb-4",
                                                    ),
                                                ],
                                                width=2,
                                            ),
                                        ],
                                        className="d-flex align-items-end justify-content-center",
                                    ),
                                    html.Div(id="rebalance-suggestions"),
                                    html.Div(id="transfer-form"),
                                    # Add Store for suggestions data
                                    dcc.Store(id="suggestions-store"),
                                    # Add blank hidden components to satisfy callback requirements
                                    html.Div(
                                        dcc.Dropdown(id="transfer-component-selector"),
                                        style={"display": "none"},
                                    ),
                                    html.Div(
                                        dbc.Input(
                                            id="transfer-quantity", type="number"
                                        ),
                                        style={"display": "none"},
                                    ),
                                    html.Div(
                                        dbc.Button(id="schedule-transfers", n_clicks=0),
                                        style={"display": "none"},
                                    ),
                                    # Add transfer modal
                                    dbc.Modal(
                                        [
                                            dbc.ModalHeader("Schedule Transfer"),
                                            dbc.ModalBody(
                                                [
                                                    dbc.Form(
                                                        [
                                                            dbc.Row(
                                                                [
                                                                    dbc.Col(
                                                                        [
                                                                            html.Label(
                                                                                "Shipment Date:"
                                                                            ),
                                                                            dcc.DatePickerSingle(
                                                                                id="shipment-date",
                                                                                min_date_allowed=date.today(),
                                                                                date=date.today(),
                                                                                className="mb-3",
                                                                            ),
                                                                        ]
                                                                    )
                                                                ]
                                                            ),
                                                            html.Div(
                                                                id="transfer-kit-selector"
                                                            ),
                                                            html.Div(
                                                                id="transfer-quantity-input"
                                                            ),
                                                            html.Div(
                                                                id="transfer-message",
                                                                className="mt-3",
                                                            ),
                                                        ]
                                                    )
                                                ]
                                            ),
                                            dbc.ModalFooter(
                                                [
                                                    dbc.Button(
                                                        "Cancel",
                                                        id="cancel-transfer",
                                                        className="me-2",
                                                    ),
                                                    dbc.Button(
                                                        "Confirm Transfer",
                                                        id="confirm-transfer",
                                                        color="primary",
                                                    ),
                                                ]
                                            ),
                                        ],
                                        id="transfer-modal",
                                        is_open=False,
                                    ),
                                ],
                                id="rebalance-container",
                                style={"display": "none"},
                            ),
                        ],
                        className="left-column",
                    ),
                    # Right column (map)
                    html.Div(
                        [
                            dbc.Card(
                                dbc.CardBody(
                                    [
                                        html.Label(
                                            "Active Warehouse:",
                                            className="mb-2 fw-bold",
                                        ),
                                        dcc.Dropdown(
                                            id="common-warehouse-selector",
                                            className="mb-2",
                                        ),
                                    ]
                                ),
                                className="mb-4 mt-3",
                            ),
                            html.Div(
                                dcc.Graph(
                                    figure=fig,
                                    id="map-content",
                                    className="map-content",
                                ),
                                className="map-container",
                            ),
                        ],
                        className="right-column",
                    ),
                ],
                className="main-content",
            ),
        ]
    )
