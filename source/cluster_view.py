import streamlit as st
import numpy as np
import os
from sklearn.cluster import AgglomerativeClustering
from sklearn.decomposition import PCA


# --- Callbacks for guaranteed state accuracy ---
def navigate_down(cluster_ids):
    """Callback to drill down into a specific cluster's IDs."""
    st.session_state.cluster_history.append(cluster_ids)


def navigate_up(level_idx):
    """Callback to navigate back up the breadcrumb trail."""
    if level_idx == -1:
        st.session_state.cluster_history = []
    else:
        st.session_state.cluster_history = st.session_state.cluster_history[:level_idx + 1]


def cluster_view(df):
    st.subheader("📁 Postcard Topic Clusters")
    st.write("Click on a visual cluster to drill down into deeper sub-themes.")

    # --- 1. Guard rail check ---
    valid_df = df[df['embedding'].notna()].copy()
    if valid_df.empty:
        st.warning("No postcard embeddings found to generate clusters.")
        return

    # --- 2. Filter Change Detection ---
    current_filter_hash = hash(tuple(valid_df['id'].tolist()))
    if st.session_state.get('last_filter_hash') != current_filter_hash:
        st.session_state.last_filter_hash = current_filter_hash
        st.session_state.cluster_history = []

    if 'cluster_history' not in st.session_state:
        st.session_state.cluster_history = []

    # --- 3. Breadcrumb Navigation ---
    if st.session_state.cluster_history:
        cols = st.columns(len(st.session_state.cluster_history) + 1)

        # Using on_click for immediate state updates
        cols[0].button("🏠 Main Collections", key="btn_home", on_click=navigate_up, args=(-1,))

        for idx, history_node in enumerate(st.session_state.cluster_history):
            cols[idx + 1].button(f"📂 Level {idx + 1}", key=f"btn_lvl_{idx}", on_click=navigate_up, args=(idx,))
        st.divider()

    # --- 4. Isolate the Current Subset ---
    if st.session_state.cluster_history:
        active_ids = st.session_state.cluster_history[-1]
        current_df = valid_df[valid_df['id'].isin(active_ids)].copy()
    else:
        current_df = valid_df.copy()

    total_items = len(current_df)
    depth = len(st.session_state.cluster_history)

    # --- 5. Render Leaf Nodes (Increased cutoff to 10) ---
    if total_items <= 10 or depth >= 4:
        st.info(f"📍 Showing final selection list ({total_items} postcards)")

        grid_cols = st.columns(3)
        for idx, (_, row) in enumerate(current_df.iterrows()):
            with grid_cols[idx % 3]:
                img_path = os.path.join("../Images", row['name'])
                if os.path.exists(img_path):
                    st.image(img_path, use_container_width=True)
                st.caption(f"**ID:** {row['id']} | **From:** {row['origin_country']}")
        return

    # --- 6. Hierarchical Clustering ---
    X = np.stack(current_df['embedding'].values)

    n_components = min(32, X.shape[1], total_items)
    pca = PCA(n_components=n_components)
    X_reduced = pca.fit_transform(X)

    dynamic_threshold = max(0.5, 1.4 - (depth * 0.25))

    clusterer = AgglomerativeClustering(
        n_clusters=None,
        distance_threshold=dynamic_threshold,
        metric='euclidean',
        linkage='ward'
    )
    cluster_labels = clusterer.fit_predict(X_reduced)

    current_df['next_branch_id'] = cluster_labels
    unique_clusters = sorted(current_df['next_branch_id'].unique())

    # UI SAFETY FALLBACK
    if len(unique_clusters) > 12 or (len(unique_clusters) == 1 and total_items > 10):
        fallback_clusters = min(12, max(2, int(np.sqrt(total_items))))

        clusterer = AgglomerativeClustering(n_clusters=fallback_clusters, metric='euclidean', linkage='ward')
        cluster_labels = clusterer.fit_predict(X_reduced)
        current_df['next_branch_id'] = cluster_labels
        unique_clusters = sorted(current_df['next_branch_id'].unique())

    st.write(f"### Choose a visual theme (Found {len(unique_clusters)} groups):")

    cols = st.columns(min(4, max(1, len(unique_clusters))))

    for i, c_id in enumerate(unique_clusters):
        sub_group = current_df[current_df['next_branch_id'] == c_id]
        group_count = len(sub_group)

        with cols[i % len(cols)]:
            with st.container(border=True):
                st.markdown(f"**Group {i + 1}**  \n*{group_count} postcards*")

                preview_samples = sub_group.head(4)
                preview_chunks = [preview_samples.iloc[j:j + 2] for j in range(0, len(preview_samples), 2)]

                for chunk in preview_chunks:
                    p_cols = st.columns(2)
                    for k, (_, row) in enumerate(chunk.iterrows()):
                        img_path = os.path.join("../Images", row['name'])
                        if os.path.exists(img_path):
                            p_cols[k].image(img_path, use_container_width=True)

                btn_key = f"btn_explore_lvl{depth}_c{c_id}"

                # --- The Fix: Using on_click to pass exact IDs before script reruns ---
                st.button(
                    "Explore Group",
                    key=btn_key,
                    use_container_width=True,
                    on_click=navigate_down,
                    args=(sub_group['id'].tolist(),)
                )