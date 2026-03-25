"""
Sidebar Component - Main navigation and controls.
"""

from typing import Optional, Dict, Any, List, Callable
import streamlit as st
from datetime import datetime
from utils.session_state import get_state, set_state


def render_sidebar(
    analysis_service,
    on_new_analysis: Callable,
    on_select_analysis: Callable,
    on_settings_click: Callable,
    on_upload: Callable,  # ADICIONADO: Essencial para a Sprint 1
) -> Optional[str]:
    """Render the main sidebar with three sections."""
    selected_analysis_id = None

    with st.sidebar:
        # SEÇÃO SUPERIOR - Ações
        st.markdown("### 📁 Ações")
        col1, col2 = st.columns(2)

        with col1:
            if st.button("➕ Novo", use_container_width=True, type="primary"):
                on_new_analysis()

        with col2:
            if st.button("📂 Abrir", use_container_width=True):
                set_state("show_uploader", True)

        # Logica do Uploader na Sidebar
        if get_state("show_uploader"):
            st.markdown("---")
            st.markdown("#### ⬆️ Carregar Dados")
            analysis_name = st.text_input("Nome da Análise", value="Nova Análise Comercial")
            uploaded_file = st.file_uploader("Selecione o Excel/CSV", type=["xlsx", "xls", "csv"])

            if uploaded_file is not None:
                if st.button("Confirmar Upload", type="primary", use_container_width=True):
                    # Chama o processamento no app.py que ativa o mapeador
                    on_upload(uploaded_file, analysis_name)
                    set_state("show_uploader", False)
            
            if st.button("Cancelar", use_container_width=True):
                set_state("show_uploader", False)
                st.rerun()

        st.markdown("---")

        # SEÇÃO MÉDIA - Histórico
        st.markdown("### 📜 Histórico")
        history = analysis_service.get_analysis_history()

        if history:
            history.sort(key=lambda x: x.get("updated_at", ""), reverse=True)

            for item in history[:10]:
                analysis_id = item.get("id")
                name = item.get("name", "Sem nome")
                file_name = item.get("file_name", "Sem arquivo")
                is_active = st.session_state.get("current_analysis_id") == analysis_id

                if st.button(
                    f"{'▶ ' if is_active else ''}{name}",
                    key=f"history_{analysis_id}",
                    use_container_width=True,
                    type="primary" if is_active else "secondary",
                ):
                    selected_analysis_id = analysis_id
                    on_select_analysis(analysis_id)

                st.caption(f"📄 {file_name}")
        else:
            st.info("Nenhuma análise encontrada.")

        st.markdown("---")

        # SEÇÃO INFERIOR - Configurações
        st.markdown("### ⚙️ Configurações")
        if st.button("⚙️ Definições", use_container_width=True):
            on_settings_click()

        settings = analysis_service.get_settings()
        auto_save = st.toggle("Salvamento Automático", value=settings.get("auto_save", True))
        if auto_save != settings.get("auto_save"):
            analysis_service.update_settings({"auto_save": auto_save})

        st.caption("Smart-BI v1.0.0")

    return selected_analysis_id

def render_secondary_sidebar(
    data_schema: Optional[Any], on_add_visualization: Callable, visible: bool = True
) -> None:
    """Render secondary sidebar with visualization options."""
    if not visible or not data_schema:
        return

    with st.expander("📊 Adicionar Visualização", expanded=True):
        from domain.entities import VisualizationType

        chart_types = [
            ("📊 Barras", VisualizationType.BAR_CHART),
            ("📈 Linhas", VisualizationType.LINE_CHART),
            ("🥧 Pizza", VisualizationType.PIE_CHART),
            ("📉 Área", VisualizationType.AREA_CHART),
            ("⚬ Dispersão", VisualizationType.SCATTER_PLOT),
            ("▊ Histograma", VisualizationType.HISTOGRAM),
            ("📋 Tabela", VisualizationType.TABLE),
            ("💳 Métrica", VisualizationType.METRIC_CARD),
        ]

        cols = st.columns(2) # Ajustado para 2 colunas para melhor leitura no Windows
        for i, (label, viz_type) in enumerate(chart_types):
            with cols[i % 2]:
                if st.button(
                    label, key=f"add_{viz_type.value}", use_container_width=True
                ):
                    on_add_visualization(viz_type)