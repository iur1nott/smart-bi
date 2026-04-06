"""
Session State Management - Utilities for managing Streamlit session state.
"""

from typing import Any, Dict, Optional
import streamlit as st


class SessionStateManager:
    """
    Manages Streamlit session state with a clean interface.
    Provides methods for getting, setting, and managing state values.
    """

    @staticmethod
    def get(key: str, default: Any = None) -> Any:
        """
        Get a value from session state.

        Args:
            key: The key to retrieve
            default: Default value if key doesn't exist

        Returns:
            The value from session state or the default
        """
        return st.session_state.get(key, default)

    @staticmethod
    def set(key: str, value: Any) -> None:
        """
        Set a value in session state.

        Args:
            key: The key to set
            value: The value to store
        """
        st.session_state[key] = value

    @staticmethod
    def delete(key: str) -> None:
        """
        Delete a key from session state.

        Args:
            key: The key to delete
        """
        if key in st.session_state:
            del st.session_state[key]

    @staticmethod
    def clear() -> None:
        """Clear all session state."""
        st.session_state.clear()

    @staticmethod
    def has(key: str) -> bool:
        """
        Check if a key exists in session state.

        Args:
            key: The key to check

        Returns:
            True if key exists, False otherwise
        """
        return key in st.session_state

    @staticmethod
    def get_all() -> Dict[str, Any]:
        """
        Get all session state as a dictionary.

        Returns:
            Dictionary of all session state values
        """
        return dict(st.session_state)

    @staticmethod
    def update(data: Dict[str, Any]) -> None:
        """
        Update multiple values in session state.

        Args:
            data: Dictionary of key-value pairs to update
        """
        st.session_state.update(data)


def init_session_state(defaults: Optional[Dict[str, Any]] = None) -> None:
    """
    Initialize session state with default values.

    Args:
        defaults: Dictionary of default key-value pairs
    """
    if defaults is None:
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
            "commenting_viz_id": None,
            "notification": None,
            "session_data": {},
        }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_state(key: str, default: Any = None) -> Any:
    """
    Get a value from session state.

    Args:
        key: The key to retrieve
        default: Default value if key doesn't exist

    Returns:
        The value from session state or the default
    """
    return SessionStateManager.get(key, default)


def set_state(key: str, value: Any) -> None:
    """
    Set a value in session state.

    Args:
        key: The key to set
        value: The value to store
    """
    SessionStateManager.set(key, value)
