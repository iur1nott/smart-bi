"""
Repository Interfaces - Abstract repository interfaces following the Repository Pattern.
These define the contracts that infrastructure implementations must fulfill.
Following the Dependency Inversion Principle - domain defines interfaces,
infrastructure provides implementations.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from .entities import User, Analysis, UserSession


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
        raise NotImplementedError

    @abstractmethod
    def find_by_id(self, user_id: str) -> Optional[User]:
        """
        Find a user by their ID.

        Args:
            user_id: The unique identifier of the user

        Returns:
            User entity if found, None otherwise
        """
        raise NotImplementedError

    @abstractmethod
    def find_by_username(self, username: str) -> Optional[User]:
        """
        Find a user by their username.

        Args:
            username: The username to search for

        Returns:
            User entity if found, None otherwise
        """
        raise NotImplementedError

    @abstractmethod
    def find_by_email(self, email: str) -> Optional[User]:
        """
        Find a user by their email address.

        Args:
            email: The email address to search for

        Returns:
            User entity if found, None otherwise
        """
        raise NotImplementedError

    @abstractmethod
    def delete(self, user_id: str) -> bool:
        """
        Delete a user from the repository.

        Args:
            user_id: The unique identifier of the user to delete

        Returns:
            True if successful, False otherwise
        """
        raise NotImplementedError

    @abstractmethod
    def list_all(self, limit: int = 100, offset: int = 0) -> List[User]:
        """
        List all users with pagination.

        Args:
            limit: Maximum number of users to return
            offset: Number of users to skip

        Returns:
            List of User entities
        """
        raise NotImplementedError

    @abstractmethod
    def update_last_login(self, user_id: str) -> bool:
        """
        Update the last login timestamp for a user.

        Args:
            user_id: The unique identifier of the user

        Returns:
            True if successful, False otherwise
        """
        raise NotImplementedError


class AnalysisRepository(ABC):
    """
    Abstract repository interface for Analysis entities.
    Defines the contract for analysis persistence operations.
    """

    @abstractmethod
    def save(self, analysis: Analysis) -> bool:
        """
        Save an analysis to the repository.

        Args:
            analysis: The analysis entity to save

        Returns:
            True if successful, False otherwise
        """
        raise NotImplementedError

    @abstractmethod
    def find_by_id(self, analysis_id: str) -> Optional[Analysis]:
        """
        Find an analysis by its ID.

        Args:
            analysis_id: The unique identifier of the analysis

        Returns:
            Analysis entity if found, None otherwise
        """
        raise NotImplementedError

    @abstractmethod
    def find_by_user_id(
        self, user_id: str, limit: int = 50, offset: int = 0
    ) -> List[Analysis]:
        """
        Find all analyses for a specific user.

        Args:
            user_id: The unique identifier of the user
            limit: Maximum number of analyses to return
            offset: Number of analyses to skip

        Returns:
            List of Analysis entities
        """
        raise NotImplementedError

    @abstractmethod
    def delete(self, analysis_id: str) -> bool:
        """
        Delete an analysis from the repository.

        Args:
            analysis_id: The unique identifier of the analysis to delete

        Returns:
            True if successful, False otherwise
        """
        raise NotImplementedError

    @abstractmethod
    def list_recent(self, user_id: str, limit: int = 10) -> List[Analysis]:
        """
        List recent analyses for a user.

        Args:
            user_id: The unique identifier of the user
            limit: Maximum number of analyses to return

        Returns:
            List of Analysis entities ordered by update time
        """
        raise NotImplementedError

    @abstractmethod
    def search(self, user_id: str, query: str, limit: int = 20) -> List[Analysis]:
        """
        Search analyses by name or content.

        Args:
            user_id: The unique identifier of the user
            query: Search query string
            limit: Maximum number of results

        Returns:
            List of matching Analysis entities
        """
        raise NotImplementedError

    @abstractmethod
    def count_by_user(self, user_id: str) -> int:
        """
        Count total analyses for a user.

        Args:
            user_id: The unique identifier of the user

        Returns:
            Total count of analyses
        """
        raise NotImplementedError


class SessionRepository(ABC):
    """
    Abstract repository interface for session management.
    Defines the contract for session persistence operations.
    """

    @abstractmethod
    def save(self, session: UserSession) -> bool:
        """
        Save a session to the repository.

        Args:
            session: The session entity to save

        Returns:
            True if successful, False otherwise
        """
        raise NotImplementedError

    @abstractmethod
    def find_by_id(self, session_id: str) -> Optional[UserSession]:
        """
        Find a session by its ID.

        Args:
            session_id: The unique identifier of the session

        Returns:
            UserSession entity if found, None otherwise
        """
        raise NotImplementedError

    @abstractmethod
    def find_by_user_id(self, user_id: str) -> Optional[UserSession]:
        """
        Find the active session for a user.

        Args:
            user_id: The unique identifier of the user

        Returns:
            UserSession entity if found, None otherwise
        """
        raise NotImplementedError

    @abstractmethod
    def delete(self, session_id: str) -> bool:
        """
        Delete a session from the repository.

        Args:
            session_id: The unique identifier of the session to delete

        Returns:
            True if successful, False otherwise
        """
        raise NotImplementedError

    @abstractmethod
    def delete_by_user_id(self, user_id: str) -> bool:
        """
        Delete all sessions for a user.

        Args:
            user_id: The unique identifier of the user

        Returns:
            True if successful, False otherwise
        """
        raise NotImplementedError

    @abstractmethod
    def cleanup_expired(self, max_age_hours: int = 24) -> int:
        """
        Clean up expired sessions.

        Args:
            max_age_hours: Maximum session age in hours

        Returns:
            Number of sessions cleaned up
        """
        raise NotImplementedError


class DataRepository(ABC):
    """
    Abstract repository interface for data file management.
    Defines the contract for data file storage operations.
    """

    @abstractmethod
    def save_file(self, file_id: str, file_bytes: bytes, filename: str) -> str:
        """
        Save a data file to storage.

        Args:
            file_id: Unique identifier for the file
            file_bytes: Raw file content as bytes
            filename: Original filename

        Returns:
            Path or identifier where the file is stored
        """
        raise NotImplementedError

    @abstractmethod
    def load_file(self, file_id: str) -> Optional[bytes]:
        """
        Load a data file from storage.

        Args:
            file_id: Unique identifier for the file

        Returns:
            File content as bytes if found, None otherwise
        """
        raise NotImplementedError

    @abstractmethod
    def delete_file(self, file_id: str) -> bool:
        """
        Delete a data file from storage.

        Args:
            file_id: Unique identifier for the file

        Returns:
            True if successful, False otherwise
        """
        raise NotImplementedError

    @abstractmethod
    def file_exists(self, file_id: str) -> bool:
        """
        Check if a file exists in storage.

        Args:
            file_id: Unique identifier for the file

        Returns:
            True if file exists, False otherwise
        """
        raise NotImplementedError
