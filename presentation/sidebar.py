"""
Sidebar Component - Main navigation sidebar with dual-sidebar support.
Implements the UI layout shown in interface_principal.png with:
- Top section: New analysis button
- Middle section: Analysis history
- Bottom section: Settings
"""

from typing import Callable, List, Optional, Any
import streamlit as st
from datetime import datetime

from domain.entities import Analysis


def render_main_sidebar(
    user_id: str,
    analyses: List[Analysis],
    current_analysis_id: Optional[str],
    on_new_analysis: Callable[[], None],
    on_select_analysis: Callable[[str], None],
    on_delete_analysis: Callable[[str], None],
    on_settings_click: Callable[[], None],
    on_logout: Callable[[], None],
) -> Optional[str]:
    """
    Render the main navigation sidebar.

    Args:
        user_id: Current user ID
        analyses: List of user's analyses
        current_analysis_id: ID of currently selected analysis
        on_new_analysis: Callback for new analysis button
        on_select_analysis: Callback when selecting an analysis
        on_delete_analysis: Callback when deleting an analysis
        on_settings_click: Callback for settings button
        on_logout: Callback for logout button

    Returns:
        Selected analysis ID if any
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
                section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
                    display: flex;
                    flex-direction: column;
                    height: 100vh;
                }
                section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
                    flex: 1;
                    display: flex;
                    flex-direction: column;
                }
                .sidebar-section-title {
                    font-size: 11px;
                    font-weight: 600;
                    color: #64748B;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                    margin: 16px 0 8px 0;
                }
                .analysis-item {
                    background: white;
                    border-radius: 8px;
                    padding: 12px;
                    margin-bottom: 8px;
                    border: 1px solid #E2E8F0;
                    cursor: pointer;
                }
                .analysis-item:hover {
                    border-color: #10B981;
                }
                .analysis-item.active {
                    border-color: #10B981;
                    background: #F0FDF4;
                }
                .analysis-name {
                    font-weight: 600;
                    color: #1E293B;
                    font-size: 14px;
                }
                .analysis-meta {
                    font-size: 11px;
                    color: #64748B;
                    margin-top: 4px;
                }
            </style>
            """,
            unsafe_allow_html=True,
        )

        # Section 1: Header and New Analysis
        st.markdown(
            """
            <div style='text-align: center; padding: 12px 0; margin-bottom: 12px;'>
                <h2 style='margin: 0; color: #10B981; font-weight: 700; font-size: 22px;'>📊 Análise</h2>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button(
            "➕ Nova Análise",
            type="primary",
            key="sb_new_analysis",
            use_container_width=True,
        ):
            on_new_analysis()

        # Section 2: History
        st.markdown(
            "<div class='sidebar-section-title'>Histórico</div>",
            unsafe_allow_html=True,
        )

        # History container with scroll
        history_container = st.container()

        with history_container:
            if analyses:
                # Sort by updated_at descending
                sorted_analyses = sorted(
                    analyses, key=lambda a: a.updated_at, reverse=True
                )

                for analysis in sorted_analyses[:10]:
                    is_active = analysis.id == current_analysis_id

                    # Create analysis item
                    col1, col2 = st.columns([5, 1])

                    with col1:
                        if is_active:
                            st.markdown(
                                f"""
                                <div class='analysis-item active'>
                                    <div class='analysis-name'>▶ {analysis.name}</div>
                                    <div class='analysis-meta'>
                                        {len(analysis.slides)} slides • {analysis.updated_at.strftime("%d/%m/%Y")}
                                    </div>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )
                        else:
                            if st.button(
                                f"📂 {analysis.name}",
                                key=f"history_{analysis.id}",
                                use_container_width=True,
                            ):
                                selected_id = analysis.id
                                on_select_analysis(analysis.id)

                    with col2:
                        if st.button(
                            "🗑️", key=f"del_{analysis.id}", help="Excluir análise"
                        ):
                            on_delete_analysis(analysis.id)
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
                            Nenhuma análise ainda<br>
                            <span style='font-size: 11px;'>Clique em "Nova Análise" para começar</span>
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        # Spacer to push settings to bottom
        st.markdown('<div style="flex-grow: 1;"></div>', unsafe_allow_html=True)

        # Section 3: Settings and Logout
        st.markdown("---")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("⚙️ Config", key="sb_settings", use_container_width=True):
                on_settings_click()

        with col2:
            if st.button("🚪 Sair", key="sb_logout", use_container_width=True):
                on_logout()
                st.rerun()

        st.caption("v1.0.0 | Dashboard Builder")

    return selected_id


def render_file_uploader(
    on_upload: Callable[[Any], None], on_cancel: Callable[[], None]
) -> None:
    """
    Render the file uploader dialog for XLSX files.

    Args:
        on_upload: Callback when file is uploaded
        on_cancel: Callback when upload is cancelled
    """
    st.markdown(
        """
        <div style='
            background: white;
            border-radius: 12px;
            padding: 24px;
            border: 1px solid #E2E8F0;
            margin: 20px 0;
        '>
            <h3 style='margin: 0 0 16px 0; color: #1E293B;'>📂 Carregar Arquivo XLSX</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader(
        "Selecione um arquivo Excel",
        type=["xlsx", "xls"],
        label_visibility="collapsed",
        key="file_uploader_widget",
    )

    if uploaded_file:
        st.info(f"📁 {uploaded_file.name} ({uploaded_file.size / 1024:.1f} KB)")

    col1, col2 = st.columns(2)

    with col1:
        if st.button(
            "✓ Carregar Arquivo",
            type="primary",
            key="upload_load_btn",
            use_container_width=True,
            disabled=uploaded_file is None,
        ):
            if uploaded_file:
                on_upload(uploaded_file)

    with col2:
        if st.button("✗ Cancelar", key="upload_cancel_btn", use_container_width=True):
            on_cancel()
