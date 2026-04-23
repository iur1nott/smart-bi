"""
Configuration Module - Centralized application configuration for Streamlit Cloud.

This module contains all configurable variables, constants, and settings
used throughout the application. Designed for Streamlit Community Cloud deployment.

Configuration Priority:
1. Streamlit secrets (st.secrets) - for Streamlit Cloud deployment
2. Environment variables - for local development or Docker deployment
3. Default values - fallback defaults

Usage:
    from config import settings

    database_url = settings.database.url
    session_timeout = settings.session.timeout_hours
"""

import os
import streamlit as st
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


def _get_secret(key: str, section: str = None, default: Any = None) -> Any:
    """
    Get configuration value from Streamlit secrets or environment variables.

    Priority:
    1. st.secrets[section][key] if section provided
    2. st.secrets[key] directly if no section
    3. os.getenv(key.upper()) or os.getenv(key)
    4. default value

    Args:
        key: Configuration key name
        section: Optional section name in secrets.toml
        default: Default value if not found

    Returns:
        Configuration value
    """
    # Try Streamlit secrets first
    try:
        if section:
            if section in st.secrets and key in st.secrets[section]:
                return st.secrets[section][key]
        else:
            if key in st.secrets:
                return st.secrets[key]
    except Exception:
        # st.secrets not available (e.g., before st.set_page_config)
        pass

    # Try environment variables
    env_key = key.upper()
    env_value = os.getenv(env_key) or os.getenv(key)
    if env_value is not None:
        return env_value

    return default


def _get_int_secret(key: str, section: str = None, default: int = 0) -> int:
    """Get integer configuration value."""
    value = _get_secret(key, section, default)
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _get_float_secret(key: str, section: str = None, default: float = 0.0) -> float:
    """Get float configuration value."""
    value = _get_secret(key, section, default)
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _get_bool_secret(key: str, section: str = None, default: bool = False) -> bool:
    """Get boolean configuration value."""
    value = _get_secret(key, section, default)
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes", "on")
    return default


@dataclass
class DatabaseSettings:
    """
    Database connection and pool settings.

    Secrets (secrets.toml):
        [database]
        url = "postgresql://..."
        pool_size = 5
        max_overflow = 10
        pool_recycle = 3600
    """

    url: str = field(
        default_factory=lambda: _get_secret(
            "url", "database", "postgresql://postgres:postgres@localhost:5432/smartxl"
        )
    )
    pool_size: int = field(
        default_factory=lambda: _get_int_secret("pool_size", "database", 5)
    )
    max_overflow: int = field(
        default_factory=lambda: _get_int_secret("max_overflow", "database", 10)
    )
    pool_recycle: int = field(
        default_factory=lambda: _get_int_secret("pool_recycle", "database", 3600)
    )
    echo_sql: bool = field(
        default_factory=lambda: _get_bool_secret("echo_sql", "database", False)
    )

    # Connection timeout in seconds
    connection_timeout: int = 30


@dataclass
class S3StorageSettings:
    """
    S3/Supabase storage settings for file management.

    Secrets (secrets.toml):
        [storage]
        endpoint_url = "https://..."
        access_key = "your-access-key"
        secret_key = "your-secret-key"
        bucket_name = "smartxl-files"
        region = "us-east-1"
        use_ssl = true
        presigned_url_expiration = 3600
    """

    endpoint_url: str = field(
        default_factory=lambda: _get_secret("endpoint_url", "storage", "")
    )
    access_key: str = field(
        default_factory=lambda: _get_secret("access_key", "storage", "")
    )
    secret_key: str = field(
        default_factory=lambda: _get_secret("secret_key", "storage", "")
    )
    bucket_name: str = field(
        default_factory=lambda: _get_secret("bucket_name", "storage", "smartxl-files")
    )
    region: str = field(
        default_factory=lambda: _get_secret("region", "storage", "us-east-1")
    )
    use_ssl: bool = field(
        default_factory=lambda: _get_bool_secret("use_ssl", "storage", True)
    )

    # File path prefix within bucket
    files_prefix: str = "files"

    # Presigned URL expiration in seconds
    presigned_url_expiration: int = field(
        default_factory=lambda: _get_int_secret(
            "presigned_url_expiration", "storage", 3600
        )
    )

    @property
    def is_configured(self) -> bool:
        """Check if S3 is properly configured."""
        return bool(self.access_key and self.secret_key and self.bucket_name)


@dataclass
class JWTSettings:
    """
    JWT authentication settings.

    Secrets (secrets.toml):
        [jwt]
        secret_key = "your-secure-random-string"
        algorithm = "HS256"
        access_token_expire_minutes = 60
        refresh_token_expire_days = 7
    """

    secret_key: str = field(
        default_factory=lambda: _get_secret(
            "secret_key", "jwt", "your-super-secret-key-change-in-production"
        )
    )
    algorithm: str = field(
        default_factory=lambda: _get_secret("algorithm", "jwt", "HS256")
    )
    access_token_expire_minutes: int = field(
        default_factory=lambda: _get_int_secret(
            "access_token_expire_minutes", "jwt", 60
        )
    )
    refresh_token_expire_days: int = field(
        default_factory=lambda: _get_int_secret("refresh_token_expire_days", "jwt", 7)
    )


@dataclass
class SessionSettings:
    """
    User session settings.

    Secrets (secrets.toml):
        [session]
        timeout_hours = 24
        cleanup_interval_hours = 1
    """

    timeout_hours: int = field(
        default_factory=lambda: _get_int_secret("timeout_hours", "session", 24)
    )
    cleanup_interval_hours: int = field(
        default_factory=lambda: _get_int_secret("cleanup_interval_hours", "session", 1)
    )


@dataclass
class ApplicationSettings:
    """
    General application settings.

    Secrets (secrets.toml):
        [app]
        name = "SmartXL"
        version = "2.0.0"
        debug = false
    """

    name: str = field(default_factory=lambda: _get_secret("name", "app", "SmartXL"))
    version: str = field(default_factory=lambda: _get_secret("version", "app", "2.0.0"))
    debug: bool = field(default_factory=lambda: _get_bool_secret("debug", "app", False))
    port: int = field(default_factory=lambda: _get_int_secret("port", "app", 8501))
    host: str = field(default_factory=lambda: _get_secret("host", "app", "0.0.0.0"))

    # Streamlit-specific settings
    page_title: str = "SmartXL - Dashboard Builder"
    page_icon: str = "📊"
    layout: str = "wide"
    initial_sidebar_state: str = "expanded"


@dataclass
class DataSettings:
    """
    Data processing settings.

    Secrets (secrets.toml):
        [data]
        max_file_size_mb = 50
        max_rows_preview = 100
        sample_values_count = 10
        max_unique_values_display = 100
    """

    max_file_size_mb: int = field(
        default_factory=lambda: _get_int_secret("max_file_size_mb", "data", 50)
    )
    max_rows_preview: int = field(
        default_factory=lambda: _get_int_secret("max_rows_preview", "data", 100)
    )
    sample_values_count: int = field(
        default_factory=lambda: _get_int_secret("sample_values_count", "data", 10)
    )
    max_unique_values_display: int = field(
        default_factory=lambda: _get_int_secret(
            "max_unique_values_display", "data", 100
        )
    )
    datetime_detection_threshold: float = field(
        default_factory=lambda: _get_float_secret(
            "datetime_detection_threshold", "data", 0.7
        )
    )
    categorical_threshold: float = field(
        default_factory=lambda: _get_float_secret("categorical_threshold", "data", 0.5)
    )
    text_threshold: float = field(
        default_factory=lambda: _get_float_secret("text_threshold", "data", 0.8)
    )

    # Allowed file extensions
    allowed_extensions: List[str] = field(default_factory=lambda: [".xlsx", ".xls"])


@dataclass
class ExportSettings:
    """
    Export settings for PDF, HTML, and LaTeX generation.
    """

    output_dir: str = field(
        default_factory=lambda: _get_secret("output_dir", "export", "./exports")
    )
    default_paper_size: str = field(
        default_factory=lambda: _get_secret("default_paper_size", "export", "a4")
    )
    default_orientation: str = field(
        default_factory=lambda: _get_secret("default_orientation", "export", "portrait")
    )
    include_comments_default: bool = field(
        default_factory=lambda: _get_bool_secret("include_comments", "export", True)
    )

    # Available paper sizes
    paper_sizes: List[str] = field(default_factory=lambda: ["a4", "letter", "legal"])
    # Available formats
    formats: List[str] = field(default_factory=lambda: ["pdf", "html", "latex"])


@dataclass
class LoggingSettings:
    """
    Logging configuration.
    """

    level: str = field(default_factory=lambda: _get_secret("level", "logging", "INFO"))
    format: str = field(
        default_factory=lambda: _get_secret(
            "format", "logging", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    )
    file: str = field(default_factory=lambda: _get_secret("file", "logging", ""))


@dataclass
class ChartSettings:
    """
    Chart visualization settings.
    """

    default_color_scheme: str = field(
        default_factory=lambda: _get_secret("default_color_scheme", "chart", "default")
    )
    default_width: int = field(
        default_factory=lambda: _get_int_secret("default_width", "chart", 400)
    )
    default_height: int = field(
        default_factory=lambda: _get_int_secret("default_height", "chart", 300)
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

    Secrets (secrets.toml):
        [security]
        password_min_length = 8
        max_login_attempts = 5
        login_lockout_minutes = 15
    """

    password_min_length: int = field(
        default_factory=lambda: _get_int_secret("password_min_length", "security", 8)
    )
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    password_require_digit: bool = True
    password_require_special: bool = False
    max_login_attempts: int = field(
        default_factory=lambda: _get_int_secret("max_login_attempts", "security", 5)
    )
    login_lockout_minutes: int = field(
        default_factory=lambda: _get_int_secret("login_lockout_minutes", "security", 15)
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

        # Access S3 settings
        bucket = settings.storage.bucket_name
    """

    database: DatabaseSettings = field(default_factory=DatabaseSettings)
    storage: S3StorageSettings = field(default_factory=S3StorageSettings)
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
                    "WARNING: Using default JWT secret key! Set jwt.secret_key in secrets.toml."
                )

        # Warn if S3 is not configured
        if not self.storage.is_configured:
            print(
                "WARNING: S3 storage is not fully configured. File uploads may not work."
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
            "storage": {
                "bucket_name": self.storage.bucket_name,
                "region": self.storage.region,
                "is_configured": self.storage.is_configured,
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


# Global settings instance - lazy initialization
_settings_instance: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get the global settings instance.
    Creates a new instance if none exists.

    Returns:
        Settings instance
    """
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance


# For backward compatibility - settings property
class _SettingsProxy:
    """Proxy class for lazy settings initialization."""

    def __getattr__(self, name):
        return getattr(get_settings(), name)


settings = _SettingsProxy()


# Convenience functions for backward compatibility
def get_database_url() -> str:
    """Get the database URL."""
    return get_settings().database.url


def get_jwt_secret_key() -> str:
    """Get the JWT secret key."""
    return get_settings().jwt.secret_key


def get_session_timeout_hours() -> int:
    """Get the session timeout in hours."""
    return get_settings().session.timeout_hours


# Constants that are not configurable (business logic constants)
class Constants:
    """
    Non-configurable constants used throughout the application.
    These are hardcoded values that represent business rules or technical limits.
    """

    # Visualization types (maps to viz_type in database)
    VISUALIZATION_TYPES = [
        "bar",
        "line",
        "pie",
        "area",
        "scatter",
        "histogram",
        "box",
        "heatmap",
        "table",
        "metric_card",
    ]

    # Column types (maps to data_type in sheet_columns)
    COLUMN_TYPES = [
        "Int64",
        "Float64",
        "String",
        "Boolean",
        "Date",
        "Datetime",
        "Time",
    ]

    # Polars to DB type mapping
    POLARS_TO_DB_TYPE = {
        "Int8": "Int64",
        "Int16": "Int64",
        "Int32": "Int64",
        "Int64": "Int64",
        "UInt8": "Int64",
        "UInt16": "Int64",
        "UInt32": "Int64",
        "UInt64": "Int64",
        "Float32": "Float64",
        "Float64": "Float64",
        "String": "String",
        "Utf8": "String",
        "Boolean": "Boolean",
        "Date": "Date",
        "Datetime": "Datetime",
        "Time": "Time",
    }

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
