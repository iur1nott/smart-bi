"""
Components Module - Reusable UI components with loading states and notifications.
"""

from typing import Dict, Any, List, Optional, Callable
import streamlit as st
from datetime import datetime
import time
import os


def render_settings_modal(current_settings: Dict[str, Any], on_save: Callable) -> None:
    """Render the settings modal with proper feedback."""
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
            index=["pdf", "latex", "html"].index(current_settings.get("export_format", "pdf")),
        )
        paper_size = st.selectbox(
            "Paper Size",
            ["a4", "letter", "legal"],
            index=["a4", "letter", "legal"].index(current_settings.get("paper_size", "a4")),
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
    if st.button("💾 Save Settings", type="primary", key="save_settings_button"):
        try:
            with st.spinner("Salvando configurações..."):
                time.sleep(0.6)  # simulação de processamento
                new_settings = {
                    "theme": theme,
                    "grid_visible": grid_visible,
                    "export_format": export_format,
                    "paper_size": paper_size,
                    "include_comments": include_comments,
                    "auto_save": auto_save,
                }
                on_save(new_settings)
            
            st.success("✅ Configurações salvas com sucesso!", icon="💾")
            st.toast("Configurações atualizadas", icon="✅")
            
        except Exception as e:
            st.error(f"❌ Erro ao salvar configurações: {str(e)}", icon="🚨")


def render_analysis_history(
    analyses: List[Dict[str, Any]],
    on_select: Callable,
    on_delete: Callable,
    on_rename: Callable,
) -> None:
    """Render the analysis history list with improved feedback."""
    st.markdown("## 📜 Analysis History")

    if not analyses:
        st.info("Nenhuma análise encontrada. Crie uma nova para começar.", icon="📋")
        return

    for analysis in analyses:
        with st.container(border=True):
            col1, col2, col3 = st.columns([4, 1.2, 1])

            with col1:
                st.markdown(f"**{analysis.get('name', 'Sem nome')}**")
                st.caption(
                    f"📄 {analysis.get('file_name', 'Sem arquivo')} | "
                    f"📊 {analysis.get('slide_count', 0)} slides"
                )
                updated = analysis.get("updated_at", "")
                if updated:
                    try:
                        dt = datetime.fromisoformat(updated)
                        st.caption(f"Atualizado: {dt.strftime('%d/%m/%Y %H:%M')}")
                    except Exception:
                        pass

            with col2:
                if st.button("📂 Abrir", key=f"open_{analysis['id']}", use_container_width=True):
                    on_select(analysis["id"])

            with col3:
                if st.button("🗑️", key=f"delete_{analysis['id']}", help="Excluir análise"):
                    if st.session_state.get("confirm_delete") != analysis["id"]:
                        st.session_state.confirm_delete = analysis["id"]
                        st.rerun()
                    else:
                        on_delete(analysis["id"])
                        st.session_state.pop("confirm_delete", None)
                        st.rerun()

            # Confirmação de exclusão inline
            if st.session_state.get("confirm_delete") == analysis["id"]:
                st.warning("Tem certeza que deseja excluir esta análise?", icon="⚠️")
                col_yes, col_no = st.columns(2)
                with col_yes:
                    if st.button("Sim, excluir", type="primary", key=f"confirm_delete_{analysis['id']}"):
                        on_delete(analysis["id"])
                        st.session_state.pop("confirm_delete", None)
                        st.rerun()
                with col_no:
                    if st.button("Cancelar", key=f"cancel_delete_{analysis['id']}"):
                        st.session_state.pop("confirm_delete", None)
                        st.rerun()

            st.markdown("---")


def render_export_dialog(analysis, on_export: Callable) -> None:
    """Render the export dialog with loading feedback."""
    st.markdown("## 📤 Exportar Análise")
    st.markdown(f"**Análise:** {getattr(analysis, 'name', 'Sem nome')}")
    st.markdown(f"**Slides:** {len(getattr(analysis, 'slides', []))}")

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        export_format = st.selectbox("Formato de Exportação", ["PDF", "LaTeX", "HTML"])
        paper_size = st.selectbox("Tamanho do Papel", ["A4", "Letter", "Legal"])

    with col2:
        orientation = st.selectbox("Orientação", ["Portrait", "Landscape"])
        include_comments = st.checkbox("Incluir Comentários", value=True)

    header_text = st.text_input("Texto do Cabeçalho (Opcional)", placeholder="Digite o texto...")
    footer_text = st.text_input("Texto do Rodapé (Opcional)", placeholder="Digite o texto...")

    st.markdown("---")

    if st.button("📤 Exportar Agora", type="primary", use_container_width=True, key="export_button"):
        try:
            with st.spinner("Gerando arquivo de exportação..."):
                time.sleep(1.2)  # simulação de processamento
                
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
                st.success(f"✅ Exportação concluída com sucesso!", icon="🎉")
                st.toast("Arquivo exportado!", icon="📤")
                
                # Botão de download
                try:
                    with open(result, "rb") as f:
                        file_data = f.read()
                    st.download_button(
                        label="📥 Baixar Arquivo",
                        data=file_data,
                        file_name=os.path.basename(result),
                        mime="application/pdf" if export_format.lower() == "pdf" else "text/plain",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"Erro ao preparar download: {e}")
            else:
                st.error("❌ Falha na exportação.")
                
        except Exception as e:
            st.error(f"❌ Erro durante a exportação: {str(e)}", icon="🚨")


def render_welcome_screen(on_new_analysis: Callable) -> None:
    """Render the welcome screen."""
    st.markdown(
        """
        <div style='text-align: center; padding: 60px 20px;'>
            <h1 style='color: #2196F3; font-size: 52px;'>📊 Dashboard Builder</h1>
            <p style='font-size: 20px; color: #666; margin: 20px 0;'>
                Crie dashboards profissionais a partir dos seus dados Excel
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("### Vamos começar?")

        if st.button(
            "📁 Criar Nova Análise + Upload de Arquivo",
            type="primary",
            use_container_width=True,
            key="welcome_new_analysis"
        ):
            with st.spinner("Iniciando nova análise..."):
                time.sleep(0.5)
            on_new_analysis()

        st.markdown("---")
        st.markdown("""
        **Recursos disponíveis:**
        - 📊 Gráficos interativos (Bar, Line, Pie, Scatter...)
        - 📋 Tabelas dinâmicas
        - 📝 Comentários nas visualizações
        - 📄 Exportação para PDF/LaTeX
        - 💾 Salvamento automático
        """)


def render_notification(message: str, type: str = "info") -> None:
    """Render a notification message."""
    if type == "success":
        st.success(message, icon="✅")
        st.toast(message, icon="✅")
    elif type == "error":
        st.error(message, icon="🚨")
        st.toast("Erro na operação", icon="❌")
    elif type == "warning":
        st.warning(message, icon="⚠️")
    else:
        st.info(message, icon="ℹ️")


def render_confirmation_dialog(
    title: str, message: str, on_confirm: Callable, on_cancel: Callable
) -> None:
    """Render a confirmation dialog with better UX."""
    st.markdown(f"### {title}")
    st.markdown(message)

    col1, col2 = st.columns(2)

    with col1:
        if st.button("✅ Confirmar", type="primary", use_container_width=True):
            on_confirm()

    with col2:
        if st.button("❌ Cancelar", use_container_width=True):
            on_cancel()