import os
import pandas as pd
import streamlit as st
import pydeck as pdk

def handle_map_selection():
    sel = st.session_state.map_selection
    if sel and getattr(sel, "selection", None) and sel.selection.get("objects") and sel.selection["objects"].get("arcs"):
        clicked_object = sel.selection["objects"]["arcs"][0]
        origin = clicked_object["origin_continent"]
        receiving = clicked_object["receiving_continent"]

        st.session_state.selected_origin_continents = [origin]
        st.session_state.selected_receiving_continents = [receiving]
        st.session_state.selected_origin_country = []
        st.session_state.selected_receiving_country = []
        st.session_state.current_page = 1

def map_view(df):
    # Aggregate postcard counts and coordinates between continents
    path_counts = df.groupby(['origin_continent', 'receiving_continent']).agg(
        count=('id', 'size'),
        origin_continent_coord=('origin_continent_coord', 'first'),
        receiving_continent_coord=('receiving_continent_coord', 'first')
    ).reset_index()

    # Drop rows where coordinates might be missing
    path_counts.dropna(subset=['origin_continent_coord', 'receiving_continent_coord'], inplace=True)

    if path_counts.empty:
        st.warning("No postcard paths to display for the selected filters.")
        return

    # Define the ArcLayer
    arc_layer = pdk.Layer(
        "ArcLayer",
        data=path_counts,
        id="arcs",
        get_source_position="origin_continent_coord",
        get_target_position="receiving_continent_coord",
        get_source_color=[64, 255, 0, 160],  # Green for origin
        get_target_color=[255, 0, 64, 160],  # Red for destination
        get_width='count / 50',  # Scale arc width by postcard count
        pickable=True,
        auto_highlight=True,
    )

    deck = pdk.Deck(
            map_style=None,  # Use Streamlit theme to pick map style
            initial_view_state=pdk.ViewState(
                latitude=20,
                longitude=0,
                zoom=1,
                pitch=45,
            ),
            layers=[arc_layer],
            tooltip={"html": "<b>{count}</b> postcards from {origin_continent} to {receiving_continent}"}
        )

    st.pydeck_chart(
        deck, 
        use_container_width=True,
        on_select=handle_map_selection,
        selection_mode="single-object",
        key="map_selection"
    )