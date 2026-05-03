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

import logging
import os
import sys
from typing import Any, Dict, Optional

import polars as pl
import streamlit as st

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logger = logging.getLogger(__name__)

# Domain imports
from domain.entities import (
    Analysis,
    ColumnType,
    Dashboard,
    File,
    FileSheet,
    User,
    Visualization,
    VisualizationConfig,
    VisualizationType,
)
from domain.value_objects import ExportOptions
from infrastructure.auth import JWTHandler

# Infrastructure imports
from infrastructure.chart_factory import ChartFactory
from infrastructure.database import get_database, init_database
from infrastructure.pdf_generator import PDFGenerator
from infrastructure.repositories import (
    DashboardRepositoryImpl,
    FileRepositoryImpl,
    UserRepositoryImpl,
)
from infrastructure.storage import get_s3_client
from presentation.canvas import render_canvas, render_slide_navigator
from presentation.components import (
    render_export_dialog,
    render_header_bar,
    render_notification,
    render_settings_modal,
    render_welcome_screen,
)

# Presentation imports
from presentation.login import render_login_page, render_user_menu
from presentation.sidebar import (
    render_file_uploader,
    render_main_sidebar,
    render_sidebar,
)
from presentation.widget_palette import (
    render_column_mapper,
    render_column_mapping,
    render_viz_config_dialog,
    render_widget_palette,
)
from presentation.widgets import (
    render_data_preview,
    render_widget_palette as render_widget_palette_v2,
)

# Use case imports
from use_cases.auth_service import AuthService
from use_cases.dashboard_service import DashboardService
from use_cases.data_service import DataService
from use_cases.export_service import ExportService
from use_cases.file_service import FileService
from utils.session_state import (
    SessionStateManager,
    init_session_state,
    get_state,
    set_state,
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

# Apply custom CSS (pastel design tokens ported from dev-03)
st.markdown(
    """
<style>
    /* ── Design tokens — pastel palette ────────────────────────────────────── */
    :root {
        --primary:      #7BAFC8;
        --primary-dark: #5B8FA8;
        --surface:      #FAF9F6;
        --surface-alt:  #F0EDE8;
        --border:       #DDD8D0;
        --text-main:    #2C2B28;
        --text-muted:   #7A7870;
        --success:      #80B498;
        --danger:       #C4806A;
        --warning:      #C4A460;
        --radius:       10px;
        --radius-sm:    6px;
        --shadow-sm:    0 1px 3px rgba(0,0,0,.04), 0 1px 2px rgba(0,0,0,.03);
        --shadow-md:    0 4px 12px rgba(0,0,0,.07), 0 2px 4px rgba(0,0,0,.03);
    }

    /* ── Layout ────────────────────────────────────────────────────────────── */
    .main .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 1400px;
        background-color: var(--surface);
    }
    [data-testid="stAppViewContainer"] {
        background-color: var(--surface);
    }

    /* ── Sidebar ───────────────────────────────────────────────────────────── */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #2E2C2A 0%, #1C1B18 100%);
    }
    section[data-testid="stSidebar"] * {
        color: #C8C4BC !important;
    }
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #EDE9E3 !important;
    }
    section[data-testid="stSidebar"] .stButton > button {
        background: rgba(255,255,255,.06);
        border: 1px solid rgba(255,255,255,.10);
        color: #C8C4BC !important;
        border-radius: var(--radius-sm);
        transition: background .15s;
    }
    section[data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(255,255,255,.11);
    }
    section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {
        background: rgba(255,255,255,.04);
        border: 1px dashed rgba(255,255,255,.18);
        border-radius: var(--radius-sm);
    }

    /* ── Buttons ───────────────────────────────────────────────────────────── */
    .stButton > button {
        border-radius: var(--radius-sm);
        font-weight: 500;
        transition: all .15s ease;
        border: 1px solid var(--border);
        background: white;
        color: var(--text-main) !important;
        font-size: 0.83rem;
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: var(--shadow-sm);
        background: var(--surface-alt);
    }
    .stButton > button[kind="primary"] {
        background: var(--primary);
        border-color: var(--primary-dark);
        color: white !important;
    }
    .stButton > button[kind="primary"]:hover {
        background: var(--primary-dark);
        box-shadow: 0 4px 12px rgba(91,143,168,.30);
    }

    /* ── Inputs & Selects ──────────────────────────────────────────────────── */
    .stTextInput > div > div > input,
    .stSelectbox > div > div,
    .stMultiSelect > div > div,
    .stNumberInput > div > div > input {
        border-radius: var(--radius-sm) !important;
        border-color: var(--border) !important;
        background-color: white !important;
        color: var(--text-main) !important;
        font-size: 0.875rem;
    }
    .stTextInput > div > div > input:focus,
    .stSelectbox > div > div:focus-within {
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 3px rgba(123,175,200,.18) !important;
    }

    /* ── Expanders (Filtros / Comentários) ─────────────────────────────────── */
    .streamlit-expanderHeader {
        font-weight: 600;
        font-size: 0.82rem;
        color: var(--text-muted) !important;
        background: var(--surface-alt);
        border-radius: var(--radius-sm);
        border: 1px solid var(--border);
        padding: 6px 10px !important;
    }
    .streamlit-expanderHeader:hover {
        background: var(--border);
    }
    .streamlit-expanderContent {
        border: 1px solid var(--border);
        border-top: none;
        border-radius: 0 0 var(--radius-sm) var(--radius-sm);
        background: white;
        padding: 10px 12px !important;
    }

    /* ── Visualization card wrapper ─────────────────────────────────────────── */
    .viz-card {
        background: #FEFEFE;
        border: 1px solid var(--border);
        border-radius: var(--radius);
        box-shadow: var(--shadow-sm);
        padding: 16px 18px 12px;
        margin-bottom: 18px;
        transition: box-shadow .2s;
    }
    .viz-card:hover {
        box-shadow: var(--shadow-md);
        border-color: #C8C4BC;
    }
    .viz-card-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 8px;
    }
    .viz-card-title {
        font-size: 0.88rem;
        font-weight: 600;
        color: var(--text-main);
        margin: 0;
        letter-spacing: -0.01em;
    }

    /* ── Metric card ───────────────────────────────────────────────────────── */
    .stMetric > div {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 1rem 1.25rem;
        box-shadow: var(--shadow-sm);
    }

    /* ── Dataframe ─────────────────────────────────────────────────────────── */
    .stDataFrame {
        border: 1px solid var(--border);
        border-radius: var(--radius);
        overflow: hidden;
        box-shadow: var(--shadow-sm);
    }

    /* ── Plotly chart ───────────────────────────────────────────────────────── */
    .stPlotlyChart {
        border-radius: var(--radius);
        overflow: hidden;
    }

    /* ── Tabs ──────────────────────────────────────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 3px;
        background: var(--surface-alt);
        border-radius: var(--radius-sm);
        padding: 4px;
        border: 1px solid var(--border);
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: var(--radius-sm);
        font-weight: 500;
        font-size: 0.83rem;
        color: var(--text-muted);
        padding: 5px 12px;
    }
    .stTabs [aria-selected="true"] {
        background: white !important;
        color: var(--primary-dark) !important;
        box-shadow: var(--shadow-sm);
    }

    /* ── Alerts / Info boxes ────────────────────────────────────────────────── */
    .stAlert {
        border-radius: var(--radius-sm);
        border: none;
        font-size: 0.875rem;
    }

    /* ── Captions & labels ──────────────────────────────────────────────────── */
    .stCaption, small {
        color: var(--text-muted) !important;
        font-size: 0.78rem;
    }

    /* ── Dividers ───────────────────────────────────────────────────────────── */
    hr {
        border: none;
        border-top: 1px solid var(--border);
        margin: 1rem 0;
    }

    /* ── Toast / Notification ───────────────────────────────────────────────── */
    [data-testid="stToast"] {
        border-radius: var(--radius);
        font-size: 0.875rem;
    }

    /* ── Scrollbar ──────────────────────────────────────────────────────────── */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: var(--surface-alt); }
    ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: #94A3B8; }

    /* ── Hide Streamlit chrome ──────────────────────────────────────────────── */
    #MainMenu { visibility: hidden; }
    footer    { visibility: hidden; }
    header    { visibility: hidden; }
    [data-testid="stToolbar"] { display: none; }
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
            "show_column_type_editor": False,
            "pending_upload": None,
            "new_viz_type": None,
            "editing_viz_id": None,
            "notification": None,
            "data_cache": {},
            "sheet_cache": {},
            "current_file": None,
            "dashboards_cache": None,
            "dashboards_cache_time": None,
        }

        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value

    def _init_services(self) -> None:
        """
        Initialize application services once per Streamlit session and reuse
        them across reruns. The previous implementation rebuilt every
        repository and re-ran ``init_database()`` (which calls
        ``Base.metadata.create_all``) on every button click — Postgres
        round-trips dominated each interaction. Caching here is the
        single biggest perf win.
        """
        if not st.session_state.get("_services_ready"):
            try:
                init_database()
            except Exception as e:
                st.warning(f"Database connection issue: {e}")

            user_repo = UserRepositoryImpl()
            file_repo = FileRepositoryImpl()
            dashboard_repo = DashboardRepositoryImpl()
            jwt_handler = JWTHandler()

            st.session_state.auth_service = AuthService(user_repo, None, jwt_handler)
            st.session_state.file_service = FileService(file_repo)
            st.session_state.dashboard_service = DashboardService(
                dashboard_repo, file_repo
            )
            st.session_state.data_service = DataService()
            st.session_state.export_service = ExportService()
            st.session_state._services_ready = True

        self.auth_service = st.session_state.auth_service
        self.file_service = st.session_state.file_service
        self.dashboard_service = st.session_state.dashboard_service
        self.data_service = st.session_state.data_service
        self.export_service = st.session_state.export_service
        self.chart_factory = ChartFactory()
        self.pdf_generator = PDFGenerator()

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

        # Column-type editor takes the whole canvas while pending
        if st.session_state.show_column_type_editor:
            self._render_column_type_editor_screen()
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
        import time

        cache_age = (
            time.time() - st.session_state.dashboards_cache_time
            if st.session_state.dashboards_cache_time
            else float("inf")
        )

        # Refresh cache if older than 30 seconds or not set
        if st.session_state.dashboards_cache is None or cache_age > 30:
            st.session_state.dashboards_cache = (
                self.dashboard_service.get_user_dashboards()
            )
            st.session_state.dashboards_cache_time = time.time()

        dashboards = st.session_state.dashboards_cache
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

        st.markdown(
            "<hr style='border:none;border-top:1px solid #E2E8F0;margin:8px 0 16px;'/>",
            unsafe_allow_html=True,
        )

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
                dashboard_id=dashboard.dashboard_id,
                on_update_measures=self._on_update_measures,
            )

        # Column mapping dialog (quick-add flow from widget palette button)
        if st.session_state.show_column_mapping and st.session_state.new_viz_type:
            self._render_column_mapping_dialog()

        # Edit-viz dialog (triggered by ✏️ button on a card)
        editing_id = st.session_state.get("editing_viz_id")
        if editing_id and current_sheet:
            viz = dashboard.get_visualization(editing_id)
            if viz:
                def _on_save_config(cfg):
                    self._on_update_visualization(editing_id, cfg)
                    st.session_state.editing_viz_id = None
                    st.rerun()
                def _on_cancel_config():
                    st.session_state.editing_viz_id = None
                    st.rerun()
                render_viz_config_dialog(
                    viz_type=viz.viz_type,
                    sheet=current_sheet,
                    existing_config=viz.config,
                    on_save=_on_save_config,
                    on_cancel=_on_cancel_config,
                    is_new=False,
                )

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
        """Render the export modal with chart images embedded."""
        dashboard = st.session_state.current_dashboard
        if not dashboard:
            return

        # Render charts to PNG for embedding in PDF/HTML
        chart_images: Dict[str, bytes] = {}
        df = self.data_service.get_cached_sheet(st.session_state.current_sheet_id or "")
        if df is not None:
            from presentation.canvas import _VIZ_TYPE_MAP
            for viz in dashboard.visualizations:
                if viz.config and viz.viz_type not in ("table", "metric_card", "measures"):
                    try:
                        vt = _VIZ_TYPE_MAP.get(viz.viz_type)
                        if vt:
                            fig = self.chart_factory.create_chart(df, viz.config, vt)
                            chart_images[viz.viz_id] = self.chart_factory.export_figure_to_bytes(fig)
                    except Exception:
                        pass

        render_export_dialog(
            dashboard=dashboard,
            export_service=self.export_service,
            chart_images=chart_images,
        )

        if st.button("Fechar", key="close_export_btn"):
            st.session_state.show_export = False
            st.rerun()

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

    # ── Callback methods ──────────────────────────────────────────────────────

    def _on_new_dashboard(self) -> None:
        """Handle new dashboard button click."""
        st.session_state.show_uploader = True

    def _on_select_dashboard(self, dashboard_id: str) -> None:
        """Handle selection of an existing dashboard."""
        dashboard = self.dashboard_service.get_dashboard(dashboard_id)
        if dashboard:
            st.session_state.current_dashboard = dashboard

            # Set current_sheet_id from visualizations
            if dashboard.visualizations:
                st.session_state.current_sheet_id = dashboard.visualizations[0].sheet_id

            # Load file data from S3 if available
            if dashboard.file:
                file_entity = dashboard.file
                sheet_id = st.session_state.current_sheet_id

                # Check if data is already cached
                if sheet_id and self.data_service.get_cached_sheet(sheet_id) is None:
                    # Find the sheet entity to get sheet_name
                    sheet = self.file_service.get_sheet(sheet_id)

                    if sheet and file_entity.storage_path:
                        # Load data from S3
                        loaded_sheet, df = self.data_service.load_file_from_s3(
                            storage_path=file_entity.storage_path,
                            file_id=file_entity.file_id,
                            sheet_name=sheet.sheet_name if sheet else None,
                            existing_sheet=sheet,
                        )

                        if loaded_sheet and df is not None:
                            logger.info(f"Loaded data from S3 for sheet {sheet_id}")

                # Set current_file for widget palette to work
                st.session_state.current_file = file_entity

            st.rerun()

    def _on_delete_dashboard(self, dashboard_id: str) -> None:
        """
        Delete a dashboard. Visualizations cascade-delete via SQLAlchemy,
        but the file (and its sheets, columns, S3 object) are owned
        independently — so we explicitly drop any file that no other
        dashboard still references.
        """
        # Resolve files referenced by this dashboard's visualizations BEFORE
        # the dashboard is deleted, otherwise the join is gone.
        dashboard = self.dashboard_service.get_dashboard(dashboard_id)
        candidate_file_ids: set = set()
        if dashboard:
            for viz in dashboard.visualizations:
                sheet = self.file_service.get_sheet(viz.sheet_id)
                if sheet and sheet.file_id:
                    candidate_file_ids.add(sheet.file_id)

        if not self.dashboard_service.delete_dashboard(dashboard_id):
            st.session_state.notification = ("Falha ao excluir dashboard", "error")
            st.rerun()
            return

        # Drop S3 + DB rows for files no other dashboard uses any more.
        for file_id in candidate_file_ids:
            if not self.dashboard_service.is_file_used_by_any_dashboard(file_id):
                self.file_service.delete_file(file_id)

        st.session_state.dashboards_cache = None
        st.session_state.dashboards_cache_time = None
        if (
            st.session_state.current_dashboard
            and st.session_state.current_dashboard.dashboard_id == dashboard_id
        ):
            st.session_state.current_dashboard = None
            st.session_state.current_sheet_id = None
            st.session_state.current_file = None
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
        dashboard = st.session_state.current_dashboard
        if not dashboard:
            return

        viz = dashboard.get_visualization(viz_id)
        if viz:
            viz.comment = comment

    def _on_update_measures(self, measures: list) -> None:
        """Persist measures list in session_state (in-memory only)."""
        dashboard = st.session_state.current_dashboard
        if dashboard:
            key = f"measures_{dashboard.dashboard_id}"
            st.session_state[key] = measures

    def _process_uploaded_file(self, uploaded_file: Any) -> None:
        """
        Stage one of upload: parse the file in-memory, detect column types,
        and route the user to the column-type editor screen. Nothing is
        persisted to S3 or Postgres until the user confirms.
        """
        try:
            file_bytes = uploaded_file.getvalue()
            sheet, df = self.data_service.load_excel_from_bytes(
                file_bytes=file_bytes,
                file_name=uploaded_file.name,
                file_id="pending",
            )

            if sheet is None or df is None:
                st.error("Falha ao ler arquivo")
                return

            st.session_state.pending_upload = {
                "file_bytes": file_bytes,
                "filename": uploaded_file.name,
                "sheet": sheet,
                "df": df,
            }
            st.session_state.show_uploader = False
            st.session_state.show_column_type_editor = True
            st.rerun()

        except Exception as e:
            st.error(f"Erro ao ler arquivo: {str(e)}")

    def _render_column_type_editor_screen(self) -> None:
        """Show the post-upload column-type editor."""
        pending = st.session_state.pending_upload
        if not pending:
            st.session_state.show_column_type_editor = False
            st.rerun()
            return

        st.markdown(
            "<h2 style='color:#1E293B;font-weight:700;margin-bottom:4px;'>"
            "🛠️ Configurar Colunas</h2>"
            "<p style='color:#64748B;margin-bottom:24px;'>"
            f"Arquivo <b>{pending['filename']}</b> — "
            "confirme ou ajuste o tipo detectado para cada coluna.</p>",
            unsafe_allow_html=True,
        )

        mapping = render_column_mapper(pending["sheet"], df=pending["df"])

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        col1, col2 = st.columns([3, 1])
        with col1:
            confirm = st.button(
                "✓ Validar e criar dashboard",
                type="primary",
                use_container_width=True,
            )
        with col2:
            cancel = st.button("✗ Cancelar", use_container_width=True)

        if cancel:
            st.session_state.pending_upload = None
            st.session_state.show_column_type_editor = False
            st.rerun()
        elif confirm:
            self._confirm_column_mapping(mapping)

    def _confirm_column_mapping(self, mapping: Dict[str, str]) -> None:
        """
        Stage two of upload: apply the user-confirmed type mapping, upload
        the file to S3, persist file/sheet/columns/dashboard to Postgres,
        and seed the dashboard with a default table viz.
        """
        pending = st.session_state.pending_upload
        if not pending:
            return

        try:
            df_typed = self.data_service.cast_column_types(pending["df"], mapping)

            # Apply the user's choices to the in-memory sheet so file_service
            # persists the right data_types when it saves the new file rows.
            for col in pending["sheet"].columns:
                if col.column_name in mapping:
                    col.data_type = mapping[col.column_name]

            file_entity = self.file_service.upload_file(
                file_data=pending["file_bytes"],
                filename=pending["filename"],
                user_id=st.session_state.user.user_id,
            )

            if not file_entity:
                st.error("Falha ao carregar arquivo")
                return

            # Override DB-side detected types with the user's choices
            if file_entity.sheets:
                first_sheet = file_entity.sheets[0]
                for col in first_sheet.columns:
                    if col.column_name in mapping:
                        col.data_type = mapping[col.column_name]
                self.file_service._file_repo.save_file(file_entity)
            else:
                st.error("Falha ao extrair planilhas do arquivo")
                return

            name = pending["filename"].rsplit(".", 1)[0]
            dashboard = self.dashboard_service.create_dashboard(
                title=name,
                file_id=file_entity.file_id,
            )
            if not dashboard:
                st.error("Falha ao criar dashboard")
                return

            # Cache typed dataframe under the canonical sheet_id from the DB
            self.data_service.set_cached_sheet(first_sheet.sheet_id, df_typed)
            self.data_service.set_cached_data(file_entity.file_id, df_typed)

            st.session_state.current_sheet_id = first_sheet.sheet_id
            st.session_state.current_file = file_entity

            self.dashboard_service.add_visualization(
                dashboard_id=dashboard.dashboard_id,
                sheet_id=first_sheet.sheet_id,
                viz_type="table",
                config=VisualizationConfig(title="Data Preview"),
            )

            st.session_state.current_dashboard = self.dashboard_service.get_dashboard(
                dashboard.dashboard_id
            )
            st.session_state.dashboards_cache = None
            st.session_state.dashboards_cache_time = None
            st.session_state.pending_upload = None
            st.session_state.show_column_type_editor = False
            st.success(
                f"✓ Carregado {len(df_typed)} linhas de {pending['filename']}"
            )
            st.rerun()

        except Exception as e:
            st.error(f"Erro ao confirmar mapeamento: {str(e)}")

    def _get_current_sheet(self) -> Optional[FileSheet]:
        """Get the current sheet being edited."""
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

    # ── dev-03 methods (analysis-based features) ──────────────────────────────

    def _apply_filters_to_df(self, df: pl.DataFrame, viz_id: str) -> pl.DataFrame:
        """Aplica os filtros salvos em session_state para a visualização ao df."""
        filters = st.session_state.get(f"filters_{viz_id}", [])
        result = df
        for f in filters:
            col, op, val = f.get("col"), f.get("op"), f.get("val")
            if not col or col not in result.columns:
                continue
            try:
                c = pl.col(col)
                dtype = result.schema.get(col)
                numeric_types = (
                    pl.Float64, pl.Float32, pl.Int64, pl.Int32,
                    pl.Int16, pl.Int8, pl.UInt64, pl.UInt32,
                )

                def _cast(v):
                    if dtype in (pl.Float64, pl.Float32):
                        try:
                            return float(v)
                        except Exception:
                            return v
                    if dtype in (pl.Int64, pl.Int32, pl.Int16, pl.Int8, pl.UInt64, pl.UInt32):
                        try:
                            return int(float(v))
                        except Exception:
                            return v
                    return v

                if op == "is_null":
                    result = result.filter(c.is_null())
                elif op == "is_not_null":
                    result = result.filter(c.is_not_null())
                elif op == "in":
                    vals = [v.strip() for v in str(val).split(",") if v.strip()]
                    result = result.filter(c.cast(pl.String).is_in(vals))
                elif op == "contains":
                    result = result.filter(c.cast(pl.String).str.contains(str(val), literal=True))
                elif op == "starts_with":
                    result = result.filter(c.cast(pl.String).str.starts_with(str(val)))
                elif op == "eq":
                    if isinstance(val, list):
                        result = result.filter(c.cast(pl.String).is_in([str(v) for v in val]))
                    else:
                        result = result.filter(c == _cast(val))
                elif op == "ne":
                    result = result.filter(c != _cast(val))
                elif op == "gt":
                    result = result.filter(c > _cast(val))
                elif op == "lt":
                    result = result.filter(c < _cast(val))
                elif op == "gte":
                    result = result.filter(c >= _cast(val))
                elif op == "lte":
                    result = result.filter(c <= _cast(val))
            except Exception:
                pass
        return result

    def _on_export(self, analysis: Analysis, options: Dict[str, Any]) -> Optional[str]:
        """Exporta a análise para PDF aplicando filtros e medidas como estão na tela."""
        try:
            df_base = self.data_service.get_cached_data(analysis.id)
            if df_base is None:
                st.error("Sem dados carregados para exportar.")
                return None

            # Aplica medidas calculadas
            measures = getattr(analysis, "measures", None) or []
            if measures:
                try:
                    df_base = self.data_service.compute_measures(df_base, measures)
                except Exception:
                    pass

            chart_images: Dict[str, bytes] = {}
            table_data: Dict[str, Dict] = {}
            metric_data: Dict[str, Dict] = {}

            for slide in analysis.slides:
                for viz in slide.visualizations:
                    if not viz.config:
                        continue
                    vtype = viz.config.visualization_type

                    # Painel de medidas não vai para o PDF
                    if vtype == VisualizationType.MEASURES:
                        continue

                    # Aplica filtros da sessão específicos desta viz
                    df_viz = self._apply_filters_to_df(df_base, viz.id)

                    if vtype == VisualizationType.TABLE:
                        config = viz.config
                        if config.y_columns:
                            cols = [c for c in config.y_columns if c in df_viz.columns]
                        elif config.x_column or config.y_column:
                            cols = [
                                c for c in [config.x_column, config.y_column, config.color_column]
                                if c and c in df_viz.columns
                            ]
                        else:
                            cols = list(df_viz.columns[:10])
                        if cols:
                            tdf = df_viz.select(cols).head(100)
                            table_data[viz.id] = {
                                "columns": cols,
                                "data": tdf.to_pandas().to_dict(orient="records"),
                                "title": config.title or "Tabela",
                            }

                    elif vtype == VisualizationType.METRIC_CARD:
                        config = viz.config
                        if config.y_column and config.y_column in df_viz.columns:
                            col = df_viz[config.y_column]
                            agg = config.aggregation or "sum"
                            if agg == "mean":
                                val = col.mean()
                            elif agg == "count":
                                val = col.count()
                            elif agg == "min":
                                val = col.min()
                            elif agg == "max":
                                val = col.max()
                            else:
                                val = col.sum()
                            metric_data[viz.id] = {
                                "value": val,
                                "column": config.y_column,
                                "agg": agg,
                                "title": config.title or config.y_column,
                            }

                    else:
                        try:
                            img_bytes = self.chart_factory.render_to_image_bytes(
                                df_viz, viz.config
                            )
                            chart_images[viz.id] = img_bytes
                        except Exception as e:
                            print(f"Erro ao gerar imagem para {viz.id}: {e}")

            export_options = ExportOptions(
                format=options.get("format", "pdf"),
                paper_size=options.get("paper_size", "a4"),
                orientation=options.get("orientation", "portrait"),
                include_comments=options.get("include_comments", True),
                header_text=options.get("header_text", ""),
                footer_text=options.get("footer_text", ""),
            )

            output_path = self.pdf_generator.generate_pdf(
                analysis,
                export_options,
                chart_images,
                table_data=table_data,
                metric_data=metric_data,
            )
            return output_path

        except Exception as e:
            st.error(f"Erro na exportação: {str(e)}")
            return None

    def _get_effective_schema(self, analysis):
        """Retorna o DataSchema da análise enriquecido com as medidas como colunas NUMERIC."""
        schema = analysis.data_schema
        if not schema:
            return schema
        measures = getattr(analysis, "measures", None) or []
        if not measures:
            return schema
        existing_names = {c.name for c in schema.columns}
        extra = []
        for m in measures:
            name = (m.get("name") or "").strip()
            if name and name not in existing_names:
                from domain.entities import Column
                extra.append(Column(name=name, data_type=ColumnType.NUMERIC))
        if not extra:
            return schema
        from domain.entities import DataSchema
        return DataSchema(
            columns=list(schema.columns) + extra,
            row_count=schema.row_count,
            file_name=schema.file_name,
            file_size=schema.file_size,
        )

    def _on_slide_change(self, slide_id: str) -> None:
        """Handle slide change — stored in session_state for canvas to pick up."""
        st.session_state["current_slide_id"] = slide_id
        st.rerun()

    def _on_add_slide(self) -> None:
        """Handle adding a new slide."""
        pass  # Implemented through analysis_service when available

    def _on_delete_slide(self, slide_id: str) -> None:
        """Handle slide deletion."""
        pass  # Implemented through analysis_service when available


def main():
    """Application entry point."""
    app = SmartXLApp()
    app.run()


if __name__ == "__main__":
    main()
