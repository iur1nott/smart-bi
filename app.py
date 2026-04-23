"""
SmartXL Dashboard Builder - Main Application Entry Point
A Streamlit application for building dashboards from Excel data.
Following Clean Architecture with SOLID principles.

Features:
- User authentication with PostgreSQL
- S3-compatible file storage (AWS, Supabase, MinIO)
- Dashboard and visualization management
- Canvas-based visualization editing
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
    Dashboard,
    Visualization,
    VisualizationConfig,
    File,
    FileSheet,
)

# Infrastructure imports
from infrastructure.database import init_database, get_database
from infrastructure.repositories import (
    UserRepositoryImpl,
    FileRepositoryImpl,
    DashboardRepositoryImpl,
)
from infrastructure.auth import JWTHandler
from infrastructure.storage import get_s3_client

# Use case imports
from use_cases.auth_service import AuthService
from use_cases.file_service import FileService
from use_cases.dashboard_service import DashboardService
from use_cases.data_service import DataService
from use_cases.export_service import ExportService

# Presentation imports
from presentation.login import render_login_page, render_user_menu
from presentation.sidebar import render_main_sidebar, render_file_uploader
from presentation.widget_palette import render_widget_palette, render_column_mapping
from presentation.canvas import render_canvas
from presentation.components import (
    render_settings_modal,
    render_export_dialog,
    render_welcome_screen,
    render_notification,
    render_header_bar,
)

# Configure Streamlit page
st.set_page_config(
    page_title="SmartXL - Dashboard Builder",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": "SmartXL - Crie dashboards profissionais",
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


class SmartXLApp:
    """Main application class following the Facade pattern."""

    def __init__(self):
        """Initialize the application with all required services."""
        self._init_session_state()
        self._init_services()

    def _init_session_state(self) -> None:
        """Initialize Streamlit session state with default values."""
        defaults = {
            "user": None,
            "current_dashboard": None,
            "current_sheet_id": None,
            "show_settings": False,
            "show_export": False,
            "show_uploader": False,
            "show_column_mapping": False,
            "new_viz_type": None,
            "editing_viz_id": None,
            "notification": None,
            "data_cache": {},
            "sheet_cache": {},
            "current_file": None,
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
        file_repo = FileRepositoryImpl()
        dashboard_repo = DashboardRepositoryImpl()

        # Initialize services
        jwt_handler = JWTHandler()
        self.auth_service = AuthService(user_repo, None, jwt_handler)
        self.file_service = FileService(file_repo)
        self.dashboard_service = DashboardService(dashboard_repo, file_repo)
        self.data_service = DataService()
        self.export_service = ExportService()

    def run(self) -> None:
        """Run the main application."""
        # Check if user is logged in
        if not st.session_state.user:
            self._render_login_flow()
        else:
            self._render_main_application()

    def _render_login_flow(self) -> None:
        """Render the login/registration flow."""

        def on_login_success(user: User, session: Any) -> None:
            st.session_state.user = user
            self.dashboard_service.set_current_user(user.user_id)

        render_login_page(self.auth_service, on_login_success)

    def _render_main_application(self) -> None:
        """Render the main application for logged-in users."""
        # Set user context
        self.dashboard_service.set_current_user(st.session_state.user.user_id)

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
        if not st.session_state.current_dashboard:
            render_welcome_screen(self._on_new_dashboard)
            if st.session_state.show_uploader:
                self._render_uploader_dialog()
        else:
            self._render_main_layout()

        # Handle notifications
        self._handle_notifications()

    def _render_sidebar(self) -> None:
        """Render the main sidebar."""
        dashboards = self.dashboard_service.get_user_dashboards()
        current_id = (
            st.session_state.current_dashboard.dashboard_id
            if st.session_state.current_dashboard
            else None
        )

        selected_id = render_main_sidebar(
            user_id=st.session_state.user.user_id,
            dashboards=dashboards,
            current_dashboard_id=current_id,
            on_new_dashboard=self._on_new_dashboard,
            on_select_dashboard=self._on_select_dashboard,
            on_delete_dashboard=self._on_delete_dashboard,
            on_settings_click=lambda: setattr(st.session_state, "show_settings", True),
            on_logout=self._on_logout,
        )

        if selected_id:
            self._on_select_dashboard(selected_id)

    def _render_main_layout(self) -> None:
        """Render the main content layout with dual sidebar."""
        dashboard = st.session_state.current_dashboard

        # Header bar
        render_header_bar(
            analysis_name=dashboard.title,
            on_save=self._on_save,
            on_export=lambda: setattr(st.session_state, "show_export", True),
            on_rename=self._on_rename,
        )

        st.markdown("---")

        # Main content with widget palette
        main_col, widget_col = st.columns([4, 1])

        # Get current sheet
        current_sheet = self._get_current_sheet()

        with widget_col:
            render_widget_palette(
                sheet=current_sheet,
                on_add_visualization=self._on_add_visualization,
            )

        with main_col:
            # Get sheet_id for data
            sheet_id = st.session_state.current_sheet_id
            if not sheet_id and dashboard.visualizations:
                sheet_id = dashboard.visualizations[0].sheet_id
                st.session_state.current_sheet_id = sheet_id

            render_canvas(
                visualizations=dashboard.visualizations,
                data_service=self.data_service,
                sheet_id=sheet_id or "",
                on_update_visualization=self._on_update_visualization,
                on_delete_visualization=self._on_delete_visualization,
                on_add_comment=self._on_add_comment,
                sheet=current_sheet,
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
        sheet = self._get_current_sheet()
        if not sheet:
            return

        render_column_mapping(
            sheet=sheet,
            viz_type=st.session_state.new_viz_type,
            on_map=self._on_column_mapped,
            on_cancel=self._on_column_mapping_cancel,
        )

    def _render_settings_modal(self) -> None:
        """Render the settings modal."""
        render_settings_modal(
            current_settings={},
            on_save=self._on_save_settings,
        )

        if st.button("Fechar", key="close_settings_btn"):
            st.session_state.show_settings = False
            st.rerun()

    def _render_export_modal(self) -> None:
        """Render the export modal."""
        dashboard = st.session_state.current_dashboard
        if not dashboard:
            return

        render_export_dialog(
            analysis=dashboard,
            on_export=self._on_export,
        )

        if st.button("Fechar", key="close_export_btn"):
            st.session_state.show_export = False
            st.rerun()

    # Callback methods
    def _on_new_dashboard(self) -> None:
        """Handle new dashboard button click."""
        st.session_state.show_uploader = True

    def _on_select_dashboard(self, dashboard_id: str) -> None:
        """Handle selection of an existing dashboard."""
        dashboard = self.dashboard_service.get_dashboard(dashboard_id)
        if dashboard:
            st.session_state.current_dashboard = dashboard
            if dashboard.visualizations:
                st.session_state.current_sheet_id = dashboard.visualizations[0].sheet_id
            st.rerun()

    def _on_delete_dashboard(self, dashboard_id: str) -> None:
        """Handle deletion of a dashboard."""
        self.dashboard_service.delete_dashboard(dashboard_id)
        if (
            st.session_state.current_dashboard
            and st.session_state.current_dashboard.dashboard_id == dashboard_id
        ):
            st.session_state.current_dashboard = None
            st.session_state.current_sheet_id = None
        st.rerun()

    def _on_logout(self) -> None:
        """Handle user logout."""
        st.session_state.user = None
        st.session_state.current_dashboard = None
        st.session_state.current_sheet_id = None
        st.rerun()

    def _on_save(self) -> None:
        """Handle save action."""
        if st.session_state.current_dashboard:
            self.dashboard_service.save_dashboard(st.session_state.current_dashboard)
            st.session_state.notification = ("Dashboard salvo!", "success")

    def _on_rename(self, new_name: str) -> None:
        """Handle dashboard rename."""
        if st.session_state.current_dashboard:
            self.dashboard_service.update_dashboard_title(
                st.session_state.current_dashboard.dashboard_id, new_name
            )
            st.session_state.current_dashboard.title = new_name

    def _on_save_settings(self, settings: Dict[str, Any]) -> None:
        """Handle settings save."""
        pass  # Settings not implemented in new schema

    def _on_add_visualization(self, viz_type: str) -> None:
        """Handle add visualization button click."""
        st.session_state.new_viz_type = viz_type
        st.session_state.show_column_mapping = True

    def _on_column_mapped(self, config: Dict[str, Any]) -> None:
        """Handle column mapping completion."""
        dashboard = st.session_state.current_dashboard
        if not dashboard:
            return

        sheet_id = st.session_state.current_sheet_id
        if not sheet_id:
            return

        viz_config = VisualizationConfig(
            title=config.get("title", ""),
            x_column=config.get("x_column"),
            y_column=config.get("y_column"),
            color_column=config.get("color_column"),
            aggregation=config.get("aggregation", "sum"),
        )

        viz = self.dashboard_service.add_visualization(
            dashboard_id=dashboard.dashboard_id,
            sheet_id=sheet_id,
            viz_type=st.session_state.new_viz_type,
            config=viz_config,
        )

        if viz:
            # Update local state
            updated_dashboard = self.dashboard_service.get_dashboard(
                dashboard.dashboard_id
            )
            if updated_dashboard:
                st.session_state.current_dashboard = updated_dashboard

        st.session_state.show_column_mapping = False
        st.session_state.new_viz_type = None
        st.rerun()

    def _on_column_mapping_cancel(self) -> None:
        """Handle column mapping cancellation."""
        st.session_state.show_column_mapping = False
        st.session_state.new_viz_type = None
        st.rerun()

    def _on_update_visualization(
        self, viz_id: str, config: VisualizationConfig
    ) -> None:
        """Handle visualization update."""
        dashboard = st.session_state.current_dashboard
        if not dashboard:
            return

        self.dashboard_service.update_visualization(
            viz_id=viz_id,
            config=config,
        )

        # Update local state
        updated_dashboard = self.dashboard_service.get_dashboard(dashboard.dashboard_id)
        if updated_dashboard:
            st.session_state.current_dashboard = updated_dashboard

    def _on_delete_visualization(self, viz_id: str) -> None:
        """Handle visualization deletion."""
        dashboard = st.session_state.current_dashboard
        if not dashboard:
            return

        self.dashboard_service.delete_visualization(viz_id)

        # Update local state
        updated_dashboard = self.dashboard_service.get_dashboard(dashboard.dashboard_id)
        if updated_dashboard:
            st.session_state.current_dashboard = updated_dashboard
        st.rerun()

    def _on_add_comment(self, viz_id: str, comment: str) -> None:
        """Handle comment addition."""
        # Comments stored in visualization transient data
        dashboard = st.session_state.current_dashboard
        if not dashboard:
            return

        viz = dashboard.get_visualization(viz_id)
        if viz:
            viz.comment = comment

    def _on_export(
        self, dashboard: Dashboard, options: Dict[str, Any]
    ) -> Optional[str]:
        """Handle export action."""
        # Export functionality
        st.info("Export functionality coming soon!")
        return None

    def _process_uploaded_file(self, uploaded_file: Any) -> None:
        """Process an uploaded XLSX file."""
        try:
            # Upload file to S3 and save metadata
            file_entity = self.file_service.upload_file(
                file_data=uploaded_file.getvalue(),
                filename=uploaded_file.name,
                user_id=st.session_state.user.user_id,
            )

            if not file_entity:
                st.error("Falha ao carregar arquivo")
                return

            # Create new dashboard
            name = uploaded_file.name.rsplit(".", 1)[0]
            dashboard = self.dashboard_service.create_dashboard(
                title=name,
                file_id=file_entity.file_id,
            )

            if not dashboard:
                st.error("Falha ao criar dashboard")
                return

            # Load data into cache
            sheet, df = self.data_service.load_excel_from_bytes(
                file_bytes=uploaded_file.getvalue(),
                file_name=uploaded_file.name,
                file_id=file_entity.file_id,
            )

            if sheet and df:
                # Store sheet reference
                st.session_state.current_sheet_id = sheet.sheet_id
                st.session_state.current_file = file_entity

                # Create a visualization with the first sheet
                self.dashboard_service.add_visualization(
                    dashboard_id=dashboard.dashboard_id,
                    sheet_id=sheet.sheet_id,
                    viz_type="table",
                    config=VisualizationConfig(title="Data Preview"),
                )

            # Update session state
            dashboard = self.dashboard_service.get_dashboard(dashboard.dashboard_id)
            st.session_state.current_dashboard = dashboard
            st.session_state.show_uploader = False
            st.success(
                f"✓ Carregado {len(df) if df is not None else 0} linhas de {uploaded_file.name}"
            )
            st.rerun()

        except Exception as e:
            st.error(f"Erro ao carregar arquivo: {str(e)}")

    def _get_current_sheet(self) -> Optional[FileSheet]:
        """Get the current sheet being edited."""
        # Get from current file
        if st.session_state.current_file:
            file = st.session_state.current_file
            if file.sheets:
                sheet_id = st.session_state.current_sheet_id
                if sheet_id:
                    for sheet in file.sheets:
                        if sheet.sheet_id == sheet_id:
                            return sheet
                return file.sheets[0]
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
    app = SmartXLApp()
    app.run()


if __name__ == "__main__":
    main()
