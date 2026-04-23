"""
Domain Layer - Core business entities and value objects.
This layer contains pure business logic with no external dependencies.
Matches the database schema defined in smartxl_db_creator.sql
"""

from .entities import (
    User,
    File,
    FileSheet,
    SheetColumn,
    Dashboard,
    Visualization,
    VisualizationConfig,
    VisualizationType,
    ColumnDataType,
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
    DashboardRepository,
    FileRepository,
)

# Type aliases for backward compatibility
Analysis = Dashboard
Slide = Visualization

__all__ = [
    # Entities
    "User",
    "File",
    "FileSheet",
    "SheetColumn",
    "Dashboard",
    "Visualization",
    "VisualizationConfig",
    "VisualizationType",
    "ColumnDataType",
    "ExportFormat",
    # Backward compatibility aliases
    "Analysis",
    "Slide",
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
    "DashboardRepository",
    "FileRepository",
]
