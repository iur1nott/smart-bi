"""
Value Objects - Immutable value objects used across the domain.
These represent concepts identified by their attributes rather than identity.
Value objects are immutable and compared by value.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from enum import Enum


class ExportFormat(Enum):
    """Enumeration of supported export formats."""

    PDF = "pdf"
    LATEX = "latex"
    HTML = "html"


class PaperSize(Enum):
    """Enumeration of supported paper sizes."""

    A4 = "a4"
    LETTER = "letter"
    LEGAL = "legal"


class Orientation(Enum):
    """Enumeration of page orientations."""

    PORTRAIT = "portrait"
    LANDSCAPE = "landscape"


@dataclass(frozen=True)
class Credentials:
    """
    Immutable value object representing user credentials.
    Used for authentication requests.
    """

    username: str
    password: str

    def is_valid(self) -> bool:
        """Check if credentials have valid format."""
        return len(self.username) >= 3 and len(self.password) >= 6


@dataclass(frozen=True)
class FilterCondition:
    """
    Immutable value object representing a filter condition.
    Used for data filtering operations.
    """

    column_name: str
    operator: str
    value: Any

    def __post_init__(self) -> None:
        """Validate the filter condition."""
        valid_operators = [
            "eq",
            "ne",
            "gt",
            "lt",
            "gte",
            "lte",
            "contains",
            "starts_with",
            "ends_with",
            "in",
            "not_in",
            "is_null",
            "is_not_null",
        ]
        if self.operator not in valid_operators:
            raise ValueError(f"Invalid operator: {self.operator}")

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "column_name": self.column_name,
            "operator": self.operator,
            "value": self.value,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FilterCondition":
        """Deserialize from dictionary."""
        return cls(
            column_name=data["column_name"],
            operator=data["operator"],
            value=data["value"],
        )


@dataclass(frozen=True)
class AggregationConfig:
    """
    Immutable value object representing aggregation configuration.
    Used for data aggregation operations.
    """

    group_by_columns: tuple
    aggregation_column: str
    aggregation_function: str

    def __post_init__(self) -> None:
        """Validate the aggregation configuration."""
        valid_functions = [
            "sum",
            "mean",
            "median",
            "min",
            "max",
            "count",
            "std",
            "var",
            "first",
            "last",
        ]
        if self.aggregation_function not in valid_functions:
            raise ValueError(
                f"Invalid aggregation function: {self.aggregation_function}"
            )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "group_by_columns": list(self.group_by_columns),
            "aggregation_column": self.aggregation_column,
            "aggregation_function": self.aggregation_function,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AggregationConfig":
        """Deserialize from dictionary."""
        return cls(
            group_by_columns=tuple(data["group_by_columns"]),
            aggregation_column=data["aggregation_column"],
            aggregation_function=data["aggregation_function"],
        )


@dataclass
class ExportOptions:
    """
    Value object representing export configuration options.
    Contains all parameters needed for document export.
    """

    format: str = "pdf"
    paper_size: str = "a4"
    orientation: str = "portrait"
    margin_mm: int = 20
    font_size: int = 11
    include_comments: bool = True
    include_page_numbers: bool = True
    include_timestamp: bool = True
    header_text: str = ""
    footer_text: str = ""
    title_page: bool = False
    color_scheme: str = "default"
    custom_css: str = ""
    chart_dpi: int = 150
    max_rows_per_table: int = 100

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "format": self.format,
            "paper_size": self.paper_size,
            "orientation": self.orientation,
            "margin_mm": self.margin_mm,
            "font_size": self.font_size,
            "include_comments": self.include_comments,
            "include_page_numbers": self.include_page_numbers,
            "include_timestamp": self.include_timestamp,
            "header_text": self.header_text,
            "footer_text": self.footer_text,
            "title_page": self.title_page,
            "color_scheme": self.color_scheme,
            "custom_css": self.custom_css,
            "chart_dpi": self.chart_dpi,
            "max_rows_per_table": self.max_rows_per_table,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExportOptions":
        """Deserialize from dictionary."""
        return cls(
            format=data.get("format", "pdf"),
            paper_size=data.get("paper_size", "a4"),
            orientation=data.get("orientation", "portrait"),
            margin_mm=data.get("margin_mm", 20),
            font_size=data.get("font_size", 11),
            include_comments=data.get("include_comments", True),
            include_page_numbers=data.get("include_page_numbers", True),
            include_timestamp=data.get("include_timestamp", True),
            header_text=data.get("header_text", ""),
            footer_text=data.get("footer_text", ""),
            title_page=data.get("title_page", False),
            color_scheme=data.get("color_scheme", "default"),
            custom_css=data.get("custom_css", ""),
            chart_dpi=data.get("chart_dpi", 150),
            max_rows_per_table=data.get("max_rows_per_table", 100),
        )


@dataclass(frozen=True)
class ChartColors:
    """
    Immutable value object representing a color palette for charts.
    Provides consistent colors across visualizations.
    """

    primary: str = "#10B981"
    secondary: str = "#3B82F6"
    tertiary: str = "#F59E0B"
    quaternary: str = "#EF4444"
    quinary: str = "#8B5CF6"
    senary: str = "#EC4899"
    palette: tuple = field(
        default_factory=lambda: (
            "#10B981",
            "#3B82F6",
            "#F59E0B",
            "#EF4444",
            "#8B5CF6",
            "#EC4899",
            "#06B6D4",
            "#84CC16",
            "#F97316",
            "#6366F1",
            "#14B8A6",
            "#A855F7",
        )
    )

    def get_color(self, index: int) -> str:
        """Get a color from the palette by index."""
        return self.palette[index % len(self.palette)]

    def get_gradient(self, count: int) -> List[str]:
        """Get a gradient of colors for a given count."""
        return [self.get_color(i) for i in range(count)]


@dataclass(frozen=True)
class Position:
    """
    Immutable value object representing a 2D position.
    Used for element positioning on slides.
    """

    x: float
    y: float

    def to_dict(self) -> Dict[str, float]:
        """Serialize to dictionary."""
        return {"x": self.x, "y": self.y}

    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> "Position":
        """Deserialize from dictionary."""
        return cls(x=data["x"], y=data["y"])


@dataclass(frozen=True)
class Size:
    """
    Immutable value object representing dimensions.
    Used for element sizing on slides.
    """

    width: float
    height: float

    def to_dict(self) -> Dict[str, float]:
        """Serialize to dictionary."""
        return {"width": self.width, "height": self.height}

    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> "Size":
        """Deserialize from dictionary."""
        return cls(width=data["width"], height=data["height"])

    @property
    def aspect_ratio(self) -> float:
        """Calculate aspect ratio."""
        return self.width / self.height if self.height > 0 else 0


@dataclass(frozen=True)
class Pagination:
    """
    Immutable value object representing pagination state.
    Used for data table pagination.
    """

    page: int
    page_size: int
    total_items: int

    @property
    def total_pages(self) -> int:
        """Calculate total number of pages."""
        return (self.total_items + self.page_size - 1) // self.page_size

    @property
    def offset(self) -> int:
        """Calculate the offset for database queries."""
        return (self.page - 1) * self.page_size

    @property
    def has_next(self) -> bool:
        """Check if there is a next page."""
        return self.page < self.total_pages

    @property
    def has_previous(self) -> bool:
        """Check if there is a previous page."""
        return self.page > 1


@dataclass(frozen=True)
class SortOrder:
    """
    Immutable value object representing sort configuration.
    Used for data sorting operations.
    """

    column: str
    direction: str = "asc"

    def __post_init__(self) -> None:
        """Validate the sort direction."""
        if self.direction not in ("asc", "desc"):
            raise ValueError(f"Invalid sort direction: {self.direction}")

    def to_dict(self) -> Dict[str, str]:
        """Serialize to dictionary."""
        return {"column": self.column, "direction": self.direction}

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "SortOrder":
        """Deserialize from dictionary."""
        return cls(column=data["column"], direction=data.get("direction", "asc"))
