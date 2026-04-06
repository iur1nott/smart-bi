"""
Presentation Layer - Streamlit UI components and views.
This layer handles all user interface rendering and interactions.
"""

from .login import render_login_page, render_user_menu
from .sidebar import render_main_sidebar, render_file_uploader
from .widget_palette import render_widget_palette, render_column_mapping
from .canvas import render_canvas, render_slide_navigator
from .components import (
    render_settings_modal,
    render_export_dialog,
    render_welcome_screen,
    render_notification,
    render_header_bar,
)

__all__ = [
    "render_login_page",
    "render_user_menu",
    "render_main_sidebar",
    "render_file_uploader",
    "render_widget_palette",
    "render_column_mapping",
    "render_canvas",
    "render_slide_navigator",
    "render_settings_modal",
    "render_export_dialog",
    "render_welcome_screen",
    "render_notification",
    "render_header_bar",
]
