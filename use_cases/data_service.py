"""
Data Service - Handles data processing and transformation operations.
Follows Single Responsibility Principle - only handles data operations.
Updated to work with new file-based schema.
"""

import logging
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import polars as pl
import streamlit as st

from config import Constants, settings
from domain.entities import (
    Dashboard,
    File,
    FileSheet,
    SheetColumn,
    Visualization,
    VisualizationConfig,
    VisualizationType,
)
from domain.value_objects import AggregationConfig, FilterCondition
from infrastructure.storage.s3_client import get_s3_client

logger = logging.getLogger(__name__)


class DataService:
    """
    Service responsible for data operations including:
    - Loading and parsing XLSX files from S3
    - Schema inference and column type detection
    - Data filtering and aggregation
    - Data transformation for visualizations
    - Caching data in Streamlit session state
    """

    def __init__(self):
        """Initialize the data service."""
        # Use session state for caching
        if "data_cache" not in st.session_state:
            st.session_state.data_cache = {}
        if "sheet_cache" not in st.session_state:
            st.session_state.sheet_cache = {}

    @property
    def _data_cache(self) -> Dict[str, pl.DataFrame]:
        """Get the data cache from session state."""
        return st.session_state.data_cache

    @property
    def _sheet_cache(self) -> Dict[str, pl.DataFrame]:
        """Get the sheet cache from session state."""
        return st.session_state.sheet_cache

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

    def load_excel_from_streamlit(
        self, uploaded_file: Any, file_id: str, sheet_name: Optional[str] = None
    ) -> Tuple[Optional[FileSheet], Optional[pl.DataFrame]]:
        """
        Load an Excel file from Streamlit's file uploader.

        Args:
            uploaded_file: Streamlit UploadedFile object
            file_id: ID for caching
            sheet_name: Optional sheet name (uses first sheet if not specified)

        Returns:
            Tuple of (FileSheet, DataFrame), or (None, None) on failure
        """
        file_bytes = uploaded_file.getvalue()
        return self.load_excel_from_bytes(
            file_bytes, uploaded_file.name, file_id, sheet_name
        )

    def load_excel_from_bytes(
        self,
        file_bytes: bytes,
        file_name: str,
        file_id: str,
        sheet_name: Optional[str] = None,
        existing_sheet: Optional[FileSheet] = None,
    ) -> Tuple[Optional[FileSheet], Optional[pl.DataFrame]]:
        """
        Load an Excel file from bytes.

        Args:
            file_bytes: Raw bytes of the Excel file
            file_name: Original file name
            file_id: ID for caching
            sheet_name: Optional sheet name (uses first sheet if not specified)
            existing_sheet: Optional existing FileSheet entity to use its sheet_id

        Returns:
            Tuple of (FileSheet, DataFrame), or (None, None) on failure
        """
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name

        try:
            # Get sheet names
            sheet_names = self._get_sheet_names(tmp_path)
            if not sheet_names:
                return None, None

            # Determine which sheet to read
            target_sheet = sheet_name or sheet_names[0]
            if target_sheet not in sheet_names:
                target_sheet = sheet_names[0]

            # Read the data
            df = pl.read_excel(tmp_path, sheet_name=target_sheet)
            df = self._clean_duplicate_columns(df)

            # Use existing sheet or create new one
            if existing_sheet:
                sheet = existing_sheet
                sheet_id = sheet.sheet_id
            else:
                # Create FileSheet entity with composite ID (for backward compatibility)
                sheet_id = f"{file_id}_{target_sheet}"
                sheet = FileSheet(
                    sheet_id=sheet_id,
                    file_id=file_id,
                    sheet_name=target_sheet,
                )

                # Extract columns
                columns = []
                for col_name in df.columns:
                    col_series = df[col_name]
                    polars_type = str(col_series.dtype)
                    db_type = Constants.POLARS_TO_DB_TYPE.get(polars_type, "String")

                    column = SheetColumn(
                        column_id=f"{sheet_id}_{col_name}",
                        sheet_id=sheet_id,
                        column_name=col_name,
                        data_type=db_type,
                    )
                    columns.append(column)

                sheet.columns = columns

            # Cache the DataFrame with the proper sheet_id
            st.session_state.sheet_cache[sheet_id] = df
            st.session_state.data_cache[file_id] = df

            return sheet, df

        except Exception as e:
            logger.error(f"Error loading Excel file: {e}")
            return None, None
        finally:
            os.unlink(tmp_path)

    def load_file_from_s3(
        self,
        storage_path: str,
        file_id: str,
        sheet_name: Optional[str] = None,
        existing_sheet: Optional[FileSheet] = None,
    ) -> Tuple[Optional[FileSheet], Optional[pl.DataFrame]]:
        """
        Load an Excel file from S3.

        Args:
            storage_path: S3 path to the file
            file_id: ID for caching
            sheet_name: Optional sheet name (uses first sheet if not specified)
            existing_sheet: Optional existing FileSheet entity to use its sheet_id

        Returns:
            Tuple of (FileSheet, DataFrame), or (None, None) on failure
        """
        try:
            s3_client = get_s3_client()
            file_bytes = s3_client.download_file(storage_path)

            if not file_bytes:
                return None, None

            return self.load_excel_from_bytes(
                file_bytes, "file.xlsx", file_id, sheet_name, existing_sheet
            )

        except Exception as e:
            logger.error(f"Error loading file from S3: {e}")
            return None, None

    def _get_sheet_names(self, file_path: str) -> List[str]:
        """Get all sheet names from an Excel file."""
        try:
            from openpyxl import load_workbook

            wb = load_workbook(file_path, read_only=True, data_only=True)
            return wb.sheetnames
        except Exception as e:
            logger.error(f"Error getting sheet names: {e}")
            return ["Sheet1"]

    def get_cached_data(self, file_id: str) -> Optional[pl.DataFrame]:
        """Get cached DataFrame for a file."""
        return st.session_state.data_cache.get(file_id)

    def get_cached_sheet(self, sheet_id: str) -> Optional[pl.DataFrame]:
        """Get cached DataFrame for a sheet."""
        return st.session_state.sheet_cache.get(sheet_id)

    def set_cached_data(self, file_id: str, df: pl.DataFrame) -> None:
        """Set cached DataFrame for a file."""
        st.session_state.data_cache[file_id] = df

    def set_cached_sheet(self, sheet_id: str, df: pl.DataFrame) -> None:
        """Set cached DataFrame for a sheet."""
        st.session_state.sheet_cache[sheet_id] = df

    def clear_cache(
        self, file_id: Optional[str] = None, sheet_id: Optional[str] = None
    ):
        """Clear cached data."""
        if file_id:
            st.session_state.data_cache.pop(file_id, None)
        if sheet_id:
            st.session_state.sheet_cache.pop(sheet_id, None)
        if not file_id and not sheet_id:
            st.session_state.data_cache.clear()
            st.session_state.sheet_cache.clear()

    # Map of supabase data_type names -> Polars dtype for casting
    _DTYPE_MAP = {
        "Int64": pl.Int64,
        "Float64": pl.Float64,
        "String": pl.String,
        "Boolean": pl.Boolean,
        "Date": pl.Date,
        "Datetime": pl.Datetime,
        "Time": pl.Time,
    }

    def cast_column_types(
        self, df: pl.DataFrame, mapping: Dict[str, str]
    ) -> pl.DataFrame:
        """
        Cast each column in `df` to the target supabase data_type given by `mapping`.

        Args:
            df: Source DataFrame.
            mapping: {column_name: data_type_str} where data_type_str is one of
                Int64, Float64, String, Boolean, Date, Datetime, Time.

        Returns:
            New DataFrame with columns cast. Columns whose cast fails are
            converted to String as a safe fallback so the rest of the dataset
            stays usable.
        """
        result = df
        for col_name, target_type in mapping.items():
            if col_name not in result.columns:
                continue
            polars_type = self._DTYPE_MAP.get(target_type)
            if polars_type is None:
                continue
            try:
                result = result.with_columns(
                    pl.col(col_name).cast(polars_type, strict=False).alias(col_name)
                )
            except Exception as e:
                logger.warning(
                    f"Cast {col_name} -> {target_type} failed ({e}); falling back to String"
                )
                result = result.with_columns(
                    pl.col(col_name).cast(pl.String, strict=False).alias(col_name)
                )
        return result

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

    def prepare_chart_data(
        self,
        df: pl.DataFrame,
        config: VisualizationConfig,
    ) -> pl.DataFrame:
        """
        Prepare data for chart visualization.

        Args:
            df: Input DataFrame
            config: Visualization configuration

        Returns:
            Prepared DataFrame for charting
        """
        result = df

        # Handle aggregation
        if config.x_column and config.y_column:
            if config.aggregation and config.aggregation != "none":
                agg_col = pl.col(config.y_column)

                if config.aggregation == "sum":
                    agg_expr = agg_col.sum()
                elif config.aggregation == "mean":
                    agg_expr = agg_col.mean()
                elif config.aggregation == "count":
                    agg_expr = agg_col.count()
                elif config.aggregation == "min":
                    agg_expr = agg_col.min()
                elif config.aggregation == "max":
                    agg_expr = agg_col.max()
                elif config.aggregation == "median":
                    agg_expr = agg_col.median()
                else:
                    agg_expr = agg_col.sum()

                group_cols = [config.x_column]
                if config.color_column and config.color_column != config.x_column:
                    group_cols.append(config.color_column)

                result = df.group_by(group_cols).agg(agg_expr.alias(config.y_column))

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
