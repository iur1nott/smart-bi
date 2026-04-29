"""
Sidebar Component - Main navigation sidebar with dashboard management.
Updated for new schema with dashboards instead of analyses.
"""

from datetime import datetime
from typing import Any, Callable, List, Optional

import streamlit as st

from domain.entities import Dashboard


def render_main_sidebar(
    user_id: str,
    dashboards: List[Dashboard],
    current_dashboard_id: Optional[str],
    on_new_dashboard: Callable[[], None],
    on_select_dashboard: Callable[[str], None],
    on_delete_dashboard: Callable[[str], None],
    on_settings_click: Callable[[], None],
    on_logout: Callable[[], None],
) -> Optional[str]:
    """
    Render the main navigation sidebar.

    Args:
        user_id: Current user ID
        dashboards: List of user's dashboards
        current_dashboard_id: ID of currently selected dashboard
        on_new_dashboard: Callback for new dashboard button
        on_select_dashboard: Callback when selecting a dashboard
        on_delete_dashboard: Callback when deleting a dashboard
        on_settings_click: Callback for settings button
        on_logout: Callback for logout button

    Returns:
        Selected dashboard ID if any
    """
    selected_id = None

    with st.sidebar:
        # Apply custom styles
        st.markdown(
            """
            <style>
                section[data-testid="stSidebar"] {
                    background-color: #F8FAFC;
                }
                .sidebar-section-title {
                    font-size: 11px;
                    font-weight: 600;
                    color: #64748B;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                    margin: 16px 0 8px 0;
                }
                .dashboard-item {
                    background: white;
                    border-radius: 8px;
                    padding: 12px;
                    margin-bottom: 8px;
                    border: 1px solid #E2E8F0;
                }
            </style>
            """,
            unsafe_allow_html=True,
        )

        # Header and New Dashboard button
        st.markdown(
            """
            <div style='text-align: center; padding: 12px 0; margin-bottom: 12px;'>
                <h2 style='margin: 0; color: #10B981; font-weight: 700; font-size: 22px;'>📊 SmartXL</h2>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button(
            "➕ Novo Dashboard",
            type="primary",
            key="sb_new_dashboard",
            use_container_width=True,
        ):
            on_new_dashboard()

        # History section
        st.markdown(
            "<div class='sidebar-section-title'>Dashboards</div>",
            unsafe_allow_html=True,
        )

        # History container
        history_container = st.container()

        with history_container:
            if dashboards:
                # Sort by created_at descending
                sorted_dashboards = sorted(
                    dashboards, key=lambda d: d.created_at, reverse=True
                )

                for dashboard in sorted_dashboards[:10]:
                    is_active = dashboard.dashboard_id == current_dashboard_id

                    col1, col2 = st.columns([5, 1])

                    with col1:
                        if is_active:
                            st.markdown(
                                f"""
                                <div class='dashboard-item' style='border-color: #10B981; background: #F0FDF4;'>
                                    <div style='font-weight: 600; color: #1E293B;'>▶ {dashboard.title}</div>
                                    <div style='font-size: 11px; color: #64748B;'>
                                        {len(dashboard.visualizations)} visualizações • {dashboard.created_at.strftime("%d/%m/%Y")}
                                    </div>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )
                        else:
                            if st.button(
                                f"📂 {dashboard.title}",
                                key=f"history_{dashboard.dashboard_id}",
                                use_container_width=True,
                            ):
                                selected_id = dashboard.dashboard_id
                                on_select_dashboard(dashboard.dashboard_id)

                    with col2:
                        if st.button(
                            "🗑️",
                            key=f"del_{dashboard.dashboard_id}",
                            help="Excluir dashboard",
                        ):
                            on_delete_dashboard(dashboard.dashboard_id)
                            st.rerun()
            else:
                st.markdown(
                    """
                    <div style='
                        text-align: center;
                        padding: 20px;
                        background: #F8FAFC;
                        border-radius: 8px;
                        border: 1px dashed #CBD5E1;
                    '>
                        <p style='color: #64748B; margin: 0; font-size: 13px;'>
                            Nenhum dashboard ainda<br>
                            <span style='font-size: 11px;'>Clique em "Novo Dashboard" para começar</span>
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        # Settings and Logout at bottom
        st.markdown("---")
        col_settings, col_logout = st.columns(2)

        with col_settings:
            if st.button("⚙️ Config", key="sb_settings", use_container_width=True):
                on_settings_click()

        with col_logout:
            if st.button("🚪 Sair", key="sb_logout", use_container_width=True):
                on_logout()

    return selected_id


def render_file_uploader(
    on_upload: Callable[[Any], None],
    on_cancel: Callable[[], None],
) -> None:
    """Render the file uploader dialog."""
    st.markdown("### 📂 Carregar Arquivo")

    uploaded_file = st.file_uploader(
        "Selecione um arquivo Excel",
        type=["xlsx", "xls"],
        help="Faça upload de um arquivo Excel para iniciar um novo dashboard",
    )

    if uploaded_file is not None:
        st.info(f"📄 **{uploaded_file.name}** ({uploaded_file.size / 1024:.1f} KB)")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("📁 Carregar", type="primary", use_container_width=True):
                on_upload(uploaded_file)

        with col2:
            if st.button("✗ Cancelar", use_container_width=True):
                on_cancel()
