"""
Analysis Repository Implementation - PostgreSQL-based analysis persistence.
Implements the AnalysisRepository interface using SQLAlchemy.
"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_

from domain.entities import (
    Analysis,
    Slide,
    Visualization,
    VisualizationConfig,
    DataSchema,
)
from domain.repositories import AnalysisRepository
from infrastructure.database import Database, get_database
from infrastructure.models import AnalysisModel
import logging
import json

logger = logging.getLogger(__name__)


class AnalysisRepositoryImpl(AnalysisRepository):
    """
    PostgreSQL implementation of the AnalysisRepository interface.
    Handles analysis persistence operations using SQLAlchemy ORM.
    """

    def __init__(self, database: Optional[Database] = None):
        """
        Initialize the repository with a database connection.

        Args:
            database: Optional Database instance. Uses global instance if not provided.
        """
        self._db = database or get_database()

    def save(self, analysis: Analysis) -> bool:
        """
        Save an analysis to the database.

        Args:
            analysis: The analysis entity to save

        Returns:
            True if successful, False otherwise
        """
        try:
            with self._db.session_scope() as session:
                # Check if analysis exists
                existing = (
                    session.query(AnalysisModel)
                    .filter(AnalysisModel.id == analysis.id)
                    .first()
                )

                # Serialize analysis data
                analysis_data = analysis.to_dict()

                if existing:
                    # Update existing analysis
                    existing.name = analysis.name
                    existing.file_path = analysis.file_path
                    existing.data_schema = (
                        analysis.data_schema.to_dict() if analysis.data_schema else None
                    )
                    existing.slides = [s.to_dict() for s in analysis.slides]
                    existing.settings = analysis.settings
                    existing.updated_at = datetime.utcnow()
                else:
                    # Create new analysis
                    model = AnalysisModel(
                        id=analysis.id,
                        user_id=analysis.user_id,
                        name=analysis.name,
                        file_path=analysis.file_path,
                        data_schema=analysis.data_schema.to_dict()
                        if analysis.data_schema
                        else None,
                        slides=[s.to_dict() for s in analysis.slides],
                        settings=analysis.settings,
                        created_at=analysis.created_at,
                        updated_at=analysis.updated_at,
                    )
                    session.add(model)

                return True

        except Exception as e:
            logger.error(f"Error saving analysis {analysis.id}: {e}")
            return False

    def find_by_id(self, analysis_id: str) -> Optional[Analysis]:
        """
        Find an analysis by its ID.

        Args:
            analysis_id: The unique identifier of the analysis

        Returns:
            Analysis entity if found, None otherwise
        """
        try:
            with self._db.session_scope() as session:
                model = (
                    session.query(AnalysisModel)
                    .filter(AnalysisModel.id == analysis_id)
                    .first()
                )

                if model:
                    return self._model_to_entity(model)
                return None

        except Exception as e:
            logger.error(f"Error finding analysis by ID {analysis_id}: {e}")
            return None

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
        try:
            with self._db.session_scope() as session:
                models = (
                    session.query(AnalysisModel)
                    .filter(AnalysisModel.user_id == user_id)
                    .order_by(AnalysisModel.updated_at.desc())
                    .offset(offset)
                    .limit(limit)
                    .all()
                )

                return [self._model_to_entity(m) for m in models]

        except Exception as e:
            logger.error(f"Error finding analyses for user {user_id}: {e}")
            return []

    def delete(self, analysis_id: str) -> bool:
        """
        Delete an analysis from the database.

        Args:
            analysis_id: The unique identifier of the analysis to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            with self._db.session_scope() as session:
                deleted = (
                    session.query(AnalysisModel)
                    .filter(AnalysisModel.id == analysis_id)
                    .delete()
                )
                return deleted > 0

        except Exception as e:
            logger.error(f"Error deleting analysis {analysis_id}: {e}")
            return False

    def list_recent(self, user_id: str, limit: int = 10) -> List[Analysis]:
        """
        List recent analyses for a user.

        Args:
            user_id: The unique identifier of the user
            limit: Maximum number of analyses to return

        Returns:
            List of Analysis entities ordered by update time
        """
        try:
            with self._db.session_scope() as session:
                models = (
                    session.query(AnalysisModel)
                    .filter(AnalysisModel.user_id == user_id)
                    .order_by(AnalysisModel.updated_at.desc())
                    .limit(limit)
                    .all()
                )

                return [self._model_to_entity(m) for m in models]

        except Exception as e:
            logger.error(f"Error listing recent analyses for user {user_id}: {e}")
            return []

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
        try:
            with self._db.session_scope() as session:
                search_pattern = f"%{query}%"
                models = (
                    session.query(AnalysisModel)
                    .filter(
                        AnalysisModel.user_id == user_id,
                        AnalysisModel.name.ilike(search_pattern),
                    )
                    .order_by(AnalysisModel.updated_at.desc())
                    .limit(limit)
                    .all()
                )

                return [self._model_to_entity(m) for m in models]

        except Exception as e:
            logger.error(f"Error searching analyses: {e}")
            return []

    def count_by_user(self, user_id: str) -> int:
        """
        Count total analyses for a user.

        Args:
            user_id: The unique identifier of the user

        Returns:
            Total count of analyses
        """
        try:
            with self._db.session_scope() as session:
                count = (
                    session.query(AnalysisModel)
                    .filter(AnalysisModel.user_id == user_id)
                    .count()
                )
                return count

        except Exception as e:
            logger.error(f"Error counting analyses for user {user_id}: {e}")
            return 0

    def _model_to_entity(self, model: AnalysisModel) -> Analysis:
        """
        Convert a SQLAlchemy model to a domain entity.

        Args:
            model: SQLAlchemy AnalysisModel instance

        Returns:
            Analysis domain entity
        """
        # Deserialize slides
        slides = []
        for slide_data in model.slides or []:
            slide = Slide.from_dict(slide_data)
            slides.append(slide)

        # Deserialize data schema
        data_schema = None
        if model.data_schema:
            data_schema = DataSchema.from_dict(model.data_schema)

        return Analysis(
            id=str(model.id),
            user_id=str(model.user_id),
            name=model.name,
            file_path=model.file_path or "",
            data_schema=data_schema,
            slides=slides,
            settings=model.settings or {},
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
