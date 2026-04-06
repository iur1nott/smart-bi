"""
Domain Repository Interfaces - Abstract repository interfaces following DDD.
These interfaces define the contracts for data persistence without implementation details.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

from .entities import User, UserSession, Analysis


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


class SessionRepository(ABC):
    """
    Abstract repository interface for UserSession entities.
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
        pass

    @abstractmethod
    def find_by_id(self, session_id: str) -> Optional[UserSession]:
        """
        Find a session by its unique identifier.

        Args:
            session_id: The unique identifier of the session

        Returns:
            UserSession entity if found, None otherwise
        """
        pass

    @abstractmethod
    def find_by_user_id(self, user_id: str) -> Optional[UserSession]:
        """
        Find a session by user ID.

        Args:
            user_id: The unique identifier of the user

        Returns:
            UserSession entity if found, None otherwise
        """
        pass

    @abstractmethod
    def find_by_token_hash(self, token_hash: str) -> Optional[UserSession]:
        """
        Find a session by its token hash.

        Args:
            token_hash: The hash of the session token

        Returns:
            UserSession entity if found, None otherwise
        """
        pass

    @abstractmethod
    def delete(self, session_id: str) -> bool:
        """
        Delete a session from the repository.

        Args:
            session_id: The unique identifier of the session to delete

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def delete_by_user_id(self, user_id: str) -> bool:
        """
        Delete all sessions for a user.

        Args:
            user_id: The unique identifier of the user

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def delete_expired(self) -> int:
        """
        Delete all expired sessions.

        Returns:
            Number of sessions deleted
        """
        pass

    @abstractmethod
    def update_activity(self, session_id: str) -> bool:
        """
        Update the last activity timestamp for a session.

        Args:
            session_id: The unique identifier of the session

        Returns:
            True if successful, False otherwise
        """
        pass


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
        pass

    @abstractmethod
    def find_by_id(self, analysis_id: str) -> Optional[Analysis]:
        """
        Find an analysis by its unique identifier.

        Args:
            analysis_id: The unique identifier of the analysis

        Returns:
            Analysis entity if found, None otherwise
        """
        pass

    @abstractmethod
    def find_by_user_id(self, user_id: str, limit: int = 50, offset: int = 0) -> List[Analysis]:
        """
        Find all analyses for a user with pagination.

        Args:
            user_id: The unique identifier of the user
            limit: Maximum number of analyses to return
            offset: Number of analyses to skip

        Returns:
            List of Analysis entities
        """
        pass

    @abstractmethod
    def list_recent(self, user_id: str, limit: int = 10) -> List[Analysis]:
        """
        Find recent analyses for a user.

        Args:
            user_id: The unique identifier of the user
            limit: Maximum number of analyses to return

        Returns:
            List of Analysis entities ordered by update time
        """
        pass

    @abstractmethod
    def search(
        self,
        user_id: str,
        query: str,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Analysis]:
        """
        Search analyses by name or content.

        Args:
            user_id: The unique identifier of the user
            query: Search query string
            limit: Maximum number of results to return
            offset: Number of results to skip

        Returns:
            List of matching Analysis entities
        """
        pass

    @abstractmethod
    def delete(self, analysis_id: str) -> bool:
        """
        Delete an analysis from the repository.

        Args:
            analysis_id: The unique identifier of the analysis to delete

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def count_by_user(self, user_id: str) -> int:
        """
        Count the total number of analyses for a user.

        Args:
            user_id: The unique identifier of the user

        Returns:
            Total analysis count for the user
        """
        pass

    @abstractmethod
    def update_slide_data(
        self,
        analysis_id: str,
        slides_data: List[Dict[str, Any]],
    ) -> bool:
        """
        Update only the slide data for an analysis.
        More efficient than full save for slide updates.

        Args:
            analysis_id: The unique identifier of the analysis
            slides_data: List of slide data dictionaries

        Returns:
            True if successful, False otherwise
        """
        pass


class DataRepository(ABC):
    """
    Abstract repository interface for cached data files.
    Defines the contract for data file persistence operations.
    """

    @abstractmethod
    def save_data_file(
        self,
        user_id: str,
        analysis_id: str,
        file_name: str,
        file_content: bytes,
    ) -> str:
        """
        Save a data file and return its identifier.

        Args:
            user_id: The unique identifier of the user
            analysis_id: The unique identifier of the analysis
            file_name: Original file name
            file_content: Raw file content bytes

        Returns:
            File identifier/path
        """
        pass

    @abstractmethod
    def get_data_file(self, analysis_id: str) -> Optional[bytes]:
        """
        Retrieve a data file by analysis ID.

        Args:
            analysis_id: The unique identifier of the analysis

        Returns:
            File content bytes if found, None otherwise
        """
        pass

    @abstractmethod
    def delete_data_file(self, analysis_id: str) -> bool:
        """
        Delete a data file.

        Args:
            analysis_id: The unique identifier of the analysis

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def get_file_metadata(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a data file.

        Args:
            analysis_id: The unique identifier of the analysis

        Returns:
            Metadata dictionary if found, None otherwise
        """
        pass
