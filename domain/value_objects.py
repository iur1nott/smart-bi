"""
Value Objects - Immutable objects that represent descriptive aspects of the domain.
Value objects have no identity and are defined by their attributes.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import re


@dataclass(frozen=True)
class FileMetadata:
    """Immutable value object representing file metadata."""

    file_name: str
    file_size: int
    file_extension: str
    upload_timestamp: datetime

    @property
    def size_mb(self) -> float:
        """Get file size in megabytes."""
        return self.file_size / (1024 * 1024)

    @property
    def is_valid_excel(self) -> bool:
        """Check if file is a valid Excel file."""
        return self.file_extension.lower() in [".xlsx", ".xls"]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "file_name": self.file_name,
            "file_size": self.file_size,
            "file_extension": self.file_extension,
            "upload_timestamp": self.upload_timestamp.isoformat(),
        }


@dataclass(frozen=True)
class ChartColors:
    """Immutable value object for chart color schemes."""

    primary: str
    secondary: str
    accent: str
    background: str
    text: str
    grid: str
    series: tuple = field(
        default_factory=lambda: (
            "#1f77b4",
            "#ff7f0e",
            "#2ca02c",
            "#d62728",
            "#9467bd",
            "#8c564b",
            "#e377c2",
            "#7f7f7f",
            "#bcbd22",
            "#17becf",
        )
    )

    PRESET_SCHEMES = {
        "default": {
            "primary": "#1f77b4",
            "secondary": "#ff7f0e",
            "accent": "#2ca02c",
            "background": "#FFFFFF",
            "text": "#2D3748",
            "grid": "#E2E8F0",
        },
        "dark": {
            "primary": "#4299E1",
            "secondary": "#F6AD55",
            "accent": "#68D391",
            "background": "#1A202C",
            "text": "#E2E8F0",
            "grid": "#2D3748",
        },
        "pastel": {
            "primary": "#A5B4FC",
            "secondary": "#FCA5A5",
            "accent": "#86EFAC",
            "background": "#FAFAFA",
            "text": "#374151",
            "grid": "#F3F4F6",
        },
        "corporate": {
            "primary": "#2563EB",
            "secondary": "#DC2626",
            "accent": "#059669",
            "background": "#FFFFFF",
            "text": "#111827",
            "grid": "#D1D5DB",
        },
    }

    @classmethod
    def from_scheme(cls, scheme_name: str) -> "ChartColors":
        """Create colors from a preset scheme."""
        if scheme_name not in cls.PRESET_SCHEMES:
            scheme_name = "default"
        scheme = cls.PRESET_SCHEMES[scheme_name]
        return cls(
            primary=scheme["primary"],
            secondary=scheme["secondary"],
            accent=scheme["accent"],
            background=scheme["background"],
            text=scheme["text"],
            grid=scheme["grid"],
        )


@dataclass(frozen=True)
class Position:
    """Immutable value object representing position coordinates."""

    x: float
    y: float

    def move(self, dx: float, dy: float) -> "Position":
        """Create a new position moved by the specified offset."""
        return Position(x=self.x + dx, y=self.y + dy)

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary representation."""
        return {"x": self.x, "y": self.y}


@dataclass(frozen=True)
class Size:
    """Immutable value object representing dimensions."""

    width: float
    height: float

    @property
    def aspect_ratio(self) -> float:
        """Calculate aspect ratio."""
        return self.width / self.height if self.height > 0 else 1.0

    def resize(self, scale: float) -> "Size":
        """Create a new size scaled by the factor."""
        return Size(width=self.width * scale, height=self.height * scale)

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary representation."""
        return {"width": self.width, "height": self.height}


@dataclass(frozen=True)
class LayoutConstraints:
    """Immutable value object for layout constraints."""

    min_width: float = 200
    max_width: float = 1200
    min_height: float = 150
    max_height: float = 800
    margin: float = 16
    padding: float = 8

    def is_valid_size(self, size: Size) -> bool:
        """Check if size is within constraints."""
        return (
            self.min_width <= size.width <= self.max_width
            and self.min_height <= size.height <= self.max_height
        )


@dataclass(frozen=True)
class FilterCondition:
    """Immutable value object representing a filter condition."""

    column_name: str
    operator: (
        str  # eq, ne, gt, lt, gte, lte, contains, starts_with, ends_with, in, not_in
    )
    value: Any

    VALID_OPERATORS = {
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
    }

    def __post_init__(self):
        """Validate the filter condition."""
        if self.operator not in self.VALID_OPERATORS:
            raise ValueError(f"Invalid operator: {self.operator}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "column_name": self.column_name,
            "operator": self.operator,
            "value": self.value,
        }


@dataclass(frozen=True)
class AggregationConfig:
    """Immutable value object for aggregation configuration."""

    group_by_columns: tuple
    aggregation_column: str
    aggregation_function: str  # sum, mean, median, min, max, count, std, var

    VALID_FUNCTIONS = {
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
    }

    def __post_init__(self):
        """Validate the aggregation config."""
        if self.aggregation_function not in self.VALID_FUNCTIONS:
            raise ValueError(
                f"Invalid aggregation function: {self.aggregation_function}"
            )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "group_by_columns": list(self.group_by_columns),
            "aggregation_column": self.aggregation_column,
            "aggregation_function": self.aggregation_function,
        }


@dataclass(frozen=True)
class ExportOptions:
    """Immutable value object for export configuration."""

    format: str  # pdf, latex, html
    include_comments: bool = True
    include_page_numbers: bool = True
    paper_size: str = "a4"  # a4, letter, legal
    orientation: str = "portrait"  # portrait, landscape
    margin_mm: float = 20.0
    font_size: int = 11
    header_text: str = ""
    footer_text: str = ""
    quality: str = "high"  # low, medium, high
    file_name: str = ""
    subtitle: str = ""

    VALID_FORMATS = {"pdf", "latex", "html"}
    VALID_PAPER_SIZES = {"a4", "letter", "legal"}
    VALID_ORIENTATIONS = {"portrait", "landscape"}
    VALID_QUALITIES = {"low", "medium", "high"}

    def __post_init__(self):
        """Validate the export options."""
        if self.format not in self.VALID_FORMATS:
            raise ValueError(f"Invalid format: {self.format}")
        if self.paper_size not in self.VALID_PAPER_SIZES:
            raise ValueError(f"Invalid paper size: {self.paper_size}")
        if self.orientation not in self.VALID_ORIENTATIONS:
            raise ValueError(f"Invalid orientation: {self.orientation}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "format": self.format,
            "include_comments": self.include_comments,
            "include_page_numbers": self.include_page_numbers,
            "paper_size": self.paper_size,
            "orientation": self.orientation,
            "margin_mm": self.margin_mm,
            "font_size": self.font_size,
            "header_text": self.header_text,
            "footer_text": self.footer_text,
            "quality": self.quality,
        }


# ---------------------------------------------------------------------------
# Auth value objects (from backend/merge branch)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Credentials:
    username: str
    password: str

    def is_valid(self) -> bool:
        return len(self.username) >= 3 and len(self.password) >= 6
