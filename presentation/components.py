"""
Components - Reusable UI components for the dashboard builder.
Updated for new schema with dashboards.
"""

from typing import Callable, Dict, Any, Optional
import streamlit as st

from domain.entities import Dashboard


def render_welcome_screen(on_new_dashboard: Callable[[], None]) -> None:
    """Render the welcome screen for new users."""
    st.markdown(
        """
        <div style='
            text-align: center;
            padding: 60px 40px;
            background: linear-gradient(135deg, #F0FDF4 0%, #ECFDF5 100%);
            border-radius: 20px;
            margin: 20px 0;
        '>
            <div style='font-size: 80px; margin-bottom: 20px;'>📊</div>
            <h1 style='color: #10B981; margin: 0; font-size: 32px;'>Bem-vindo ao SmartXL</h1>
            <p style='color: #64748B; font-size: 18px; margin-top: 16px;'>
                Crie dashboards profissionais a partir dos seus dados Excel
            </p>
            <div style='margin-top: 30px; display: flex; justify-content: center; gap: 20px;'>
                <div style='text-align: center;'>
                    <div style='font-size: 32px;'>📁</div>
                    <div style='color: #475569; font-size: 14px; margin-top: 8px;'>Carregue seus dados</div>
                </div>
                <div style='text-align: center;'>
                    <div style='font-size: 32px;'>📊</div>
                    <div style='color: #475569; font-size: 14px; margin-top: 8px;'>Crie visualizações</div>
                </div>
                <div style='text-align: center;'>
                    <div style='font-size: 32px;'>📤</div>
                    <div style='color: #475569; font-size: 14px; margin-top: 8px;'>Exporte relatórios</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("➕ Criar Novo Dashboard", type="primary", use_container_width=True):
        on_new_dashboard()


def render_header_bar(
    analysis_name: str,
    on_save: Callable[[], None],
    on_export: Callable[[], None],
    on_rename: Callable[[str], None],
) -> None:
    """Render the header bar with dashboard name and actions."""
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

    with col1:
        new_name = st.text_input(
            "Nome do Dashboard",
            value=analysis_name,
            label_visibility="collapsed",
            key="header_dashboard_name",
        )
        if new_name != analysis_name:
            on_rename(new_name)

    with col2:
        if st.button("💾 Salvar", use_container_width=True):
            on_save()

    with col3:
        if st.button("📤 Exportar", type="primary", use_container_width=True):
            on_export()


def render_settings_modal(
    current_settings: Dict[str, Any],
    on_save: Callable[[Dict[str, Any]], None],
) -> None:
    """Render the settings modal."""
    st.markdown("### ⚙️ Configurações")

    # Theme settings
    theme = st.selectbox(
        "Tema",
        ["Claro", "Escuro", "Automático"],
        index=["light", "dark", "auto"].index(current_settings.get("theme", "light")),
        key="settings_theme",
    )

    # Language settings
    language = st.selectbox(
        "Idioma",
        ["Português", "English", "Español"],
        index=["pt", "en", "es"].index(current_settings.get("language", "pt")),
        key="settings_language",
    )

    # Export settings
    default_format = st.selectbox(
        "Formato de Exportação Padrão",
        ["PDF", "HTML", "LaTeX"],
        index=["pdf", "html", "latex"].index(
            current_settings.get("default_export_format", "pdf")
        ),
        key="settings_export_format",
    )

    # Chart settings
    chart_colors = st.selectbox(
        "Esquema de Cores",
        ["Padrão", "Corporativo", "Pastel", "Escuro"],
        index=["default", "corporate", "pastel", "dark"].index(
            current_settings.get("chart_colors", "default")
        ),
        key="settings_chart_colors",
    )

    # Save button
    if st.button("Salvar Configurações", type="primary"):
        new_settings = {
            "theme": theme.lower(),
            "language": language.lower(),
            "default_export_format": default_format.lower(),
            "chart_colors": chart_colors.lower(),
        }
        on_save(new_settings)
        st.success("Configurações salvas!")


def render_export_dialog(
    dashboard: Dashboard,
    export_service: Any,
    chart_images: Optional[Dict[str, bytes]] = None,
) -> None:
    """
    Export dialog: renders options and triggers ExportService.
    Provides a download button on success so the user gets the file directly
    without needing server-side file storage.
    """
    from domain.value_objects import ExportOptions

    st.markdown("### 📤 Exportar Dashboard")

    c1, c2 = st.columns(2)
    with c1:
        fmt = st.selectbox("Formato", ["PDF", "HTML", "LaTeX (.tex)"],
                           key="exp_fmt")
    with c2:
        layout = st.selectbox("Layout (PDF/LaTeX)", ["Relatório", "Slides (Beamer)"],
                              key="exp_layout", help="Apenas relevante para PDF e LaTeX")

    c3, c4 = st.columns(2)
    with c3:
        paper = st.selectbox("Papel", ["a4", "letter", "legal"], key="exp_paper")
    with c4:
        orient = st.radio("Orientação", ["Retrato", "Paisagem"],
                          horizontal=True, key="exp_orient")

    c5, c6 = st.columns(2)
    with c5:
        inc_cmt = st.checkbox("Incluir comentários", value=True, key="exp_cmt")
    with c6:
        inc_ts  = st.checkbox("Incluir data/hora",  value=True, key="exp_ts")

    header_txt = st.text_input("Cabeçalho (opcional)", key="exp_header")
    footer_txt = st.text_input("Rodapé (opcional)",    key="exp_footer")

    if st.button("📥 Gerar", type="primary", use_container_width=True):
        opts = ExportOptions(
            paper_size=paper,
            orientation="portrait" if orient == "Retrato" else "landscape",
            include_comments=inc_cmt,
            include_timestamp=inc_ts,
            header_text=header_txt,
            footer_text=footer_txt,
        )
        use_slides = layout == "Slides (Beamer)"
        images = chart_images or {}

        with st.spinner("Gerando…"):
            fmt_lower = fmt.lower()
            if "pdf" in fmt_lower:
                data = export_service.export_to_pdf(
                    dashboard, opts, images, use_slides=use_slides
                )
                if data:
                    st.download_button(
                        "⬇️ Baixar PDF",
                        data=data,
                        file_name=f"{dashboard.title.replace(' ','_')}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )
                else:
                    st.error("Falha ao gerar PDF. Verifique se pdflatex está instalado ou se reportlab está disponível.")
            elif "html" in fmt_lower:
                data = export_service.export_to_html(dashboard, opts, images)
                if data:
                    st.download_button(
                        "⬇️ Baixar HTML",
                        data=data,
                        file_name=f"{dashboard.title.replace(' ','_')}.html",
                        mime="text/html",
                        use_container_width=True,
                    )
            else:
                data = export_service.export_to_latex(
                    dashboard, opts, images, use_slides=use_slides
                )
                if data:
                    st.download_button(
                        "⬇️ Baixar LaTeX",
                        data=data,
                        file_name=f"{dashboard.title.replace(' ','_')}.tex",
                        mime="text/plain",
                        use_container_width=True,
                    )


def render_notification(message: str, level: str = "info") -> None:
    """Render a notification message."""
    if level == "success":
        st.success(message)
    elif level == "error":
        st.error(message)
    elif level == "warning":
        st.warning(message)
    else:
        st.info(message)


def render_dashboard_history(
    dashboards: list,
    current_dashboard_id: Optional[str],
    on_select: Callable[[str], None],
    on_delete: Callable[[str], None],
) -> None:
    """Render the dashboard history list."""
    st.markdown("### 📜 Dashboards")

    if not dashboards:
        st.info("Nenhum dashboard anterior")
        return

    for dashboard in dashboards:
        is_current = dashboard.dashboard_id == current_dashboard_id

        with st.container():
            col1, col2 = st.columns([4, 1])

            with col1:
                if is_current:
                    st.markdown(
                        f"**▶ {dashboard.title}**",
                    )
                else:
                    if st.button(
                        f"📂 {dashboard.title}",
                        key=f"history_item_{dashboard.dashboard_id}",
                        use_container_width=True,
                    ):
                        on_select(dashboard.dashboard_id)

            with col2:
                if st.button("🗑️", key=f"delete_history_{dashboard.dashboard_id}"):
                    on_delete(dashboard.dashboard_id)
                    st.rerun()

            st.caption(
                f"{len(dashboard.visualizations)} visualizações • {dashboard.created_at.strftime('%d/%m/%Y %H:%M')}"
            )
            st.markdown("---")
