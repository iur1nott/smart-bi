"""
Presentation layer - Streamlit UI components.
Centralized imports for all presentation modules.
"""

# Sidebar components
from .sidebar import render_sidebar, render_secondary_sidebar, render_file_uploader

# Canvas components
from .canvas import (
    render_canvas,
    render_visualization,
    render_slide_navigator,
)

# Widgets
from .widgets import (
    render_widget_palette,
    render_data_preview,
)

# Main components
from .components import (
    render_settings_modal,
    render_analysis_history,
    render_export_dialog,
    render_welcome_screen,
    render_notification,
    render_confirmation_dialog,
)

__all__ = [
    # Sidebar
    "render_sidebar",
    "render_secondary_sidebar",
    "render_file_uploader",
    
    # Canvas
    "render_canvas",
    "render_visualization",
    "render_slide_navigator",
    
    # Widgets
    "render_widget_palette",
    "render_data_preview",
    
    # Components
    "render_settings_modal",
    "render_analysis_history",
    "render_export_dialog",
    "render_welcome_screen",
    "render_notification",
    "render_confirmation_dialog",
]