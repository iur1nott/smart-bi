"""
Domain Entities - Core business entities representing the main concepts.
These are pure Python classes with no external dependencies for business logic.
All entities follow SOLID principles with single responsibility and proper encapsulation.
Matches the database schema defined in smartxl_db_creator.sql
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

    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    AREA = "area"
    SCATTER = "scatter"
    HISTOGRAM = "histogram"
    BOX = "box"
    HEATMAP = "heatmap"
    TABLE = "table"
    METRIC_CARD = "metric_card"


class ColumnDataType(Enum):
    """Enumeration of column data types for schema detection."""

    INT64 = "Int64"
    FLOAT64 = "Float64"
    STRING = "String"
    BOOLEAN = "Boolean"
    DATE = "Date"
    DATETIME = "Datetime"
    TIME = "Time"


class ExportFormat(Enum):
    """Enumeration of supported export formats."""

    PDF = "pdf"
    LATEX = "latex"
    HTML = "html"


@dataclass
class User:
    """
    Represents a user of the application.
    Contains authentication and profile information.
    """

    user_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    username: str = ""
    email: str = ""
    password_hash: str = ""
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize user to dictionary."""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email,
            "password_hash": self.password_hash,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "User":
        """Deserialize user from dictionary."""
        return cls(
            user_id=data.get("user_id", str(uuid.uuid4())),
            username=data.get("username", ""),
            email=data.get("email", ""),
            password_hash=data.get("password_hash", ""),
            created_at=datetime.fromisoformat(data["created_at"])
            if data.get("created_at")
            else datetime.now(),
        )


@dataclass
class File:
    """
    Represents an uploaded file stored in S3.
    Contains file metadata and storage path.
    """

    file_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    file_name: str = ""
    storage_path: str = ""  # S3 path
    file_size_kb: int = 0
    uploaded_at: datetime = field(default_factory=datetime.now)

    # Transient data (not persisted)
    sheets: List["FileSheet"] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize file to dictionary."""
        return {
            "file_id": self.file_id,
            "user_id": self.user_id,
            "file_name": self.file_name,
            "storage_path": self.storage_path,
            "file_size_kb": self.file_size_kb,
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None,
            "sheets": [s.to_dict() for s in self.sheets] if self.sheets else [],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "File":
        """Deserialize file from dictionary."""
        return cls(
            file_id=data.get("file_id", str(uuid.uuid4())),
            user_id=data.get("user_id", ""),
            file_name=data.get("file_name", ""),
            storage_path=data.get("storage_path", ""),
            file_size_kb=data.get("file_size_kb", 0),
            uploaded_at=datetime.fromisoformat(data["uploaded_at"])
            if data.get("uploaded_at")
            else datetime.now(),
            sheets=[FileSheet.from_dict(s) for s in data.get("sheets", [])],
        )


@dataclass
class SheetColumn:
    """
    Represents a column in a sheet.
    Contains column metadata and data type.
    """

    column_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sheet_id: str = ""
    column_name: str = ""
    data_type: str = "String"  # Int64, Float64, String, Boolean, Date, Datetime, Time

    def to_dict(self) -> Dict[str, Any]:
        """Serialize column to dictionary."""
        return {
            "column_id": self.column_id,
            "sheet_id": self.sheet_id,
            "column_name": self.column_name,
            "data_type": self.data_type,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SheetColumn":
        """Deserialize column from dictionary."""
        return cls(
            column_id=data.get("column_id", str(uuid.uuid4())),
            sheet_id=data.get("sheet_id", ""),
            column_name=data.get("column_name", ""),
            data_type=data.get("data_type", "String"),
        )


@dataclass
class FileSheet:
    """
    Represents a sheet within an Excel file.
    Contains sheet metadata and columns.
    """

    sheet_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    file_id: str = ""
    sheet_name: str = ""

    # Transient data (not persisted)
    columns: List[SheetColumn] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize sheet to dictionary."""
        return {
            "sheet_id": self.sheet_id,
            "file_id": self.file_id,
            "sheet_name": self.sheet_name,
            "columns": [c.to_dict() for c in self.columns] if self.columns else [],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FileSheet":
        """Deserialize sheet from dictionary."""
        return cls(
            sheet_id=data.get("sheet_id", str(uuid.uuid4())),
            file_id=data.get("file_id", ""),
            sheet_name=data.get("sheet_name", ""),
            columns=[SheetColumn.from_dict(c) for c in data.get("columns", [])],
        )

    def get_column_names(self) -> List[str]:
        """Get list of all column names."""
        return [col.column_name for col in self.columns]

    def get_column(self, name: str) -> Optional[SheetColumn]:
        """Get a column by name."""
        for col in self.columns:
            if col.column_name == name:
                return col
        return None


@dataclass
class VisualizationConfig:
    """
    Configuration for a visualization component.
    Stored as JSONB in the database.
    Contains all settings needed to render a chart or table.
    """

    title: str = ""
    x_column: Optional[str] = None
    y_column: Optional[str] = None
    # Multi-Y support: when non-empty overrides y_column for bar/column/line charts.
    y_columns: List[str] = field(default_factory=list)
    color_column: Optional[str] = None
    size_column: Optional[str] = None
    aggregation: str = "sum"  # sum, mean, count, min, max
    show_legend: bool = True
    show_grid: bool = True
    show_values: bool = False  # show data labels on charts
    color_scheme: str = "default"
    position: Dict[str, float] = field(default_factory=lambda: {"x": 0, "y": 0})
    size: Dict[str, float] = field(
        default_factory=lambda: {"width": 400, "height": 300}
    )
    custom_options: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize config to dictionary."""
        return {
            "title": self.title,
            "x_column": self.x_column,
            "y_column": self.y_column,
            "y_columns": self.y_columns,
            "color_column": self.color_column,
            "size_column": self.size_column,
            "aggregation": self.aggregation,
            "show_legend": self.show_legend,
            "show_grid": self.show_grid,
            "show_values": self.show_values,
            "color_scheme": self.color_scheme,
            "position": self.position,
            "size": self.size,
            "custom_options": self.custom_options,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VisualizationConfig":
        """Deserialize config from dictionary."""
        if data is None:
            return cls()
        return cls(
            title=data.get("title", ""),
            x_column=data.get("x_column"),
            y_column=data.get("y_column"),
            y_columns=data.get("y_columns", []),
            color_column=data.get("color_column"),
            size_column=data.get("size_column"),
            aggregation=data.get("aggregation", "sum"),
            show_legend=data.get("show_legend", True),
            show_grid=data.get("show_grid", True),
            show_values=data.get("show_values", False),
            color_scheme=data.get("color_scheme", "default"),
            position=data.get("position", {"x": 0, "y": 0}),
            size=data.get("size", {"width": 400, "height": 300}),
            custom_options=data.get("custom_options", {}),
        )


@dataclass
class Visualization:
    """
    Represents a visualization in a dashboard.
    Contains the type, configuration, and reference to source sheet.
    """

    viz_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    dashboard_id: str = ""
    sheet_id: str = ""
    viz_type: str = "bar"  # bar, line, pie, scatter, etc.
    config: VisualizationConfig = field(default_factory=VisualizationConfig)
    created_at: datetime = field(default_factory=datetime.now)

    # Transient data (not persisted)
    comment: str = ""  # Optional comment for export

    def to_dict(self) -> Dict[str, Any]:
        """Serialize visualization to dictionary."""
        return {
            "viz_id": self.viz_id,
            "dashboard_id": self.dashboard_id,
            "sheet_id": self.sheet_id,
            "viz_type": self.viz_type,
            "config": self.config.to_dict() if self.config else {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Visualization":
        """Deserialize visualization from dictionary."""
        return cls(
            viz_id=data.get("viz_id", str(uuid.uuid4())),
            dashboard_id=data.get("dashboard_id", ""),
            sheet_id=data.get("sheet_id", ""),
            viz_type=data.get("viz_type", "bar"),
            config=VisualizationConfig.from_dict(data.get("config", {})),
            created_at=datetime.fromisoformat(data["created_at"])
            if data.get("created_at")
            else datetime.now(),
        )


@dataclass
class Dashboard:
    """
    Represents a dashboard containing visualizations.
    A dashboard is the main analysis unit for users.
    """

    dashboard_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    title: str = "New Dashboard"
    created_at: datetime = field(default_factory=datetime.now)

    # Transient data (not persisted)
    visualizations: List[Visualization] = field(default_factory=list)
    file: Optional[File] = None  # Associated file for data

    def add_visualization(self, viz: Visualization) -> None:
        """Add a visualization to the dashboard."""
        self.visualizations.append(viz)

    def remove_visualization(self, viz_id: str) -> bool:
        """Remove a visualization from the dashboard."""
        for i, viz in enumerate(self.visualizations):
            if viz.viz_id == viz_id:
                self.visualizations.pop(i)
                return True
        return False

    def get_visualization(self, viz_id: str) -> Optional[Visualization]:
        """Get a visualization by ID."""
        for viz in self.visualizations:
            if viz.viz_id == viz_id:
                return viz
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize dashboard to dictionary."""
        return {
            "dashboard_id": self.dashboard_id,
            "user_id": self.user_id,
            "title": self.title,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "visualizations": [v.to_dict() for v in self.visualizations],
            "file": self.file.to_dict() if self.file else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Dashboard":
        """Deserialize dashboard from dictionary."""
        return cls(
            dashboard_id=data.get("dashboard_id", str(uuid.uuid4())),
            user_id=data.get("user_id", ""),
            title=data.get("title", "New Dashboard"),
            created_at=datetime.fromisoformat(data["created_at"])
            if data.get("created_at")
            else datetime.now(),
            visualizations=[
                Visualization.from_dict(v) for v in data.get("visualizations", [])
            ],
            file=File.from_dict(data["file"]) if data.get("file") else None,
        )


# Type alias for backward compatibility
Analysis = Dashboard
Slide = Visualization
