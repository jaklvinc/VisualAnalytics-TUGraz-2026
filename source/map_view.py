import os
import pandas as pd
import streamlit as st
import pydeck as pdk

def handle_map_selection():
    sel = st.session_state.map_selection
    # Ensure selection data is valid
    if not (sel and getattr(sel, "selection", None) and sel.selection.get("objects")):
        return

    objects = sel.selection["objects"]
    if objects.get("continent_arcs"):
        clicked_object = objects["continent_arcs"][0]
        origin = clicked_object["origin"]
        destination = clicked_object["destination"]

        st.session_state.selected_origin_continents = [origin]
        st.session_state.selected_receiving_continents = [destination]
        st.session_state.selected_origin_country = []
        st.session_state.selected_receiving_country = []
        st.session_state.current_page = 1
    elif objects.get("country_arcs"):
        clicked_object = objects["country_arcs"][0]
        origin = clicked_object["origin"]
        destination = clicked_object["destination"]

        st.session_state.selected_origin_continents = []
        st.session_state.selected_receiving_continents = []
        st.session_state.selected_origin_country = [origin]
        st.session_state.selected_receiving_country = [destination]
        st.session_state.current_page = 1

def map_view(df):
    # Check if any continent or country filter is currently active in the session state
    has_continent_filter = bool(st.session_state.get('selected_origin_continents', [])) or bool(st.session_state.get('selected_receiving_continents', []))
    has_country_filter = bool(st.session_state.get('selected_origin_country', [])) or bool(st.session_state.get('selected_receiving_country', []))
    
    view_mode = "Countries" if (has_continent_filter or has_country_filter) else "Continents"

    # --- Continent Paths ---
    continent_paths = df.groupby(['origin_continent', 'receiving_continent']).agg(
        count=('id', 'size'),
        origin_coord=('origin_continent_coord', 'first'),
        receiving_coord=('receiving_continent_coord', 'first')
    ).reset_index().rename(columns={
        'origin_continent': 'origin',
        'receiving_continent': 'destination'
    })
    continent_paths.dropna(subset=['origin_coord', 'receiving_coord'], inplace=True)
    continent_paths.sort_values(by='count', ascending=False, inplace=True)

    # --- Country Paths ---
    # Assuming 'origin_country_coord' and 'receiving_country_coord' exist in the dataframe
    country_paths = df.groupby(['origin_country', 'receiving_country']).agg(
        count=('id', 'size'),
        origin_coord=('origin_country_pos', 'first'),
        receiving_coord=('receiving_country_pos', 'first')
    ).reset_index().rename(columns={
        'origin_country': 'origin',
        'receiving_country': 'destination'
    })
    country_paths.dropna(subset=['origin_coord', 'receiving_coord'], inplace=True)
    country_paths.sort_values(by='count', ascending=False, inplace=True)

    if view_mode == "Countries" and not country_paths.empty:
        max_count = int(country_paths['count'].max())
        if max_count > 1:
            min_count = st.slider("Minimum postcards per path to display:", 1, max_count, 1)
            country_paths = country_paths[country_paths['count'] >= min_count]

    # --- Layer Definitions ---
    layers = []

    if view_mode == "Continents":
        if continent_paths.empty:
            st.warning("No continent paths to display for the selected filters.")
            return
            
        continent_arc_layer = pdk.Layer(
            "ArcLayer",
            data=continent_paths,
            id="continent_arcs",
            get_source_position="origin_coord",
            get_target_position="receiving_coord",
            get_source_color=[64, 255, 0, 160],  # Green for origin
            get_target_color=[255, 0, 64, 160],  # Red for destination
            get_width='count/50',  # Scale arc width by postcard count
            get_tilt=10,
            pickable=True,
            auto_highlight=True,
            widthMinPixels=2,
            numSegments=2
        )
        layers.append(continent_arc_layer)
    else:
        if country_paths.empty:
            st.warning("No country paths to display for the selected filters.")
            return
            
        country_arc_layer = pdk.Layer(
            "ArcLayer",
            data=country_paths,
            id="country_arcs",
            get_source_position="origin_coord",
            get_target_position="receiving_coord",
            get_source_color=[64, 255, 0, 160],  # Green for origin
            get_target_color=[255, 0, 64, 160],  # Red for destination
            get_width='count/5',
            get_tilt=10,
            pickable=True,
            auto_highlight=True,
            widthMinPixels=1,
            numSegments=2
        )
        layers.append(country_arc_layer)

        # --- Legend ---
    legend_html = """
    <div style="display: flex; justify-content: flex-start; gap: 20px; margin-bottom: 10px; font-family: sans-serif;">
        <div style="display: flex; align-items: center;">
            <div style="width: 16px; height: 16px; background-color: rgba(64, 255, 0, 0.6); border-radius: 50%; margin-right: 8px;"></div>
            <span><b>Origin</b> (Sending)</span>
        </div>
        <div style="display: flex; align-items: center;">
            <div style="width: 16px; height: 16px; background-color: rgba(255, 0, 64, 0.6); border-radius: 50%; margin-right: 8px;"></div>
            <span><b>Destination</b> (Receiving)</span>
        </div>
    </div>
    """
    st.markdown(legend_html, unsafe_allow_html=True)

    deck = pdk.Deck(
            map_style=None,  # Use Streamlit theme to pick map style
            initial_view_state=pdk.ViewState(
                latitude=20,
                longitude=0,
                zoom=1,
                pitch=0,
            ),
            layers=layers,
            tooltip={"html": "<b>{count}</b> postcards from {origin} to {destination}"}
        )

    st.pydeck_chart(
        deck, 
        use_container_width=True,
        on_select=handle_map_selection,
        selection_mode="single-object",
        key="map_selection"
    )