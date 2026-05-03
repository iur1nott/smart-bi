"""
Presentation Layer - Streamlit UI components and views.
"""

from .sidebar import render_sidebar, render_secondary_sidebar
from .canvas import (
    render_canvas,
    render_visualization,
    render_slide_navigator,
)
from .widgets import (
    render_widget_palette,
    render_data_preview,
    render_column_mapper,
)
from .components import (
    render_export_dialog,
    render_welcome_screen,
    render_notification,
    render_settings_modal,
)
from .login import render_login_page, render_user_menu
from .sidebar import render_file_uploader, render_main_sidebar
from .widget_palette import (
    render_column_mapper,
    render_column_mapping,
    render_viz_config_dialog,
    render_data_preview,
)

__all__ = [
    # dev-03 sidebar
    "render_sidebar",
    "render_secondary_sidebar",
    # canvas
    "render_canvas",
    "render_visualization",
    "render_slide_navigator",
    # widgets
    "render_widget_palette",
    "render_data_preview",
    "render_column_mapper",
    # auth (merge)
    "render_login_page",
    "render_user_menu",
    "render_main_sidebar",
    "render_file_uploader",
    "render_column_mapping",
    "render_viz_config_dialog",
    # components
    "render_settings_modal",
    "render_export_dialog",
    "render_welcome_screen",
    "render_notification",
    "render_header_bar",
]
