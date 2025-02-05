from dash import Input, Output, html, dash_table
import dash_bootstrap_components as dbc


def register_callbacks(app):
    @app.callback(
        Output("dashboard-content", "children"), [Input("tabs", "active_tab")]
    )
    def update_dashboard(active_tab):
        if active_tab == "home":
            return html.Div(
                [
                    # html.H2("Welcome to the Kit Readiness Dashboard", className="mb-4"),
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
            )
        ### Todo: Warehouse Inventory Tab

        elif active_tab == "tab-3":
            return "Dashboard content for Tab 3"
        return "Select a tab to see dashboard content"
