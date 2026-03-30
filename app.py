"""
Dashboard Builder - Main Application Entry Point
A Streamlit application for building dashboards from Excel data.
"""

import streamlit as st
import polars as pl
import os
import sys
import uuid
from datetime import datetime
import unicodedata
import time
from typing import Optional, Dict, Any

# Supabase Integration
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "uploads")

supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Supabase conectado com sucesso")
    except Exception as e:
        print(f"❌ Erro ao conectar Supabase: {e}")
else:
    print("⚠️ Supabase não configurado – usando apenas armazenamento local")


def sanitize_filename(filename: str) -> str:
    normalized = unicodedata.normalize('NFKD', filename).encode('ascii', 'ignore').decode('ascii')
    cleaned = ''.join(c if c.isalnum() or c in ('_', '-') else '_' for c in normalized)
    cleaned = '_'.join(filter(None, cleaned.split('_'))).strip('_')
    return cleaned


# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# ====================== IMPORTS ======================
from domain.entities import (
    Analysis,
    Slide,
    Visualization,
    VisualizationConfig,
    VisualizationType,
)
from domain.value_objects import ExportOptions
from use_cases.analysis_service import AnalysisService, FileAnalysisRepository
from use_cases.data_service import DataService
from use_cases.export_service import ExportService
from infrastructure.chart_factory import ChartFactory
from infrastructure.pdf_generator import PDFGenerator

from utils.session_state import init_session_state, get_state, set_state

# Presentation components
from presentation.sidebar import render_sidebar, render_secondary_sidebar
from presentation.canvas import render_canvas, render_slide_navigator
from presentation.widgets import render_widget_palette, render_data_preview
from presentation.components import (
    render_settings_modal,
    render_analysis_history,
    render_export_dialog,
    render_welcome_screen,
    render_notification,
)


# ====================== PAGE CONFIG ======================
st.set_page_config(
    page_title="Dashboard Builder",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown(
    """
<style>
    .main .block-container { padding-top: 2rem; }
    .stButton > button { border-radius: 0.5rem; }
    .streamlit-expanderHeader { font-weight: bold; }
    .stDataFrame, .stPlotlyChart { border-radius: 0.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
    footer {visibility: hidden;}
</style>
""",
    unsafe_allow_html=True,
)


class DashboardBuilderApp:
    def __init__(self):
        init_session_state()
        self._init_services()
        self.chart_factory = ChartFactory()

    def _init_services(self) -> None:
        data_dir = "data"
        os.makedirs(data_dir, exist_ok=True)

        if "analysis_service" not in st.session_state:
            repository = FileAnalysisRepository(data_dir)
            st.session_state.analysis_service = AnalysisService(repository)
            st.session_state.analysis_service.initialize_session(get_state("session_data"))

        if "data_service" not in st.session_state:
            st.session_state.data_service = DataService()

        if "export_service" not in st.session_state:
            st.session_state.export_service = ExportService()

        if "pdf_generator" not in st.session_state:
            st.session_state.pdf_generator = PDFGenerator()

    @property
    def analysis_service(self) -> AnalysisService:
        return st.session_state.analysis_service

    @property
    def data_service(self) -> DataService:
        return st.session_state.data_service

    @property
    def export_service(self) -> ExportService:
        return st.session_state.export_service

    @property
    def pdf_generator(self) -> PDFGenerator:
        return st.session_state.pdf_generator

    def run(self) -> None:
        self._render_header()

        current_analysis = self.analysis_service.get_current_analysis()

        if not current_analysis:
            render_welcome_screen(self._on_new_analysis)
            self._render_uploader_dialog()
        else:
            self._render_main_layout()

        if get_state("show_settings"):
            self._render_settings_modal()
        if get_state("show_export"):
            self._render_export_dialog()

        self._handle_notifications()

    def _render_header(self) -> None:
        col1, col2, col3, col4 = st.columns([2, 1.5, 1, 1])

        with col1:
            st.title("📊 Dashboard Builder")

        with col2:
            current_analysis = self.analysis_service.get_current_analysis()
            if current_analysis:
                new_name = st.text_input(
                    "Nome da Análise",
                    value=current_analysis.name,
                    label_visibility="collapsed",
                    key="analysis_name_input"
                )
                if new_name and new_name != current_analysis.name:
                    self.analysis_service.rename_analysis(current_analysis.id, new_name)

        with col3:
            if current_analysis and st.button("💾 Salvar", use_container_width=True):
                with st.spinner("Salvando análise..."):
                    success = self.analysis_service.save_current_analysis()
                if success:
                    st.success("✅ Análise salva!", icon="💾")
                    st.toast("Salvo com sucesso", icon="💾")

        with col4:
            if current_analysis and st.button("📤 Exportar", type="primary", use_container_width=True):
                set_state("show_export", True)

        st.markdown("---")

    def _render_main_layout(self) -> None:
        current_analysis = self.analysis_service.get_current_analysis()
        if not current_analysis:
            return

        col_main, col_widgets = st.columns([3, 1])

        with col_widgets:
            self._render_widget_sidebar()

        with col_main:
            current_slide = self.analysis_service.get_current_slide()
            render_canvas(
                slide=current_slide,
                data_service=self.data_service,
                analysis_id=current_analysis.id,
                on_update_visualization=self._on_update_visualization,
                on_delete_visualization=self._on_delete_visualization,
                on_add_comment=self._on_add_comment,
            )

            if current_analysis.slides:
                render_slide_navigator(
                    slides=current_analysis.slides,
                    current_slide_id=getattr(current_slide, 'id', None) if current_slide else None,
                    on_slide_change=self._on_slide_change,
                    on_add_slide=self._on_add_slide,
                    on_delete_slide=self._on_delete_slide,
                )

    def _render_widget_sidebar(self) -> None:
        current_analysis = self.analysis_service.get_current_analysis()

        if not current_analysis or not getattr(current_analysis, 'data_schema', None):
            st.info("📁 Faça upload de um arquivo para adicionar visualizações")
            if st.button("📂 Upload XLSX", use_container_width=True):
                set_state("show_uploader", True)
            return

        with st.expander("📁 Data Preview", expanded=False):
            df = self.data_service.get_cached_data(current_analysis.id)
            if df is not None:
                render_data_preview(current_analysis.data_schema, df)

        render_widget_palette(
            current_analysis.data_schema, self._start_visualization_config
        )

        if get_state("configuring_new_viz"):
            self._render_config_dialog()
        if get_state("editing_viz_id"):
            self._render_edit_config_dialog()

    def _render_uploader_dialog(self) -> None:
        if not get_state("show_uploader"):
            return

        with st.expander("📂 Upload de Arquivo XLSX", expanded=True):
            uploaded_file = st.file_uploader(
                "Escolha um arquivo Excel",
                type=["xlsx", "xls"]
            )

            if uploaded_file:
                name_input = st.text_input(
                    "Nome da Análise",
                    value=uploaded_file.name.rsplit(".", 1)[0]
                )

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("📁 Carregar Arquivo", type="primary", use_container_width=True):
                        self._process_uploaded_file(uploaded_file, name_input)
                with col2:
                    if st.button("✗ Cancelar", use_container_width=True):
                        set_state("show_uploader", False)
                        st.rerun()

    def _render_export_dialog(self) -> None:
        current_analysis = self.analysis_service.get_current_analysis()
        if not current_analysis:
            return

        with st.expander("📤 Exportar Análise", expanded=True):
            render_export_dialog(
                analysis=current_analysis,
                on_export=self._on_export
            )
            if st.button("Fechar", key="close_export"):
                set_state("show_export", False)
                st.rerun()

    def _render_settings_modal(self) -> None:
        with st.expander("⚙️ Configurações", expanded=True):
            render_settings_modal(
                current_settings=self.analysis_service.get_settings(),
                on_save=self._on_save_settings,
            )
            if st.button("Fechar Configurações"):
                set_state("show_settings", False)
                st.rerun()

    # ==================== FUNÇÃO ATUALIZADA ====================
    def _process_uploaded_file(self, uploaded_file, name: str) -> None:
        try:
            file_bytes = uploaded_file.getvalue()
            file_path_supabase = None

            if supabase:
                with st.spinner("Enviando arquivo para Supabase Storage..."):
                    timestamp = datetime.now().strftime("%Y-%m-%d")
                    unique_id = uuid.uuid4().hex[:12]
                    safe_name = sanitize_filename(uploaded_file.name)
                    file_ext = os.path.splitext(uploaded_file.name)[1].lower()

                    file_path_supabase = f"{timestamp}/{unique_id}_{safe_name}{file_ext}"

                    content_type = uploaded_file.type or "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

                    try:
                        supabase.storage.from_(SUPABASE_BUCKET).upload(
                            path=file_path_supabase,
                            file=file_bytes,
                            file_options={"content-type": content_type}
                        )
                        st.success("✅ Arquivo enviado para Storage", icon="☁️")
                    except Exception as e:
                        st.error(f"❌ Falha no upload: {e}")
                        return

            # Cria a análise local
            analysis = self.analysis_service.create_analysis(name)

            # Insere registro no banco Supabase
            if supabase and file_path_supabase:
                with st.spinner("Salvando registro na tabela analysis_history..."):
                    try:
                        supabase.table("analysis_history").insert({
                            "analysis_name": name,
                            "file_name": uploaded_file.name,
                            "file_path": file_path_supabase,
                            "bucket": SUPABASE_BUCKET,
                        }).execute()
                        st.success("✅ Registro salvo na tabela!", icon="📊")
                    except Exception as db_error:
                        st.warning(f"⚠️ Upload ok, mas falha ao salvar no banco: {db_error}")

            # Processa o Excel
            with st.spinner("Processando arquivo Excel..."):
                schema, df = self.data_service.load_excel_from_bytes(
                    file_bytes, uploaded_file.name, analysis.id
                )

            analysis.data_schema = schema
            analysis.file_path = file_path_supabase
            analysis.original_filename = uploaded_file.name
            analysis.uploaded_at = datetime.now()

            self.analysis_service.save_current_analysis()

            set_state("show_uploader", False)
            st.success(f"✅ {uploaded_file.name} carregado com sucesso!", icon="🎉")
            st.rerun()

        except Exception as e:
            st.error(f"❌ Erro ao processar arquivo: {str(e)}")
            import traceback
            traceback.print_exc()

    def _on_new_analysis(self) -> None:
        set_state("show_uploader", True)
        st.rerun()

    # ==================== CALLBACKS ====================
    def _on_update_visualization(self, slide_id: str, viz_id: str, config: VisualizationConfig):
        self.analysis_service.update_visualization(slide_id, viz_id, config=config)
        self.analysis_service.save_current_analysis()
        st.success("Visualização atualizada!", icon="✅")
        st.rerun()

    def _on_delete_visualization(self, slide_id: str, viz_id: str):
        self.analysis_service.delete_visualization(slide_id, viz_id)
        st.success("Visualização removida", icon="🗑️")
        st.rerun()

    def _on_add_comment(self, slide_id: str, viz_id: str, comment: str):
        self.analysis_service.update_visualization(slide_id, viz_id, comment=comment)

    def _on_slide_change(self, slide_id: str):
        self.analysis_service.set_current_slide(slide_id)
        st.rerun()

    def _on_add_slide(self):
        slide = self.analysis_service.add_slide()
        if slide:
            st.success(f"Slide adicionado: {slide.title}")
            st.rerun()

    def _on_delete_slide(self, slide_id: str):
        self.analysis_service.delete_slide(slide_id)
        st.success("Slide removido")
        st.rerun()

    def _on_export(self, analysis: Analysis, options: Dict[str, Any]) -> Optional[str]:
        if not analysis:
            st.error("Nenhuma análise carregada para exportar.")
            return None

        try:
            with st.spinner("Gerando arquivo PDF... Isso pode levar alguns segundos..."):
                chart_images = {}
                df = self.data_service.get_cached_data(analysis.id)

                if df is None:
                    st.warning("⚠️ Nenhum dado encontrado em cache.")
                else:
                    for slide in getattr(analysis, 'slides', []):
                        for viz in getattr(slide, 'visualizations', []):
                            if (getattr(viz, 'config', None) and 
                                getattr(viz.config, 'visualization_type', None) != VisualizationType.TABLE):
                                try:
                                    fig = self.chart_factory.create_chart(df, viz.config)
                                    img_bytes = self.chart_factory.export_figure_to_bytes(fig, "png")
                                    chart_images[viz.id] = img_bytes
                                except Exception as e:
                                    st.warning(f"Não foi possível gerar o gráfico {getattr(viz, 'id', 'desconhecido')}: {e}")

                st.success(f"✅ Exportação simulada! {len(chart_images)} gráficos gerados.")
                return None

        except Exception as e:
            st.error(f"❌ Falha na exportação: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def _on_save_settings(self, settings: Dict[str, Any]):
        self.analysis_service.update_settings(settings)
        st.success("Configurações salvas!")

    def _start_visualization_config(self, viz_type: VisualizationType):
        set_state("configuring_new_viz", viz_type)
        st.rerun()

    def _render_config_dialog(self):
        pass

    def _render_edit_config_dialog(self):
        pass

    def _handle_notifications(self):
        notification = get_state("notification")
        if notification:
            message, level = notification
            render_notification(message, level)
            set_state("notification", None)


def main():
    app = DashboardBuilderApp()
    app.run()


if __name__ == "__main__":
    main()