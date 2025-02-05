from dash import Dash
import dash_bootstrap_components as dbc
from layout import create_layout
from callbacks import register_callbacks
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Get env variables
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Initialize the Dash app
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Include custom CSS
app.css.append_css({"external_url": "/assets/style.css"})

# Set the layout of the app
app.layout = create_layout()

# Register the callbacks
register_callbacks(app)

# Run the server
if __name__ == '__main__':
    app.run_server(debug=DEBUG)
