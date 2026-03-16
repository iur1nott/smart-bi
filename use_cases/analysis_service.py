"""
Analysis Service - Handles analysis, slide, and visualization management.
Implements business logic for creating, updating, and managing analyses.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from domain.entities import (
    Analysis,
    Slide,
    Visualization,
    VisualizationConfig,
    VisualizationType,
    UserSession,
    DataSchema,
)
from domain.repositories import AnalysisRepository, SessionRepository
from infrastructure.repositories import AnalysisRepositoryImpl, SessionRepositoryImpl

logger = logging.getLogger(__name__)


class AnalysisService:
    """
    Service responsible for managing analyses, slides, and visualizations.
    Implements the business logic for the analysis domain following SOLID principles.
    """

    def __init__(
        self,
        analysis_repository: Optional[AnalysisRepository] = None,
        session_repository: Optional[SessionRepository] = None,
    ):
        """
        Initialize the analysis service.

        Args:
            analysis_repository: Repository for analysis persistence
            session_repository: Repository for session persistence
        """
        self._analysis_repository = analysis_repository or AnalysisRepositoryImpl()
        self._session_repository = session_repository or SessionRepositoryImpl()
        self._current_user_id: Optional[str] = None

    def set_current_user(self, user_id: str) -> None:
        """
        Set the current user context.

        Args:
            user_id: The unique identifier of the current user
        """
        self._current_user_id = user_id

    def create_analysis(self, name: str = "New Analysis") -> Optional[Analysis]:
        """
        Create a new analysis for the current user.

        Args:
            name: Name for the new analysis

        Returns:
            Created Analysis entity, or None if no user is set
        """
        if not self._current_user_id:
            logger.warning("Cannot create analysis: no user set")
            return None

        analysis = Analysis(
            name=name,
            user_id=self._current_user_id,
        )

        if self._analysis_repository.save(analysis):
            logger.info(
                f"Created analysis: {analysis.id} for user {self._current_user_id}"
            )
            return analysis

        return None

    def get_analysis(self, analysis_id: str) -> Optional[Analysis]:
        """
        Get an analysis by ID.

        Args:
            analysis_id: The unique identifier of the analysis

        Returns:
            Analysis entity if found, None otherwise
        """
        analysis = self._analysis_repository.find_by_id(analysis_id)

        # Verify ownership
        if analysis and analysis.user_id != self._current_user_id:
            logger.warning(
                f"User {self._current_user_id} attempted to access analysis {analysis_id}"
            )
            return None

        return analysis

    def get_user_analyses(self, limit: int = 50, offset: int = 0) -> List[Analysis]:
        """
        Get all analyses for the current user.

        Args:
            limit: Maximum number of analyses to return
            offset: Number of analyses to skip

        Returns:
            List of Analysis entities
        """
        if not self._current_user_id:
            return []

        return self._analysis_repository.find_by_user_id(
            self._current_user_id, limit=limit, offset=offset
        )

    def get_recent_analyses(self, limit: int = 10) -> List[Analysis]:
        """
        Get recent analyses for the current user.

        Args:
            limit: Maximum number of analyses to return

        Returns:
            List of Analysis entities ordered by update time
        """
        if not self._current_user_id:
            return []

        return self._analysis_repository.list_recent(self._current_user_id, limit)

    def save_analysis(self, analysis: Analysis) -> bool:
        """
        Save an analysis.

        Args:
            analysis: The analysis to save

        Returns:
            True if successful, False otherwise
        """
        analysis.updated_at = datetime.now()
        return self._analysis_repository.save(analysis)

    def delete_analysis(self, analysis_id: str) -> bool:
        """
        Delete an analysis.

        Args:
            analysis_id: The unique identifier of the analysis to delete

        Returns:
            True if successful, False otherwise
        """
        # Verify ownership
        analysis = self.get_analysis(analysis_id)
        if not analysis:
            return False

        result = self._analysis_repository.delete(analysis_id)

        if result:
            logger.info(f"Deleted analysis: {analysis_id}")

        return result

    def rename_analysis(self, analysis_id: str, new_name: str) -> bool:
        """
        Rename an analysis.

        Args:
            analysis_id: The unique identifier of the analysis
            new_name: New name for the analysis

        Returns:
            True if successful, False otherwise
        """
        analysis = self.get_analysis(analysis_id)
        if not analysis:
            return False

        analysis.name = new_name
        analysis.updated_at = datetime.now()
        return self._analysis_repository.save(analysis)

    def set_data_schema(self, analysis_id: str, schema: DataSchema) -> bool:
        """
        Set the data schema for an analysis.

        Args:
            analysis_id: The unique identifier of the analysis
            schema: DataSchema to set

        Returns:
            True if successful, False otherwise
        """
        analysis = self.get_analysis(analysis_id)
        if not analysis:
            return False

        analysis.data_schema = schema
        analysis.updated_at = datetime.now()
        return self._analysis_repository.save(analysis)

    def add_slide(
        self, analysis_id: str, title: Optional[str] = None
    ) -> Optional[Slide]:
        """
        Add a new slide to an analysis.

        Args:
            analysis_id: The unique identifier of the analysis
            title: Optional title for the slide

        Returns:
            Created Slide entity, or None if analysis not found
        """
        analysis = self.get_analysis(analysis_id)
        if not analysis:
            return None

        slide = Slide(title=title or f"Slide {len(analysis.slides) + 1}")
        analysis.add_slide(slide)
        analysis.updated_at = datetime.now()

        if self._analysis_repository.save(analysis):
            return slide

        return None

    def get_slide(self, analysis_id: str, slide_id: str) -> Optional[Slide]:
        """
        Get a slide from an analysis.

        Args:
            analysis_id: The unique identifier of the analysis
            slide_id: The unique identifier of the slide

        Returns:
            Slide entity if found, None otherwise
        """
        analysis = self.get_analysis(analysis_id)
        if not analysis:
            return None

        return analysis.get_slide(slide_id)

    def update_slide_title(self, analysis_id: str, slide_id: str, title: str) -> bool:
        """
        Update a slide's title.

        Args:
            analysis_id: The unique identifier of the analysis
            slide_id: The unique identifier of the slide
            title: New title for the slide

        Returns:
            True if successful, False otherwise
        """
        analysis = self.get_analysis(analysis_id)
        if not analysis:
            return False

        slide = analysis.get_slide(slide_id)
        if not slide:
            return False

        slide.title = title
        slide.updated_at = datetime.now()
        analysis.updated_at = datetime.now()

        return self._analysis_repository.save(analysis)

    def delete_slide(self, analysis_id: str, slide_id: str) -> bool:
        """
        Delete a slide from an analysis.

        Args:
            analysis_id: The unique identifier of the analysis
            slide_id: The unique identifier of the slide to delete

        Returns:
            True if successful, False otherwise
        """
        analysis = self.get_analysis(analysis_id)
        if not analysis:
            return False

        result = analysis.remove_slide(slide_id)
        if result:
            analysis.updated_at = datetime.now()
            self._analysis_repository.save(analysis)

        return result

    def add_visualization(
        self,
        analysis_id: str,
        slide_id: str,
        config: VisualizationConfig,
        position: Optional[Dict[str, float]] = None,
        size: Optional[Dict[str, float]] = None,
    ) -> Optional[Visualization]:
        """
        Add a visualization to a slide.

        Args:
            analysis_id: The unique identifier of the analysis
            slide_id: The unique identifier of the slide
            config: Visualization configuration
            position: Optional position {x, y}
            size: Optional size {width, height}

        Returns:
            Created Visualization entity, or None if not found
        """
        analysis = self.get_analysis(analysis_id)
        if not analysis:
            return None

        slide = analysis.get_slide(slide_id)
        if not slide:
            return None

        viz = Visualization(
            config=config,
            position=position or {"x": 0, "y": 0},
            size=size or {"width": 400, "height": 300},
        )

        slide.add_visualization(viz)
        analysis.updated_at = datetime.now()

        if self._analysis_repository.save(analysis):
            logger.info(f"Added visualization {viz.id} to slide {slide_id}")
            return viz

        return None

    def update_visualization(
        self,
        analysis_id: str,
        slide_id: str,
        viz_id: str,
        config: Optional[VisualizationConfig] = None,
        position: Optional[Dict[str, float]] = None,
        size: Optional[Dict[str, float]] = None,
        comment: Optional[str] = None,
    ) -> bool:
        """
        Update a visualization.

        Args:
            analysis_id: The unique identifier of the analysis
            slide_id: The unique identifier of the slide
            viz_id: The unique identifier of the visualization
            config: Optional new configuration
            position: Optional new position
            size: Optional new size
            comment: Optional comment to set

        Returns:
            True if successful, False otherwise
        """
        analysis = self.get_analysis(analysis_id)
        if not analysis:
            return False

        slide = analysis.get_slide(slide_id)
        if not slide:
            return False

        viz = slide.get_visualization(viz_id)
        if not viz:
            return False

        if config is not None:
            viz.config = config
        if position is not None:
            viz.position = position
        if size is not None:
            viz.size = size
        if comment is not None:
            viz.comment = comment

        viz.updated_at = datetime.now()
        slide.updated_at = datetime.now()
        analysis.updated_at = datetime.now()

        return self._analysis_repository.save(analysis)

    def delete_visualization(
        self, analysis_id: str, slide_id: str, viz_id: str
    ) -> bool:
        """
        Delete a visualization from a slide.

        Args:
            analysis_id: The unique identifier of the analysis
            slide_id: The unique identifier of the slide
            viz_id: The unique identifier of the visualization

        Returns:
            True if successful, False otherwise
        """
        analysis = self.get_analysis(analysis_id)
        if not analysis:
            return False

        slide = analysis.get_slide(slide_id)
        if not slide:
            return False

        result = slide.remove_visualization(viz_id)
        if result:
            analysis.updated_at = datetime.now()
            self._analysis_repository.save(analysis)

        return result

    def update_visualization_data(
        self,
        analysis_id: str,
        slide_id: str,
        viz_id: str,
        data_snapshot: Dict[str, Any],
    ) -> bool:
        """
        Update the data snapshot for a visualization.

        Args:
            analysis_id: The unique identifier of the analysis
            slide_id: The unique identifier of the slide
            viz_id: The unique identifier of the visualization
            data_snapshot: Data snapshot to store

        Returns:
            True if successful, False otherwise
        """
        analysis = self.get_analysis(analysis_id)
        if not analysis:
            return False

        slide = analysis.get_slide(slide_id)
        if not slide:
            return False

        viz = slide.get_visualization(viz_id)
        if not viz:
            return False

        viz.data_snapshot = data_snapshot
        viz.updated_at = datetime.now()

        return self._analysis_repository.save(analysis)

    def search_analyses(self, query: str, limit: int = 20) -> List[Analysis]:
        """
        Search analyses by name.

        Args:
            query: Search query string
            limit: Maximum number of results

        Returns:
            List of matching Analysis entities
        """
        if not self._current_user_id:
            return []

        return self._analysis_repository.search(self._current_user_id, query, limit)

    def get_analysis_count(self) -> int:
        """
        Get total count of analyses for the current user.

        Returns:
            Total count of analyses
        """
        if not self._current_user_id:
            return 0

        return self._analysis_repository.count_by_user(self._current_user_id)

    def update_analysis_settings(
        self, analysis_id: str, settings: Dict[str, Any]
    ) -> bool:
        """
        Update settings for an analysis.

        Args:
            analysis_id: The unique identifier of the analysis
            settings: Settings to merge

        Returns:
            True if successful, False otherwise
        """
        analysis = self.get_analysis(analysis_id)
        if not analysis:
            return False

        analysis.settings.update(settings)
        analysis.updated_at = datetime.now()

        return self._analysis_repository.save(analysis)
