"""
Widgets Component - Visualization configuration UI.
"""

from typing import Optional, List, Callable
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
    """Render widget palette for adding visualizations."""
    st.markdown("### 📊 Add Visualization")

    chart_types = [
        ("📊 Bar", VisualizationType.BAR_CHART),
        ("📈 Line", VisualizationType.LINE_CHART),
        ("🥧 Pie", VisualizationType.PIE_CHART),
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
) -> Optional[VisualizationConfig]:
    """Render configuration form for a visualization."""
    st.markdown(f"### Configure {viz_type.value.replace('_', ' ').title()}")

    numeric_cols = data_schema.get_numeric_columns()
    all_cols = data_schema.get_column_names()

    title = st.text_input(
        "Title", value=existing_config.title if existing_config else ""
    )

    col1, col2 = st.columns(2)

    with col1:
        x_column = st.selectbox("X Column", all_cols, key="cfg_x")

    with col2:
        y_column = st.selectbox(
            "Y Column", numeric_cols if numeric_cols else all_cols, key="cfg_y"
        )

    return VisualizationConfig(
        visualization_type=viz_type,
        title=title,
        x_column=x_column,
        y_column=y_column,
        aggregation="sum",
    )


def render_data_preview(data_schema: DataSchema, df: pl.DataFrame) -> None:
    """Render a preview of the loaded data."""
    st.markdown(f"**File:** {data_schema.file_name}")
    st.markdown(
        f"**Rows:** {data_schema.row_count:,} | **Columns:** {len(data_schema.columns)}"
    )

    st.markdown("#### Column Types")
    for col in data_schema.columns:
        icon = {
            ColumnType.NUMERIC: "🔢",
            ColumnType.CATEGORICAL: "📝",
            ColumnType.DATETIME: "📅",
        }.get(col.data_type, "❓")
        st.markdown(f"{icon} **{col.name}** - {col.data_type.value}")

    st.markdown("#### Sample Data")
    st.dataframe(df.head(10).to_pandas(), use_container_width=True)
