import os
import streamlit as st
import pydeck as pdk

def map_view(df):

    

    map = st.pydeck_chart(pdk.Deck(
            map_style=None,  # Use Streamlit theme to pick map style
            initial_view_state=pdk.ViewState(
                latitude=37.76,
                longitude=-122.4,
                zoom=2,
                pitch=30,
            ),
            layers=[
                pdk.Layer(
                    "HexagonLayer",
                    data=df,
                    get_position="[lon, lat]",
                    radius=200,
                    elevation_scale=4,
                    elevation_range=[0, 1000],
                    pickable=True,
                    extruded=True,
                ),
                pdk.Layer(
                    "ScatterplotLayer",
                    data=df,
                    get_position="[lon, lat]",
                    get_color="[200, 30, 0, 160]",
                    get_radius=200,
                ),
            ],
        )
    )