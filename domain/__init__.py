"""
Domain Layer - Core business entities and value objects.
This layer contains pure business logic with no external dependencies.
"""

from .entities import (
    User,
    UserSession,
    Analysis,
    Slide,
    Visualization,
    VisualizationConfig,
    VisualizationType,
    DataSchema,
    Column,
    ColumnType,
    ExportFormat,
)
from .value_objects import (
    Credentials,
    ExportOptions,
    FilterCondition,
    AggregationConfig,
    ChartColors,
    Position,
    Size,
    Pagination,
    SortOrder,
    FileMetadata,
    LayoutConstraints,
)
from .repositories import (
    UserRepository,
    AnalysisRepository,
    SessionRepository,
    DataRepository,
)

__all__ = [
    # Entities
    "User",
    "UserSession",
    "Analysis",
    "Slide",
    "Visualization",
    "VisualizationConfig",
    "VisualizationType",
    "DataSchema",
    "Column",
    "ColumnType",
    "ExportFormat",
    # Value Objects
    "Credentials",
    "ExportOptions",
    "FilterCondition",
    "AggregationConfig",
    "ChartColors",
    "Position",
    "Size",
    "Pagination",
    "SortOrder",
    "FileMetadata",
    "LayoutConstraints",
    # Repository Interfaces
    "UserRepository",
    "AnalysisRepository",
    "SessionRepository",
    "DataRepository",
]
