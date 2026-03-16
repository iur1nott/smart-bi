"""
Presentation Layer - Streamlit UI components and views.
This layer handles all user interface rendering and interactions.
"""

from .login import render_login_page
from .sidebar import render_main_sidebar
from .widget_palette import render_widget_palette
from .canvas import render_canvas, render_slide_navigator
from .components import (
    render_settings_modal,
    render_export_dialog,
    render_welcome_screen,
    render_notification,
)

__all__ = [
    "render_login_page",
    "render_main_sidebar",
    "render_widget_palette",
    "render_canvas",
    "render_slide_navigator",
    "render_settings_modal",
    "render_export_dialog",
    "render_welcome_screen",
    "render_notification",
]
