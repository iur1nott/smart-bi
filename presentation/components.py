"""
Components Module - Reusable UI components for the application.
Contains settings modal, export dialog, notifications, and other shared components.
"""

from typing import Dict, Any, List, Optional, Callable
import streamlit as st
from datetime import datetime
import os

from domain.entities import Analysis


def render_settings_modal(
    current_settings: Dict[str, Any], on_save: Callable[[Dict[str, Any]], None]
) -> None:
    """Render the settings modal with modern design."""
    st.markdown(
        """
        <div style='
            background: white;
            border-radius: 16px;
            padding: 24px;
            border: 1px solid #E2E8F0;
            margin-bottom: 20px;
        '>
            <h2 style='margin: 0 0 20px 0; color: #1E293B;'>⚙️ Configurações</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab1, tab2, tab3 = st.tabs(["🎨 Aparência", "📄 Exportação", "💾 Dados"])

    with tab1:
        st.markdown("### Aparência")
        theme = st.selectbox(
            "Tema",
            ["light", "dark"],
            index=0 if current_settings.get("theme", "light") == "light" else 1,
            key="settings_theme_select",
        )
        grid_visible = st.checkbox(
            "Mostrar linhas de grade",
            value=current_settings.get("grid_visible", True),
            key="settings_grid_checkbox",
        )
        auto_save = st.checkbox(
            "Auto-salvar alterações",
            value=current_settings.get("auto_save", True),
            key="settings_auto_save_checkbox",
        )

    with tab2:
        st.markdown("### Exportação")
        export_format = st.selectbox(
            "Formato padrão",
            ["pdf", "latex", "html"],
            index=["pdf", "latex", "html"].index(
                current_settings.get("export_format", "pdf")
            ),
            key="settings_export_format_select",
        )
        paper_size = st.selectbox(
            "Tamanho do papel",
            ["a4", "letter", "legal"],
            index=["a4", "letter", "legal"].index(
                current_settings.get("paper_size", "a4")
            ),
            key="settings_paper_size_select",
        )
        include_comments = st.checkbox(
            "Incluir comentários",
            value=current_settings.get("include_comments", True),
            key="settings_include_comments_checkbox",
        )
        include_page_numbers = st.checkbox(
            "Incluir números de página",
            value=current_settings.get("include_page_numbers", True),
            key="settings_page_numbers_checkbox",
        )

    with tab3:
        st.markdown("### Dados")
        max_rows = st.number_input(
            "Máximo de linhas por tabela",
            min_value=10,
            max_value=1000,
            value=current_settings.get("max_rows_per_table", 100),
            key="settings_max_rows",
        )
        cache_enabled = st.checkbox(
            "Habilitar cache de dados",
            value=current_settings.get("cache_enabled", True),
            key="settings_cache_checkbox",
        )

    st.markdown("---")
    if st.button("💾 Salvar Configurações", type="primary", key="save_settings_btn"):
        new_settings = {
            "theme": theme,
            "grid_visible": grid_visible,
            "auto_save": auto_save,
            "export_format": export_format,
            "paper_size": paper_size,
            "include_comments": include_comments,
            "include_page_numbers": include_page_numbers,
            "max_rows_per_table": max_rows,
            "cache_enabled": cache_enabled,
        }
        on_save(new_settings)
        st.success("✓ Configurações salvas!")


def render_export_dialog(
    analysis: Analysis, on_export: Callable[[Analysis, Dict[str, Any]], Optional[str]]
) -> None:
    """Render the export dialog with modern design."""
    st.markdown(
        f"""
        <div style='
            background: white;
            border-radius: 16px;
            padding: 24px;
            border: 1px solid #E2E8F0;
            margin-bottom: 20px;
        '>
            <h2 style='margin: 0 0 8px 0; color: #1E293B;'>📤 Exportar Análise</h2>
            <p style='color: #64748B; margin: 0;'>{analysis.name} • {len(analysis.slides)} slides</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)

    with col1:
        export_format = st.selectbox(
            "Formato", ["PDF", "LaTeX", "HTML"], key="export_format_select"
        )
        paper_size = st.selectbox(
            "Tamanho do Papel", ["A4", "Carta", "Legal"], key="export_paper_size_select"
        )

    with col2:
        orientation = st.selectbox(
            "Orientação", ["Retrato", "Paisagem"], key="export_orientation_select"
        )
        include_comments = st.checkbox(
            "Incluir comentários", value=True, key="export_include_comments_checkbox"
        )

    header_text = st.text_input(
        "Texto de Cabeçalho (Opcional)",
        placeholder="Digite o cabeçalho...",
        key="export_header_input",
    )
    footer_text = st.text_input(
        "Texto de Rodapé (Opcional)",
        placeholder="Digite o rodapé...",
        key="export_footer_input",
    )

    title_page = st.checkbox("Incluir página de título", key="export_title_page")

    st.markdown("---")

    if st.button(
        "📤 Exportar", type="primary", key="export_submit_btn", use_container_width=True
    ):
        with st.spinner("Gerando exportação..."):
            export_options = {
                "format": export_format.lower(),
                "paper_size": paper_size.lower(),
                "orientation": "portrait" if orientation == "Retrato" else "landscape",
                "include_comments": include_comments,
                "header_text": header_text,
                "footer_text": footer_text,
                "title_page": title_page,
            }
            result = on_export(analysis, export_options)

            if result:
                st.success("✓ Exportado com sucesso!")
                try:
                    with open(result, "rb") as f:
                        file_data = f.read()

                    file_ext = (
                        "pdf"
                        if export_format.lower() == "pdf"
                        else ("tex" if export_format.lower() == "latex" else "html")
                    )
                    mime_type = "application/pdf" if file_ext == "pdf" else "text/plain"

                    st.download_button(
                        label="📥 Baixar Arquivo",
                        data=file_data,
                        file_name=os.path.basename(result),
                        mime=mime_type,
                        key="download_export_file_btn",
                        use_container_width=True,
                    )
                except Exception as e:
                    st.error(f"Erro ao ler arquivo: {str(e)}")


def render_welcome_screen(on_new_analysis: Callable[[], None]) -> None:
    """Render the welcome screen for new users."""
    st.markdown(
        """
        <div style="
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 60px 20px;
            text-align: center;
        ">
            <div style="
                background: linear-gradient(135deg, #10B981 0%, #059669 100%);
                width: 100px;
                height: 100px;
                border-radius: 24px;
                display: flex;
                align-items: center;
                justify-content: center;
                margin-bottom: 32px;
                box-shadow: 0 10px 15px -3px rgba(16, 185, 129, 0.3);
            ">
                <span style="font-size: 48px;">📊</span>
            </div>
            <h1 style="color: #1E293B; margin: 0 0 12px 0; font-size: 32px;">Dashboard Builder</h1>
            <p style="color: #64748B; font-size: 18px; margin: 0 0 40px 0;">
                Crie dashboards profissionais a partir dos seus dados Excel
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        if st.button(
            "📁 Carregar Arquivo XLSX",
            type="primary",
            key="welcome_upload_btn",
            use_container_width=True,
        ):
            on_new_analysis()

        st.markdown("<div style='height: 32px;'></div>", unsafe_allow_html=True)

        st.markdown(
            """
            <div style="
                background: #F8FAFC;
                border-radius: 12px;
                padding: 24px;
                text-align: left;
                border: 1px solid #E2E8F0;
            ">
                <h4 style="color: #1E293B; margin: 0 0 16px 0;">✨ Recursos</h4>
                <ul style="color: #475569; margin: 0; padding-left: 20px; line-height: 2;">
                    <li>📊 Múltiplos tipos de gráficos</li>
                    <li>📋 Tabelas interativas</li>
                    <li>💬 Comentários em visualizações</li>
                    <li>📄 Exportação para PDF/LaTeX</li>
                    <li>💾 Salvamento automático</li>
                    <li>🔐 Conta de usuário segura</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )


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
    title: str,
    message: str,
    on_confirm: Callable[[], None],
    on_cancel: Callable[[], None],
) -> None:
    """Render a confirmation dialog."""
    st.markdown(
        f"""
        <div style='
            background: white;
            border-radius: 12px;
            padding: 24px;
            border: 1px solid #E2E8F0;
            margin-bottom: 20px;
        '>
            <h3 style='color: #1E293B; margin: 0 0 12px 0;'>{title}</h3>
            <p style='color: #64748B; margin: 0;'>{message}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button(
            "✓ Confirmar",
            type="primary",
            key="confirm_dialog_yes_btn",
            use_container_width=True,
        ):
            on_confirm()

    with col2:
        if st.button(
            "✗ Cancelar", key="confirm_dialog_no_btn", use_container_width=True
        ):
            on_cancel()


def render_analysis_list(
    analyses: List[Analysis],
    on_select: Callable[[str], None],
    on_delete: Callable[[str], None],
    on_rename: Callable[[str, str], None],
) -> None:
    """Render a list of analyses with actions."""
    st.markdown(
        """
        <h2 style='color: #1E293B; margin-bottom: 20px;'>📜 Histórico de Análises</h2>
        """,
        unsafe_allow_html=True,
    )

    if not analyses:
        st.markdown(
            """
            <div style='
                text-align: center;
                padding: 40px;
                background: #F8FAFC;
                border-radius: 12px;
                border: 1px dashed #CBD5E1;
            '>
                <div style='font-size: 48px; margin-bottom: 16px;'>📭</div>
                <p style='color: #64748B;'>Nenhuma análise ainda</p>
                <p style='color: #94A3B8; font-size: 13px;'>Crie uma nova análise para começar</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    for idx, analysis in enumerate(analyses):
        with st.container():
            col1, col2, col3 = st.columns([4, 1, 1])

            with col1:
                st.markdown(f"**{analysis.name}**")
                st.caption(
                    f"📄 {analysis.data_schema.file_name if analysis.data_schema else 'Sem arquivo'} • 📊 {len(analysis.slides)} slides"
                )

                if analysis.updated_at:
                    try:
                        st.caption(
                            f"Atualizado: {analysis.updated_at.strftime('%d/%m/%Y %H:%M')}"
                        )
                    except Exception:
                        pass

            with col2:
                if st.button(
                    "📂 Abrir",
                    key=f"history_open_{idx}_{analysis.id}",
                    use_container_width=True,
                ):
                    on_select(analysis.id)

            with col3:
                if st.button(
                    "🗑️",
                    key=f"history_del_{idx}_{analysis.id}",
                    help="Excluir análise",
                ):
                    on_delete(analysis.id)
                    st.rerun()

            st.markdown("---")


def render_header_bar(
    analysis_name: str,
    on_save: Callable[[], None],
    on_export: Callable[[], None],
    on_rename: Callable[[str], None],
) -> None:
    """Render the header bar with analysis name and actions."""
    col1, col2, col3, col4 = st.columns([3, 2, 1, 1])

    with col1:
        st.markdown(
            f"""
            <div style='display: flex; align-items: center; gap: 12px;'>
                <h1 style='margin: 0; font-size: 24px; color: #1E293B;'>📊 {analysis_name}</h1>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        new_name = st.text_input(
            "Nome",
            value=analysis_name,
            label_visibility="collapsed",
            key="analysis_name_input",
        )
        if new_name != analysis_name:
            on_rename(new_name)
            st.rerun()

    with col3:
        if st.button("💾 Salvar", use_container_width=True):
            on_save()

    with col4:
        if st.button("📤 Exportar", type="primary", use_container_width=True):
            on_export()
