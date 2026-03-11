"""
Dashboard Builder - Main Application Entry Point
A Streamlit application for building dashboards from Excel data.

This application follows Clean Architecture principles:
- Domain Layer: Core business entities and value objects
- Use Cases Layer: Application services and business logic
- Infrastructure Layer: External services and implementations
- Presentation Layer: Streamlit UI components
"""

import streamlit as st
import polars as pl
from typing import Optional, Dict, Any
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import application components
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
from utils.session_state import (
    SessionStateManager,
    init_session_state,
    get_state,
    set_state,
)

# Import presentation components
from presentation.sidebar import render_sidebar, render_secondary_sidebar
from presentation.canvas import render_canvas, render_slide_navigator
from presentation.widgets import (
    render_widget_palette,
    render_visualization_config,
    render_data_preview,
)
from presentation.components import (
    render_settings_modal,
    render_analysis_history,
    render_export_dialog,
    render_welcome_screen,
    render_notification,
)


# Configure Streamlit page
st.set_page_config(
    page_title="Dashboard Builder",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": "Dashboard Builder - Create beautiful dashboards from Excel data",
    },
)

# Apply custom CSS
st.markdown(
    """
<style>
    /* Main content styling */
    .main .block-container {
        padding-top: 2rem;
    }

    /* Card styling */
    .stMetric > div {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e9ecef;
    }

    /* Button styling */
    .stButton > button {
        border-radius: 0.5rem;
    }

    /* Expander styling */
    .streamlit-expanderHeader {
        font-weight: bold;
        color: #2c3e50;
    }

    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #f8f9fa;
    }

    /* Dataframe styling */
    .stDataFrame {
        border: 1px solid #e9ecef;
        border-radius: 0.5rem;
    }

    /* Chart container */
    .stPlotlyChart {
        background-color: white;
        border-radius: 0.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }

    /* Hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""",
    unsafe_allow_html=True,
)


class DashboardBuilderApp:
    """
    Main application class.
    Coordinates between UI components and services.
    """

    def __init__(self):
        """Initialize the application."""
        # Initialize session state
        init_session_state()

        # Initialize services
        self._init_services()

        # Initialize chart factory
        self.chart_factory = ChartFactory()

    def _init_services(self) -> None:
        """Initialize application services."""
        # Create data directory if needed
        data_dir = "data"
        os.makedirs(data_dir, exist_ok=True)

        # Initialize services
        if "analysis_service" not in st.session_state:
            repository = FileAnalysisRepository(data_dir)
            st.session_state.analysis_service = AnalysisService(repository)
            st.session_state.analysis_service.initialize_session(
                get_state("session_data")
            )

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
        """Run the main application."""
        # Render header with export button
        self._render_header()

        # Check if there's a current analysis
        current_analysis = self.analysis_service.get_current_analysis()

        if not current_analysis:
            # Show welcome screen
            render_welcome_screen(self._on_new_analysis)
            self._render_uploader_dialog()
        else:
            # Render main layout
            self._render_main_layout()

        # Render settings modal if open
        if get_state("show_settings"):
            self._render_settings_modal()

        # Render export dialog if open
        if get_state("show_export"):
            self._render_export_dialog()

        # Handle notifications
        self._handle_notifications()

    def _render_header(self) -> None:
        """Render the application header with actions."""
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

        with col1:
            st.title("📊 Dashboard Builder")

        with col2:
            current_analysis = self.analysis_service.get_current_analysis()
            if current_analysis:
                # Rename analysis
                new_name = st.text_input(
                    "Analysis Name",
                    value=current_analysis.name,
                    label_visibility="collapsed",
                    key="analysis_name_input",
                )
                if new_name != current_analysis.name:
                    self.analysis_service.rename_analysis(current_analysis.id, new_name)
                    st.rerun()

        with col3:
            if current_analysis:
                if st.button("💾 Save", use_container_width=True):
                    self.analysis_service.save_current_analysis()
                    set_state("notification", ("Analysis saved!", "success"))

        with col4:
            if current_analysis:
                if st.button("📤 Export", type="primary", use_container_width=True):
                    set_state("show_export", True)

        st.markdown("---")

    def _render_main_layout(self) -> None:
        """Render the main application layout."""
        current_analysis = self.analysis_service.get_current_analysis()

        if not current_analysis:
            return

        # Main content area with columns
        col_main, col_widgets = st.columns([3, 1])

        with col_widgets:
            # Widget palette for adding visualizations
            self._render_widget_sidebar()

        with col_main:
            # Render current slide canvas
            current_slide = self.analysis_service.get_current_slide()

            # Render canvas
            render_canvas(
                slide=current_slide,
                data_service=self.data_service,
                analysis_id=current_analysis.id,
                on_update_visualization=self._on_update_visualization,
                on_delete_visualization=self._on_delete_visualization,
                on_add_comment=self._on_add_comment,
            )

            # Render slide navigator
            if current_analysis.slides:
                render_slide_navigator(
                    slides=current_analysis.slides,
                    current_slide_id=current_slide.id if current_slide else None,
                    on_slide_change=self._on_slide_change,
                    on_add_slide=self._on_add_slide,
                    on_delete_slide=self._on_delete_slide,
                )

    def _render_widget_sidebar(self) -> None:
        """Render the widget sidebar for adding visualizations."""
        current_analysis = self.analysis_service.get_current_analysis()

        if not current_analysis or not current_analysis.data_schema:
            st.info("📁 Upload data to add visualizations")
            if st.button("📂 Upload XLSX", use_container_width=True):
                set_state("show_uploader", True)
            return

        # Data preview
        with st.expander("📁 Data Preview", expanded=False):
            df = self.data_service.get_cached_data(current_analysis.id)
            if df is not None:
                render_data_preview(current_analysis.data_schema, df)

        # Add visualization section
        st.markdown("### ➕ Add Visualization")

        # Chart type buttons
        chart_types = [
            ("📊 Bar", VisualizationType.BAR_CHART),
            ("📈 Line", VisualizationType.LINE_CHART),
            ("🥧 Pie", VisualizationType.PIE_CHART),
            ("📉 Area", VisualizationType.AREA_CHART),
            ("⚬ Scatter", VisualizationType.SCATTER_PLOT),
            ("▊ Histogram", VisualizationType.HISTOGRAM),
            ("📦 Box", VisualizationType.BOX_PLOT),
            ("📋 Table", VisualizationType.TABLE),
            ("💳 Metric", VisualizationType.METRIC_CARD),
        ]

        cols = st.columns(3)
        for i, (label, viz_type) in enumerate(chart_types):
            with cols[i % 3]:
                if st.button(
                    label, key=f"add_{viz_type.value}", use_container_width=True
                ):
                    self._on_add_visualization(viz_type)

    def _render_uploader_dialog(self) -> None:
        """Render file uploader dialog."""
        if get_state("show_uploader"):
            with st.expander("📂 Upload XLSX File", expanded=True):
                uploaded_file = st.file_uploader(
                    "Select an Excel file",
                    type=["xlsx", "xls"],
                    help="Upload an Excel file to start a new analysis",
                )

                if uploaded_file is not None:
                    name_input = st.text_input(
                        "Analysis Name", value=uploaded_file.name.rsplit(".", 1)[0]
                    )

                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(
                            "📁 Load File", type="primary", use_container_width=True
                        ):
                            self._process_uploaded_file(uploaded_file, name_input)

                    with col2:
                        if st.button("✗ Cancel", use_container_width=True):
                            set_state("show_uploader", False)
                            st.rerun()

    def _render_settings_modal(self) -> None:
        """Render settings modal."""
        with st.expander("⚙️ Settings", expanded=True):
            render_settings_modal(
                current_settings=self.analysis_service.get_settings(),
                on_save=self._on_save_settings,
            )
            if st.button("Close Settings"):
                set_state("show_settings", False)
                st.rerun()

    def _render_export_dialog(self) -> None:
        """Render export dialog."""
        current_analysis = self.analysis_service.get_current_analysis()
        if current_analysis:
            with st.expander("📤 Export Analysis", expanded=True):
                render_export_dialog(
                    analysis=current_analysis, on_export=self._on_export
                )
                if st.button("Close Export"):
                    set_state("show_export", False)
                    st.rerun()

    def _handle_notifications(self) -> None:
        """Display and clear notifications."""
        notification = get_state("notification")
        if notification:
            message, level = notification
            render_notification(message, level)
            set_state("notification", None)

    # Callback methods

    def _on_new_analysis(self) -> None:
        """Handle new analysis creation."""
        set_state("show_uploader", True)

    def _process_uploaded_file(self, uploaded_file, name: str) -> None:
        """Process an uploaded XLSX file."""
        try:
            # Create new analysis
            analysis = self.analysis_service.create_analysis(name)

            # Read file bytes
            file_bytes = uploaded_file.getvalue()

            # Load data and get schema
            schema, df = self.data_service.load_excel_from_bytes(
                file_bytes, uploaded_file.name, analysis.id
            )

            # Update analysis with schema
            analysis.data_schema = schema
            analysis.file_path = uploaded_file.name

            # Save analysis
            self.analysis_service.save_current_analysis()

            # Hide uploader and rerun
            set_state("show_uploader", False)
            st.success(f"✓ Loaded {schema.row_count} rows from {uploaded_file.name}")
            st.rerun()

        except Exception as e:
            st.error(f"Error loading file: {str(e)}")

    def _on_select_analysis(self, analysis_id: str) -> None:
        """Handle analysis selection."""
        self.analysis_service.set_current_analysis(analysis_id)
        st.rerun()

    def _on_save_settings(self, settings: Dict[str, Any]) -> None:
        """Handle settings save."""
        self.analysis_service.update_settings(settings)

    def _on_add_visualization(self, viz_type: VisualizationType) -> None:
        """Handle adding a new visualization."""
        current_slide = self.analysis_service.get_current_slide()
        current_analysis = self.analysis_service.get_current_analysis()

        if (
            not current_slide
            or not current_analysis
            or not current_analysis.data_schema
        ):
            st.warning("Please upload data first")
            return

        # Create default config
        numeric_cols = current_analysis.data_schema.get_numeric_columns()
        categorical_cols = current_analysis.data_schema.get_categorical_columns()
        all_cols = current_analysis.data_schema.get_column_names()

        # Set default columns based on type
        x_col = (
            categorical_cols[0]
            if categorical_cols
            else all_cols[0]
            if all_cols
            else None
        )
        y_col = numeric_cols[0] if numeric_cols else None

        config = VisualizationConfig(
            visualization_type=viz_type,
            title=f"New {viz_type.value.replace('_', ' ').title()}",
            x_column=x_col,
            y_column=y_col,
            aggregation="sum",
        )

        # Add visualization
        viz = self.analysis_service.add_visualization(current_slide.id, config)

        if viz:
            # Store data snapshot for tables
            df = self.data_service.get_cached_data(current_analysis.id)
            if df is not None and viz_type == VisualizationType.TABLE:
                data = df.head(100).to_pandas().to_dict(orient="records")
                viz.data_snapshot = {"data": data, "columns": all_cols[:10]}
                self.analysis_service.save_current_analysis()

            st.success(f"Added {viz_type.value}")
            st.rerun()

    def _on_update_visualization(
        self, slide_id: str, viz_id: str, config: VisualizationConfig
    ) -> None:
        """Handle visualization update."""
        self.analysis_service.update_visualization(slide_id, viz_id, config=config)

    def _on_delete_visualization(self, slide_id: str, viz_id: str) -> None:
        """Handle visualization deletion."""
        self.analysis_service.delete_visualization(slide_id, viz_id)
        st.success("Visualization deleted")
        st.rerun()

    def _on_add_comment(self, slide_id: str, viz_id: str, comment: str) -> None:
        """Handle adding a comment."""
        self.analysis_service.update_visualization(slide_id, viz_id, comment=comment)

    def _on_slide_change(self, slide_id: str) -> None:
        """Handle slide change."""
        self.analysis_service.set_current_slide(slide_id)

    def _on_add_slide(self) -> None:
        """Handle adding a new slide."""
        slide = self.analysis_service.add_slide()
        if slide:
            st.success(f"Added {slide.title}")
            st.rerun()

    def _on_delete_slide(self, slide_id: str) -> None:
        """Handle slide deletion."""
        self.analysis_service.delete_slide(slide_id)
        st.success("Slide deleted")
        st.rerun()

    def _on_export(self, analysis: Analysis, options: Dict[str, Any]) -> Optional[str]:
        """Handle export request."""
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
                                    fig, "png"
                                )
                                chart_images[viz.id] = img_bytes
                            except Exception as e:
                                print(f"Error generating chart image: {e}")

            # Create export options
            export_options = ExportOptions(
                format=options.get("format", "pdf"),
                paper_size=options.get("paper_size", "a4"),
                orientation=options.get("orientation", "portrait"),
                include_comments=options.get("include_comments", True),
                header_text=options.get("header_text", ""),
                footer_text=options.get("footer_text", ""),
            )

            # Export based on format
            if options.get("format") == "latex":
                output_path = self.export_service.export_to_latex(
                    analysis, export_options, chart_images
                )
            elif options.get("format") == "html":
                output_path = self.export_service.export_to_html(
                    analysis, export_options, chart_images
                )
            else:
                # Try PDF via LaTeX first, fallback to ReportLab
                try:
                    output_path = self.pdf_generator.generate_pdf(
                        analysis, export_options, chart_images
                    )
                except Exception as e:
                    print(f"PDF generation error: {e}")
                    output_path = self.export_service.export_to_html(
                        analysis, export_options, chart_images
                    )

            return output_path

        except Exception as e:
            st.error(f"Export failed: {str(e)}")
            return None


def main():
    """Main entry point."""
    app = DashboardBuilderApp()
    app.run()


if __name__ == "__main__":
    main()
