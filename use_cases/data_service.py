"""
Data Service - Handles data loading, processing, and transformation.
Implements business logic for working with Excel files and data operations.
"""

from typing import Dict, List, Any, Optional, Tuple
import polars as pl
from pathlib import Path
import tempfile
import os
import io
import logging

from domain.entities import (
    Analysis,
    DataSchema,
    Column,
    ColumnType,
    Visualization,
    VisualizationConfig,
    VisualizationType,
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
    """

    def __init__(self):
        """Initialize the data service with a data cache."""
        self._data_cache: Dict[str, pl.DataFrame] = {}

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
        df = pl.read_excel(file_path)
        self._data_cache[analysis_id] = df

        file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
        file_name = os.path.basename(file_path)

        schema = self._infer_schema(df, file_name, file_size)
        logger.info(f"Loaded Excel file: {file_name} with {len(df)} rows")

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
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name

        try:
            df = pl.read_excel(tmp_path)
            self._data_cache[analysis_id] = df
            schema = self._infer_schema(df, file_name, len(file_bytes))
            logger.info(f"Loaded Excel from bytes: {file_name} with {len(df)} rows")
            return schema, df
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def load_excel_from_streamlit(
        self, uploaded_file: Any, analysis_id: str
    ) -> Tuple[DataSchema, pl.DataFrame]:
        """
        Load an Excel file from a Streamlit UploadedFile object.

        Args:
            uploaded_file: Streamlit UploadedFile object
            analysis_id: ID of the analysis for caching

        Returns:
            Tuple of DataSchema and Polars DataFrame
        """
        file_bytes = uploaded_file.getvalue()
        return self.load_excel_from_bytes(file_bytes, uploaded_file.name, analysis_id)

    def get_cached_data(self, analysis_id: str) -> Optional[pl.DataFrame]:
        """
        Get cached DataFrame for an analysis.

        Args:
            analysis_id: The analysis ID

        Returns:
            Cached DataFrame or None if not found
        """
        return self._data_cache.get(analysis_id)

    def clear_cache(self, analysis_id: Optional[str] = None) -> None:
        """
        Clear cached data for specific analysis or all.

        Args:
            analysis_id: Optional specific analysis ID to clear
        """
        if analysis_id:
            self._data_cache.pop(analysis_id, None)
        else:
            self._data_cache.clear()

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

            sample_values = col_series.drop_nulls().head(10).to_list()
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
            columns=columns,
            row_count=len(df),
            file_name=file_name,
            file_size=file_size,
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

        # Check Polars dtype for numeric types
        numeric_dtypes = [
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
        ]
        if dtype in numeric_dtypes:
            return ColumnType.NUMERIC

        # Check for datetime types
        if dtype in [pl.Date, pl.Datetime, pl.Time]:
            return ColumnType.DATETIME

        # Check for boolean
        if dtype == pl.Boolean:
            return ColumnType.BOOLEAN

        # For string types, infer further
        if dtype in [pl.String, pl.Utf8]:
            null_count = series.null_count()
            non_null_count = len(series) - null_count

            if non_null_count == 0:
                return ColumnType.UNKNOWN

            unique_ratio = (
                series.n_unique() / non_null_count if non_null_count > 0 else 1.0
            )

            # If unique ratio is low, it's likely categorical
            if unique_ratio < 0.5:
                return ColumnType.CATEGORICAL

            # Check if values look like dates
            sample = series.drop_nulls().head(100).to_list()
            if sample and self._looks_like_datetime(sample):
                return ColumnType.DATETIME

            # Default to text for high cardinality strings
            if unique_ratio > 0.8:
                return ColumnType.TEXT

            return ColumnType.CATEGORICAL

        return ColumnType.UNKNOWN

    def _looks_like_datetime(self, values: List[str]) -> bool:
        """Check if string values look like datetime values."""
        import re

        date_patterns = [
            r"^\d{4}-\d{2}-\d{2}",
            r"^\d{2}/\d{2}/\d{4}",
            r"^\d{2}-\d{2}-\d{4}",
            r"^\d{4}/\d{2}/\d{2}",
        ]

        if not values:
            return False

        matches = 0
        for val in values[:10]:
            if any(re.match(pattern, str(val)) for pattern in date_patterns):
                matches += 1

        return matches / min(len(values), 10) > 0.7

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
                values = f.value if isinstance(f.value, list) else [f.value]
                result = result.filter(col.is_in(values))
            elif f.operator == "not_in":
                values = f.value if isinstance(f.value, list) else [f.value]
                result = result.filter(~col.is_in(values))
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

    def prepare_visualization_data(
        self, df: pl.DataFrame, config: VisualizationConfig
    ) -> Dict[str, Any]:
        """
        Prepare data for a specific visualization type.

        Args:
            df: Input DataFrame
            config: Visualization configuration

        Returns:
            Dictionary with processed data ready for visualization
        """
        result = {"type": config.visualization_type.value}

        # Apply aggregation if needed
        if config.x_column and config.y_column and config.aggregation:
            if config.visualization_type not in [
                VisualizationType.SCATTER_PLOT,
                VisualizationType.HISTOGRAM,
            ]:
                agg_config = AggregationConfig(
                    group_by_columns=(config.x_column,),
                    aggregation_column=config.y_column,
                    aggregation_function=config.aggregation,
                )
                df = self.apply_aggregation(df, agg_config)

        # Extract data based on visualization type
        if config.visualization_type == VisualizationType.TABLE:
            result["data"] = df.to_pandas().to_dict(orient="records")
            result["columns"] = df.columns

        elif config.visualization_type in [
            VisualizationType.LINE_CHART,
            VisualizationType.BAR_CHART,
            VisualizationType.AREA_CHART,
        ]:
            if config.x_column:
                result["x"] = df[config.x_column].to_list()
            if config.y_column:
                agg_col_name = (
                    f"{config.y_column}_{config.aggregation}"
                    if config.aggregation != "sum"
                    else config.y_column
                )
                y_col = agg_col_name if agg_col_name in df.columns else config.y_column
                result["y"] = df[y_col].to_list()
            if config.color_column:
                result["color"] = df[config.color_column].to_list()

        elif config.visualization_type == VisualizationType.PIE_CHART:
            if config.x_column and config.y_column:
                agg_col_name = (
                    f"{config.y_column}_{config.aggregation}"
                    if config.aggregation != "sum"
                    else config.y_column
                )
                y_col = agg_col_name if agg_col_name in df.columns else config.y_column
                result["labels"] = df[config.x_column].to_list()
                result["values"] = df[y_col].to_list()

        elif config.visualization_type == VisualizationType.SCATTER_PLOT:
            if config.x_column:
                result["x"] = df[config.x_column].to_list()
            if config.y_column:
                result["y"] = df[config.y_column].to_list()
            if config.color_column:
                result["color"] = df[config.color_column].to_list()
            if config.size_column:
                result["size"] = df[config.size_column].to_list()

        elif config.visualization_type == VisualizationType.HISTOGRAM:
            if config.x_column:
                result["x"] = df[config.x_column].to_list()

        elif config.visualization_type == VisualizationType.BOX_PLOT:
            if config.y_column:
                result["y"] = df[config.y_column].to_list()
            if config.x_column:
                result["x"] = df[config.x_column].to_list()

        elif config.visualization_type == VisualizationType.METRIC_CARD:
            if config.y_column:
                col = df[config.y_column]
                if config.aggregation == "mean":
                    result["value"] = float(col.mean())
                elif config.aggregation == "sum":
                    result["value"] = float(col.sum())
                elif config.aggregation == "count":
                    result["value"] = int(col.count())
                elif config.aggregation == "min":
                    result["value"] = float(col.min())
                elif config.aggregation == "max":
                    result["value"] = float(col.max())
                else:
                    result["value"] = float(col.sum())
                result["format"] = "number"

        elif config.visualization_type == VisualizationType.HEATMAP:
            if config.x_column and config.y_column:
                pivot_df = df.pivot(
                    values=config.y_column,
                    index=config.x_column,
                    columns=config.color_column
                    if config.color_column
                    else config.x_column,
                )
                result["data"] = pivot_df.to_numpy().tolist()
                result["x_labels"] = pivot_df.columns
                result["y_labels"] = pivot_df[config.x_column].to_list()

        return result

    def get_column_unique_values(
        self, df: pl.DataFrame, column_name: str, limit: int = 100
    ) -> List[Any]:
        """Get unique values from a column."""
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

    def export_to_csv(self, df: pl.DataFrame, output_path: str) -> str:
        """
        Export DataFrame to CSV file.

        Args:
            df: DataFrame to export
            output_path: Path for output file

        Returns:
            Path to the exported file
        """
        df.write_csv(output_path)
        return output_path
