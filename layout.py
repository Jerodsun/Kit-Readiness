import dash_bootstrap_components as dbc
from dash import html, dcc
import plotly.express as px
from database.connector import get_all_warehouses


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
        showlegend=False,
        paper_bgcolor="white",
        plot_bgcolor="white",
    )

    return html.Div(
        [
            html.Div(
                [
                    html.H1("Readiness Dashboard", className="header"),
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
                        style={"position": "absolute", "right": "20px", "top": "20px"},
                    ),
                ],
                style={"position": "relative", "width": "100%", "marginBottom": "20px"},
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
                                ],
                                id="tabs",
                                active_tab="home",
                            ),
                            html.Div(id="dashboard-content"),
                            # Add inventory management container to initial layout
                            html.Div(
                                [
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                [
                                                    html.Label("Select Warehouse:"),
                                                    dcc.Dropdown(
                                                        id="warehouse-selector",
                                                        className="mb-4",
                                                    ),
                                                ],
                                                width=6,
                                            ),
                                        ]
                                    ),
                                    html.Div(id="inventory-table-container"),
                                ],
                                id="inventory-management",
                                style={"display": "none"},
                            ),  # Hidden by default
                            # Add kit calculator containers
                            html.Div(id="kit-calculation-results"),
                            html.Div(id="kit-components-detail"),
                            html.Div(
                                [
                                    dcc.Dropdown(
                                        id="kit-calculator-warehouse", className="mb-4"
                                    ),
                                ],
                                id="kit-calculator-warehouse-selector",
                                style={"display": "none"},
                            ),
                        ],
                        className="left-column",
                    ),
                    # Right column (map)
                    html.Div(
                        [
                            dcc.Graph(
                                figure=fig, id="map-content", className="map-content"
                            )
                        ],
                        className="right-column",
                    ),
                ],
                className="main-content",
            ),
        ]
    )
