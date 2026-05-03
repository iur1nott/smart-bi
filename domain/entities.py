"""
Core domain entities following SOLID principles.
Entities represent business objects with unique identity.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, List, Any
from enum import Enum
import uuid
import json
import polars as pl

class ColumnType(Enum):
    """Enumeration of supported column data types."""

    NUMERIC = "numeric"
    CATEGORICAL = "categorical"
    DATETIME = "datetime"
    TEXT = "text"
    BOOLEAN = "boolean"
    UNKNOWN = "unknown"


class VisualizationType(Enum):
    """Enumeration of supported visualization types."""

    LINE_CHART = "line_chart"
    BAR_CHART = "bar_chart"
    PIE_CHART = "pie_chart"
    SCATTER_PLOT = "scatter_plot"
    HISTOGRAM = "histogram"
    AREA_CHART = "area_chart"
    TABLE = "table"
    METRIC_CARD = "metric_card"
    COLUMN_CHART = "column_chart"
    HEATMAP = "heatmap"
    BOX_PLOT = "box_plot"
    MEASURES = "measures"


class ExportFormat(Enum):
    """Enumeration of supported export formats."""

    PDF = "pdf"
    LATEX = "latex"
    HTML = "html"


@dataclass
class Column:
    """Represents a column in the uploaded dataset."""

    name: str
    data_type: ColumnType
    sample_values: List[Any] = field(default_factory=list)
    null_count: int = 0
    unique_count: int = 0
    statistics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert column to dictionary representation."""
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
        """Create column from dictionary representation."""
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
    """Represents the schema of uploaded data."""

    columns: List[Column] = field(default_factory=list)
    row_count: int = 0
    file_name: str = ""
    file_size: int = 0

    @classmethod
    def from_polars(cls, df: pl.DataFrame) -> "DataSchema":
        """
        Cria um DataSchema automaticamente a partir de um DataFrame Polars.
        Mapeia os tipos do Polars para o ColumnType do sistema.
        """
        new_columns = []
        for col_name in df.columns:
            dtype = df.schema[col_name]
            
            # Lógica de mapeamento de tipos
            if dtype in [pl.Float64, pl.Int64, pl.Int32, pl.Decimal]:
                col_type = ColumnType.NUMERIC
            elif dtype in [pl.Date, pl.Datetime]:
                col_type = ColumnType.DATETIME
            else:
                col_type = ColumnType.CATEGORICAL
            
            # Criando o objeto Column (ajuste o nome do atributo se for 'type' ou 'data_type')
            new_columns.append(Column(name=col_name, data_type=col_type))
            
        return cls(
            columns=new_columns,
            row_count=len(df)
        )

    def get_column_names(self) -> List[str]:
        """Get list of all column names."""
        return [col.name for col in self.columns]

    def get_columns_by_type(self, column_type: ColumnType) -> List[Column]:
        """Filter columns by type."""
        return [col for col in self.columns if col.data_type == column_type]

    def get_numeric_columns(self) -> List[str]:
        """Get names of numeric columns."""
        return [col.name for col in self.columns if col.data_type == ColumnType.NUMERIC]

    def get_categorical_columns(self) -> List[str]:
        """Get names of categorical columns."""
        return [
            col.name for col in self.columns if col.data_type == ColumnType.CATEGORICAL
        ]

    def to_dict(self) -> Dict[str, Any]:
        """Convert schema to dictionary representation."""
        return {
            "columns": [col.to_dict() for col in self.columns],
            "row_count": self.row_count,
            "file_name": self.file_name,
            "file_size": self.file_size,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DataSchema":
        """Create schema from dictionary representation."""
        return cls(
            columns=[Column.from_dict(col) for col in data.get("columns", [])],
            row_count=data.get("row_count", 0),
            file_name=data.get("file_name", ""),
            file_size=data.get("file_size", 0),
        )


from typing import List, Union, Optional, Dict, Any

@dataclass
class VisualizationConfig:
    """Configuration for a visualization component."""

    visualization_type: VisualizationType
    title: str = ""
    x_column: Optional[str] = None
    y_column: Optional[str] = None
    y_columns: List[str] = field(default_factory=list)
    color_column: Optional[str] = None
    size_column: Optional[str] = None
    aggregation: str = "sum"
    show_legend: bool = True
    show_grid: bool = True
    show_values: bool = False
    color_scheme: str = "default"
    custom_options: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary representation."""
        return {
            "visualization_type": self.visualization_type.value,
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
            "custom_options": self.custom_options,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VisualizationConfig":
        """Create config from dictionary representation."""
        return cls(
            visualization_type=VisualizationType(data["visualization_type"]),
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
            custom_options=data.get("custom_options", {}),
        )


@dataclass
class Visualization:
    """Represents a visualization component on a slide."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    config: Optional[VisualizationConfig] = None
    position: Dict[str, float] = field(default_factory=lambda: {"x": 0, "y": 0})
    size: Dict[str, float] = field(
        default_factory=lambda: {"width": 400, "height": 300}
    )
    comment: str = ""
    data_snapshot: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert visualization to dictionary representation."""
        return {
            "id": self.id,
            "config": self.config.to_dict() if self.config else None,
            "position": self.position,
            "size": self.size,
            "comment": self.comment,
            "data_snapshot": self.data_snapshot,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Visualization":
        """Create visualization from dictionary representation."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            config=VisualizationConfig.from_dict(data["config"])
            if data.get("config")
            else None,
            position=data.get("position", {"x": 0, "y": 0}),
            size=data.get("size", {"width": 400, "height": 300}),
            comment=data.get("comment", ""),
            data_snapshot=data.get("data_snapshot"),
        )


@dataclass
class Slide:
    """Represents a single slide/document page."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = "Untitled Slide"
    visualizations: List[Visualization] = field(default_factory=list)
    layout: str = "single"  # single, two_column, three_column, grid
    background_color: str = "#FFFFFF"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def add_visualization(self, visualization: Visualization) -> None:
        """Add a visualization to the slide."""
        self.visualizations.append(visualization)
        self.updated_at = datetime.now()

    def remove_visualization(self, viz_id: str) -> bool:
        """Remove a visualization by ID."""
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
        """Convert slide to dictionary representation."""
        return {
            "id": self.id,
            "title": self.title,
            "visualizations": [viz.to_dict() for viz in self.visualizations],
            "layout": self.layout,
            "background_color": self.background_color,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Slide":
        """Create slide from dictionary representation."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            title=data.get("title", "Untitled Slide"),
            visualizations=[
                Visualization.from_dict(v) for v in data.get("visualizations", [])
            ],
            layout=data.get("layout", "single"),
            background_color=data.get("background_color", "#FFFFFF"),
            created_at=datetime.fromisoformat(data["created_at"])
            if "created_at" in data
            else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"])
            if "updated_at" in data
            else datetime.now(),
        )


@dataclass
class Analysis:
    """Represents a complete analysis session."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "New Analysis"
    data_schema: Optional[DataSchema] = None
    slides: List[Slide] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    file_path: Optional[str] = None
    measures: List[Dict[str, str]] = field(default_factory=list)

    def add_slide(self, slide: Optional[Slide] = None) -> Slide:
        """Add a new slide to the analysis."""
        if slide is None:
            slide = Slide(title=f"Slide {len(self.slides) + 1}")
        self.slides.append(slide)
        self.updated_at = datetime.now()
        return slide

    def remove_slide(self, slide_id: str) -> bool:
        """Remove a slide by ID."""
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
        """Reorder slides according to new order of IDs."""
        slide_map = {s.id: s for s in self.slides}
        self.slides = [slide_map[sid] for sid in new_order if sid in slide_map]
        self.updated_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert analysis to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "data_schema": self.data_schema.to_dict() if self.data_schema else None,
            "slides": [slide.to_dict() for slide in self.slides],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "file_path": self.file_path,
            "measures": self.measures,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Analysis":
        """Create analysis from dictionary representation."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", "New Analysis"),
            data_schema=DataSchema.from_dict(data["data_schema"])
            if data.get("data_schema")
            else None,
            slides=[Slide.from_dict(s) for s in data.get("slides", [])],
            created_at=datetime.fromisoformat(data["created_at"])
            if "created_at" in data
            else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"])
            if "updated_at" in data
            else datetime.now(),
            file_path=data.get("file_path"),
            measures=data.get("measures", []),
        )


@dataclass
class UserSession:
    """Represents a user's session state."""

    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    analyses: List[Analysis] = field(default_factory=list)
    current_analysis_id: Optional[str] = None
    current_slide_id: Optional[str] = None
    settings: Dict[str, Any] = field(
        default_factory=lambda: {
            "theme": "light",
            "default_chart_colors": [
                "#1f77b4",
                "#ff7f0e",
                "#2ca02c",
                "#d62728",
                "#9467bd",
            ],
            "export_format": "pdf",
            "auto_save": True,
            "grid_visible": True,
        }
    )

    def create_analysis(self, name: str = "New Analysis") -> Analysis:
        """Create a new analysis and set it as current."""
        analysis = Analysis(name=name)
        analysis.add_slide()  # Add initial slide
        self.analyses.append(analysis)
        self.current_analysis_id = analysis.id
        self.current_slide_id = analysis.slides[0].id if analysis.slides else None
        return analysis

    def get_current_analysis(self) -> Optional[Analysis]:
        """Get the currently active analysis."""
        for analysis in self.analyses:
            if analysis.id == self.current_analysis_id:
                return analysis
        return None

    def get_current_slide(self) -> Optional[Slide]:
        """Get the currently active slide."""
        analysis = self.get_current_analysis()
        if analysis:
            for slide in analysis.slides:
                if slide.id == self.current_slide_id:
                    return slide
        return None

    def delete_analysis(self, analysis_id: str) -> bool:
        """Delete an analysis by ID."""
        for i, analysis in enumerate(self.analyses):
            if analysis.id == analysis_id:
                self.analyses.pop(i)
                if self.current_analysis_id == analysis_id:
                    self.current_analysis_id = (
                        self.analyses[0].id if self.analyses else None
                    )
                    if self.current_analysis_id:
                        analysis = self.get_current_analysis()
                        self.current_slide_id = (
                            analysis.slides[0].id
                            if analysis and analysis.slides
                            else None
                        )
                    else:
                        self.current_slide_id = None
                return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary representation."""
        return {
            "session_id": self.session_id,
            "analyses": [a.to_dict() for a in self.analyses],
            "current_analysis_id": self.current_analysis_id,
            "current_slide_id": self.current_slide_id,
            "settings": self.settings,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserSession":
        """Create session from dictionary representation."""
        return cls(
            session_id=data.get("session_id", str(uuid.uuid4())),
            analyses=[Analysis.from_dict(a) for a in data.get("analyses", [])],
            current_analysis_id=data.get("current_analysis_id"),
            current_slide_id=data.get("current_slide_id"),
            settings=data.get(
                "settings",
                {
                    "theme": "light",
                    "default_chart_colors": [
                        "#1f77b4",
                        "#ff7f0e",
                        "#2ca02c",
                        "#d62728",
                        "#9467bd",
                    ],
                    "export_format": "pdf",
                    "auto_save": True,
                    "grid_visible": True,
                },
            ),
        )


# ---------------------------------------------------------------------------
# Auth / persistence entities (from backend/merge branch)
# ---------------------------------------------------------------------------

@dataclass
class User:
    user_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    username: str = ""
    email: str = ""
    password_hash: str = ""
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email,
            "password_hash": self.password_hash,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "User":
        return cls(
            user_id=data.get("user_id", str(uuid.uuid4())),
            username=data.get("username", ""),
            email=data.get("email", ""),
            password_hash=data.get("password_hash", ""),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
        )


@dataclass
class AuthSession:
    """Auth token session stored in DB (distinct from UserSession work state)."""
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    token: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    is_active: bool = True


@dataclass
class SheetColumn:
    column_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sheet_id: str = ""
    column_name: str = ""
    data_type: str = "String"

    def to_dict(self) -> Dict[str, Any]:
        return {"column_id": self.column_id, "sheet_id": self.sheet_id, "column_name": self.column_name, "data_type": self.data_type}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SheetColumn":
        return cls(column_id=data.get("column_id", str(uuid.uuid4())), sheet_id=data.get("sheet_id", ""), column_name=data.get("column_name", ""), data_type=data.get("data_type", "String"))


@dataclass
class FileSheet:
    sheet_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    file_id: str = ""
    sheet_name: str = ""
    columns: List[SheetColumn] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"sheet_id": self.sheet_id, "file_id": self.file_id, "sheet_name": self.sheet_name, "columns": [c.to_dict() for c in self.columns]}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FileSheet":
        return cls(sheet_id=data.get("sheet_id", str(uuid.uuid4())), file_id=data.get("file_id", ""), sheet_name=data.get("sheet_name", ""), columns=[SheetColumn.from_dict(c) for c in data.get("columns", [])])

    def get_column_names(self) -> List[str]:
        return [c.column_name for c in self.columns]

    def get_column(self, name: str) -> Optional[SheetColumn]:
        return next((c for c in self.columns if c.column_name == name), None)


@dataclass
class File:
    file_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    file_name: str = ""
    storage_path: str = ""
    file_size_kb: int = 0
    uploaded_at: datetime = field(default_factory=datetime.now)
    sheets: List[FileSheet] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"file_id": self.file_id, "user_id": self.user_id, "file_name": self.file_name, "storage_path": self.storage_path, "file_size_kb": self.file_size_kb, "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None, "sheets": [s.to_dict() for s in self.sheets]}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "File":
        return cls(file_id=data.get("file_id", str(uuid.uuid4())), user_id=data.get("user_id", ""), file_name=data.get("file_name", ""), storage_path=data.get("storage_path", ""), file_size_kb=data.get("file_size_kb", 0), uploaded_at=datetime.fromisoformat(data["uploaded_at"]) if data.get("uploaded_at") else datetime.now(), sheets=[FileSheet.from_dict(s) for s in data.get("sheets", [])])


@dataclass
class Dashboard:
    """Legacy persistence entity used by DashboardRepository."""
    dashboard_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    title: str = "New Dashboard"
    created_at: datetime = field(default_factory=datetime.now)
    visualizations: List[Any] = field(default_factory=list)
    file: Optional[Any] = None

    def to_dict(self) -> Dict[str, Any]:
        return {"dashboard_id": self.dashboard_id, "user_id": self.user_id, "title": self.title, "created_at": self.created_at.isoformat() if self.created_at else None}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Dashboard":
        return cls(dashboard_id=data.get("dashboard_id", str(uuid.uuid4())), user_id=data.get("user_id", ""), title=data.get("title", "New Dashboard"), created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now())
