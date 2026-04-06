"""
Domain Entities - Core business entities representing the main concepts.
These are pure Python classes with no external dependencies for business logic.
All entities follow SOLID principles with single responsibility and proper encapsulation.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime, date, time
from enum import Enum
import uuid
import json


def _make_json_serializable(value: Any) -> Any:
    """Convert a value to a JSON-serializable format."""
    if value is None:
        return None
    if isinstance(value, (date, time)):
        return value.isoformat()
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: _make_json_serializable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_make_json_serializable(v) for v in value]
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


class VisualizationType(Enum):
    """Enumeration of supported visualization types."""

    BAR_CHART = "bar_chart"
    LINE_CHART = "line_chart"
    PIE_CHART = "pie_chart"
    AREA_CHART = "area_chart"
    SCATTER_PLOT = "scatter_plot"
    HISTOGRAM = "histogram"
    BOX_PLOT = "box_plot"
    HEATMAP = "heatmap"
    TABLE = "table"
    METRIC_CARD = "metric_card"


class ColumnType(Enum):
    """Enumeration of column data types for schema detection."""

    NUMERIC = "numeric"
    CATEGORICAL = "categorical"
    DATETIME = "datetime"
    TEXT = "text"
    BOOLEAN = "boolean"
    UNKNOWN = "unknown"


class ExportFormat(Enum):
    """Enumeration of supported export formats."""

    PDF = "pdf"
    LATEX = "latex"
    HTML = "html"


@dataclass
class Column:
    """
    Represents a column in the data schema.
    Contains metadata about the column type and statistics.
    """

    name: str
    data_type: ColumnType
    sample_values: List[Any] = field(default_factory=list)
    null_count: int = 0
    unique_count: int = 0
    statistics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize column to dictionary."""
        return {
            "name": self.name,
            "data_type": self.data_type.value,
            "sample_values": _make_json_serializable(self.sample_values[:10]),
            "null_count": self.null_count,
            "unique_count": self.unique_count,
            "statistics": _make_json_serializable(self.statistics),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Column":
        """Deserialize column from dictionary."""
        return cls(
            name=data["name"],
            data_type=ColumnType(data["data_type"]),
            sample_values=data.get("sample_values", []),
            null_count=data.get("null_count", 0),
            unique_count=data.get("unique_count", 0),
            statistics=data.get("statistics", {}),
        )


@dataclass
class DataSchema:
    """
    Represents the schema of uploaded data.
    Contains column definitions and metadata about the dataset.
    """

    columns: List[Column]
    row_count: int = 0
    file_name: str = ""
    file_size: int = 0
    created_at: datetime = field(default_factory=datetime.now)

    def get_column_names(self) -> List[str]:
        """Get list of all column names."""
        return [col.name for col in self.columns]

    def get_numeric_columns(self) -> List[str]:
        """Get list of numeric column names."""
        return [col.name for col in self.columns if col.data_type == ColumnType.NUMERIC]

    def get_categorical_columns(self) -> List[str]:
        """Get list of categorical column names."""
        return [
            col.name for col in self.columns if col.data_type == ColumnType.CATEGORICAL
        ]

    def get_datetime_columns(self) -> List[str]:
        """Get list of datetime column names."""
        return [
            col.name for col in self.columns if col.data_type == ColumnType.DATETIME
        ]

    def get_column(self, name: str) -> Optional[Column]:
        """Get a column by name."""
        for col in self.columns:
            if col.name == name:
                return col
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize schema to dictionary."""
        return {
            "columns": [col.to_dict() for col in self.columns],
            "row_count": self.row_count,
            "file_name": self.file_name,
            "file_size": self.file_size,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DataSchema":
        """Deserialize schema from dictionary."""
        return cls(
            columns=[Column.from_dict(c) for c in data.get("columns", [])],
            row_count=data.get("row_count", 0),
            file_name=data.get("file_name", ""),
            file_size=data.get("file_size", 0),
            created_at=datetime.fromisoformat(data["created_at"])
            if data.get("created_at")
            else datetime.now(),
        )


@dataclass
class VisualizationConfig:
    """
    Configuration for a visualization component.
    Contains all settings needed to render a chart or table.
    """

    visualization_type: VisualizationType
    title: str = ""
    x_column: Optional[str] = None
    y_column: Optional[str] = None
    color_column: Optional[str] = None
    size_column: Optional[str] = None
    aggregation: str = "sum"  # sum, mean, count, min, max
    show_legend: bool = True
    show_grid: bool = True
    color_scheme: str = "default"
    custom_options: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize config to dictionary."""
        return {
            "visualization_type": self.visualization_type.value,
            "title": self.title,
            "x_column": self.x_column,
            "y_column": self.y_column,
            "color_column": self.color_column,
            "size_column": self.size_column,
            "aggregation": self.aggregation,
            "show_legend": self.show_legend,
            "show_grid": self.show_grid,
            "color_scheme": self.color_scheme,
            "custom_options": self.custom_options,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VisualizationConfig":
        """Deserialize config from dictionary."""
        return cls(
            visualization_type=VisualizationType(data["visualization_type"]),
            title=data.get("title", ""),
            x_column=data.get("x_column"),
            y_column=data.get("y_column"),
            color_column=data.get("color_column"),
            size_column=data.get("size_column"),
            aggregation=data.get("aggregation", "sum"),
            show_legend=data.get("show_legend", True),
            show_grid=data.get("show_grid", True),
            color_scheme=data.get("color_scheme", "default"),
            custom_options=data.get("custom_options", {}),
        )


@dataclass
class Visualization:
    """
    Represents a visualization component on a slide.
    Contains the configuration, position, size, and any comments.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    config: Optional[VisualizationConfig] = None
    position: Dict[str, float] = field(default_factory=lambda: {"x": 0, "y": 0})
    size: Dict[str, float] = field(
        default_factory=lambda: {"width": 400, "height": 300}
    )
    comment: str = ""
    data_snapshot: Optional[Dict[str, Any]] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize visualization to dictionary."""
        return {
            "id": self.id,
            "config": self.config.to_dict() if self.config else None,
            "position": self.position,
            "size": self.size,
            "comment": self.comment,
            "data_snapshot": self.data_snapshot,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Visualization":
        """Deserialize visualization from dictionary."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            config=VisualizationConfig.from_dict(data["config"])
            if data.get("config")
            else None,
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


@dataclass
class Slide:
    """
    Represents a slide in an analysis dashboard.
    Contains a collection of visualizations with layout information.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = "Untitled Slide"
    visualizations: List[Visualization] = field(default_factory=list)
    layout: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def add_visualization(self, viz: Visualization) -> None:
        """Add a visualization to the slide."""
        self.visualizations.append(viz)
        self.updated_at = datetime.now()

    def remove_visualization(self, viz_id: str) -> bool:
        """Remove a visualization from the slide."""
        for i, viz in enumerate(self.visualizations):
            if viz.id == viz_id:
                self.visualizations.pop(i)
                self.updated_at = datetime.now()
                return True
        return False

    def get_visualization(self, viz_id: str) -> Optional[Visualization]:
        """Get a visualization by ID."""
        for viz in self.visualizations:
            if viz.id == viz_id:
                return viz
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize slide to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "visualizations": [viz.to_dict() for viz in self.visualizations],
            "layout": self.layout,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Slide":
        """Deserialize slide from dictionary."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            title=data.get("title", "Untitled Slide"),
            visualizations=[
                Visualization.from_dict(v) for v in data.get("visualizations", [])
            ],
            layout=data.get("layout", {}),
            created_at=datetime.fromisoformat(data["created_at"])
            if data.get("created_at")
            else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"])
            if data.get("updated_at")
            else datetime.now(),
        )


@dataclass
class Analysis:
    """
    Represents a complete analysis project.
    Contains slides, data schema, and analysis settings.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    name: str = "New Analysis"
    slides: List[Slide] = field(default_factory=list)
    data_schema: Optional[DataSchema] = None
    file_path: str = ""
    settings: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def add_slide(self, slide: Optional[Slide] = None) -> Slide:
        """Add a slide to the analysis."""
        if slide is None:
            slide = Slide(title=f"Slide {len(self.slides) + 1}")
        self.slides.append(slide)
        self.updated_at = datetime.now()
        return slide

    def remove_slide(self, slide_id: str) -> bool:
        """Remove a slide from the analysis."""
        for i, slide in enumerate(self.slides):
            if slide.id == slide_id:
                self.slides.pop(i)
                self.updated_at = datetime.now()
                return True
        return False

    def get_slide(self, slide_id: str) -> Optional[Slide]:
        """Get a slide by ID."""
        for slide in self.slides:
            if slide.id == slide_id:
                return slide
        return None

    def reorder_slides(self, new_order: List[str]) -> None:
        """Reorder slides based on a list of slide IDs."""
        reordered = []
        for slide_id in new_order:
            slide = self.get_slide(slide_id)
            if slide:
                reordered.append(slide)
        self.slides = reordered
        self.updated_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize analysis to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "slides": [slide.to_dict() for slide in self.slides],
            "data_schema": self.data_schema.to_dict() if self.data_schema else None,
            "file_path": self.file_path,
            "settings": self.settings,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Analysis":
        """Deserialize analysis from dictionary."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            user_id=data.get("user_id"),
            name=data.get("name", "New Analysis"),
            slides=[Slide.from_dict(s) for s in data.get("slides", [])],
            data_schema=DataSchema.from_dict(data["data_schema"])
            if data.get("data_schema")
            else None,
            file_path=data.get("file_path", ""),
            settings=data.get("settings", {}),
            created_at=datetime.fromisoformat(data["created_at"])
            if data.get("created_at")
            else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"])
            if data.get("updated_at")
            else datetime.now(),
        )


@dataclass
class User:
    """
    Represents a user of the application.
    Contains authentication and profile information.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    username: str = ""
    email: str = ""
    password_hash: str = ""
    full_name: str = ""
    is_active: bool = True
    is_admin: bool = False
    settings: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    last_login: Optional[datetime] = None

    def update_last_login(self) -> None:
        """Update the last login timestamp."""
        self.last_login = datetime.now()

    def update_settings(self, new_settings: Dict[str, Any]) -> None:
        """Update user settings."""
        self.settings.update(new_settings)
        self.updated_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize user to dictionary."""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "password_hash": self.password_hash,
            "full_name": self.full_name,
            "is_active": self.is_active,
            "is_admin": self.is_admin,
            "settings": self.settings,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "User":
        """Deserialize user from dictionary."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            username=data.get("username", ""),
            email=data.get("email", ""),
            password_hash=data.get("password_hash", ""),
            full_name=data.get("full_name", ""),
            is_active=data.get("is_active", True),
            is_admin=data.get("is_admin", False),
            settings=data.get("settings", {}),
            created_at=datetime.fromisoformat(data["created_at"])
            if data.get("created_at")
            else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"])
            if data.get("updated_at")
            else datetime.now(),
            last_login=datetime.fromisoformat(data["last_login"])
            if data.get("last_login")
            else None,
        )


@dataclass
class UserSession:
    """
    Represents a user session.
    Contains session state for authenticated users.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    token_hash: str = ""
    session_data: Dict[str, Any] = field(default_factory=dict)
    settings: Dict[str, Any] = field(default_factory=dict)
    current_analysis_id: Optional[str] = None
    current_slide_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    last_activity: datetime = field(default_factory=datetime.now)

    def is_expired(self) -> bool:
        """Check if session has expired."""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at

    def update_activity(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize session to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "token_hash": self.token_hash,
            "session_data": self.session_data,
            "settings": self.settings,
            "current_analysis_id": self.current_analysis_id,
            "current_slide_id": self.current_slide_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "last_activity": self.last_activity.isoformat()
            if self.last_activity
            else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserSession":
        """Deserialize session from dictionary."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            user_id=data.get("user_id", ""),
            token_hash=data.get("token_hash", ""),
            session_data=data.get("session_data", {}),
            settings=data.get("settings", {}),
            current_analysis_id=data.get("current_analysis_id"),
            current_slide_id=data.get("current_slide_id"),
            created_at=datetime.fromisoformat(data["created_at"])
            if data.get("created_at")
            else datetime.now(),
            expires_at=datetime.fromisoformat(data["expires_at"])
            if data.get("expires_at")
            else None,
            last_activity=datetime.fromisoformat(data["last_activity"])
            if data.get("last_activity")
            else datetime.now(),
        )
