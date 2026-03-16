"""
Session State Manager - Manages Streamlit session state.
Provides centralized state management for the application.
"""

from typing import Any, Dict, Optional
import streamlit as st
import json
import os
from datetime import datetime


class SessionStateManager:
    """
    Manages application session state.
    Provides a centralized interface for state management.
    """

    STATE_FILE = "data/session.json"

    # Default state keys and values
    DEFAULT_STATE = {
        "session_id": None,
        "current_analysis_id": None,
        "current_slide_id": None,
        "show_settings": False,
        "show_export": False,
        "show_uploader": False,
        "editing_viz_id": None,
        "sidebar_collapsed": False,
        "theme": "light",
        "notifications": [],
    }

    @classmethod
    def initialize(cls) -> None:
        """Initialize session state with default values."""
        for key, value in cls.DEFAULT_STATE.items():
            if key not in st.session_state:
                st.session_state[key] = value

        # Try to restore from file
        cls._restore_from_file()

    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """
        Get a value from session state.

        Args:
            key: State key
            default: Default value if key not found

        Returns:
            Value from session state or default
        """
        return st.session_state.get(key, default)

    @classmethod
    def set(cls, key: str, value: Any) -> None:
        """
        Set a value in session state.

        Args:
            key: State key
            value: Value to set
        """
        st.session_state[key] = value

    @classmethod
    def delete(cls, key: str) -> None:
        """
        Delete a key from session state.

        Args:
            key: State key to delete
        """
        if key in st.session_state:
            del st.session_state[key]

    @classmethod
    def clear(cls) -> None:
        """Clear all session state."""
        st.session_state.clear()
        cls.initialize()

    @classmethod
    def get_all(cls) -> Dict[str, Any]:
        """
        Get all session state as dictionary.

        Returns:
            Dictionary of all session state
        """
        return dict(st.session_state)

    @classmethod
    def save_to_file(cls) -> bool:
        """
        Save session state to file.

        Returns:
            True if successful, False otherwise
        """
        try:
            os.makedirs(os.path.dirname(cls.STATE_FILE), exist_ok=True)

            # Serialize session state (excluding non-serializable items)
            serializable_state = {}
            for key, value in st.session_state.items():
                try:
                    # Test if serializable
                    json.dumps({key: value})
                    serializable_state[key] = value
                except (TypeError, ValueError):
                    # Skip non-serializable items
                    pass

            with open(cls.STATE_FILE, "w") as f:
                json.dump(serializable_state, f, default=str)

            return True
        except Exception as e:
            print(f"Error saving session state: {e}")
            return False

    @classmethod
    def _restore_from_file(cls) -> bool:
        """
        Restore session state from file.

        Returns:
            True if successful, False otherwise
        """
        try:
            if os.path.exists(cls.STATE_FILE):
                with open(cls.STATE_FILE, "r") as f:
                    saved_state = json.load(f)

                # Restore saved state
                for key, value in saved_state.items():
                    if key not in st.session_state or st.session_state[key] is None:
                        st.session_state[key] = value

                return True
        except Exception as e:
            print(f"Error restoring session state: {e}")

        return False

    @classmethod
    def add_notification(cls, message: str, level: str = "info") -> None:
        """
        Add a notification to the queue.

        Args:
            message: Notification message
            level: Notification level (info, success, warning, error)
        """
        notifications = cls.get("notifications", [])
        notifications.append(
            {
                "message": message,
                "level": level,
                "timestamp": datetime.now().isoformat(),
            }
        )
        cls.set("notifications", notifications)

    @classmethod
    def get_notifications(cls) -> list:
        """
        Get and clear notifications.

        Returns:
            List of notifications
        """
        notifications = cls.get("notifications", [])
        cls.set("notifications", [])
        return notifications

    @classmethod
    def update_current_analysis(cls, analysis_id: str, slide_id: Optional[str] = None) -> None:
        """
        Update current analysis and slide IDs.

        Args:
            analysis_id: Analysis ID
            slide_id: Optional slide ID
        """
        cls.set("current_analysis_id", analysis_id)
        if slide_id:
            cls.set("current_slide_id", slide_id)

    @classmethod
    def get_current_ids(cls) -> tuple:
        """
        Get current analysis and slide IDs.

        Returns:
            Tuple of (analysis_id, slide_id)
        """
        return (cls.get("current_analysis_id"), cls.get("current_slide_id"))


def init_session_state() -> None:
    """Initialize session state - convenience function."""
    SessionStateManager.initialize()


def get_state(key: str, default: Any = None) -> Any:
    """Get state value - convenience function."""
    return SessionStateManager.get(key, default)


def set_state(key: str, value: Any) -> None:
    """Set state value - convenience function."""
    SessionStateManager.set(key, value)
