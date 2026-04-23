"""
Dashboard Repository Implementation - PostgreSQL-based dashboard persistence.
Handles dashboards and visualizations.
"""

from typing import List, Optional
from datetime import datetime
import logging
import uuid

from domain.entities import Dashboard, Visualization, VisualizationConfig
from infrastructure.database import Database, get_database
from infrastructure.models import DashboardModel, VisualizationModel

logger = logging.getLogger(__name__)


class DashboardRepositoryImpl:
    """
    PostgreSQL implementation for dashboard persistence.
    Handles dashboards and their visualizations using SQLAlchemy ORM.
    """

    def __init__(self, database: Optional[Database] = None):
        """
        Initialize the repository with a database connection.

        Args:
            database: Optional Database instance. Uses global instance if not provided.
        """
        self._db = database or get_database()

    def save_dashboard(self, dashboard: Dashboard) -> bool:
        """
        Save a dashboard to the database.

        Args:
            dashboard: The dashboard entity to save

        Returns:
            True if successful, False otherwise
        """
        try:
            with self._db.session_scope() as session:
                # Check if dashboard exists
                existing = (
                    session.query(DashboardModel)
                    .filter(DashboardModel.dashboard_id == dashboard.dashboard_id)
                    .first()
                )

                if existing:
                    # Update existing dashboard
                    existing.title = dashboard.title
                else:
                    # Create new dashboard
                    model = DashboardModel(
                        dashboard_id=dashboard.dashboard_id,
                        user_id=dashboard.user_id,
                        title=dashboard.title,
                        created_at=dashboard.created_at,
                    )
                    session.add(model)

                return True

        except Exception as e:
            logger.error(f"Error saving dashboard {dashboard.dashboard_id}: {e}")
            return False

    def find_dashboard_by_id(self, dashboard_id: str) -> Optional[Dashboard]:
        """
        Find a dashboard by its ID with visualizations.

        Args:
            dashboard_id: The unique identifier of the dashboard

        Returns:
            Dashboard entity if found, None otherwise
        """
        try:
            with self._db.session_scope() as session:
                model = (
                    session.query(DashboardModel)
                    .filter(DashboardModel.dashboard_id == dashboard_id)
                    .first()
                )

                if model:
                    return self._dashboard_model_to_entity(session, model)
                return None

        except Exception as e:
            logger.error(f"Error finding dashboard by ID {dashboard_id}: {e}")
            return None

    def find_dashboards_by_user(self, user_id: str) -> List[Dashboard]:
        """
        Find all dashboards for a user.

        Args:
            user_id: The user ID to search for

        Returns:
            List of Dashboard entities
        """
        try:
            with self._db.session_scope() as session:
                models = (
                    session.query(DashboardModel)
                    .filter(DashboardModel.user_id == user_id)
                    .order_by(DashboardModel.created_at.desc())
                    .all()
                )

                return [self._dashboard_model_to_entity(session, m) for m in models]

        except Exception as e:
            logger.error(f"Error finding dashboards for user {user_id}: {e}")
            return []

    def delete_dashboard(self, dashboard_id: str) -> bool:
        """
        Delete a dashboard from the database.
        Cascade deletes visualizations.

        Args:
            dashboard_id: The unique identifier of the dashboard to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            with self._db.session_scope() as session:
                model = (
                    session.query(DashboardModel)
                    .filter(DashboardModel.dashboard_id == dashboard_id)
                    .first()
                )

                if model:
                    session.delete(model)
                    return True
                return False

        except Exception as e:
            logger.error(f"Error deleting dashboard {dashboard_id}: {e}")
            return False

    def update_dashboard_title(self, dashboard_id: str, title: str) -> bool:
        """
        Update the title of a dashboard.

        Args:
            dashboard_id: The dashboard ID
            title: New title

        Returns:
            True if successful, False otherwise
        """
        try:
            with self._db.session_scope() as session:
                model = (
                    session.query(DashboardModel)
                    .filter(DashboardModel.dashboard_id == dashboard_id)
                    .first()
                )

                if model:
                    model.title = title
                    return True
                return False

        except Exception as e:
            logger.error(f"Error updating dashboard title {dashboard_id}: {e}")
            return False

    # Visualization operations
    def save_visualization(self, viz: Visualization) -> bool:
        """
        Save a visualization to the database.

        Args:
            viz: The visualization entity to save

        Returns:
            True if successful, False otherwise
        """
        try:
            with self._db.session_scope() as session:
                # Check if visualization exists
                existing = (
                    session.query(VisualizationModel)
                    .filter(VisualizationModel.viz_id == viz.viz_id)
                    .first()
                )

                if existing:
                    # Update existing visualization
                    existing.viz_type = viz.viz_type
                    existing.config = viz.config.to_dict() if viz.config else {}
                else:
                    # Create new visualization
                    model = VisualizationModel(
                        viz_id=viz.viz_id,
                        dashboard_id=viz.dashboard_id,
                        sheet_id=viz.sheet_id,
                        viz_type=viz.viz_type,
                        config=viz.config.to_dict() if viz.config else {},
                        created_at=viz.created_at,
                    )
                    session.add(model)

                return True

        except Exception as e:
            logger.error(f"Error saving visualization {viz.viz_id}: {e}")
            return False

    def find_visualization_by_id(self, viz_id: str) -> Optional[Visualization]:
        """
        Find a visualization by its ID.

        Args:
            viz_id: The unique identifier of the visualization

        Returns:
            Visualization entity if found, None otherwise
        """
        try:
            with self._db.session_scope() as session:
                model = (
                    session.query(VisualizationModel)
                    .filter(VisualizationModel.viz_id == viz_id)
                    .first()
                )

                if model:
                    return self._visualization_model_to_entity(model)
                return None

        except Exception as e:
            logger.error(f"Error finding visualization by ID {viz_id}: {e}")
            return None

    def find_visualizations_by_dashboard(
        self, dashboard_id: str
    ) -> List[Visualization]:
        """
        Find all visualizations for a dashboard.

        Args:
            dashboard_id: The dashboard ID to search for

        Returns:
            List of Visualization entities
        """
        try:
            with self._db.session_scope() as session:
                models = (
                    session.query(VisualizationModel)
                    .filter(VisualizationModel.dashboard_id == dashboard_id)
                    .order_by(VisualizationModel.created_at.asc())
                    .all()
                )

                return [self._visualization_model_to_entity(m) for m in models]

        except Exception as e:
            logger.error(
                f"Error finding visualizations for dashboard {dashboard_id}: {e}"
            )
            return []

    def delete_visualization(self, viz_id: str) -> bool:
        """
        Delete a visualization from the database.

        Args:
            viz_id: The unique identifier of the visualization to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            with self._db.session_scope() as session:
                model = (
                    session.query(VisualizationModel)
                    .filter(VisualizationModel.viz_id == viz_id)
                    .first()
                )

                if model:
                    session.delete(model)
                    return True
                return False

        except Exception as e:
            logger.error(f"Error deleting visualization {viz_id}: {e}")
            return False

    # Model to Entity converters
    def _dashboard_model_to_entity(self, session, model: DashboardModel) -> Dashboard:
        """Convert a DashboardModel to a Dashboard entity with visualizations."""
        # Load visualizations
        visualizations = (
            session.query(VisualizationModel)
            .filter(VisualizationModel.dashboard_id == model.dashboard_id)
            .all()
        )

        return Dashboard(
            dashboard_id=str(model.dashboard_id),
            user_id=str(model.user_id),
            title=model.title,
            created_at=model.created_at,
            visualizations=[
                self._visualization_model_to_entity(v) for v in visualizations
            ],
        )

    def _visualization_model_to_entity(
        self, model: VisualizationModel
    ) -> Visualization:
        """Convert a VisualizationModel to a Visualization entity."""
        return Visualization(
            viz_id=str(model.viz_id),
            dashboard_id=str(model.dashboard_id),
            sheet_id=str(model.sheet_id),
            viz_type=model.viz_type,
            config=VisualizationConfig.from_dict(model.config or {}),
            created_at=model.created_at,
        )
