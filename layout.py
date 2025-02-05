import dash_bootstrap_components as dbc
from dash import html, dcc
import plotly.express as px


def create_layout():
    # Create a map
    fig = px.scatter_mapbox(
        lat=[37.0902], lon=[-95.7129], zoom=3, mapbox_style="carto-positron"
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
                                        label="Warehouse Inventory",
                                        tab_id="warehouse-inventory",
                                    ),
                                    dbc.Tab(label="Tab 3", tab_id="tab-3"),
                                ],
                                id="tabs",
                                active_tab="home",
                            ),
                            html.Div(id="dashboard-content"),
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
