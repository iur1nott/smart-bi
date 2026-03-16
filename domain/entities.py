"""
Domain Entities - Core business entities representing the main concepts.
These are pure Python classes with no external dependencies for business logic.
All entities follow SOLID principles with single responsibility and proper encapsulation.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum
import uuid
import json


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
            "sample_values": self.sample_values[:10],
            "null_count": self.null_count,
            "unique_count": self.unique_count,
            "statistics": self.statistics,
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
    Configuration for a visualization.
    Contains all parameters needed to render a chart or table.
    """

    visualization_type: VisualizationType
    title: str = ""
    x_column: Optional[str] = None
    y_column: Optional[str] = None
    color_column: Optional[str] = None
    size_column: Optional[str] = None
    aggregation: str = "sum"
    sort_by: Optional[str] = None
    sort_order: str = "asc"
    limit: Optional[int] = None
    filters: List[Dict[str, Any]] = field(default_factory=list)
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
            "sort_by": self.sort_by,
            "sort_order": self.sort_order,
            "limit": self.limit,
            "filters": self.filters,
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
            sort_by=data.get("sort_by"),
            sort_order=data.get("sort_order", "asc"),
            limit=data.get("limit"),
            filters=data.get("filters", []),
            custom_options=data.get("custom_options", {}),
        )


@dataclass
class Visualization:
    """
    Represents a visualization on a slide.
    Contains configuration, position, size, and data snapshot.
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
            id=data["id"],
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
    Represents a slide/page in an analysis.
    Contains visualizations and layout information.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = "Untitled Slide"
    visualizations: List[Visualization] = field(default_factory=list)
    layout: str = "single"
    background_color: str = "#ffffff"
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
            "visualizations": [v.to_dict() for v in self.visualizations],
            "layout": self.layout,
            "background_color": self.background_color,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Slide":
        """Deserialize slide from dictionary."""
        return cls(
            id=data["id"],
            title=data.get("title", "Untitled Slide"),
            visualizations=[
                Visualization.from_dict(v) for v in data.get("visualizations", [])
            ],
            layout=data.get("layout", "single"),
            background_color=data.get("background_color", "#ffffff"),
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
    Represents a complete analysis with data, slides, and metadata.
    This is the aggregate root for the analysis domain.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "New Analysis"
    user_id: str = ""
    slides: List[Slide] = field(default_factory=list)
    data_schema: Optional[DataSchema] = None
    file_path: str = ""
    settings: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        """Ensure at least one slide exists."""
        if not self.slides:
            self.slides = [Slide(title="Slide 1")]

    def add_slide(self, slide: Optional[Slide] = None) -> Slide:
        """Add a new slide to the analysis."""
        new_slide = slide or Slide(title=f"Slide {len(self.slides) + 1}")
        self.slides.append(new_slide)
        self.updated_at = datetime.now()
        return new_slide

    def remove_slide(self, slide_id: str) -> bool:
        """Remove a slide from the analysis."""
        if len(self.slides) <= 1:
            return False
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

    def to_dict(self) -> Dict[str, Any]:
        """Serialize analysis to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "user_id": self.user_id,
            "slides": [s.to_dict() for s in self.slides],
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
            id=data["id"],
            name=data.get("name", "New Analysis"),
            user_id=data.get("user_id", ""),
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

    def update_settings(self, settings: Dict[str, Any]) -> None:
        """Update user settings."""
        self.settings.update(settings)
        self.updated_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize user to dictionary (excludes password hash)."""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
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
            id=data["id"],
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
    Represents a user session with current state.
    Tracks the current analysis and slide being edited.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    analyses: List[Analysis] = field(default_factory=list)
    current_analysis_id: Optional[str] = None
    current_slide_id: Optional[str] = None
    settings: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def create_analysis(self, name: str = "New Analysis") -> Analysis:
        """Create a new analysis and add it to the session."""
        analysis = Analysis(name=name, user_id=self.user_id)
        self.analyses.append(analysis)
        self.current_analysis_id = analysis.id
        if analysis.slides:
            self.current_slide_id = analysis.slides[0].id
        return analysis

    def get_current_analysis(self) -> Optional[Analysis]:
        """Get the currently active analysis."""
        if not self.current_analysis_id:
            return None
        for analysis in self.analyses:
            if analysis.id == self.current_analysis_id:
                return analysis
        return None

    def get_current_slide(self) -> Optional[Slide]:
        """Get the currently active slide."""
        analysis = self.get_current_analysis()
        if not analysis or not self.current_slide_id:
            if analysis and analysis.slides:
                return analysis.slides[0]
            return None
        return analysis.get_slide(self.current_slide_id)

    def delete_analysis(self, analysis_id: str) -> bool:
        """Remove an analysis from the session."""
        for i, analysis in enumerate(self.analyses):
            if analysis.id == analysis_id:
                self.analyses.pop(i)
                if self.current_analysis_id == analysis_id:
                    self.current_analysis_id = (
                        self.analyses[0].id if self.analyses else None
                    )
                    if self.current_analysis_id and self.analyses:
                        self.current_slide_id = (
                            self.analyses[0].slides[0].id
                            if self.analyses[0].slides
                            else None
                        )
                    else:
                        self.current_slide_id = None
                return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Serialize session to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "analyses": [a.to_dict() for a in self.analyses],
            "current_analysis_id": self.current_analysis_id,
            "current_slide_id": self.current_slide_id,
            "settings": self.settings,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserSession":
        """Deserialize session from dictionary."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            user_id=data.get("user_id", ""),
            analyses=[Analysis.from_dict(a) for a in data.get("analyses", [])],
            current_analysis_id=data.get("current_analysis_id"),
            current_slide_id=data.get("current_slide_id"),
            settings=data.get("settings", {}),
            created_at=datetime.fromisoformat(data["created_at"])
            if data.get("created_at")
            else datetime.now(),
        )
