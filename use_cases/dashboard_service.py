"""
Dashboard Service - Handles dashboard and visualization management.
Coordinates between repositories and provides business logic.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
import uuid

from domain.entities import (
    Dashboard,
    Visualization,
    VisualizationConfig,
    VisualizationType,
)
from infrastructure.repositories.dashboard_repository import DashboardRepositoryImpl
from infrastructure.repositories.file_repository import FileRepositoryImpl

logger = logging.getLogger(__name__)


class DashboardService:
    """
    Service responsible for dashboard and visualization operations including:
    - Creating and managing dashboards
    - Adding, updating, and deleting visualizations
    - Managing dashboard metadata
    """

    def __init__(
        self,
        dashboard_repo: Optional[DashboardRepositoryImpl] = None,
        file_repo: Optional[FileRepositoryImpl] = None,
    ):
        """
        Initialize the dashboard service.

        Args:
            dashboard_repo: Optional DashboardRepositoryImpl instance
            file_repo: Optional FileRepositoryImpl instance
        """
        self._dashboard_repo = dashboard_repo or DashboardRepositoryImpl()
        self._file_repo = file_repo or FileRepositoryImpl()
        self._current_user_id: Optional[str] = None

    def set_current_user(self, user_id: str) -> None:
        """Set the current user context."""
        self._current_user_id = user_id

    # Dashboard operations
    def create_dashboard(
        self, title: str, file_id: Optional[str] = None
    ) -> Optional[Dashboard]:
        """
        Create a new dashboard.

        Args:
            title: Dashboard title
            file_id: Optional file ID to associate with the dashboard

        Returns:
            Created Dashboard entity, or None on failure
        """
        if not self._current_user_id:
            logger.error("No user context set")
            return None

        try:
            dashboard_id = str(uuid.uuid4())
            dashboard = Dashboard(
                dashboard_id=dashboard_id,
                user_id=self._current_user_id,
                title=title,
                created_at=datetime.now(),
            )

            # Associate file if provided
            if file_id:
                file_entity = self._file_repo.find_file_by_id(file_id)
                if file_entity:
                    dashboard.file = file_entity

            # Save to database
            if self._dashboard_repo.save_dashboard(dashboard):
                logger.info(f"Created dashboard {dashboard_id}")
                return dashboard

            return None

        except Exception as e:
            logger.error(f"Error creating dashboard: {e}")
            return None

    def get_dashboard(self, dashboard_id: str) -> Optional[Dashboard]:
        """
        Get a dashboard by ID with all visualizations.

        Args:
            dashboard_id: The dashboard ID

        Returns:
            Dashboard entity, or None if not found
        """
        dashboard = self._dashboard_repo.find_dashboard_by_id(dashboard_id)

        # Load associated file if available
        if dashboard and dashboard.visualizations:
            # Get the first sheet's file
            first_viz = dashboard.visualizations[0]
            sheet = self._file_repo.find_sheet_by_id(first_viz.sheet_id)
            if sheet:
                file_entity = self._file_repo.find_file_by_id(sheet.file_id)
                dashboard.file = file_entity

        return dashboard

    def get_user_dashboards(self, user_id: Optional[str] = None) -> List[Dashboard]:
        """
        Get all dashboards for a user.

        Args:
            user_id: Optional user ID (uses current user if not specified)

        Returns:
            List of Dashboard entities
        """
        uid = user_id or self._current_user_id
        if not uid:
            return []

        return self._dashboard_repo.find_dashboards_by_user(uid)

    def update_dashboard_title(self, dashboard_id: str, title: str) -> bool:
        """
        Update a dashboard's title.

        Args:
            dashboard_id: The dashboard ID
            title: New title

        Returns:
            True if successful, False otherwise
        """
        return self._dashboard_repo.update_dashboard_title(dashboard_id, title)

    def delete_dashboard(self, dashboard_id: str) -> bool:
        """
        Delete a dashboard and all its visualizations.

        Args:
            dashboard_id: The dashboard ID to delete

        Returns:
            True if successful, False otherwise
        """
        return self._dashboard_repo.delete_dashboard(dashboard_id)

    def save_dashboard(self, dashboard: Dashboard) -> bool:
        """
        Save a dashboard (for updates).

        Args:
            dashboard: The dashboard entity to save

        Returns:
            True if successful, False otherwise
        """
        return self._dashboard_repo.save_dashboard(dashboard)

    # Visualization operations
    def add_visualization(
        self,
        dashboard_id: str,
        sheet_id: str,
        viz_type: str,
        config: VisualizationConfig,
    ) -> Optional[Visualization]:
        """
        Add a visualization to a dashboard.

        Args:
            dashboard_id: The dashboard ID
            sheet_id: The sheet ID for data source
            viz_type: Type of visualization (bar, line, pie, etc.)
            config: Visualization configuration

        Returns:
            Created Visualization entity, or None on failure
        """
        try:
            viz_id = str(uuid.uuid4())
            visualization = Visualization(
                viz_id=viz_id,
                dashboard_id=dashboard_id,
                sheet_id=sheet_id,
                viz_type=viz_type,
                config=config,
                created_at=datetime.now(),
            )

            if self._dashboard_repo.save_visualization(visualization):
                logger.info(f"Created visualization {viz_id}")
                return visualization

            return None

        except Exception as e:
            logger.error(f"Error adding visualization: {e}")
            return None

    def update_visualization(
        self,
        viz_id: str,
        config: Optional[VisualizationConfig] = None,
        viz_type: Optional[str] = None,
    ) -> bool:
        """
        Update a visualization.

        Args:
            viz_id: The visualization ID
            config: Optional new configuration
            viz_type: Optional new visualization type

        Returns:
            True if successful, False otherwise
        """
        try:
            viz = self._dashboard_repo.find_visualization_by_id(viz_id)
            if not viz:
                return False

            if config:
                viz.config = config
            if viz_type:
                viz.viz_type = viz_type

            return self._dashboard_repo.save_visualization(viz)

        except Exception as e:
            logger.error(f"Error updating visualization {viz_id}: {e}")
            return False

    def delete_visualization(self, viz_id: str) -> bool:
        """
        Delete a visualization.

        Args:
            viz_id: The visualization ID to delete

        Returns:
            True if successful, False otherwise
        """
        return self._dashboard_repo.delete_visualization(viz_id)

    def get_visualization(self, viz_id: str) -> Optional[Visualization]:
        """
        Get a visualization by ID.

        Args:
            viz_id: The visualization ID

        Returns:
            Visualization entity, or None if not found
        """
        return self._dashboard_repo.find_visualization_by_id(viz_id)

    def get_dashboard_visualizations(self, dashboard_id: str) -> List[Visualization]:
        """
        Get all visualizations for a dashboard.

        Args:
            dashboard_id: The dashboard ID

        Returns:
            List of Visualization entities
        """
        return self._dashboard_repo.find_visualizations_by_dashboard(dashboard_id)

    # Utility methods
    def get_available_viz_types(self) -> List[Dict[str, str]]:
        """
        Get available visualization types.

        Returns:
            List of visualization type info
        """
        return [
            {"type": "bar", "name": "Bar Chart", "icon": "📊"},
            {"type": "line", "name": "Line Chart", "icon": "📈"},
            {"type": "pie", "name": "Pie Chart", "icon": "🥧"},
            {"type": "area", "name": "Area Chart", "icon": "📉"},
            {"type": "scatter", "name": "Scatter Plot", "icon": "⚬"},
            {"type": "histogram", "name": "Histogram", "icon": "📊"},
            {"type": "box", "name": "Box Plot", "icon": "📦"},
            {"type": "heatmap", "name": "Heatmap", "icon": "🔥"},
            {"type": "table", "name": "Table", "icon": "📋"},
            {"type": "metric_card", "name": "Metric Card", "icon": "🎴"},
        ]

    def get_aggregation_options(self) -> List[str]:
        """
        Get available aggregation options.

        Returns:
            List of aggregation function names
        """
        return Constants.AGGREGATION_FUNCTIONS
