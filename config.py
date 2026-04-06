"""
Configuration Module - Centralized application configuration.

This module contains all configurable variables, constants, and settings
used throughout the application. Developers should modify this file
or set environment variables to customize the application behavior.

Usage:
    from config import settings

    database_url = settings.DATABASE_URL
    session_timeout = settings.SESSION_TIMEOUT_HOURS
"""

import os
from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class DatabaseSettings:
    """
    Database connection and pool settings.

    Environment Variables:
        DATABASE_URL: Full PostgreSQL connection string
        DB_POOL_SIZE: Number of connections to keep in the pool
        DB_MAX_OVERFLOW: Maximum overflow connections
        DB_POOL_RECYCLE: Recycle connections after N seconds
        SQL_ECHO: Echo SQL statements (for debugging)
    """

    url: str = field(
        default_factory=lambda: os.getenv(
            "DATABASE_URL",
            "postgresql://postgres:Pst|Grs@localhost:5432/postgres",
        )
    )
    pool_size: int = field(default_factory=lambda: int(os.getenv("DB_POOL_SIZE", "5")))
    max_overflow: int = field(
        default_factory=lambda: int(os.getenv("DB_MAX_OVERFLOW", "10"))
    )
    pool_recycle: int = field(
        default_factory=lambda: int(os.getenv("DB_POOL_RECYCLE", "3600"))
    )
    echo_sql: bool = field(
        default_factory=lambda: os.getenv("SQL_ECHO", "false").lower() == "true"
    )

    # Connection timeout in seconds
    connection_timeout: int = 30


@dataclass
class JWTSettings:
    """
    JWT authentication settings.

    Environment Variables:
        JWT_SECRET_KEY: Secret key for signing JWT tokens (CHANGE IN PRODUCTION!)
        JWT_ALGORITHM: Token signing algorithm
        JWT_ACCESS_TOKEN_EXPIRE_MINUTES: Access token lifetime in minutes
        JWT_REFRESH_TOKEN_EXPIRE_DAYS: Refresh token lifetime in days
    """

    secret_key: str = field(
        default_factory=lambda: os.getenv(
            "JWT_SECRET_KEY", "your-super-secret-key-change-in-production"
        )
    )
    algorithm: str = field(default_factory=lambda: os.getenv("JWT_ALGORITHM", "HS256"))
    access_token_expire_minutes: int = field(
        default_factory=lambda: int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    )
    refresh_token_expire_days: int = field(
        default_factory=lambda: int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    )


@dataclass
class SessionSettings:
    """
    User session settings.

    Environment Variables:
        SESSION_TIMEOUT_HOURS: Session timeout in hours
        SESSION_CLEANUP_INTERVAL_HOURS: How often to clean up expired sessions
    """

    timeout_hours: int = field(
        default_factory=lambda: int(os.getenv("SESSION_TIMEOUT_HOURS", "24"))
    )
    cleanup_interval_hours: int = field(
        default_factory=lambda: int(os.getenv("SESSION_CLEANUP_INTERVAL_HOURS", "1"))
    )


@dataclass
class ApplicationSettings:
    """
    General application settings.

    Environment Variables:
        APP_NAME: Application name
        APP_VERSION: Application version
        DEBUG_MODE: Enable debug mode
        APP_PORT: Port to run the application on
        APP_HOST: Host to bind to
    """

    name: str = field(
        default_factory=lambda: os.getenv("APP_NAME", "Dashboard Builder")
    )
    version: str = field(default_factory=lambda: os.getenv("APP_VERSION", "1.0.0"))
    debug: bool = field(
        default_factory=lambda: os.getenv("DEBUG_MODE", "false").lower() == "true"
    )
    port: int = field(default_factory=lambda: int(os.getenv("APP_PORT", "8501")))
    host: str = field(default_factory=lambda: os.getenv("APP_HOST", "0.0.0.0"))

    # Streamlit-specific settings
    page_title: str = "Dashboard Builder"
    page_icon: str = "📊"
    layout: str = "wide"
    initial_sidebar_state: str = "expanded"


@dataclass
class DataSettings:
    """
    Data processing settings.

    Environment Variables:
        MAX_FILE_SIZE_MB: Maximum upload file size in MB
        MAX_ROWS_PREVIEW: Maximum rows to show in preview
        SAMPLE_VALUES_COUNT: Number of sample values to show per column
        MAX_UNIQUE_VALUES_DISPLAY: Maximum unique values to display in filters
        DATETIME_DETECTION_THRESHOLD: Threshold for datetime detection (0.0-1.0)
        CATEGORICAL_THRESHOLD: Unique ratio threshold for categorical detection
        TEXT_THRESHOLD: Unique ratio threshold for text detection
    """

    max_file_size_mb: int = field(
        default_factory=lambda: int(os.getenv("MAX_FILE_SIZE_MB", "50"))
    )
    max_rows_preview: int = field(
        default_factory=lambda: int(os.getenv("MAX_ROWS_PREVIEW", "100"))
    )
    sample_values_count: int = field(
        default_factory=lambda: int(os.getenv("SAMPLE_VALUES_COUNT", "10"))
    )
    max_unique_values_display: int = field(
        default_factory=lambda: int(os.getenv("MAX_UNIQUE_VALUES_DISPLAY", "100"))
    )
    datetime_detection_threshold: float = field(
        default_factory=lambda: float(os.getenv("DATETIME_DETECTION_THRESHOLD", "0.7"))
    )
    categorical_threshold: float = field(
        default_factory=lambda: float(os.getenv("CATEGORICAL_THRESHOLD", "0.5"))
    )
    text_threshold: float = field(
        default_factory=lambda: float(os.getenv("TEXT_THRESHOLD", "0.8"))
    )

    # Allowed file extensions
    allowed_extensions: List[str] = field(default_factory=lambda: [".xlsx", ".xls"])


@dataclass
class ExportSettings:
    """
    Export settings for PDF, HTML, and LaTeX generation.

    Environment Variables:
        EXPORT_OUTPUT_DIR: Directory to save exported files
        EXPORT_PAPER_SIZE: Default paper size (a4, letter, legal)
        EXPORT_ORIENTATION: Default orientation (portrait, landscape)
        EXPORT_INCLUDE_COMMENTS: Include comments in exports by default
    """

    output_dir: str = field(
        default_factory=lambda: os.getenv("EXPORT_OUTPUT_DIR", "./exports")
    )
    default_paper_size: str = field(
        default_factory=lambda: os.getenv("EXPORT_PAPER_SIZE", "a4")
    )
    default_orientation: str = field(
        default_factory=lambda: os.getenv("EXPORT_ORIENTATION", "portrait")
    )
    include_comments_default: bool = field(
        default_factory=lambda: (
            os.getenv("EXPORT_INCLUDE_COMMENTS", "true").lower() == "true"
        )
    )

    # Available paper sizes
    paper_sizes: List[str] = field(default_factory=lambda: ["a4", "letter", "legal"])
    # Available formats
    formats: List[str] = field(default_factory=lambda: ["pdf", "html", "latex"])


@dataclass
class LoggingSettings:
    """
    Logging configuration.

    Environment Variables:
        LOG_LEVEL: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        LOG_FORMAT: Log message format
        LOG_FILE: Optional log file path
    """

    level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    format: str = field(
        default_factory=lambda: os.getenv(
            "LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    )
    file: str = field(default_factory=lambda: os.getenv("LOG_FILE", ""))


@dataclass
class ChartSettings:
    """
    Chart visualization settings.

    Environment Variables:
        CHART_DEFAULT_COLOR_SCHEME: Default color scheme for charts
        CHART_DEFAULT_WIDTH: Default chart width in pixels
        CHART_DEFAULT_HEIGHT: Default chart height in pixels
        CHART_SHOW_LEGEND: Show legend by default
        CHART_SHOW_GRID: Show grid by default
    """

    default_color_scheme: str = field(
        default_factory=lambda: os.getenv("CHART_DEFAULT_COLOR_SCHEME", "default")
    )
    default_width: int = field(
        default_factory=lambda: int(os.getenv("CHART_DEFAULT_WIDTH", "400"))
    )
    default_height: int = field(
        default_factory=lambda: int(os.getenv("CHART_DEFAULT_HEIGHT", "300"))
    )
    show_legend_default: bool = True
    show_grid_default: bool = True

    # Aggregation options
    aggregation_options: List[str] = field(
        default_factory=lambda: ["sum", "mean", "count", "min", "max", "median", "std"]
    )


@dataclass
class SecuritySettings:
    """
    Security-related settings.

    Environment Variables:
        PASSWORD_MIN_LENGTH: Minimum password length
        PASSWORD_REQUIRE_UPPERCASE: Require uppercase in passwords
        PASSWORD_REQUIRE_LOWERCASE: Require lowercase in passwords
        PASSWORD_REQUIRE_DIGIT: Require digit in passwords
        PASSWORD_REQUIRE_SPECIAL: Require special character in passwords
        MAX_LOGIN_ATTEMPTS: Maximum login attempts before lockout
        LOGIN_LOCKOUT_MINUTES: Lockout duration in minutes
    """

    password_min_length: int = field(
        default_factory=lambda: int(os.getenv("PASSWORD_MIN_LENGTH", "8"))
    )
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    password_require_digit: bool = True
    password_require_special: bool = False
    max_login_attempts: int = field(
        default_factory=lambda: int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
    )
    login_lockout_minutes: int = field(
        default_factory=lambda: int(os.getenv("LOGIN_LOCKOUT_MINUTES", "15"))
    )


@dataclass
class Settings:
    """
    Main settings class that aggregates all configuration sections.

    Usage:
        from config import settings

        # Access database URL
        db_url = settings.database.url

        # Access JWT settings
        secret = settings.jwt.secret_key

        # Access session timeout
        timeout = settings.session.timeout_hours
    """

    database: DatabaseSettings = field(default_factory=DatabaseSettings)
    jwt: JWTSettings = field(default_factory=JWTSettings)
    session: SessionSettings = field(default_factory=SessionSettings)
    app: ApplicationSettings = field(default_factory=ApplicationSettings)
    data: DataSettings = field(default_factory=DataSettings)
    export: ExportSettings = field(default_factory=ExportSettings)
    logging: LoggingSettings = field(default_factory=LoggingSettings)
    chart: ChartSettings = field(default_factory=ChartSettings)
    security: SecuritySettings = field(default_factory=SecuritySettings)

    def __post_init__(self):
        """Validate settings after initialization."""
        self._validate()

    def _validate(self) -> None:
        """Validate configuration settings."""
        # Warn about default JWT secret in production
        if self.jwt.secret_key == "your-super-secret-key-change-in-production":
            if not self.app.debug:
                print(
                    "WARNING: Using default JWT secret key! Set JWT_SECRET_KEY environment variable."
                )

        # Validate thresholds are in valid range
        if not 0 <= self.data.datetime_detection_threshold <= 1:
            raise ValueError("datetime_detection_threshold must be between 0 and 1")
        if not 0 <= self.data.categorical_threshold <= 1:
            raise ValueError("categorical_threshold must be between 0 and 1")
        if not 0 <= self.data.text_threshold <= 1:
            raise ValueError("text_threshold must be between 0 and 1")

        # Validate paper size
        if self.export.default_paper_size not in self.export.paper_sizes:
            raise ValueError(f"Invalid paper size: {self.export.default_paper_size}")

        # Validate orientation
        if self.export.default_orientation not in ["portrait", "landscape"]:
            raise ValueError(f"Invalid orientation: {self.export.default_orientation}")

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return not self.app.debug

    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary for serialization."""
        return {
            "database": {
                "url": "***" if self.database.url else None,  # Hide sensitive data
                "pool_size": self.database.pool_size,
                "max_overflow": self.database.max_overflow,
                "pool_recycle": self.database.pool_recycle,
            },
            "jwt": {
                "algorithm": self.jwt.algorithm,
                "access_token_expire_minutes": self.jwt.access_token_expire_minutes,
                "refresh_token_expire_days": self.jwt.refresh_token_expire_days,
            },
            "session": {
                "timeout_hours": self.session.timeout_hours,
            },
            "app": {
                "name": self.app.name,
                "version": self.app.version,
                "debug": self.app.debug,
            },
            "data": {
                "max_file_size_mb": self.data.max_file_size_mb,
                "max_rows_preview": self.data.max_rows_preview,
            },
            "export": {
                "output_dir": self.export.output_dir,
                "default_paper_size": self.export.default_paper_size,
                "default_orientation": self.export.default_orientation,
            },
        }


# Global settings instance
settings = Settings()


# Convenience functions for backward compatibility
def get_database_url() -> str:
    """Get the database URL."""
    return settings.database.url


def get_jwt_secret_key() -> str:
    """Get the JWT secret key."""
    return settings.jwt.secret_key


def get_session_timeout_hours() -> int:
    """Get the session timeout in hours."""
    return settings.session.timeout_hours


# Constants that are not configurable (business logic constants)
class Constants:
    """
    Non-configurable constants used throughout the application.
    These are hardcoded values that represent business rules or technical limits.
    """

    # Visualization types
    VISUALIZATION_TYPES = [
        "bar_chart",
        "line_chart",
        "pie_chart",
        "area_chart",
        "scatter_plot",
        "histogram",
        "box_plot",
        "heatmap",
        "table",
        "metric_card",
    ]

    # Column types
    COLUMN_TYPES = [
        "numeric",
        "categorical",
        "datetime",
        "text",
        "boolean",
        "unknown",
    ]

    # Export formats
    EXPORT_FORMATS = ["pdf", "html", "latex"]

    # Paper sizes (in points for reportlab)
    PAPER_SIZES = {
        "a4": (595.27, 841.89),  # width, height in points
        "letter": (612, 792),
        "legal": (612, 1008),
    }

    # Date patterns for detection
    DATE_PATTERNS = [
        r"^\d{4}-\d{2}-\d{2}",  # YYYY-MM-DD
        r"^\d{2}/\d{2}/\d{4}",  # MM/DD/YYYY or DD/MM/YYYY
        r"^\d{2}-\d{2}-\d{4}",  # DD-MM-YYYY
        r"^\d{4}/\d{2}/\d{2}",  # YYYY/MM/DD
    ]

    # Default admin credentials (for initial setup only)
    DEFAULT_ADMIN_USERNAME = "admin"
    DEFAULT_ADMIN_EMAIL = "admin@example.com"
    DEFAULT_ADMIN_PASSWORD = "admin123"  # Should be changed immediately

    # Filter operators
    FILTER_OPERATORS = [
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

    # Aggregation functions
    AGGREGATION_FUNCTIONS = [
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
