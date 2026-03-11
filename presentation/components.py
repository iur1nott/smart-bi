"""
Components Module - Reusable UI components.
"""

from typing import Dict, Any, List, Optional, Callable
import streamlit as st
from datetime import datetime
import os


def render_settings_modal(current_settings: Dict[str, Any], on_save: Callable) -> None:
    """Render the settings modal/dialog."""
    st.markdown("## ⚙️ Settings")

    tab1, tab2, tab3 = st.tabs(["Appearance", "Export", "Data"])

    with tab1:
        st.markdown("### Appearance Settings")
        theme = st.selectbox(
            "Theme",
            ["light", "dark"],
            index=0 if current_settings.get("theme", "light") == "light" else 1,
        )
        grid_visible = st.checkbox(
            "Show Grid Lines", value=current_settings.get("grid_visible", True)
        )

    with tab2:
        st.markdown("### Export Settings")
        export_format = st.selectbox(
            "Default Export Format",
            ["pdf", "latex", "html"],
            index=["pdf", "latex", "html"].index(
                current_settings.get("export_format", "pdf")
            ),
        )
        paper_size = st.selectbox(
            "Paper Size",
            ["a4", "letter", "legal"],
            index=["a4", "letter", "legal"].index(
                current_settings.get("paper_size", "a4")
            ),
        )
        include_comments = st.checkbox(
            "Include Comments in Export",
            value=current_settings.get("include_comments", True),
        )

    with tab3:
        st.markdown("### Data Settings")
        auto_save = st.checkbox(
            "Auto-save Changes", value=current_settings.get("auto_save", True)
        )

    st.markdown("---")
    if st.button("💾 Save Settings", type="primary"):
        new_settings = {
            "theme": theme,
            "grid_visible": grid_visible,
            "export_format": export_format,
            "paper_size": paper_size,
            "include_comments": include_comments,
            "auto_save": auto_save,
        }
        on_save(new_settings)
        st.success("Settings saved!")


def render_analysis_history(
    analyses: List[Dict[str, Any]],
    on_select: Callable,
    on_delete: Callable,
    on_rename: Callable,
) -> None:
    """Render the analysis history list."""
    st.markdown("## 📜 Analysis History")

    if not analyses:
        st.info("No analyses yet. Create a new analysis to get started.")
        return

    for analysis in analyses:
        with st.container():
            col1, col2, col3 = st.columns([3, 1, 1])

            with col1:
                st.markdown(f"**{analysis.get('name', 'Unnamed')}**")
                st.caption(
                    f"📄 {analysis.get('file_name', 'No file')} | 📊 {analysis.get('slide_count', 0)} slides"
                )

                updated = analysis.get("updated_at", "")
                if updated:
                    try:
                        dt = datetime.fromisoformat(updated)
                        st.caption(f"Updated: {dt.strftime('%Y-%m-%d %H:%M')}")
                    except:
                        pass

            with col2:
                if st.button(
                    "📂 Open", key=f"open_{analysis['id']}", use_container_width=True
                ):
                    on_select(analysis["id"])

            with col3:
                if st.button(
                    "🗑️", key=f"delete_{analysis['id']}", help="Delete analysis"
                ):
                    on_delete(analysis["id"])
                    st.rerun()

            st.markdown("---")


def render_export_dialog(analysis, on_export: Callable) -> None:
    """Render the export dialog."""
    from domain.entities import Analysis
    from domain.value_objects import ExportOptions
    import base64

    st.markdown("## 📤 Export Analysis")
    st.markdown(f"**Analysis:** {analysis.name}")
    st.markdown(f"**Slides:** {len(analysis.slides)}")

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        export_format = st.selectbox(
            "Export Format", ["PDF", "LaTeX", "HTML"], help="Select the output format"
        )
        paper_size = st.selectbox("Paper Size", ["A4", "Letter", "Legal"])

    with col2:
        orientation = st.selectbox("Orientation", ["Portrait", "Landscape"])
        include_comments = st.checkbox("Include Comments", value=True)

    header_text = st.text_input(
        "Header Text (Optional)", placeholder="Enter header text..."
    )
    footer_text = st.text_input(
        "Footer Text (Optional)", placeholder="Enter footer text..."
    )

    st.markdown("---")

    if st.button("📤 Export", type="primary", use_container_width=True):
        with st.spinner("Generating export..."):
            export_options = {
                "format": export_format.lower(),
                "paper_size": paper_size.lower(),
                "orientation": orientation.lower(),
                "include_comments": include_comments,
                "header_text": header_text,
                "footer_text": footer_text,
            }
            result = on_export(analysis, export_options)

            if result:
                st.success(f"Export successful! File saved to: {result}")
                try:
                    with open(result, "rb") as f:
                        file_data = f.read()
                    st.download_button(
                        label="📥 Download File",
                        data=file_data,
                        file_name=os.path.basename(result),
                        mime="application/pdf"
                        if export_format.lower() == "pdf"
                        else "text/plain",
                    )
                except Exception as e:
                    st.error(f"Error reading file: {str(e)}")


def render_toolbar(
    current_slide_idx: int,
    total_slides: int,
    on_prev: Callable,
    on_next: Callable,
    on_add_slide: Callable,
    on_export: Callable,
) -> None:
    """Render the main toolbar."""
    col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])

    with col1:
        if st.button("⬅️", help="Previous Slide", disabled=current_slide_idx == 0):
            on_prev()

    with col2:
        st.markdown(
            f"<div style='text-align: center; padding-top: 8px;'>{current_slide_idx + 1} / {total_slides}</div>",
            unsafe_allow_html=True,
        )

    with col3:
        if st.button("➕ Add Slide", use_container_width=True):
            on_add_slide()

    with col4:
        if st.button(
            "➡️", help="Next Slide", disabled=current_slide_idx >= total_slides - 1
        ):
            on_next()

    with col5:
        if st.button("📤 Export", type="primary", use_container_width=True):
            on_export()


def render_welcome_screen(on_new_analysis: Callable) -> None:
    """Render the welcome screen for new users."""
    st.markdown(
        """
    <div style='text-align: center; padding: 50px;'>
        <h1 style='color: #2196F3;'>📊 Dashboard Builder</h1>
        <p style='font-size: 18px; color: #666;'>Create beautiful dashboards from your Excel data</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("### Get Started")

        if st.button("📁 Upload XLSX File", type="primary", use_container_width=True):
            on_new_analysis()

        st.markdown("---")

        st.markdown("""
        **Features:**
        - 📊 Multiple chart types (Bar, Line, Pie, Scatter, etc.)
        - 📋 Interactive tables
        - 📝 Add comments to visualizations
        - 📄 Export to PDF/LaTeX
        - 💾 Auto-save functionality
        """)


def render_notification(message: str, type: str = "info") -> None:
    """Render a notification message."""
    if type == "info":
        st.info(message)
    elif type == "success":
        st.success(message)
    elif type == "warning":
        st.warning(message)
    elif type == "error":
        st.error(message)


def render_confirmation_dialog(
    title: str, message: str, on_confirm: Callable, on_cancel: Callable
) -> None:
    """Render a confirmation dialog."""
    st.markdown(f"### {title}")
    st.markdown(message)

    col1, col2 = st.columns(2)

    with col1:
        if st.button("✓ Confirm", type="primary", use_container_width=True):
            on_confirm()

    with col2:
        if st.button("✗ Cancel", use_container_width=True):
            on_cancel()
