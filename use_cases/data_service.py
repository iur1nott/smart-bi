"""
Data Service - Handles data processing and transformation operations.
Follows Single Responsibility Principle - only handles data operations.
"""

from typing import Dict, List, Any, Optional, Tuple
import polars as pl
from pathlib import Path
import tempfile
import os
import logging
import streamlit as st

from config import settings, Constants
from domain.entities import (
    Analysis,
    DataSchema,
    Column,
    ColumnType,
    Visualization,
    VisualizationConfig,
    VisualizationType,
    Slide,
)
from domain.value_objects import FilterCondition, AggregationConfig

logger = logging.getLogger(__name__)


class DataService:
    """
    Service responsible for data operations including:
    - Loading and parsing XLSX files
    - Schema inference and column type detection
    - Data filtering and aggregation
    - Data transformation for visualizations

    Uses Streamlit session state for data caching to persist across reruns.
    """

    def __init__(self):
        """Initialize the data service."""
        # Use session state for caching instead of instance variable
        if "data_cache" not in st.session_state:
            st.session_state.data_cache = {}

    @property
    def _data_cache(self) -> Dict[str, pl.DataFrame]:
        """Get the data cache from session state."""
        return st.session_state.data_cache

    def _clean_duplicate_columns(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Rename duplicate column names to make them unique.

        Args:
            df: Polars DataFrame that may have duplicate column names

        Returns:
            DataFrame with unique column names
        """
        columns = df.columns
        seen = {}
        new_columns = []

        for col in columns:
            if col in seen:
                seen[col] += 1
                new_columns.append(f"{col}_{seen[col]}")
            else:
                seen[col] = 0
                new_columns.append(col)

        if new_columns != columns:
            logger.warning(
                f"Detected duplicate column names, renamed: {dict(zip(columns, new_columns))}"
            )
            df = df.rename(dict(zip(columns, new_columns)))

        return df

    def load_excel_file(
        self, file_path: str, analysis_id: str
    ) -> Tuple[DataSchema, pl.DataFrame]:
        """
        Load an Excel file and return its schema and data.

        Args:
            file_path: Path to the Excel file
            analysis_id: ID of the analysis for caching

        Returns:
            Tuple of DataSchema and Polars DataFrame
        """
        # Read the Excel file using Polars
        df = pl.read_excel(file_path)

        # Clean duplicate columns
        df = self._clean_duplicate_columns(df)

        # Cache the dataframe in session state
        st.session_state.data_cache[analysis_id] = df

        # Generate schema
        schema = self._infer_schema(df, file_path)

        return schema, df

    def load_excel_from_bytes(
        self, file_bytes: bytes, file_name: str, analysis_id: str
    ) -> Tuple[DataSchema, pl.DataFrame]:
        """
        Load an Excel file from bytes and return its schema and data.

        Args:
            file_bytes: Raw bytes of the Excel file
            file_name: Original file name
            analysis_id: ID of the analysis for caching

        Returns:
            Tuple of DataSchema and Polars DataFrame
        """
        # Write bytes to temporary file
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name

        try:
            df = pl.read_excel(tmp_path)
            # Clean duplicate columns
            df = self._clean_duplicate_columns(df)
            st.session_state.data_cache[analysis_id] = df
            schema = self._infer_schema(df, file_name, len(file_bytes))
            return schema, df
        finally:
            os.unlink(tmp_path)

    def load_excel_from_streamlit(
        self, uploaded_file: Any, analysis_id: str
    ) -> Tuple[DataSchema, pl.DataFrame]:
        """
        Load an Excel file from Streamlit's file uploader.

        Args:
            uploaded_file: Streamlit UploadedFile object
            analysis_id: ID of the analysis for caching

        Returns:
            Tuple of DataSchema and Polars DataFrame
        """
        file_bytes = uploaded_file.getvalue()
        return self.load_excel_from_bytes(file_bytes, uploaded_file.name, analysis_id)

    def _infer_schema(
        self, df: pl.DataFrame, file_name: str, file_size: int = 0
    ) -> DataSchema:
        """
        Infer the schema of a DataFrame including column types and statistics.

        Args:
            df: Polars DataFrame to analyze
            file_name: Name of the source file
            file_size: Size of the source file in bytes

        Returns:
            DataSchema object with inferred types and statistics
        """
        columns = []

        for col_name in df.columns:
            col_series = df[col_name]
            col_type = self._detect_column_type(col_series)

            # Get sample values (using configurable count)
            sample_values = (
                col_series.drop_nulls()
                .head(settings.data.sample_values_count)
                .to_list()
            )

            # Calculate statistics
            statistics = self._calculate_statistics(col_series, col_type)

            column = Column(
                name=col_name,
                data_type=col_type,
                sample_values=sample_values,
                null_count=col_series.null_count(),
                unique_count=col_series.n_unique(),
                statistics=statistics,
            )
            columns.append(column)

        return DataSchema(
            columns=columns, row_count=len(df), file_name=file_name, file_size=file_size
        )

    def _detect_column_type(self, series: pl.Series) -> ColumnType:
        """
        Detect the type of a column based on its data.

        Args:
            series: Polars Series to analyze

        Returns:
            ColumnType enum value
        """
        dtype = series.dtype

        # Check Polars dtype
        if dtype in [
            pl.Int8,
            pl.Int16,
            pl.Int32,
            pl.Int64,
            pl.UInt8,
            pl.UInt16,
            pl.UInt32,
            pl.UInt64,
            pl.Float32,
            pl.Float64,
        ]:
            return ColumnType.NUMERIC

        if dtype in [pl.Date, pl.Datetime, pl.Time]:
            return ColumnType.DATETIME

        if dtype == pl.Boolean:
            return ColumnType.BOOLEAN

        # For string types, try to infer further
        if dtype == pl.String or dtype == pl.Utf8:
            # Check if it could be categorical
            null_count = series.null_count()
            non_null_count = len(series) - null_count

            if non_null_count == 0:
                return ColumnType.UNKNOWN

            unique_ratio = (
                series.n_unique() / non_null_count if non_null_count > 0 else 1.0
            )

            # If unique ratio is low, it's likely categorical (using configurable threshold)
            if unique_ratio < settings.data.categorical_threshold:
                return ColumnType.CATEGORICAL

            # Check if values look like dates
            sample = series.drop_nulls().head(100).to_list()
            if sample and self._looks_like_datetime(sample):
                return ColumnType.DATETIME

            # Default to text for high cardinality strings (using configurable threshold)
            if unique_ratio > settings.data.text_threshold:
                return ColumnType.TEXT

            return ColumnType.CATEGORICAL

        return ColumnType.UNKNOWN

    def _looks_like_datetime(self, values: List[str]) -> bool:
        """Check if string values look like datetime values."""
        import re

        # Use date patterns from Constants
        date_patterns = Constants.DATE_PATTERNS

        if not values:
            return False

        matches = 0
        for val in values[:10]:
            if any(re.match(pattern, str(val)) for pattern in date_patterns):
                matches += 1

        # Use configurable threshold
        return (
            matches / min(len(values), 10) > settings.data.datetime_detection_threshold
        )

    def _calculate_statistics(
        self, series: pl.Series, col_type: ColumnType
    ) -> Dict[str, Any]:
        """
        Calculate statistics for a column based on its type.

        Args:
            series: Polars Series to analyze
            col_type: Detected column type

        Returns:
            Dictionary of statistics
        """
        stats = {}

        if col_type == ColumnType.NUMERIC:
            try:
                non_null = series.drop_nulls()
                if len(non_null) > 0:
                    stats["min"] = float(non_null.min())
                    stats["max"] = float(non_null.max())
                    stats["mean"] = float(non_null.mean())
                    stats["median"] = float(non_null.median())
                    stats["std"] = float(non_null.std()) if len(non_null) > 1 else 0.0
                    stats["sum"] = float(non_null.sum())
            except Exception:
                pass

        elif col_type == ColumnType.CATEGORICAL:
            try:
                value_counts = series.value_counts().sort("count", descending=True)
                stats["top_values"] = value_counts.head(10).to_dicts()
            except Exception:
                pass

        elif col_type == ColumnType.DATETIME:
            try:
                non_null = series.drop_nulls()
                if len(non_null) > 0:
                    stats["min_date"] = str(non_null.min())
                    stats["max_date"] = str(non_null.max())
            except Exception:
                pass

        return stats

    def get_cached_data(self, analysis_id: str) -> Optional[pl.DataFrame]:
        """Get cached DataFrame for an analysis."""
        return st.session_state.data_cache.get(analysis_id)

    def set_cached_data(self, analysis_id: str, df: pl.DataFrame) -> None:
        """Set cached DataFrame for an analysis."""
        st.session_state.data_cache[analysis_id] = df

    def clear_cache(self, analysis_id: Optional[str] = None):
        """Clear cached data for specific analysis or all."""
        if analysis_id:
            st.session_state.data_cache.pop(analysis_id, None)
        else:
            st.session_state.data_cache.clear()

    def apply_filters(
        self, df: pl.DataFrame, filters: List[FilterCondition]
    ) -> pl.DataFrame:
        """
        Apply filter conditions to a DataFrame.

        Args:
            df: Input DataFrame
            filters: List of filter conditions

        Returns:
            Filtered DataFrame
        """
        result = df

        for f in filters:
            col = pl.col(f.column_name)

            if f.operator == "eq":
                result = result.filter(col == f.value)
            elif f.operator == "ne":
                result = result.filter(col != f.value)
            elif f.operator == "gt":
                result = result.filter(col > f.value)
            elif f.operator == "lt":
                result = result.filter(col < f.value)
            elif f.operator == "gte":
                result = result.filter(col >= f.value)
            elif f.operator == "lte":
                result = result.filter(col <= f.value)
            elif f.operator == "contains":
                result = result.filter(col.str.contains(str(f.value)))
            elif f.operator == "starts_with":
                result = result.filter(col.str.starts_with(str(f.value)))
            elif f.operator == "ends_with":
                result = result.filter(col.str.ends_with(str(f.value)))
            elif f.operator == "in":
                result = result.filter(
                    col.is_in(f.value if isinstance(f.value, list) else [f.value])
                )
            elif f.operator == "not_in":
                result = result.filter(
                    ~col.is_in(f.value if isinstance(f.value, list) else [f.value])
                )
            elif f.operator == "is_null":
                result = result.filter(col.is_null())
            elif f.operator == "is_not_null":
                result = result.filter(col.is_not_null())

        return result

    def apply_aggregation(
        self, df: pl.DataFrame, config: AggregationConfig
    ) -> pl.DataFrame:
        """
        Apply aggregation to a DataFrame.

        Args:
            df: Input DataFrame
            config: Aggregation configuration

        Returns:
            Aggregated DataFrame
        """
        agg_col = pl.col(config.aggregation_column)

        if config.aggregation_function == "sum":
            agg_expr = agg_col.sum()
        elif config.aggregation_function == "mean":
            agg_expr = agg_col.mean()
        elif config.aggregation_function == "median":
            agg_expr = agg_col.median()
        elif config.aggregation_function == "min":
            agg_expr = agg_col.min()
        elif config.aggregation_function == "max":
            agg_expr = agg_col.max()
        elif config.aggregation_function == "count":
            agg_expr = agg_col.count()
        elif config.aggregation_function == "std":
            agg_expr = agg_col.std()
        elif config.aggregation_function == "var":
            agg_expr = agg_col.var()
        elif config.aggregation_function == "first":
            agg_expr = agg_col.first()
        elif config.aggregation_function == "last":
            agg_expr = agg_col.last()
        else:
            agg_expr = agg_col.sum()

        result = df.group_by(list(config.group_by_columns)).agg(
            agg_expr.alias(f"{config.aggregation_column}_{config.aggregation_function}")
        )

        return result

    def get_column_unique_values(
        self, df: pl.DataFrame, column_name: str, limit: Optional[int] = None
    ) -> List[Any]:
        """Get unique values from a column."""
        if limit is None:
            limit = settings.data.max_unique_values_display
        return df[column_name].unique().head(limit).to_list()

    def get_numeric_summary(
        self, df: pl.DataFrame, column_name: str
    ) -> Dict[str, float]:
        """Get summary statistics for a numeric column."""
        col = df[column_name]
        return {
            "min": float(col.min()),
            "max": float(col.max()),
            "mean": float(col.mean()),
            "median": float(col.median()),
            "std": float(col.std()),
            "q1": float(col.quantile(0.25)),
            "q3": float(col.quantile(0.75)),
        }
