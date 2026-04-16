import streamlit as st
import json
import os
import pandas as pd
from streamlit_extras.card_selector import *

from list_view import list_view
from map_view import map_view

# Page configuration
st.set_page_config(page_title="Postcard Viewer", layout="wide")

st.markdown(
    """
<style>
    div[data-testid="st-key-custom_img"] img{
        border: 1px solid red;
    }
</style>
""",
    unsafe_allow_html=True,
)


# Initialize session state for pagination
if 'current_page' not in st.session_state:
    st.session_state.current_page = 1

# Load data
@st.cache_data
def load_data():
    with open('../data/data_with_geography.json', 'r') as f:
        data = json.load(f)
    return pd.DataFrame(data)

df = load_data()
df['date_sent'] = pd.to_datetime(df['date_sent'])
df['date_received'] = pd.to_datetime(df['date_received'])

# --- Sidebar Filters ---
st.sidebar.title("🔍 Filters")

with st.sidebar.expander("Location", expanded=True):
    origin_countries = sorted(df['origin_country'].unique())
    selected_origin = st.multiselect("Origin Country", origin_countries)

    receiving_countries = sorted(df['receiving_country'].unique())
    selected_receiving = st.multiselect("Receiving Country", receiving_countries)

with st.sidebar.expander("Distance",expanded=True):
    min_dist, max_dist = int(df['distance'].min()), int(df['distance'].max())
    dist_range = st.slider("Distance (km)", min_dist, max_dist, (min_dist, max_dist))

with st.sidebar.expander("Dates", expanded=True):
    sent_min, sent_max = df['date_sent'].min().date(), df['date_sent'].max().date()
    received_min, received_max = df['date_received'].min().date(), df['date_received'].max().date()

    st.write("**Sent**")
    sent_range = st.date_input("Sent Range", value=(sent_min, sent_max), min_value=sent_min, max_value=sent_max, label_visibility="collapsed")
    
    st.write("**Received**")
    received_range = st.date_input("Received Range", value=(received_min, received_max), min_value=received_min, max_value=received_max, label_visibility="collapsed")


# Apply filters
filtered_df = df.copy()
if selected_origin:
    filtered_df = filtered_df[filtered_df['origin_country'].isin(selected_origin)]
if selected_receiving:
    filtered_df = filtered_df[filtered_df['receiving_country'].isin(selected_receiving)]
filtered_df = filtered_df[(filtered_df['distance'] >= dist_range[0]) & (filtered_df['distance'] <= dist_range[1])]

# Apply date filters (only if range selection is complete)
if isinstance(sent_range, (list, tuple)) and len(sent_range) == 2:
    filtered_df = filtered_df[(filtered_df['date_sent'].dt.date >= sent_range[0]) & (filtered_df['date_sent'].dt.date <= sent_range[1])]
if isinstance(received_range, (list, tuple)) and len(received_range) == 2:
    filtered_df = filtered_df[(filtered_df['date_received'].dt.date >= received_range[0]) & (filtered_df['date_received'].dt.date <= received_range[1])]

# --- Main Area ---
st.title("📮 Postcard Collection")

selected = card_selector(
    [
        dict(
            icon=":material/list:",
            title="List",
            description="Displays the postacrs in a simple list view",
        ),
        dict(
            icon=":material/view_comfy_alt:",
            title="Cluster",
            description="Displays the postcards in clusters based on topics",
        ),
        dict(
            icon=":material/map:",
            title="Map",
            description="Displays the postcards paths on a map",
        ),
    ],
    key="demo_basic",
)

if selected == 0:
    list_view(filtered_df)
elif selected == 2:
    map_view(filtered_df)


