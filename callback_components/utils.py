from dash import html
import dash_bootstrap_components as dbc


def create_health_card(title, value, color="success"):
    return dbc.Card(
        dbc.CardBody(
            [
                html.H4(title, className="card-title"),
                html.H2(value, className=f"text-{color}"),
            ]
        ),
        className="mb-4",
    )
