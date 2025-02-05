import dash_bootstrap_components as dbc
from dash import html
import dash_bootstrap_components as dbc


def create_layout():
    return html.Div(
        [
            html.H1("Readiness Dashboard", className="header"),
            html.Div(
                [
                    # Left column
                    html.Div(
                        [
                            dbc.Tabs(
                                [
                                    dbc.Tab(label="Home", tab_id="home"),
                                    dbc.Tab(
                                        label="Warehouse Inventory",
                                        tab_id="warehouse-inventory",
                                    ),
                                    dbc.Tab(
                                        label="Warehouse Health",
                                        tab_id="warehouse-health",
                                    ),
                                    dbc.Tab(label="Tab 3", tab_id="tab-3"),
                                ],
                                id="tabs",
                                active_tab="home",
                            ),
                            # ...rest of existing layout...
                        ],
                        className="left-column",
                    ),
                    # Right column
                    html.Div(id="dashboard-content", className="right-column"),
                ],
                className="main-content",
            ),
            html.Div(id="inventory-management", style={"display": "none"}),
        ]
    )


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
            html.H1("Readiness Dashboard", className="header"),
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
                                    dbc.Tab(label="Tab 3", tab_id="tab-3"),
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
