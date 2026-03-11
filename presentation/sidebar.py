"""
Sidebar Component - Main navigation and controls.
"""

from typing import Optional, Dict, Any, List, Callable
import streamlit as st
from datetime import datetime


def render_sidebar(
    analysis_service,
    on_new_analysis: Callable,
    on_select_analysis: Callable,
    on_settings_click: Callable,
) -> Optional[str]:
    """Render the main sidebar with three sections."""
    selected_analysis_id = None

    with st.sidebar:
        # TOP SECTION - Actions
        st.markdown("### 📁 Actions")
        col1, col2 = st.columns(2)

        with col1:
            if st.button("➕ New", use_container_width=True, type="primary"):
                on_new_analysis()

        with col2:
            if st.button("📂 Open", use_container_width=True):
                st.session_state.show_uploader = True

        st.markdown("---")

        # MIDDLE SECTION - History
        st.markdown("### 📜 History")
        history = analysis_service.get_analysis_history()

        if history:
            history.sort(key=lambda x: x.get("updated_at", ""), reverse=True)

            for item in history[:10]:
                analysis_id = item.get("id")
                name = item.get("name", "Unnamed")
                file_name = item.get("file_name", "No file")
                is_active = st.session_state.get("current_analysis_id") == analysis_id

                if st.button(
                    f"{'▶ ' if is_active else ''}{name}",
                    key=f"history_{analysis_id}",
                    use_container_width=True,
                    type="primary" if is_active else "secondary",
                ):
                    selected_analysis_id = analysis_id
                    on_select_analysis(analysis_id)

                st.caption(f"{file_name}")
        else:
            st.info("No analyses yet. Create a new analysis.")

        st.markdown("---")

        # BOTTOM SECTION - Settings
        st.markdown("### ⚙️ Settings")
        if st.button("⚙️ Settings", use_container_width=True):
            on_settings_click()

        settings = analysis_service.get_settings()
        auto_save = st.toggle("Auto-save", value=settings.get("auto_save", True))
        if auto_save != settings.get("auto_save"):
            analysis_service.update_settings({"auto_save": auto_save})

        st.caption("Dashboard Builder v1.0.0")

    return selected_analysis_id


def render_secondary_sidebar(
    data_schema: Optional[Any], on_add_visualization: Callable, visible: bool = True
) -> None:
    """Render secondary sidebar with visualization options."""
    if not visible or not data_schema:
        return

    with st.expander("📊 Add Visualization", expanded=True):
        from domain.entities import VisualizationType

        chart_types = [
            ("📊 Bar", VisualizationType.BAR_CHART),
            ("📈 Line", VisualizationType.LINE_CHART),
            ("🥧 Pie", VisualizationType.PIE_CHART),
            ("📉 Area", VisualizationType.AREA_CHART),
            ("⚬ Scatter", VisualizationType.SCATTER_PLOT),
            ("▊ Histogram", VisualizationType.HISTOGRAM),
            ("📋 Table", VisualizationType.TABLE),
            ("💳 Metric", VisualizationType.METRIC_CARD),
        ]

        cols = st.columns(3)
        for i, (label, viz_type) in enumerate(chart_types):
            with cols[i % 3]:
                if st.button(
                    label, key=f"add_{viz_type.value}", use_container_width=True
                ):
                    on_add_visualization(viz_type)


def render_file_uploader(on_upload: Callable) -> None:
    """Render file uploader dialog."""
    st.markdown("### 📂 Upload XLSX File")

    uploaded_file = st.file_uploader("Select an Excel file", type=["xlsx", "xls"])

    if uploaded_file is not None:
        if st.button("Load File", type="primary"):
            on_upload(uploaded_file)
            st.session_state.show_uploader = False
            st.rerun()
