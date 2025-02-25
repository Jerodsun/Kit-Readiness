from dash import Input, Output
from database.connector import (
    get_all_warehouses,
    get_all_destinations,
)
import plotly.express as px
import logging

# Get logger
logger = logging.getLogger(__name__)


def register_map_callbacks(app):

    # Update map callback to use common selector
    @app.callback(
        Output("map-content", "figure"),
        [
            Input("source-warehouse", "value"),
            Input("destination-warehouse", "value"),
            Input("common-warehouse-selector", "value"),
        ],
    )
    def update_map_with_selections(source_id, dest_id, inventory_id):
        warehouses = get_all_warehouses()
        destinations = get_all_destinations()

        # Create base map
        fig = px.scatter_mapbox(
            lat=[w["latitude"] for w in warehouses]
            + [d["latitude"] for d in destinations],
            lon=[w["longitude"] for w in warehouses]
            + [d["longitude"] for d in destinations],
            hover_name=[w["warehouse_name"] for w in warehouses]
            + [d["destination_name"] for d in destinations],
            color=["Warehouse" for _ in warehouses]
            + ["Destination" for _ in destinations],
            color_discrete_map={"Warehouse": "#3072b4", "Destination": "#e67e22"},
            zoom=3,
            mapbox_style="carto-positron",
        )

        fig.update_layout(
            mapbox=dict(bearing=0, pitch=0),
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
            showlegend=True,
            paper_bgcolor="white",
            plot_bgcolor="white",
            legend_title_text="Legend",
            legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
        )

        # Handle rebalancing warehouse connections
        if source_id and dest_id:
            source = next(
                (w for w in warehouses if w["warehouse_id"] == source_id), None
            )
            dest = next((w for w in warehouses if w["warehouse_id"] == dest_id), None)

            if source and dest:
                # Add connection line
                fig.add_trace(
                    dict(
                        type="scattermapbox",
                        lon=[source["longitude"], dest["longitude"]],
                        lat=[source["latitude"], dest["latitude"]],
                        mode="lines",
                        line=dict(
                            width=2,
                            color="#3072b4",
                        ),
                        name="Transfer Route",
                        hoverinfo="skip",
                    )
                )

                # Add source and destination markers
                fig.add_trace(
                    dict(
                        type="scattermapbox",
                        lon=[source["longitude"]],
                        lat=[source["latitude"]],
                        mode="markers",
                        marker=dict(size=12, color="#e74c3c"),
                        name="Source Warehouse",
                        hovertext=f"Source: {source['warehouse_name']}",
                    )
                )

                fig.add_trace(
                    dict(
                        type="scattermapbox",
                        lon=[dest["longitude"]],
                        lat=[dest["latitude"]],
                        mode="markers",
                        marker=dict(size=12, color="#27ae60"),
                        name="Destination Warehouse",
                        hovertext=f"Destination: {dest['warehouse_name']}",
                    )
                )

        # Handle inventory warehouse selection
        if inventory_id:
            selected = next(
                (w for w in warehouses if w["warehouse_id"] == inventory_id), None
            )
            if selected:
                # Add selection markers with proper names
                fig.add_trace(
                    dict(
                        type="scattermapbox",
                        lon=[selected["longitude"]],
                        lat=[selected["latitude"]],
                        mode="markers",
                        marker=dict(
                            size=25, color="rgba(48, 114, 180, 0.3)", symbol="circle"
                        ),
                        name="Selection Highlight",
                        hoverinfo="skip",
                        showlegend=False,
                    )
                )
                fig.add_trace(
                    dict(
                        type="scattermapbox",
                        lon=[selected["longitude"]],
                        lat=[selected["latitude"]],
                        mode="markers",
                        marker=dict(size=8, color="#3072b4"),
                        name="Active Warehouse",
                        hovertext=f"Selected: {selected['warehouse_name']}",
                    )
                )

        return fig
