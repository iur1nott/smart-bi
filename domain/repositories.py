"""
Domain Repository Interfaces - Abstract repository interfaces following DDD.
These interfaces define the contracts for data persistence without implementation details.
Updated for new schema with dashboards, files, and visualizations.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

from .entities import User, Dashboard, File, FileSheet, Visualization


class UserRepository(ABC):
    """
    Abstract repository interface for User entities.
    Defines the contract for user persistence operations.
    """

    @abstractmethod
    def save(self, user: User) -> bool:
        """
        Save a user to the repository.

        Args:
            user: The user entity to save

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def find_by_id(self, user_id: str) -> Optional[User]:
        """
        Find a user by their unique identifier.

        Args:
            user_id: The unique identifier of the user

        Returns:
            User entity if found, None otherwise
        """
        pass

    @abstractmethod
    def find_by_username(self, username: str) -> Optional[User]:
        """
        Find a user by their username.

        Args:
            username: The username to search for

        Returns:
            User entity if found, None otherwise
        """
        pass

    @abstractmethod
    def find_by_email(self, email: str) -> Optional[User]:
        """
        Find a user by their email address.

        Args:
            email: The email address to search for

        Returns:
            User entity if found, None otherwise
        """
        pass

    @abstractmethod
    def find_all(self, limit: int = 100, offset: int = 0) -> List[User]:
        """
        Find all users with pagination.

        Args:
            limit: Maximum number of users to return
            offset: Number of users to skip

        Returns:
            List of User entities
        """
        pass

    @abstractmethod
    def delete(self, user_id: str) -> bool:
        """
        Delete a user from the repository.

        Args:
            user_id: The unique identifier of the user to delete

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def count(self) -> int:
        """
        Count the total number of users.

        Returns:
            Total user count
        """
        pass


class FileRepository(ABC):
    """
    Abstract repository interface for File entities.
    Defines the contract for file metadata persistence operations.
    """

    @abstractmethod
    def save_file(self, file: File) -> bool:
        """Save a file entity with its sheets and columns."""
        pass

    @abstractmethod
    def find_file_by_id(self, file_id: str) -> Optional[File]:
        """Find a file by its ID."""
        pass

    @abstractmethod
    def find_files_by_user(self, user_id: str) -> List[File]:
        """Find all files for a user."""
        pass

    @abstractmethod
    def delete_file(self, file_id: str) -> bool:
        """Delete a file and its related data."""
        pass

    @abstractmethod
    def find_sheet_by_id(self, sheet_id: str) -> Optional[FileSheet]:
        """Find a sheet by its ID."""
        pass

    @abstractmethod
    def find_sheets_by_file(self, file_id: str) -> List[FileSheet]:
        """Find all sheets for a file."""
        pass


class DashboardRepository(ABC):
    """
    Abstract repository interface for Dashboard entities.
    Defines the contract for dashboard persistence operations.
    """

    @abstractmethod
    def save_dashboard(self, dashboard: Dashboard) -> bool:
        """Save a dashboard entity."""
        pass

    @abstractmethod
    def find_dashboard_by_id(self, dashboard_id: str) -> Optional[Dashboard]:
        """Find a dashboard by its ID."""
        pass

    @abstractmethod
    def find_dashboards_by_user(self, user_id: str) -> List[Dashboard]:
        """Find all dashboards for a user."""
        pass

    @abstractmethod
    def delete_dashboard(self, dashboard_id: str) -> bool:
        """Delete a dashboard and its visualizations."""
        pass

    @abstractmethod
    def update_dashboard_title(self, dashboard_id: str, title: str) -> bool:
        """Update the title of a dashboard."""
        pass

    @abstractmethod
    def save_visualization(self, viz: Visualization) -> bool:
        """Save a visualization entity."""
        pass

    @abstractmethod
    def find_visualization_by_id(self, viz_id: str) -> Optional[Visualization]:
        """Find a visualization by its ID."""
        pass

    @abstractmethod
    def find_visualizations_by_dashboard(
        self, dashboard_id: str
    ) -> List[Visualization]:
        """Find all visualizations for a dashboard."""
        pass

    @abstractmethod
    def delete_visualization(self, viz_id: str) -> bool:
        """Delete a visualization."""
        pass
