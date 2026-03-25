"""Presentation layer - Streamlit UI components."""

from .sidebar import render_sidebar, render_secondary_sidebar
from .canvas import (
    render_canvas,
    render_visualization,
    render_slide_navigator,
)
from .widgets import (
    render_widget_palette,
    render_data_preview,
    render_column_mapper, # Adicionado para a sua Task 2
)
from .components import (
    render_settings_modal,
    render_analysis_history,
    render_export_dialog,
    render_welcome_screen,
    render_notification,
)

__all__ = [
    "render_sidebar",
    "render_secondary_sidebar",
    "render_canvas",
    "render_visualization",
    "render_slide_navigator",
    "render_widget_palette",
    "render_data_preview",
    "render_column_mapper",
    "render_settings_modal",
    "render_analysis_history",
    "render_export_dialog",
    "render_welcome_screen",
    "render_notification",
]