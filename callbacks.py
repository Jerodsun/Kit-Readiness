from dash.exceptions import PreventUpdate
import plotly.express as px

from callback_components.dashboard_callbacks import register_dashboard_callbacks
from callback_components.inventory_callbacks import register_inventory_callbacks
from callback_components.map_callbacks import register_map_callbacks
from callback_components.rebalance_callbacks import register_rebalance_callbacks
from callback_components.shipment_callbacks import register_shipment_callbacks
from callback_components.transfer_callbacks import register_transfer_callbacks
from callback_components.warehouse_callbacks import register_warehouse_callbacks


# register all callbacks
def register_callbacks(app):
    register_dashboard_callbacks(app)
    register_inventory_callbacks(app)
    register_map_callbacks(app)
    register_rebalance_callbacks(app)
    register_shipment_callbacks(app)
    register_transfer_callbacks(app)
    register_warehouse_callbacks(app)
