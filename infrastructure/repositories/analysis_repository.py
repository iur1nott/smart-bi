"""
Analysis Repository Implementation - PostgreSQL-based analysis persistence.
Implements the AnalysisRepository interface using SQLAlchemy.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
import json

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
                    session.query(AnalysisModel).filter(AnalysisModel.id == analysis.id).first()
                )

                slides_data = [self._slide_to_dict(s) for s in analysis.slides]
                schema_data = analysis.data_schema.to_dict() if analysis.data_schema else None

                if existing:
                    # Update existing analysis
                    existing.name = analysis.name
                    existing.file_path = analysis.file_path
                    existing.data_schema = schema_data
                    existing.slides = slides_data
                    existing.settings = analysis.settings
                    existing.updated_at = datetime.utcnow()
                else:
                    # Create new analysis
                    model = AnalysisModel(
                        id=analysis.id,
                        user_id=analysis.user_id,
                        name=analysis.name,
                        file_path=analysis.file_path,
                        data_schema=schema_data,
                        slides=slides_data,
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
                model = session.query(AnalysisModel).filter(AnalysisModel.id == analysis_id).first()

                if model:
                    return self._model_to_entity(model)
                return None

        except Exception as e:
            logger.error(f"Error finding analysis by ID {analysis_id}: {e}")
            return None

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
        try:
            with self._db.session_scope() as session:
                models = (
                    session.query(AnalysisModel)
                    .filter(AnalysisModel.user_id == user_id)
                    .order_by(AnalysisModel.updated_at.desc())
                    .limit(limit)
                    .offset(offset)
                    .all()
                )

                return [self._model_to_entity(m) for m in models]

        except Exception as e:
            logger.error(f"Error finding analyses for user {user_id}: {e}")
            return []

    def list_recent(self, user_id: str, limit: int = 10) -> List[Analysis]:
        """
        Find recent analyses for a user.

        Args:
            user_id: The unique identifier of the user
            limit: Maximum number of analyses to return

        Returns:
            List of Analysis entities ordered by update time
        """
        return self.find_by_user_id(user_id, limit=limit, offset=0)

    def search(
        self,
        user_id: str,
        query: str,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Analysis]:
        """
        Search analyses by name.

        Args:
            user_id: The unique identifier of the user
            query: Search query string
            limit: Maximum number of results to return
            offset: Number of results to skip

        Returns:
            List of matching Analysis entities
        """
        try:
            with self._db.session_scope() as session:
                models = (
                    session.query(AnalysisModel)
                    .filter(
                        AnalysisModel.user_id == user_id,
                        AnalysisModel.name.ilike(f"%{query}%"),
                    )
                    .order_by(AnalysisModel.updated_at.desc())
                    .limit(limit)
                    .offset(offset)
                    .all()
                )

                return [self._model_to_entity(m) for m in models]

        except Exception as e:
            logger.error(f"Error searching analyses for user {user_id}: {e}")
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
                model = session.query(AnalysisModel).filter(AnalysisModel.id == analysis_id).first()

                if model:
                    session.delete(model)
                    return True
                return False

        except Exception as e:
            logger.error(f"Error deleting analysis {analysis_id}: {e}")
            return False

    def count_by_user(self, user_id: str) -> int:
        """
        Count the total number of analyses for a user.

        Args:
            user_id: The unique identifier of the user

        Returns:
            Total analysis count for the user
        """
        try:
            with self._db.session_scope() as session:
                return session.query(AnalysisModel).filter(AnalysisModel.user_id == user_id).count()

        except Exception as e:
            logger.error(f"Error counting analyses for user {user_id}: {e}")
            return 0

    def update_slide_data(
        self,
        analysis_id: str,
        slides_data: List[Dict[str, Any]],
    ) -> bool:
        """
        Update only the slide data for an analysis.

        Args:
            analysis_id: The unique identifier of the analysis
            slides_data: List of slide data dictionaries

        Returns:
            True if successful, False otherwise
        """
        try:
            with self._db.session_scope() as session:
                model = session.query(AnalysisModel).filter(AnalysisModel.id == analysis_id).first()

                if model:
                    model.slides = slides_data
                    model.updated_at = datetime.utcnow()
                    return True
                return False

        except Exception as e:
            logger.error(f"Error updating slide data for analysis {analysis_id}: {e}")
            return False

    def _model_to_entity(self, model: AnalysisModel) -> Analysis:
        """Convert a SQLAlchemy model to a domain entity."""
        analysis = Analysis(
            id=str(model.id),
            user_id=str(model.user_id),
            name=model.name,
            file_path=model.file_path or "",
            data_schema=DataSchema.from_dict(model.data_schema) if model.data_schema else None,
            slides=[],  # Will be populated below
            settings=model.settings or {},
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

        # Convert slides
        if model.slides:
            for slide_data in model.slides:
                slide = self._dict_to_slide(slide_data)
                analysis.slides.append(slide)

        return analysis

    def _slide_to_dict(self, slide: Slide) -> Dict[str, Any]:
        """Convert a Slide entity to a dictionary."""
        return {
            "id": slide.id,
            "title": slide.title,
            "visualizations": [self._viz_to_dict(v) for v in slide.visualizations],
            "layout": slide.layout,
            "created_at": slide.created_at.isoformat() if slide.created_at else None,
            "updated_at": slide.updated_at.isoformat() if slide.updated_at else None,
        }

    def _viz_to_dict(self, viz: Visualization) -> Dict[str, Any]:
        """Convert a Visualization entity to a dictionary."""
        return {
            "id": viz.id,
            "config": viz.config.to_dict() if viz.config else None,
            "position": viz.position,
            "size": viz.size,
            "comment": viz.comment,
            "data_snapshot": viz.data_snapshot,
            "created_at": viz.created_at.isoformat() if viz.created_at else None,
            "updated_at": viz.updated_at.isoformat() if viz.updated_at else None,
        }

    def _dict_to_slide(self, data: Dict[str, Any]) -> Slide:
        """Convert a dictionary to a Slide entity."""
        slide = Slide(
            id=data.get("id"),
            title=data.get("title", "Untitled Slide"),
            layout=data.get("layout", {}),
            created_at=datetime.fromisoformat(data["created_at"])
            if data.get("created_at")
            else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"])
            if data.get("updated_at")
            else datetime.now(),
        )

        # Add visualizations
        for viz_data in data.get("visualizations", []):
            viz = self._dict_to_viz(viz_data)
            slide.visualizations.append(viz)

        return slide

    def _dict_to_viz(self, data: Dict[str, Any]) -> Visualization:
        """Convert a dictionary to a Visualization entity."""
        config = None
        if data.get("config"):
            config = VisualizationConfig.from_dict(data["config"])

        return Visualization(
            id=data.get("id"),
            config=config,
            position=data.get("position", {"x": 0, "y": 0}),
            size=data.get("size", {"width": 400, "height": 300}),
            comment=data.get("comment", ""),
            data_snapshot=data.get("data_snapshot"),
            created_at=datetime.fromisoformat(data["created_at"])
            if data.get("created_at")
            else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"])
            if data.get("updated_at")
            else datetime.now(),
        )
