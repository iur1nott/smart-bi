"""
Components - Reusable UI components for the dashboard builder.
"""

from typing import Callable, Dict, Any, Optional
import streamlit as st

from domain.entities import Analysis


def render_welcome_screen(on_new_analysis: Callable[[], None]) -> None:
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
            <h1 style='color: #10B981; margin: 0; font-size: 32px;'>Bem-vindo ao Dashboard Builder</h1>
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

    if st.button("➕ Criar Nova Análise", type="primary", use_container_width=True):
        on_new_analysis()


def render_header_bar(
    analysis_name: str,
    on_save: Callable[[], None],
    on_export: Callable[[], None],
    on_rename: Callable[[str], None],
) -> None:
    """Render the header bar with analysis name and actions."""
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

    with col1:
        new_name = st.text_input(
            "Nome da Análise",
            value=analysis_name,
            label_visibility="collapsed",
            key="header_analysis_name",
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
        index=["pdf", "html", "latex"].index(current_settings.get("default_export_format", "pdf")),
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
    analysis: Analysis,
    on_export: Callable[[Analysis, Dict[str, Any]], Optional[str]],
) -> None:
    """Render the export dialog."""
    st.markdown("### 📤 Exportar Análise")

    # Export format
    export_format = st.selectbox(
        "Formato",
        ["PDF", "HTML", "LaTeX"],
        key="export_format_select",
    )

    # Paper size (for PDF)
    paper_size = st.selectbox(
        "Tamanho do Papel",
        ["A4", "Letter", "Legal"],
        key="export_paper_size",
    )

    # Orientation
    orientation = st.radio(
        "Orientação",
        ["Retrato", "Paisagem"],
        horizontal=True,
        key="export_orientation",
    )

    # Options
    include_comments = st.checkbox(
        "Incluir comentários",
        value=True,
        key="export_include_comments",
    )

    include_timestamp = st.checkbox(
        "Incluir data/hora",
        value=True,
        key="export_include_timestamp",
    )

    # Header and footer
    header_text = st.text_input(
        "Texto do Cabeçalho (opcional)",
        key="export_header_text",
    )

    footer_text = st.text_input(
        "Texto do Rodapé (opcional)",
        key="export_footer_text",
    )

    # Export button
    if st.button("📥 Exportar", type="primary", use_container_width=True):
        options = {
            "format": export_format.lower(),
            "paper_size": paper_size.lower(),
            "orientation": "portrait" if orientation == "Retrato" else "landscape",
            "include_comments": include_comments,
            "include_timestamp": include_timestamp,
            "header_text": header_text,
            "footer_text": footer_text,
        }

        result = on_export(analysis, options)
        if result:
            st.success(f"✓ Exportado com sucesso: {result}")


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


def render_analysis_history(
    analyses: list,
    current_analysis_id: Optional[str],
    on_select: Callable[[str], None],
    on_delete: Callable[[str], None],
) -> None:
    """Render the analysis history list."""
    st.markdown("### 📜 Histórico de Análises")

    if not analyses:
        st.info("Nenhuma análise anterior")
        return

    for analysis in analyses:
        is_current = analysis.id == current_analysis_id

        with st.container():
            col1, col2 = st.columns([4, 1])

            with col1:
                if is_current:
                    st.markdown(
                        f"**▶ {analysis.name}**",
                    )
                else:
                    if st.button(
                        f"📂 {analysis.name}",
                        key=f"history_item_{analysis.id}",
                        use_container_width=True,
                    ):
                        on_select(analysis.id)

            with col2:
                if st.button("🗑️", key=f"delete_history_{analysis.id}"):
                    on_delete(analysis.id)
                    st.rerun()

            st.caption(
                f"{len(analysis.slides)} slides • {analysis.updated_at.strftime('%d/%m/%Y %H:%M')}"
            )
            st.markdown("---")
