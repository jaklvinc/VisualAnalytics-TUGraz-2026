import os
import streamlit as st
from streamlit_extras.stylable_container import stylable_container

from details import show_postcard_details


def list_view(filtered_df):
    total_items = len(filtered_df)

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
                batch = page_df.iloc[i: i + cols_per_row]

                for j, (idx, item) in enumerate(batch.iterrows()):
                    img_path = os.path.join("../Images", item['name'])
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
                                st.image(img_path, width='stretch')
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
            if st.button("<<", disabled=(st.session_state.current_page <= 1), key="first", width='stretch'):
                st.session_state.current_page = 1
                st.rerun()
        with right:
            if st.button("<", disabled=(st.session_state.current_page <= 1), key="prev", width='stretch'):
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
            if st.button(">", disabled=(st.session_state.current_page >= total_pages), key="next", width='stretch'):
                st.session_state.current_page += 1
                st.rerun()
        with right:
            if st.button(">>", disabled=(st.session_state.current_page >= total_pages), key="last", width='stretch'):
                st.session_state.current_page = total_pages
                st.rerun()

    st.write(f"<p style='text-align: center; color: gray;'>Page {st.session_state.current_page} of {total_pages}</p>",
             unsafe_allow_html=True)
    pass