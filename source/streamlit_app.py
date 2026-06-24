import streamlit as st
import json
import os
import pandas as pd
import torch
import numpy as np
from transformers import CLIPProcessor, CLIPModel
from streamlit_extras.card_selector import *

from list_view import list_view
from map_view import map_view
from cluster_view import cluster_view

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
# Initialize session state for filters
if 'selected_origin_continents' not in st.session_state:
    st.session_state.selected_origin_continents = []
if 'selected_receiving_continents' not in st.session_state:
    st.session_state.selected_receiving_continents = []
if 'selected_origin_country' not in st.session_state:
    st.session_state.selected_origin_country = []
if 'selected_receiving_country' not in st.session_state:
    st.session_state.selected_receiving_country = []

@st.cache_resource
def load_clip_model():
    # Load model and processor matching your generation script
    processor = CLIPProcessor.from_pretrained('openai/clip-vit-base-patch32')
    model = CLIPModel.from_pretrained('openai/clip-vit-base-patch32')
    model.eval()
    return processor, model


def filter_by_semantic_search(df, query, threshold=0.23):
    if not query:
        return df

    processor, model = load_clip_model()

    # Vectorize the text query
    inputs = processor(text=[query], return_tensors="pt", padding=True)
    with torch.no_grad():
        outputs = model.get_text_features(**inputs)

    if hasattr(outputs, 'text_embeds'):
        features = outputs.text_embeds
    elif hasattr(outputs, 'pooler_output'):
        features = outputs.pooler_output
    else:
        features = outputs

    text_vector = features.squeeze().cpu().numpy()
    text_vector /= np.linalg.norm(text_vector)

    # Calculate similarity scores
    scores = []
    for emb in df['embedding']:
        if emb is not None:
            emb_arr = np.array(emb)
            emb_norm = np.linalg.norm(emb_arr)
            if emb_norm > 0:
                score = np.dot(text_vector, emb_arr) / emb_norm
                scores.append(score)
                continue
        scores.append(-1.0)

    df = df.copy()
    df['search_score'] = scores

    # FILTER BY THRESHOLD INSTEAD OF TOP N
    filtered = df[df['search_score'] >= threshold].sort_values(by='search_score', ascending=False)

    return filtered

# Load data
@st.cache_data
def load_data():
    with open('../data/data_with__geography_embeddings.json', 'r') as f:
        data = json.load(f)
    return pd.DataFrame(data)

df = load_data()
df['date_sent'] = pd.to_datetime(df['date_sent'])
df['date_received'] = pd.to_datetime(df['date_received'])

# --- Sidebar Filters ---
st.sidebar.title("🔍 Filters")

search_query = st.sidebar.text_input(
    "Semantic Image Search",
    placeholder="e.g., mountain sunset, city lights...",
    help="Uses CLIP embeddings to search the visual content of the postcards."
)

with st.sidebar.expander("Location", expanded=True):
    continents = sorted(df['origin_continent'].unique())
    st.multiselect("Origin Continent", continents, key='selected_origin_continents')

    if st.session_state.selected_origin_continents:
        origin_countries = sorted(df[df['origin_continent'].isin(st.session_state.selected_origin_continents)]['origin_country'].unique())
        st.multiselect("Origin Country", origin_countries, key='selected_origin_country')
    else:
        st.session_state.selected_origin_country = []

    st.divider()

    st.multiselect("Receiving Continent", continents, key='selected_receiving_continents')

    if st.session_state.selected_receiving_continents:
        receiving_countries = sorted(df[df['receiving_continent'].isin(st.session_state.selected_receiving_continents)]['receiving_country'].unique())
        st.multiselect("Receiving Country", receiving_countries, key='selected_receiving_country')
    else:
        st.session_state.selected_receiving_country = []

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
if st.session_state.selected_origin_continents:
    filtered_df = filtered_df[filtered_df['origin_continent'].isin(st.session_state.selected_origin_continents)]
if st.session_state.selected_origin_country:
    filtered_df = filtered_df[filtered_df['origin_country'].isin(st.session_state.selected_origin_country)]
if st.session_state.selected_receiving_continents:
    filtered_df = filtered_df[filtered_df['receiving_continent'].isin(st.session_state.selected_receiving_continents)]
if st.session_state.selected_receiving_country:
    filtered_df = filtered_df[filtered_df['receiving_country'].isin(st.session_state.selected_receiving_country)]
filtered_df = filtered_df[(filtered_df['distance'] >= dist_range[0]) & (filtered_df['distance'] <= dist_range[1])]

# Apply date filters (only if range selection is complete)
if isinstance(sent_range, (list, tuple)) and len(sent_range) == 2:
    filtered_df = filtered_df[(filtered_df['date_sent'].dt.date >= sent_range[0]) & (filtered_df['date_sent'].dt.date <= sent_range[1])]
if isinstance(received_range, (list, tuple)) and len(received_range) == 2:
    filtered_df = filtered_df[(filtered_df['date_received'].dt.date >= received_range[0]) & (filtered_df['date_received'].dt.date <= received_range[1])]
if search_query:
    filtered_df = filter_by_semantic_search(filtered_df, search_query)

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
elif selected == 1:
    cluster_view(filtered_df)
elif selected == 2:
    map_view(filtered_df)
