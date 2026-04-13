"""
Dashboard Builder - Main Application Entry Point
A Streamlit application for building dashboards from Excel data.
Following Clean Architecture with SOLID principles.

This merged version combines:
- User authentication and session management (from postgres branch)
- Canvas-based visualization editing (from main branch)
- PostgreSQL database integration with Docker support
"""

import streamlit as st
import polars as pl
import os
import sys
from typing import Optional, Dict, Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Domain imports
from domain.entities import (
    User,
    Analysis,
    Slide,
    Visualization,
    VisualizationConfig,
    VisualizationType,
    UserSession,
    DataSchema,
)

# Infrastructure imports
from infrastructure.database import init_database, get_database
from infrastructure.repositories import (
    UserRepositoryImpl,
    AnalysisRepositoryImpl,
    SessionRepositoryImpl,
)
from infrastructure.auth import JWTHandler
from infrastructure.chart_factory import ChartFactory

# Use case imports
from use_cases.auth_service import AuthService
from use_cases.analysis_service import AnalysisService
from use_cases.data_service import DataService
from use_cases.export_service import ExportService

# Presentation imports
from presentation.login import render_login_page, render_user_menu
from presentation.sidebar import render_main_sidebar, render_file_uploader
from presentation.widget_palette import render_widget_palette, render_column_mapping
from presentation.canvas import render_canvas, render_slide_navigator
from presentation.components import (
    render_settings_modal,
    render_export_dialog,
    render_welcome_screen,
    render_notification,
    render_header_bar,
)

# Utils imports
from utils.session_state import init_session_state, get_state, set_state


# Configure Streamlit page
st.set_page_config(
    page_title="Dashboard Builder",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": "Dashboard Builder - Crie dashboards profissionais",
    },
)

# Apply custom CSS
st.markdown(
    """
    <style>
        /* Main container */
        .main .block-container {
            padding-top: 1rem;
            padding-bottom: 0rem;
        }

        /* Sidebar styling */
        section[data-testid="stSidebar"] {
            background-color: #F8FAFC;
        }

        /* Buttons */
        .stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #10B981 0%, #059669 100%);
            border: none;
            border-radius: 8px;
            font-weight: 600;
        }

        .stButton > button[kind="primary"]:hover {
            background: linear-gradient(135deg, #059669 0%, #047857 100%);
        }

        /* Cards */
        .stMetric > div {
            background-color: #F8FAFC;
            padding: 1rem;
            border-radius: 12px;
            border: 1px solid #E2E8F0;
        }

        /* DataFrames */
        .stDataFrame {
            border: 1px solid #E2E8F0;
            border-radius: 12px;
            overflow: hidden;
        }

        /* Charts */
        .stPlotlyChart {
            border-radius: 12px;
            overflow: hidden;
        }

        /* Hide streamlit branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
    </style>
""",
    unsafe_allow_html=True,
)


class DashboardBuilderApp:
    """Main application class following the Facade pattern."""

    def __init__(self):
        """Initialize the application with all required services."""
        self._init_session_state()
        self._init_services()

    def _init_session_state(self) -> None:
        """Initialize Streamlit session state with default values."""
        defaults = {
            "user": None,
            "session": None,
            "current_analysis": None,
            "current_slide_id": None,
            "show_settings": False,
            "show_export": False,
            "show_uploader": False,
            "show_column_mapping": False,
            "new_viz_type": None,
            "editing_viz_id": None,
            "notification": None,
            "data_cache": {},  # Cache for loaded DataFrames
        }

        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value

    def _init_services(self) -> None:
        """Initialize application services."""
        # Initialize database
        try:
            init_database()
        except Exception as e:
            st.warning(f"Database connection issue: {e}")

        # Initialize repositories
        user_repo = UserRepositoryImpl()
        analysis_repo = AnalysisRepositoryImpl()
        session_repo = SessionRepositoryImpl()
        jwt_handler = JWTHandler()

        # Initialize services
        self.auth_service = AuthService(user_repo, session_repo, jwt_handler)
        self.analysis_service = AnalysisService(analysis_repo, session_repo)
        self.data_service = DataService()
        self.export_service = ExportService()
        self.chart_factory = ChartFactory()

    def run(self) -> None:
        """Run the main application."""
        # Check if user is logged in
        if not st.session_state.user:
            self._render_login_flow()
        else:
            self._render_main_application()

    def _render_login_flow(self) -> None:
        """Render the login/registration flow."""

        def on_login_success(user: User, session: UserSession) -> None:
            st.session_state.user = user
            st.session_state.session = session
            self.analysis_service.set_current_user(user.id)

        render_login_page(self.auth_service, on_login_success)

    def _render_main_application(self) -> None:
        """Render the main application for logged-in users."""
        # Set user context
        self.analysis_service.set_current_user(st.session_state.user.id)

        # Render sidebar
        self._render_sidebar()

        # Check for modals
        if st.session_state.show_settings:
            self._render_settings_modal()
            return

        if st.session_state.show_export:
            self._render_export_modal()
            return

        # Render main content
        if not st.session_state.current_analysis:
            render_welcome_screen(self._on_new_analysis)
            if st.session_state.show_uploader:
                self._render_uploader_dialog()
        else:
            self._render_main_layout()

        # Handle notifications
        self._handle_notifications()

    def _render_sidebar(self) -> None:
        """Render the main sidebar."""
        analyses = self.analysis_service.get_user_analyses()
        current_id = (
            st.session_state.current_analysis.id
            if st.session_state.current_analysis
            else None
        )

        selected_id = render_main_sidebar(
            user_id=st.session_state.user.id,
            analyses=analyses,
            current_analysis_id=current_id,
            on_new_analysis=self._on_new_analysis,
            on_select_analysis=self._on_select_analysis,
            on_delete_analysis=self._on_delete_analysis,
            on_settings_click=lambda: setattr(st.session_state, "show_settings", True),
            on_logout=self._on_logout,
        )

        if selected_id:
            self._on_select_analysis(selected_id)

    def _render_main_layout(self) -> None:
        """Render the main content layout with dual sidebar."""
        analysis = st.session_state.current_analysis

        # Header bar
        render_header_bar(
            analysis_name=analysis.name,
            on_save=self._on_save,
            on_export=lambda: setattr(st.session_state, "show_export", True),
            on_rename=self._on_rename,
        )

        st.markdown("---")

        # Main content with widget palette
        main_col, widget_col = st.columns([4, 1])

        with widget_col:
            render_widget_palette(
                data_schema=analysis.data_schema,
                on_add_visualization=self._on_add_visualization,
            )

        with main_col:
            current_slide = self._get_current_slide()

            render_canvas(
                slide=current_slide,
                data_service=self.data_service,
                analysis_id=analysis.id,
                on_update_visualization=self._on_update_visualization,
                on_delete_visualization=self._on_delete_visualization,
                on_add_comment=self._on_add_comment,
                data_schema=analysis.data_schema,
            )

            # Slide navigator
            if analysis.slides:
                render_slide_navigator(
                    slides=analysis.slides,
                    current_slide_id=st.session_state.current_slide_id,
                    on_slide_change=self._on_slide_change,
                    on_add_slide=self._on_add_slide,
                    on_delete_slide=self._on_delete_slide,
                )

        # Column mapping dialog
        if st.session_state.show_column_mapping and st.session_state.new_viz_type:
            self._render_column_mapping_dialog()

    def _render_uploader_dialog(self) -> None:
        """Render the file uploader dialog."""
        render_file_uploader(
            on_upload=self._process_uploaded_file,
            on_cancel=lambda: setattr(st.session_state, "show_uploader", False),
        )

    def _render_column_mapping_dialog(self) -> None:
        """Render the column mapping dialog for new visualizations."""
        analysis = st.session_state.current_analysis
        if not analysis or not analysis.data_schema:
            return

        render_column_mapping(
            data_schema=analysis.data_schema,
            viz_type=st.session_state.new_viz_type,
            on_map=self._on_column_mapped,
            on_cancel=self._on_column_mapping_cancel,
        )

    def _render_settings_modal(self) -> None:
        """Render the settings modal."""
        current_settings = st.session_state.user.settings or {}

        render_settings_modal(
            current_settings=current_settings,
            on_save=self._on_save_settings,
        )

        if st.button("Fechar", key="close_settings_btn"):
            st.session_state.show_settings = False
            st.rerun()

    def _render_export_modal(self) -> None:
        """Render the export modal."""
        analysis = st.session_state.current_analysis
        if not analysis:
            return

        render_export_dialog(
            analysis=analysis,
            on_export=self._on_export,
        )

        if st.button("Fechar", key="close_export_btn"):
            st.session_state.show_export = False
            st.rerun()

    # Callback methods
    def _on_new_analysis(self) -> None:
        """Handle new analysis button click."""
        st.session_state.show_uploader = True

    def _on_select_analysis(self, analysis_id: str) -> None:
        """Handle selection of an existing analysis."""
        analysis = self.analysis_service.get_analysis(analysis_id)
        if analysis:
            st.session_state.current_analysis = analysis
            if analysis.slides:
                st.session_state.current_slide_id = analysis.slides[0].id
            st.rerun()

    def _on_delete_analysis(self, analysis_id: str) -> None:
        """Handle deletion of an analysis."""
        self.analysis_service.delete_analysis(analysis_id)
        if (
            st.session_state.current_analysis
            and st.session_state.current_analysis.id == analysis_id
        ):
            st.session_state.current_analysis = None
            st.session_state.current_slide_id = None
        st.rerun()

    def _on_logout(self) -> None:
        """Handle user logout."""
        self.auth_service.logout(st.session_state.user.id)
        st.session_state.user = None
        st.session_state.session = None
        st.session_state.current_analysis = None
        st.session_state.current_slide_id = None
        st.rerun()

    def _on_save(self) -> None:
        """Handle save action."""
        if st.session_state.current_analysis:
            self.analysis_service.save_analysis(st.session_state.current_analysis)
            st.session_state.notification = ("Análise salva!", "success")

    def _on_rename(self, new_name: str) -> None:
        """Handle analysis rename."""
        if st.session_state.current_analysis:
            self.analysis_service.rename_analysis(
                st.session_state.current_analysis.id, new_name
            )
            st.session_state.current_analysis.name = new_name

    def _on_save_settings(self, settings: Dict[str, Any]) -> None:
        """Handle settings save."""
        self.auth_service.update_user_settings(st.session_state.user.id, settings)
        st.session_state.user.settings = settings

    def _on_add_visualization(self, viz_type: VisualizationType) -> None:
        """Handle add visualization button click."""
        st.session_state.new_viz_type = viz_type
        st.session_state.show_column_mapping = True

    def _on_column_mapped(self, config: Dict[str, Any]) -> None:
        """Handle column mapping completion."""
        analysis = st.session_state.current_analysis
        current_slide = self._get_current_slide()

        if not analysis or not current_slide:
            return

        viz_config = VisualizationConfig(
            visualization_type=config["visualization_type"],
            title=config.get("title", ""),
            x_column=config.get("x_column"),
            y_column=config.get("y_column"),
            color_column=config.get("color_column"),
            aggregation=config.get("aggregation", "sum"),
        )

        viz = self.analysis_service.add_visualization(
            analysis_id=analysis.id,
            slide_id=current_slide.id,
            config=viz_config,
        )

        if viz:
            # Cache data snapshot for tables
            if viz_config.visualization_type == VisualizationType.TABLE:
                df = self.data_service.get_cached_data(analysis.id)
                if df is not None:
                    data = df.head(100).to_pandas().to_dict(orient="records")
                    viz.data_snapshot = {"data": data, "columns": df.columns}
                    self.analysis_service.save_analysis(analysis)

            # Update local state
            updated_analysis = self.analysis_service.get_analysis(analysis.id)
            if updated_analysis:
                st.session_state.current_analysis = updated_analysis

        st.session_state.show_column_mapping = False
        st.session_state.new_viz_type = None
        st.rerun()

    def _on_column_mapping_cancel(self) -> None:
        """Handle column mapping cancellation."""
        st.session_state.show_column_mapping = False
        st.session_state.new_viz_type = None
        st.rerun()

    def _on_update_visualization(
        self, slide_id: str, viz_id: str, config: VisualizationConfig
    ) -> None:
        """Handle visualization update."""
        analysis = st.session_state.current_analysis
        if not analysis:
            return

        self.analysis_service.update_visualization(
            analysis_id=analysis.id,
            slide_id=slide_id,
            viz_id=viz_id,
            config=config,
        )

        # Update local state
        updated_analysis = self.analysis_service.get_analysis(analysis.id)
        if updated_analysis:
            st.session_state.current_analysis = updated_analysis

    def _on_delete_visualization(self, slide_id: str, viz_id: str) -> None:
        """Handle visualization deletion."""
        analysis = st.session_state.current_analysis
        if not analysis:
            return

        self.analysis_service.delete_visualization(
            analysis_id=analysis.id,
            slide_id=slide_id,
            viz_id=viz_id,
        )

        # Update local state
        updated_analysis = self.analysis_service.get_analysis(analysis.id)
        if updated_analysis:
            st.session_state.current_analysis = updated_analysis
        st.rerun()

    def _on_add_comment(self, slide_id: str, viz_id: str, comment: str) -> None:
        """Handle comment addition."""
        analysis = st.session_state.current_analysis
        if not analysis:
            return

        self.analysis_service.update_visualization(
            analysis_id=analysis.id,
            slide_id=slide_id,
            viz_id=viz_id,
            comment=comment,
        )

        # Update local state
        updated_analysis = self.analysis_service.get_analysis(analysis.id)
        if updated_analysis:
            st.session_state.current_analysis = updated_analysis

    def _on_slide_change(self, slide_id: str) -> None:
        """Handle slide change."""
        st.session_state.current_slide_id = slide_id

    def _on_add_slide(self) -> None:
        """Handle add slide action."""
        analysis = st.session_state.current_analysis
        if not analysis:
            return

        slide = self.analysis_service.add_slide(analysis.id)
        if slide:
            st.session_state.current_slide_id = slide.id
            updated_analysis = self.analysis_service.get_analysis(analysis.id)
            if updated_analysis:
                st.session_state.current_analysis = updated_analysis
            st.rerun()

    def _on_delete_slide(self, slide_id: str) -> None:
        """Handle slide deletion."""
        analysis = st.session_state.current_analysis
        if not analysis:
            return

        self.analysis_service.delete_slide(analysis.id, slide_id)

        updated_analysis = self.analysis_service.get_analysis(analysis.id)
        if updated_analysis:
            st.session_state.current_analysis = updated_analysis
            if updated_analysis.slides:
                st.session_state.current_slide_id = updated_analysis.slides[0].id
        st.rerun()

    def _on_export(self, analysis: Analysis, options: Dict[str, Any]) -> Optional[str]:
        """Handle export action."""
        try:
            # Generate chart images
            chart_images = {}
            df = self.data_service.get_cached_data(analysis.id)

            if df is not None:
                for slide in analysis.slides:
                    for viz in slide.visualizations:
                        if (
                            viz.config
                            and viz.config.visualization_type != VisualizationType.TABLE
                        ):
                            try:
                                fig = self.chart_factory.create_chart(df, viz.config)
                                img_bytes = self.chart_factory.export_figure_to_bytes(
                                    fig
                                )
                                chart_images[viz.id] = img_bytes
                            except Exception as e:
                                print(f"Error generating chart: {e}")

            # Export based on format
            from domain.value_objects import ExportOptions

            export_options = ExportOptions(
                format=options.get("format", "pdf"),
                paper_size=options.get("paper_size", "a4"),
                orientation=options.get("orientation", "portrait"),
                include_comments=options.get("include_comments", True),
                header_text=options.get("header_text", ""),
                footer_text=options.get("footer_text", ""),
            )

            if export_options.format == "pdf":
                return self.export_service.export_to_pdf(
                    analysis, export_options, chart_images
                )
            elif export_options.format == "latex":
                return self.export_service.export_to_latex(
                    analysis, export_options, chart_images
                )
            else:
                return self.export_service.export_to_html(
                    analysis, export_options, chart_images
                )

        except Exception as e:
            st.error(f"Erro na exportação: {str(e)}")
            return None

    def _process_uploaded_file(self, uploaded_file: Any) -> None:
        """Process an uploaded XLSX file."""
        try:
            # Create new analysis
            name = uploaded_file.name.rsplit(".", 1)[0]
            analysis = self.analysis_service.create_analysis(name)

            if not analysis:
                st.error("Falha ao criar análise")
                return

            # Load data
            schema, df = self.data_service.load_excel_from_streamlit(
                uploaded_file, analysis.id
            )

            # Update analysis with schema
            self.analysis_service.set_data_schema(analysis.id, schema)

            # Update session state
            analysis = self.analysis_service.get_analysis(analysis.id)
            st.session_state.current_analysis = analysis
            if analysis and analysis.slides:
                st.session_state.current_slide_id = analysis.slides[0].id

            st.session_state.show_uploader = False
            st.success(f"✓ Carregado {schema.row_count} linhas de {uploaded_file.name}")
            st.rerun()

        except Exception as e:
            st.error(f"Erro ao carregar arquivo: {str(e)}")

    def _get_current_slide(self) -> Optional[Slide]:
        """Get the current slide being edited."""
        analysis = st.session_state.current_analysis
        if not analysis:
            return None

        slide_id = st.session_state.current_slide_id
        if slide_id:
            return analysis.get_slide(slide_id)

        if analysis.slides:
            return analysis.slides[0]

        return None

    def _handle_notifications(self) -> None:
        """Handle and display notifications."""
        notification = st.session_state.notification
        if notification:
            message, level = notification
            if level == "success":
                st.success(message)
            elif level == "error":
                st.error(message)
            elif level == "warning":
                st.warning(message)
            else:
                st.info(message)
            st.session_state.notification = None


def main():
    """Application entry point."""
    app = DashboardBuilderApp()
    app.run()


if __name__ == "__main__":
    main()
