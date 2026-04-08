import streamlit as st
import json
import os
import pandas as pd
from streamlit_extras.stylable_container import stylable_container

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
    with open('data.json', 'r') as f:
        data = json.load(f)
    return pd.DataFrame(data)

df = load_data()
df['date_sent'] = pd.to_datetime(df['date_sent'])
df['date_received'] = pd.to_datetime(df['date_received'])

# --- Dialog for Postcard Preview ---
@st.dialog("Postcard Details", width="large")
def show_postcard_details(item):
    img_path = os.path.join("Images", item['name'])
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if os.path.exists(img_path):
            st.image(img_path, width='stretch')
        else:
            st.error("Image file not found.")
            
    with col2:
        st.subheader(f"ID: {item['id']}")
        st.divider()
        st.write(f"**From:** {item['origin_country']}")
        st.write(f"**To:** {item['receiving_country']}")
        st.write(f"**Distance:** {item['distance']} km")
        st.write(f"**Sent:** {item['date_sent'].date().strftime('%d.%m.%Y')}")
        st.write(f"**Received:** {item['date_received'].date().strftime('%d.%m.%Y')}")
        if 'origin_region' in item:
            st.write(f"**Region:** {item['origin_region']}")

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
total_items = len(filtered_df)

st.title("📮 Postcard Collection")
st.write(f"Showing **{total_items}** postcards.")

items_per_page = st.radio("Items per page", options=[12, 24, 48, 96], index=1, horizontal=True)

total_pages = (total_items - 1) // items_per_page + 1 if total_items > 0 else 1

if st.session_state.current_page > total_pages:
    st.session_state.current_page = 1

start_idx = (st.session_state.current_page - 1) * items_per_page
end_idx = start_idx + items_per_page
page_df = filtered_df.iloc[start_idx:end_idx]

# Scrollable Window
with st.container(height=700, border=True):
    if page_df.empty:
        st.info("No postcards match the selected filters.")
    else:
        # We use a grid layout. Streamlit columns will normalize the width.
        cols_per_row = 4
        for i in range(0, len(page_df), cols_per_row):
            cols = st.columns(cols_per_row)
            batch = page_df.iloc[i : i + cols_per_row]
            
            for j, (idx, item) in enumerate(batch.iterrows()):
                img_path = os.path.join("Images", item['name'])
                with cols[j]:
                    if os.path.exists(img_path):
                        # Show the image with uniform height
                        with stylable_container(
                                key=f"custom_style_{img_path}",
                                css_styles="""
                                img {
                                    width: 100%;
                                    height: 200px;
                                    object-fit: fill;
                                    padding : 5px;
                                    border-radius: 10px;
                                }
                                
                            """
                        ):
                            st.image(img_path,width='stretch')
                        # Restore the visible button
                        if st.button(f"View {item['id']}", key=f"btn_{item['id']}", width='stretch'):
                            show_postcard_details(item)
                    else:
                        st.error(f"Missing: {item['name']}")

# --- Bottom Pagination UI ---
st.divider()
pg_cols = st.columns([1, 1, 6, 1, 1])

with pg_cols[1]:
    left, right = st.columns(2)
    with left:
        if st.button("<<", disabled=(st.session_state.current_page <= 1), key="first",width='stretch'):
            st.session_state.current_page = 1
            st.rerun()
    with right:
        if st.button("<", disabled=(st.session_state.current_page <= 1), key="prev",width='stretch'):
            st.session_state.current_page -= 1
            st.rerun()

with pg_cols[2]:
    # Show a subset of page numbers for cleaner UI
    max_visible = 7
    half = max_visible // 2
    start_pg = max(1, st.session_state.current_page - half)
    end_pg = min(total_pages, start_pg + max_visible - 1)
    if end_pg - start_pg < max_visible - 1:
        start_pg = max(1, end_pg - max_visible + 1)
    
    num_cols = st.columns(end_pg - start_pg + 1)
    for idx, p in enumerate(range(start_pg, end_pg + 1)):
        # Primary style for the current page
        btn_type = "primary" if p == st.session_state.current_page else "secondary"
        if num_cols[idx].button(str(p), key=f"pg_{p}", width='stretch', type=btn_type):
            st.session_state.current_page = p
            st.rerun()

with pg_cols[3]:
    left, right = st.columns(2)
    with left:
        if st.button(">", disabled=(st.session_state.current_page >= total_pages), key="next",width='stretch'):
            st.session_state.current_page += 1
            st.rerun()
    with right:
        if st.button(">>", disabled=(st.session_state.current_page >= total_pages), key="last",width='stretch'):
            st.session_state.current_page = total_pages
            st.rerun()

st.write(f"<p style='text-align: center; color: gray;'>Page {st.session_state.current_page} of {total_pages}</p>", unsafe_allow_html=True)
