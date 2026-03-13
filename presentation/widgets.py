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
    st.markdown("### ➕ Add Visualization")

    if not data_schema:
        st.info("📁 Upload data first")
        return

    chart_types = [
        ("📊 Bar Chart", VisualizationType.BAR_CHART),
        ("📈 Line Chart", VisualizationType.LINE_CHART),
        ("🥧 Pie Chart", VisualizationType.PIE_CHART),
        ("📉 Area Chart", VisualizationType.AREA_CHART),
        ("⚬ Scatter Plot", VisualizationType.SCATTER_PLOT),
        ("▊ Histogram", VisualizationType.HISTOGRAM),
        ("📦 Box Plot", VisualizationType.BOX_PLOT),
        ("🔥 Heatmap", VisualizationType.HEATMAP),
        ("📋 Table", VisualizationType.TABLE),
        ("💳 Metric Card", VisualizationType.METRIC_CARD),
    ]

    for label, viz_type in chart_types:
        if st.button(label, key=f"widget_{viz_type.value}", use_container_width=True):
            # Store the selected type and show config dialog
            st.session_state.configuring_new_viz = viz_type
            st.rerun()


def render_visualization_config_dialog(
    viz_type: VisualizationType,
    data_schema: DataSchema,
    existing_config: Optional[VisualizationConfig] = None,
    on_save: Callable = None,
    on_cancel: Callable = None,
    is_new: bool = False,
) -> Optional[VisualizationConfig]:
    """
    Render a full configuration dialog for a visualization.

    Args:
        viz_type: Type of visualization to configure
        data_schema: Schema of available data
        existing_config: Existing configuration to edit (for edits)
        on_save: Callback when configuration is saved
        on_cancel: Callback when configuration is cancelled
        is_new: Whether this is a new visualization

    Returns:
        Configured VisualizationConfig or None
    """
    # Get column options
    numeric_cols = data_schema.get_numeric_columns()
    categorical_cols = data_schema.get_categorical_columns()
    datetime_cols = [
        c.name for c in data_schema.columns if c.data_type == ColumnType.DATETIME
    ]
    all_cols = data_schema.get_column_names()

    # Dialog header
    action = "Configure New" if is_new else "Edit"
    st.markdown(f"### {action} {viz_type.value.replace('_', ' ').title()}")
    st.markdown("---")

    config = None

    # Title input (for all types)
    default_title = existing_config.title if existing_config else ""
    title = st.text_input(
        "📊 Visualization Title",
        value=default_title,
        placeholder="Enter a title for this visualization",
        key="config_title_input",
    )

    # Configuration based on visualization type
    if viz_type == VisualizationType.TABLE:
        config = _configure_table_ui(title, all_cols, existing_config)

    elif viz_type == VisualizationType.METRIC_CARD:
        config = _configure_metric_card_ui(title, numeric_cols, existing_config)

    elif viz_type == VisualizationType.PIE_CHART:
        config = _configure_pie_chart_ui(
            title, all_cols, numeric_cols, categorical_cols, existing_config
        )

    elif viz_type == VisualizationType.BAR_CHART:
        config = _configure_bar_chart_ui(
            title, all_cols, numeric_cols, categorical_cols, existing_config
        )

    elif viz_type == VisualizationType.LINE_CHART:
        config = _configure_line_chart_ui(
            title,
            all_cols,
            numeric_cols,
            categorical_cols,
            datetime_cols,
            existing_config,
        )

    elif viz_type == VisualizationType.AREA_CHART:
        config = _configure_area_chart_ui(
            title, all_cols, numeric_cols, categorical_cols, existing_config
        )

    elif viz_type == VisualizationType.SCATTER_PLOT:
        config = _configure_scatter_plot_ui(
            title, numeric_cols, all_cols, existing_config
        )

    elif viz_type == VisualizationType.HISTOGRAM:
        config = _configure_histogram_ui(
            title, numeric_cols, categorical_cols, existing_config
        )

    elif viz_type == VisualizationType.BOX_PLOT:
        config = _configure_box_plot_ui(
            title, numeric_cols, categorical_cols, existing_config
        )

    elif viz_type == VisualizationType.HEATMAP:
        config = _configure_heatmap_ui(title, all_cols, numeric_cols, existing_config)

    else:
        # Default fallback
        config = _configure_default_ui(
            title, all_cols, numeric_cols, viz_type, existing_config
        )

    # Action buttons
    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("✓ Apply Configuration", type="primary", use_container_width=True):
            if on_save and config:
                on_save(config)
                return config

    with col2:
        if st.button("✗ Cancel", use_container_width=True):
            if on_cancel:
                on_cancel()

    return config


def _configure_table_ui(
    title: str, all_cols: List[str], existing: Optional[VisualizationConfig]
) -> VisualizationConfig:
    """Configure table visualization."""
    st.markdown("**📋 Table Configuration**")
    st.markdown("Select columns to display in the table:")

    # Get default selected columns
    default_cols = all_cols[:5]
    if existing:
        default_cols = []
        if existing.x_column:
            default_cols.append(existing.x_column)
        if existing.y_column and existing.y_column not in default_cols:
            default_cols.append(existing.y_column)

    selected_cols = st.multiselect(
        "Columns to Display", all_cols, default=default_cols, key="table_cols_select"
    )

    return VisualizationConfig(
        visualization_type=VisualizationType.TABLE,
        title=title if title else "Data Table",
        x_column=selected_cols[0] if selected_cols else None,
        y_column=selected_cols[1] if len(selected_cols) > 1 else None,
        color_column=selected_cols[2] if len(selected_cols) > 2 else None,
    )


def _configure_metric_card_ui(
    title: str, numeric_cols: List[str], existing: Optional[VisualizationConfig]
) -> VisualizationConfig:
    """Configure metric card visualization."""
    st.markdown("**💳 Metric Card Configuration**")

    if not numeric_cols:
        st.warning("⚠️ No numeric columns available. Upload data with numeric values.")
        return VisualizationConfig(
            visualization_type=VisualizationType.METRIC_CARD, title=title
        )

    col1, col2 = st.columns(2)

    with col1:
        default_idx = 0
        if existing and existing.y_column in numeric_cols:
            default_idx = numeric_cols.index(existing.y_column)

        y_column = st.selectbox(
            "📊 Value Column",
            numeric_cols,
            index=default_idx,
            key="metric_y_select",
            help="Select the numeric column to display",
        )

    with col2:
        aggregations = ["sum", "mean", "count", "min", "max"]
        default_agg = existing.aggregation if existing else "sum"
        default_agg_idx = (
            aggregations.index(default_agg) if default_agg in aggregations else 0
        )

        aggregation = st.selectbox(
            "📐 Aggregation",
            aggregations,
            index=default_agg_idx,
            key="metric_agg_select",
            help="How to aggregate the values",
        )

    return VisualizationConfig(
        visualization_type=VisualizationType.METRIC_CARD,
        title=title if title else f"{aggregation.title()} of {y_column}",
        y_column=y_column,
        aggregation=aggregation,
    )


def _configure_pie_chart_ui(
    title: str,
    all_cols: List[str],
    numeric_cols: List[str],
    categorical_cols: List[str],
    existing: Optional[VisualizationConfig],
) -> VisualizationConfig:
    """Configure pie chart visualization."""
    st.markdown("**🥧 Pie Chart Configuration**")

    # Labels (categories)
    label_cols = categorical_cols if categorical_cols else all_cols
    default_label_idx = 0
    if existing and existing.x_column in label_cols:
        default_label_idx = label_cols.index(existing.x_column)

    x_column = st.selectbox(
        "🏷️ Labels (Categories)",
        label_cols,
        index=default_label_idx,
        key="pie_labels_select",
        help="Column to use for pie slices",
    )

    # Values
    if numeric_cols:
        default_val_idx = 0
        if existing and existing.y_column in numeric_cols:
            default_val_idx = numeric_cols.index(existing.y_column)

        y_column = st.selectbox(
            "📊 Values",
            numeric_cols,
            index=default_val_idx,
            key="pie_values_select",
            help="Column to use for slice sizes",
        )
    else:
        y_column = None
        st.warning("⚠️ No numeric columns for values")

    # Aggregation
    col1, col2 = st.columns(2)
    with col1:
        aggregations = ["sum", "mean", "count"]
        default_agg = existing.aggregation if existing else "sum"
        default_agg_idx = (
            aggregations.index(default_agg) if default_agg in aggregations else 0
        )
        aggregation = st.selectbox(
            "Aggregation", aggregations, index=default_agg_idx, key="pie_agg"
        )

    with col2:
        show_legend = st.checkbox(
            "Show Legend",
            value=existing.show_legend if existing else True,
            key="pie_legend",
        )

    return VisualizationConfig(
        visualization_type=VisualizationType.PIE_CHART,
        title=title if title else f"{x_column} Distribution",
        x_column=x_column,
        y_column=y_column,
        aggregation=aggregation,
        show_legend=show_legend,
    )


def _configure_bar_chart_ui(
    title: str,
    all_cols: List[str],
    numeric_cols: List[str],
    categorical_cols: List[str],
    existing: Optional[VisualizationConfig],
) -> VisualizationConfig:
    """Configure bar chart visualization."""
    st.markdown("**📊 Bar Chart Configuration**")

    # X-Axis (Categories)
    x_cols = categorical_cols if categorical_cols else all_cols
    default_x_idx = 0
    if existing and existing.x_column in x_cols:
        default_x_idx = x_cols.index(existing.x_column)

    x_column = st.selectbox(
        "📊 X-Axis (Categories)",
        x_cols,
        index=default_x_idx,
        key="bar_x_select",
        help="Categories for the x-axis",
    )

    # Y-Axis (Values)
    if numeric_cols:
        default_y_idx = 0
        if existing and existing.y_column in numeric_cols:
            default_y_idx = numeric_cols.index(existing.y_column)

        y_column = st.selectbox(
            "📈 Y-Axis (Values)",
            numeric_cols,
            index=default_y_idx,
            key="bar_y_select",
            help="Numeric values for the y-axis",
        )
    else:
        y_column = None
        st.warning("⚠️ No numeric columns available")

    # Aggregation
    col1, col2 = st.columns(2)

    with col1:
        aggregations = ["sum", "mean", "count", "min", "max"]
        default_agg = existing.aggregation if existing else "sum"
        default_agg_idx = (
            aggregations.index(default_agg) if default_agg in aggregations else 0
        )
        aggregation = st.selectbox(
            "Aggregation", aggregations, index=default_agg_idx, key="bar_agg"
        )

    with col2:
        # Color by
        color_options = [None] + all_cols
        default_color_idx = 0
        if existing and existing.color_column:
            if existing.color_column in all_cols:
                default_color_idx = color_options.index(existing.color_column)

        color_column = st.selectbox(
            "🎨 Color by (Optional)",
            color_options,
            index=default_color_idx,
            key="bar_color",
            help="Group bars by this column",
        )

    show_legend = st.checkbox(
        "Show Legend",
        value=existing.show_legend if existing else True,
        key="bar_legend",
    )

    return VisualizationConfig(
        visualization_type=VisualizationType.BAR_CHART,
        title=title if title else f"{y_column} by {x_column}",
        x_column=x_column,
        y_column=y_column,
        color_column=color_column,
        aggregation=aggregation,
        show_legend=show_legend,
    )


def _configure_line_chart_ui(
    title: str,
    all_cols: List[str],
    numeric_cols: List[str],
    categorical_cols: List[str],
    datetime_cols: List[str],
    existing: Optional[VisualizationConfig],
) -> VisualizationConfig:
    """Configure line chart visualization."""
    st.markdown("**📈 Line Chart Configuration**")

    # X-Axis (prefer datetime or categorical)
    x_options = datetime_cols + categorical_cols + all_cols
    x_options = list(
        dict.fromkeys(x_options)
    )  # Remove duplicates while preserving order

    default_x_idx = 0
    if existing and existing.x_column in x_options:
        default_x_idx = x_options.index(existing.x_column)

    x_column = st.selectbox(
        "📊 X-Axis",
        x_options,
        index=default_x_idx,
        key="line_x_select",
        help="Values for the x-axis (time or categories work best)",
    )

    # Y-Axis
    if numeric_cols:
        default_y_idx = 0
        if existing and existing.y_column in numeric_cols:
            default_y_idx = numeric_cols.index(existing.y_column)

        y_column = st.selectbox(
            "📈 Y-Axis (Values)",
            numeric_cols,
            index=default_y_idx,
            key="line_y_select",
            help="Numeric values for the y-axis",
        )
    else:
        y_column = None
        st.warning("⚠️ No numeric columns available")

    col1, col2 = st.columns(2)

    with col1:
        aggregations = ["sum", "mean", "count", "min", "max"]
        default_agg = existing.aggregation if existing else "sum"
        default_agg_idx = (
            aggregations.index(default_agg) if default_agg in aggregations else 0
        )
        aggregation = st.selectbox(
            "Aggregation", aggregations, index=default_agg_idx, key="line_agg"
        )

    with col2:
        color_options = [None] + all_cols
        default_color_idx = 0
        if existing and existing.color_column:
            if existing.color_column in all_cols:
                default_color_idx = color_options.index(existing.color_column)

        color_column = st.selectbox(
            "🎨 Group by (Optional)",
            color_options,
            index=default_color_idx,
            key="line_color",
            help="Create separate lines for each group",
        )

    show_grid = st.checkbox(
        "Show Grid", value=existing.show_grid if existing else True, key="line_grid"
    )

    return VisualizationConfig(
        visualization_type=VisualizationType.LINE_CHART,
        title=title if title else f"{y_column} over {x_column}",
        x_column=x_column,
        y_column=y_column,
        color_column=color_column,
        aggregation=aggregation,
        show_grid=show_grid,
    )


def _configure_area_chart_ui(
    title: str,
    all_cols: List[str],
    numeric_cols: List[str],
    categorical_cols: List[str],
    existing: Optional[VisualizationConfig],
) -> VisualizationConfig:
    """Configure area chart visualization."""
    st.markdown("**📉 Area Chart Configuration**")

    x_cols = categorical_cols + all_cols
    x_cols = list(dict.fromkeys(x_cols))

    default_x_idx = 0
    if existing and existing.x_column in x_cols:
        default_x_idx = x_cols.index(existing.x_column)

    x_column = st.selectbox(
        "📊 X-Axis", x_cols, index=default_x_idx, key="area_x_select"
    )

    if numeric_cols:
        default_y_idx = 0
        if existing and existing.y_column in numeric_cols:
            default_y_idx = numeric_cols.index(existing.y_column)
        y_column = st.selectbox(
            "📈 Y-Axis", numeric_cols, index=default_y_idx, key="area_y_select"
        )
    else:
        y_column = None

    color_options = [None] + all_cols
    default_color_idx = 0
    if existing and existing.color_column:
        if existing.color_column in all_cols:
            default_color_idx = color_options.index(existing.color_column)
    color_column = st.selectbox(
        "🎨 Group by", color_options, index=default_color_idx, key="area_color"
    )

    return VisualizationConfig(
        visualization_type=VisualizationType.AREA_CHART,
        title=title if title else f"{y_column} over {x_column}",
        x_column=x_column,
        y_column=y_column,
        color_column=color_column,
        aggregation=existing.aggregation if existing else "sum",
    )


def _configure_scatter_plot_ui(
    title: str,
    numeric_cols: List[str],
    all_cols: List[str],
    existing: Optional[VisualizationConfig],
) -> VisualizationConfig:
    """Configure scatter plot visualization."""
    st.markdown("**⚬ Scatter Plot Configuration**")

    if len(numeric_cols) < 2:
        st.warning("⚠️ Need at least 2 numeric columns for scatter plot")

    col1, col2 = st.columns(2)

    with col1:
        default_x_idx = 0
        if existing and existing.x_column in numeric_cols:
            default_x_idx = numeric_cols.index(existing.x_column)
        x_column = st.selectbox(
            "📊 X-Axis",
            numeric_cols if numeric_cols else all_cols,
            index=default_x_idx,
            key="scatter_x",
        )

    with col2:
        default_y_idx = min(1, len(numeric_cols) - 1) if len(numeric_cols) > 1 else 0
        if existing and existing.y_column in numeric_cols:
            default_y_idx = numeric_cols.index(existing.y_column)
        y_column = st.selectbox(
            "📈 Y-Axis",
            numeric_cols if numeric_cols else all_cols,
            index=default_y_idx,
            key="scatter_y",
        )

    col3, col4 = st.columns(2)

    with col3:
        color_options = [None] + all_cols
        default_color_idx = 0
        if existing and existing.color_column:
            if existing.color_column in all_cols:
                default_color_idx = color_options.index(existing.color_column)
        color_column = st.selectbox(
            "🎨 Color by", color_options, index=default_color_idx, key="scatter_color"
        )

    with col4:
        size_options = [None] + numeric_cols
        default_size_idx = 0
        if existing and existing.size_column:
            if existing.size_column in numeric_cols:
                default_size_idx = size_options.index(existing.size_column)
        size_column = st.selectbox(
            "📐 Size by", size_options, index=default_size_idx, key="scatter_size"
        )

    return VisualizationConfig(
        visualization_type=VisualizationType.SCATTER_PLOT,
        title=title if title else f"{y_column} vs {x_column}",
        x_column=x_column,
        y_column=y_column,
        color_column=color_column,
        size_column=size_column,
    )


def _configure_histogram_ui(
    title: str,
    numeric_cols: List[str],
    categorical_cols: List[str],
    existing: Optional[VisualizationConfig],
) -> VisualizationConfig:
    """Configure histogram visualization."""
    st.markdown("**▊ Histogram Configuration**")

    if not numeric_cols:
        st.warning("⚠️ Need numeric columns for histogram")
        return VisualizationConfig(
            visualization_type=VisualizationType.HISTOGRAM, title=title
        )

    default_x_idx = 0
    if existing and existing.x_column in numeric_cols:
        default_x_idx = numeric_cols.index(existing.x_column)
    x_column = st.selectbox(
        "📊 Column", numeric_cols, index=default_x_idx, key="hist_x"
    )

    color_options = [None] + categorical_cols
    default_color_idx = 0
    if existing and existing.color_column:
        if existing.color_column in categorical_cols:
            default_color_idx = color_options.index(existing.color_column)
    color_column = st.selectbox(
        "🎨 Split by", color_options, index=default_color_idx, key="hist_color"
    )

    return VisualizationConfig(
        visualization_type=VisualizationType.HISTOGRAM,
        title=title if title else f"Distribution of {x_column}",
        x_column=x_column,
        color_column=color_column,
    )


def _configure_box_plot_ui(
    title: str,
    numeric_cols: List[str],
    categorical_cols: List[str],
    existing: Optional[VisualizationConfig],
) -> VisualizationConfig:
    """Configure box plot visualization."""
    st.markdown("**📦 Box Plot Configuration**")

    if not numeric_cols:
        st.warning("⚠️ Need numeric columns for box plot")
        return VisualizationConfig(
            visualization_type=VisualizationType.BOX_PLOT, title=title
        )

    col1, col2 = st.columns(2)

    with col1:
        default_y_idx = 0
        if existing and existing.y_column in numeric_cols:
            default_y_idx = numeric_cols.index(existing.y_column)
        y_column = st.selectbox(
            "📊 Values", numeric_cols, index=default_y_idx, key="box_y"
        )

    with col2:
        x_options = [None] + categorical_cols
        default_x_idx = 0
        if existing and existing.x_column:
            if existing.x_column in categorical_cols:
                default_x_idx = x_options.index(existing.x_column)
        x_column = st.selectbox(
            "📦 Group by", x_options, index=default_x_idx, key="box_x"
        )

    return VisualizationConfig(
        visualization_type=VisualizationType.BOX_PLOT,
        title=title if title else f"Distribution of {y_column}",
        x_column=x_column,
        y_column=y_column,
    )


def _configure_heatmap_ui(
    title: str,
    all_cols: List[str],
    numeric_cols: List[str],
    existing: Optional[VisualizationConfig],
) -> VisualizationConfig:
    """Configure heatmap visualization."""
    st.markdown("**🔥 Heatmap Configuration**")

    col1, col2 = st.columns(2)

    with col1:
        default_x_idx = 0
        if existing and existing.x_column in all_cols:
            default_x_idx = all_cols.index(existing.x_column)
        x_column = st.selectbox(
            "📊 X-Axis", all_cols, index=default_x_idx, key="heat_x"
        )

    with col2:
        y_options = [c for c in all_cols if c != x_column]
        default_y_idx = 0
        if existing and existing.y_column in y_options:
            default_y_idx = y_options.index(existing.y_column)
        y_column = st.selectbox(
            "📈 Y-Axis", y_options, index=default_y_idx, key="heat_y"
        )

    default_color_idx = 0
    if existing and existing.color_column in numeric_cols:
        default_color_idx = numeric_cols.index(existing.color_column)
    color_column = st.selectbox(
        "🎨 Values",
        numeric_cols if numeric_cols else all_cols,
        index=default_color_idx,
        key="heat_color",
    )

    return VisualizationConfig(
        visualization_type=VisualizationType.HEATMAP,
        title=title if title else f"Heatmap",
        x_column=x_column,
        y_column=y_column,
        color_column=color_column,
    )


def _configure_default_ui(
    title: str,
    all_cols: List[str],
    numeric_cols: List[str],
    viz_type: VisualizationType,
    existing: Optional[VisualizationConfig],
) -> VisualizationConfig:
    """Default configuration fallback."""
    st.markdown("**⚙️ Configuration**")

    col1, col2 = st.columns(2)

    with col1:
        default_x_idx = 0
        if existing and existing.x_column in all_cols:
            default_x_idx = all_cols.index(existing.x_column)
        x_column = st.selectbox(
            "📊 X-Axis", all_cols, index=default_x_idx, key="default_x"
        )

    with col2:
        y_options = numeric_cols if numeric_cols else all_cols
        default_y_idx = 0
        if existing and existing.y_column in y_options:
            default_y_idx = y_options.index(existing.y_column)
        y_column = st.selectbox(
            "📈 Y-Axis", y_options, index=default_y_idx, key="default_y"
        )

    return VisualizationConfig(
        visualization_type=viz_type, title=title, x_column=x_column, y_column=y_column
    )


def render_data_preview(data_schema: DataSchema, df: pl.DataFrame) -> None:
    """Render a preview of the loaded data."""
    st.markdown(f"**File:** {data_schema.file_name}")
    st.markdown(
        f"**Rows:** {data_schema.row_count:,} | **Columns:** {len(data_schema.columns)}"
    )

    with st.expander("📋 Column Types", expanded=False):
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

    with st.expander("📊 Sample Data", expanded=False):
        st.dataframe(df.head(10).to_pandas(), use_container_width=True)
