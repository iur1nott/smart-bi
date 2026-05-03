"""
Analysis Service - Manages analysis sessions, slides, and visualizations.
Follows Single Responsibility Principle - only handles analysis management.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import os

from domain.entities import (
    Analysis,
    Slide,
    Visualization,
    VisualizationConfig,
    UserSession,
    VisualizationType,
)


class AnalysisRepository:
    """
    Repository interface for analysis persistence.
    Following the Repository pattern from DDD.
    """

    def save(self, analysis: Analysis) -> bool:
        """Save an analysis to persistence."""
        raise NotImplementedError

    def load(self, analysis_id: str) -> Optional[Analysis]:
        """Load an analysis by ID."""
        raise NotImplementedError

    def delete(self, analysis_id: str) -> bool:
        """Delete an analysis by ID."""
        raise NotImplementedError

    def list_all(self) -> List[Analysis]:
        """List all saved analyses."""
        raise NotImplementedError


class FileAnalysisRepository(AnalysisRepository):
    """
    File-based implementation of AnalysisRepository.
    Stores analyses as JSON files.
    """

    def __init__(self, storage_dir: str = "/home/z/my-project/dashboard_builder/data"):
        """Initialize with storage directory."""
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)

    def save(self, analysis: Analysis) -> bool:
        """Save an analysis to a JSON file."""
        try:
            file_path = os.path.join(self.storage_dir, f"{analysis.id}.json")
            with open(file_path, "w") as f:
                json.dump(analysis.to_dict(), f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving analysis: {e}")
            return False

    def load(self, analysis_id: str) -> Optional[Analysis]:
        """Load an analysis from a JSON file."""
        try:
            file_path = os.path.join(self.storage_dir, f"{analysis_id}.json")
            if os.path.exists(file_path):
                with open(file_path, "r") as f:
                    data = json.load(f)
                return Analysis.from_dict(data)
        except Exception as e:
            print(f"Error loading analysis: {e}")
        return None

    def delete(self, analysis_id: str) -> bool:
        """Delete an analysis file."""
        try:
            file_path = os.path.join(self.storage_dir, f"{analysis_id}.json")
            if os.path.exists(file_path):
                os.remove(file_path)
            return True
        except Exception as e:
            print(f"Error deleting analysis: {e}")
            return False

    def list_all(self) -> List[Analysis]:
        """List all saved analyses."""
        analyses = []
        try:
            for filename in os.listdir(self.storage_dir):
                if filename.endswith(".json"):
                    analysis_id = filename[:-5]
                    analysis = self.load(analysis_id)
                    if analysis:
                        analyses.append(analysis)
        except Exception as e:
            print(f"Error listing analyses: {e}")
        return analyses


class AnalysisService:
    """
    Service for managing analyses, slides, and visualizations.
    Coordinates between domain entities and repository.
    """

    def __init__(self, repository: Optional[AnalysisRepository] = None):
        """Initialize with optional repository."""
        self.repository = repository or FileAnalysisRepository()
        self._session: Optional[UserSession] = None

    def initialize_session(
        self, session_data: Optional[Dict[str, Any]] = None
    ) -> UserSession:
        """Initialize or restore a user session."""
        if session_data:
            self._session = UserSession.from_dict(session_data)
        else:
            self._session = UserSession()
        return self._session

    def get_session(self) -> UserSession:
        """Get the current user session."""
        if self._session is None:
            self._session = UserSession()
        return self._session

    def save_session(self) -> Dict[str, Any]:
        """Save and return session data."""
        if self._session:
            return self._session.to_dict()
        return {}

    # Analysis Management
    def create_analysis(self, name: str = "New Analysis") -> Analysis:
        """Create a new analysis."""
        session = self.get_session()
        analysis = session.create_analysis(name)
        self.repository.save(analysis)
        return analysis

    def get_current_analysis(self) -> Optional[Analysis]:
        """Get the currently active analysis."""
        session = self.get_session()
        return session.get_current_analysis()

    def set_current_analysis(self, analysis_id: str) -> Optional[Analysis]:
        """Set the current active analysis."""
        session = self.get_session()
        analysis = self.repository.load(analysis_id)
        if analysis:
            # Find in session or add it
            found = False
            for a in session.analyses:
                if a.id == analysis_id:
                    found = True
                    break
            if not found:
                session.analyses.append(analysis)

            session.current_analysis_id = analysis_id
            if analysis.slides:
                session.current_slide_id = analysis.slides[0].id
        return analysis

    def delete_analysis(self, analysis_id: str) -> bool:
        """Delete an analysis."""
        session = self.get_session()
        self.repository.delete(analysis_id)
        return session.delete_analysis(analysis_id)

    def rename_analysis(self, analysis_id: str, new_name: str) -> bool:
        """Rename an analysis."""
        session = self.get_session()
        for analysis in session.analyses:
            if analysis.id == analysis_id:
                analysis.name = new_name
                analysis.updated_at = datetime.now()
                self.repository.save(analysis)
                return True
        return False

    def get_analysis_history(self) -> List[Dict[str, Any]]:
        """Get list of all analyses for history display."""
        session = self.get_session()
        return [
            {
                "id": a.id,
                "name": a.name,
                "created_at": a.created_at.isoformat(),
                "updated_at": a.updated_at.isoformat(),
                "slide_count": len(a.slides),
                "file_name": a.data_schema.file_name if a.data_schema else None,
            }
            for a in session.analyses
        ]

    # Slide Management
    def add_slide(self, title: Optional[str] = None) -> Optional[Slide]:
        """Add a new slide to the current analysis."""
        analysis = self.get_current_analysis()
        if analysis:
            slide = Slide(title=title or f"Slide {len(analysis.slides) + 1}")
            analysis.add_slide(slide)
            session = self.get_session()
            session.current_slide_id = slide.id
            self.repository.save(analysis)
            return slide
        return None

    def get_current_slide(self) -> Optional[Slide]:
        """Get the currently active slide."""
        session = self.get_session()
        return session.get_current_slide()

    def set_current_slide(self, slide_id: str) -> Optional[Slide]:
        """Set the current active slide."""
        session = self.get_session()
        analysis = session.get_current_analysis()
        if analysis:
            slide = analysis.get_slide(slide_id)
            if slide:
                session.current_slide_id = slide_id
                return slide
        return None

    def delete_slide(self, slide_id: str) -> bool:
        """Delete a slide from the current analysis."""
        analysis = self.get_current_analysis()
        if analysis and len(analysis.slides) > 1:
            result = analysis.remove_slide(slide_id)
            if result:
                session = self.get_session()
                if session.current_slide_id == slide_id:
                    session.current_slide_id = (
                        analysis.slides[0].id if analysis.slides else None
                    )
                self.repository.save(analysis)
            return result
        return False

    def update_slide_title(self, slide_id: str, title: str) -> bool:
        """Update a slide's title."""
        analysis = self.get_current_analysis()
        if analysis:
            slide = analysis.get_slide(slide_id)
            if slide:
                slide.title = title
                slide.updated_at = datetime.now()
                self.repository.save(analysis)
                return True
        return False

    def reorder_slides(self, new_order: List[str]) -> bool:
        """Reorder slides in the current analysis."""
        analysis = self.get_current_analysis()
        if analysis:
            analysis.reorder_slides(new_order)
            self.repository.save(analysis)
            return True
        return False

    # Visualization Management
    def add_visualization(
        self,
        slide_id: str,
        config: VisualizationConfig,
        position: Optional[Dict[str, float]] = None,
        size: Optional[Dict[str, float]] = None,
    ) -> Optional[Visualization]:
        """Add a visualization to a slide."""
        analysis = self.get_current_analysis()
        if analysis:
            slide = analysis.get_slide(slide_id)
            if slide:
                viz = Visualization(
                    config=config,
                    position=position or {"x": 0, "y": 0},
                    size=size or {"width": 400, "height": 300},
                )
                slide.add_visualization(viz)
                self.repository.save(analysis)
                return viz
        return None

    def update_visualization(
        self,
        slide_id: str,
        viz_id: str,
        config: Optional[VisualizationConfig] = None,
        position: Optional[Dict[str, float]] = None,
        size: Optional[Dict[str, float]] = None,
        comment: Optional[str] = None,
    ) -> bool:
        """Update a visualization's properties."""
        analysis = self.get_current_analysis()
        if analysis:
            slide = analysis.get_slide(slide_id)
            if slide:
                viz = slide.get_visualization(viz_id)
                if viz:
                    if config:
                        viz.config = config
                    if position:
                        viz.position = position
                    if size:
                        viz.size = size
                    if comment is not None:
                        viz.comment = comment
                    slide.updated_at = datetime.now()
                    self.repository.save(analysis)
                    return True
        return False

    def delete_visualization(self, slide_id: str, viz_id: str) -> bool:
        """Delete a visualization from a slide."""
        analysis = self.get_current_analysis()
        if analysis:
            slide = analysis.get_slide(slide_id)
            if slide:
                result = slide.remove_visualization(viz_id)
                if result:
                    self.repository.save(analysis)
                return result
        return False

    def get_visualization(self, slide_id: str, viz_id: str) -> Optional[Visualization]:
        """Get a specific visualization."""
        analysis = self.get_current_analysis()
        if analysis:
            slide = analysis.get_slide(slide_id)
            if slide:
                return slide.get_visualization(viz_id)
        return None

    # Settings Management
    def update_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Update user settings."""
        session = self.get_session()
        session.settings.update(settings)
        return session.settings

    def get_settings(self) -> Dict[str, Any]:
        """Get current user settings."""
        session = self.get_session()
        return session.settings

    def save_current_analysis(self) -> bool:
        """Save the current analysis to repository."""
        analysis = self.get_current_analysis()
        if analysis:
            return self.repository.save(analysis)
        return False

    def load_saved_analyses(self) -> List[Analysis]:
        """Load all saved analyses from repository."""
        return self.repository.list_all()
