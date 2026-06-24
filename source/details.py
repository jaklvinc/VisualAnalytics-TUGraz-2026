import os
import streamlit as st


# --- Dialog for Postcard Preview ---
@st.dialog("Postcard Details", width="large")
def show_postcard_details(item):
    img_path = os.path.join("../Images", item['name'])
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