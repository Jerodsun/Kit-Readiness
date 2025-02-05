from dash import Dash
import dash_bootstrap_components as dbc
from layout import create_layout
from callbacks import register_callbacks
from dotenv import load_dotenv
import os
import logging

# Load environment variables from .env file
load_dotenv()

# Get env variables
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# Configure logging
if DEBUG:
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
else:
    # Disable all logging including Werkzeug
    logging.basicConfig(level=logging.ERROR)
    logging.getLogger().disabled = True
    # Disable Flask logging
    flask_logger = logging.getLogger("werkzeug")
    flask_logger.disabled = True

# Initialize logger
logger = logging.getLogger(__name__)
logger.info("Starting Kit Readiness Dashboard")

# Initialize the Dash app
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.server.logger.disabled = True

# Set layout
app.layout = create_layout()

# Register callbacks
register_callbacks(app)

# Run the server
if __name__ == "__main__":
    app.run_server(debug=DEBUG, dev_tools_silence_routes_logging=True)
