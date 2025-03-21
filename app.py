from dash import Dash
import dash_bootstrap_components as dbc
from layout import create_layout
from callbacks import register_callbacks
from dotenv import load_dotenv
import os


# Load environment variables from .env file
load_dotenv()

# Get env variables
DEBUG = os.getenv("DEBUG", "False").lower() == "true"


# Initialize the Dash app
app = Dash(__name__, title="Kit Readiness Tool" external_stylesheets=[dbc.themes.BOOTSTRAP])

# Set layout
app.layout = create_layout()

# Register callbacks
register_callbacks(app)

# Run the server
if __name__ == "__main__":
    app.run_server(debug=DEBUG)
