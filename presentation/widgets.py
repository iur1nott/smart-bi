"""
Widgets Component - Visualization widgets and configuration UI.
"""

from typing import Optional, Dict, Any, List, Callable
import streamlit as st
import polars as pl

from domain.entities import (
    DataSchema,
    ColumnType,
    VisualizationConfig,
    VisualizationType,
)


def render_widget_palette(
    data_schema: Optional[DataSchema], on_add_visualization: Callable
) -> None:
    """Render the widget palette for adding visualizations."""
    st.markdown("### 📊 Add Visualization")

    chart_types = [
        ("📊 Bar", VisualizationType.BAR_CHART),
        ("📈 Line", VisualizationType.LINE_CHART),
        ("🥧 Pie", VisualizationType.PIE_CHART),
        ("📉 Area", VisualizationType.AREA_CHART),
        ("⚬ Scatter", VisualizationType.SCATTER_PLOT),
        ("▊ Histogram", VisualizationType.HISTOGRAM),
        ("📋 Table", VisualizationType.TABLE),
        ("💳 Metric", VisualizationType.METRIC_CARD),
    ]

    cols = st.columns(3)
    for i, (label, viz_type) in enumerate(chart_types):
        with cols[i % 3]:
            if st.button(
                label, key=f"widget_{viz_type.value}", use_container_width=True
            ):
                on_add_visualization(viz_type)


def render_visualization_config(
    viz_type: VisualizationType,
    data_schema: DataSchema,
    existing_config: Optional[VisualizationConfig] = None,
    on_save: Optional[Callable] = None,
) -> Optional[VisualizationConfig]:
    """Render configuration form for a visualization."""
    st.markdown(f"### Configure {viz_type.value.replace('_', ' ').title()}")

    numeric_cols = data_schema.get_numeric_columns()
    categorical_cols = data_schema.get_categorical_columns()
    all_cols = data_schema.get_column_names()

    title = st.text_input(
        "Title",
        value=existing_config.title if existing_config else "",
        key="config_title",
    )

    config = None

    if viz_type == VisualizationType.TABLE:
        selected_cols = st.multiselect(
            "Select Columns", all_cols, default=all_cols[:5], key="table_columns"
        )
        config = VisualizationConfig(
            visualization_type=viz_type,
            title=title,
            x_column=selected_cols[0] if selected_cols else None,
            y_column=selected_cols[1] if len(selected_cols) > 1 else None,
        )

    elif viz_type == VisualizationType.METRIC_CARD:
        y_column = st.selectbox(
            "Value Column", numeric_cols if numeric_cols else all_cols, key="metric_y"
        )
        aggregation = st.selectbox(
            "Aggregation", ["sum", "mean", "count", "min", "max"], key="metric_agg"
        )
        config = VisualizationConfig(
            visualization_type=viz_type,
            title=title,
            y_column=y_column,
            aggregation=aggregation,
        )

    elif viz_type == VisualizationType.PIE_CHART:
        x_column = st.selectbox(
            "Labels (Categories)",
            categorical_cols if categorical_cols else all_cols,
            key="pie_x",
        )
        y_column = st.selectbox(
            "Values", numeric_cols if numeric_cols else all_cols, key="pie_y"
        )
        config = VisualizationConfig(
            visualization_type=viz_type,
            title=title,
            x_column=x_column,
            y_column=y_column,
        )

    else:
        x_column = st.selectbox(
            "X-Axis", categorical_cols if categorical_cols else all_cols, key="cfg_x"
        )
        y_column = st.selectbox(
            "Y-Axis", numeric_cols if numeric_cols else all_cols, key="cfg_y"
        )
        aggregation = st.selectbox(
            "Aggregation", ["sum", "mean", "count", "min", "max"], key="cfg_agg"
        )
        config = VisualizationConfig(
            visualization_type=viz_type,
            title=title,
            x_column=x_column,
            y_column=y_column,
            aggregation=aggregation,
        )

    return config


def render_data_preview(data_schema: DataSchema, df: pl.DataFrame) -> None:
    """Render a preview of the loaded data."""
    st.markdown(f"**File:** {data_schema.file_name}")
    st.markdown(
        f"**Rows:** {data_schema.row_count:,} | **Columns:** {len(data_schema.columns)}"
    )

    st.markdown("#### Column Types")
    for col in data_schema.columns:
        type_icon = {
            ColumnType.NUMERIC: "🔢",
            ColumnType.CATEGORICAL: "📝",
            ColumnType.DATETIME: "📅",
            ColumnType.TEXT: "📄",
            ColumnType.BOOLEAN: "✓",
            ColumnType.UNKNOWN: "❓",
        }.get(col.data_type, "❓")

        st.markdown(f"{type_icon} **{col.name}** - {col.data_type.value}")

        if col.data_type == ColumnType.NUMERIC and col.statistics:
            stats = col.statistics
            min_val = stats.get("min", "N/A")
            max_val = stats.get("max", "N/A")
            mean_val = stats.get("mean", "N/A")
            if isinstance(min_val, (int, float)):
                st.caption(
                    f"Min: {min_val:.2f} | Max: {max_val:.2f} | Mean: {mean_val:.2f}"
                )

    st.markdown("#### Sample Data")
    st.dataframe(df.head(10).to_pandas(), use_container_width=True)
