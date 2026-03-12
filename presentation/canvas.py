"""
Canvas Component - Main slide editing area.
"""

from typing import Optional, List, Callable, Any
import streamlit as st
import polars as pl

from domain.entities import Slide, Visualization, VisualizationType, VisualizationConfig


def render_canvas(
    slide: Optional[Slide],
    data_service: Any,
    analysis_id: str,
    on_update_visualization: Callable,
    on_delete_visualization: Callable,
    on_add_comment: Callable,
    data_schema: Any = None,
) -> None:
    """Render the main canvas for slide editing."""
    if not slide:
        st.info("👆 Select or create a slide to start editing")
        return

    col1, col2 = st.columns([4, 1])
    with col1:
        new_title = st.text_input(
            "Slide Title", value=slide.title, key=f"slide_title_{slide.id}"
        )
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        st.caption(f"{len(slide.visualizations)} items")

    df = data_service.get_cached_data(analysis_id)
    if df is None:
        st.warning("⚠️ No data loaded. Please upload an XLSX file.")
        return

    if not slide.visualizations:
        st.markdown(
            """
        <div style='border: 2px dashed #ccc; border-radius: 10px; padding: 60px; text-align: center; color: #888; margin: 20px 0;'>
            <h3>📊 Empty Slide</h3>
            <p>Add visualizations from the toolbar to get started</p>
        </div>
        """,
            unsafe_allow_html=True,
        )
    else:
        from infrastructure.chart_factory import ChartFactory

        chart_factory = ChartFactory()

        for idx, viz in enumerate(slide.visualizations):
            render_visualization(
                viz=viz,
                df=df,
                chart_factory=chart_factory,
                index=idx,
                slide_id=slide.id,
                on_update=on_update_visualization,
                on_delete=on_delete_visualization,
                on_add_comment=on_add_comment,
                data_schema=data_schema,
            )


def render_visualization(
    viz: Visualization,
    df: pl.DataFrame,
    chart_factory: Any,
    index: int,
    slide_id: str,
    on_update: Callable,
    on_delete: Callable,
    on_add_comment: Callable,
    data_schema: Any = None,
) -> None:
    """Render a single visualization with edit capability."""
    with st.container():
        col1, col2, col3 = st.columns([4, 1, 1])

        with col1:
            title = (
                viz.config.title
                if viz.config and viz.config.title
                else f"Visualization {index + 1}"
            )
            st.markdown(f"**{title}**")

        with col2:
            if st.button("✏️", key=f"edit_{viz.id}", help="Edit visualization"):
                st.session_state.editing_viz_id = viz.id

        with col3:
            if st.button("🗑️", key=f"delete_{viz.id}", help="Delete visualization"):
                on_delete(slide_id, viz.id)
                st.rerun()

        # Show configuration editor if this viz is being edited
        if st.session_state.get("editing_viz_id") == viz.id and data_schema:
            new_config = render_visualization_editor(viz.config, data_schema, viz.id)
            if new_config:
                on_update(slide_id, viz.id, new_config)
                st.session_state.editing_viz_id = None
                st.rerun()

        # Render the visualization
        if viz.config:
            try:
                if viz.config.visualization_type == VisualizationType.TABLE:
                    render_table(viz, df)
                elif viz.config.visualization_type == VisualizationType.METRIC_CARD:
                    render_metric_card(viz, df)
                else:
                    fig = chart_factory.create_chart(df, viz.config)
                    st.plotly_chart(
                        fig, use_container_width=True, key=f"chart_{viz.id}"
                    )
            except Exception as e:
                st.error(f"Error rendering visualization: {str(e)}")

        if viz.comment:
            st.info(f"💬 {viz.comment}")

        with st.expander("Add Comment"):
            comment = st.text_area(
                "Comment", value=viz.comment, key=f"comment_{viz.id}", height=60
            )
            if st.button("Save Comment", key=f"save_comment_{viz.id}"):
                on_add_comment(slide_id, viz.id, comment)
                st.rerun()

        st.markdown("---")


def render_visualization_editor(
    current_config: VisualizationConfig, data_schema: Any, viz_id: str
) -> Optional[VisualizationConfig]:
    """
    Render an editor for visualization configuration.
    Allows user to select which columns to use for each axis.
    """
    st.markdown("### ⚙️ Configure Visualization")

    # Get column lists
    numeric_cols = data_schema.get_numeric_columns()
    categorical_cols = data_schema.get_categorical_columns()
    all_cols = data_schema.get_column_names()

    # Title
    title = st.text_input(
        "Title",
        value=current_config.title if current_config else "",
        key=f"editor_title_{viz_id}",
    )

    config = None
    viz_type = (
        current_config.visualization_type
        if current_config
        else VisualizationType.BAR_CHART
    )

    # Common aggregation options
    aggregations = ["sum", "mean", "count", "min", "max"]

    # Configuration based on visualization type
    if viz_type == VisualizationType.TABLE:
        st.markdown("**Table Configuration**")

        # Multi-select for columns
        default_cols = []
        if current_config:
            if current_config.x_column:
                default_cols.append(current_config.x_column)
            if current_config.y_column and current_config.y_column not in default_cols:
                default_cols.append(current_config.y_column)

        if not default_cols:
            default_cols = all_cols[:5]

        selected_cols = st.multiselect(
            "Select Columns to Display",
            all_cols,
            default=default_cols,
            key=f"editor_table_cols_{viz_id}",
        )

        if st.button("✓ Apply Changes", key=f"apply_table_{viz_id}", type="primary"):
            config = VisualizationConfig(
                visualization_type=viz_type,
                title=title,
                x_column=selected_cols[0] if selected_cols else None,
                y_column=selected_cols[1] if len(selected_cols) > 1 else None,
                color_column=selected_cols[2] if len(selected_cols) > 2 else None,
            )

    elif viz_type == VisualizationType.METRIC_CARD:
        st.markdown("**Metric Card Configuration**")

        col1, col2 = st.columns(2)

        with col1:
            y_column = st.selectbox(
                "Value Column (Numeric)",
                numeric_cols if numeric_cols else all_cols,
                index=numeric_cols.index(current_config.y_column)
                if current_config and current_config.y_column in numeric_cols
                else 0,
                key=f"editor_metric_y_{viz_id}",
            )

        with col2:
            current_agg = current_config.aggregation if current_config else "sum"
            aggregation = st.selectbox(
                "Aggregation",
                aggregations,
                index=aggregations.index(current_agg)
                if current_agg in aggregations
                else 0,
                key=f"editor_metric_agg_{viz_id}",
            )

        if st.button("✓ Apply Changes", key=f"apply_metric_{viz_id}", type="primary"):
            config = VisualizationConfig(
                visualization_type=viz_type,
                title=title,
                y_column=y_column,
                aggregation=aggregation,
            )

    elif viz_type == VisualizationType.PIE_CHART:
        st.markdown("**Pie Chart Configuration**")

        col1, col2 = st.columns(2)

        with col1:
            label_cols = categorical_cols if categorical_cols else all_cols
            x_column = st.selectbox(
                "Labels (Categories)",
                label_cols,
                index=label_cols.index(current_config.x_column)
                if current_config and current_config.x_column in label_cols
                else 0,
                key=f"editor_pie_x_{viz_id}",
            )

        with col2:
            y_column = st.selectbox(
                "Values (Numeric)",
                numeric_cols if numeric_cols else all_cols,
                index=numeric_cols.index(current_config.y_column)
                if current_config and current_config.y_column in numeric_cols
                else 0,
                key=f"editor_pie_y_{viz_id}",
            )

        show_legend = st.checkbox(
            "Show Legend",
            value=current_config.show_legend if current_config else True,
            key=f"editor_pie_legend_{viz_id}",
        )

        if st.button("✓ Apply Changes", key=f"apply_pie_{viz_id}", type="primary"):
            config = VisualizationConfig(
                visualization_type=viz_type,
                title=title,
                x_column=x_column,
                y_column=y_column,
                show_legend=show_legend,
            )

    elif viz_type == VisualizationType.BAR_CHART:
        st.markdown("**Bar Chart Configuration**")

        col1, col2 = st.columns(2)

        with col1:
            x_cols = categorical_cols if categorical_cols else all_cols
            x_column = st.selectbox(
                "X-Axis (Categories)",
                x_cols,
                index=x_cols.index(current_config.x_column)
                if current_config and current_config.x_column in x_cols
                else 0,
                key=f"editor_bar_x_{viz_id}",
            )

        with col2:
            y_column = st.selectbox(
                "Y-Axis (Values)",
                numeric_cols if numeric_cols else all_cols,
                index=numeric_cols.index(current_config.y_column)
                if current_config and current_config.y_column in numeric_cols
                else 0,
                key=f"editor_bar_y_{viz_id}",
            )

        col3, col4 = st.columns(2)

        with col3:
            current_agg = current_config.aggregation if current_config else "sum"
            aggregation = st.selectbox(
                "Aggregation",
                aggregations,
                index=aggregations.index(current_agg)
                if current_agg in aggregations
                else 0,
                key=f"editor_bar_agg_{viz_id}",
            )

        with col4:
            color_column = st.selectbox(
                "Color by (Optional)",
                [None] + all_cols,
                index=0
                if not current_config or not current_config.color_column
                else ([None] + all_cols).index(current_config.color_column),
                key=f"editor_bar_color_{viz_id}",
            )

        show_legend = st.checkbox(
            "Show Legend",
            value=current_config.show_legend if current_config else True,
            key=f"editor_bar_legend_{viz_id}",
        )

        if st.button("✓ Apply Changes", key=f"apply_bar_{viz_id}", type="primary"):
            config = VisualizationConfig(
                visualization_type=viz_type,
                title=title,
                x_column=x_column,
                y_column=y_column,
                aggregation=aggregation,
                color_column=color_column,
                show_legend=show_legend,
            )

    elif viz_type == VisualizationType.LINE_CHART:
        st.markdown("**Line Chart Configuration**")

        col1, col2 = st.columns(2)

        with col1:
            x_column = st.selectbox(
                "X-Axis",
                all_cols,
                index=all_cols.index(current_config.x_column)
                if current_config and current_config.x_column in all_cols
                else 0,
                key=f"editor_line_x_{viz_id}",
            )

        with col2:
            y_column = st.selectbox(
                "Y-Axis (Numeric)",
                numeric_cols if numeric_cols else all_cols,
                index=numeric_cols.index(current_config.y_column)
                if current_config and current_config.y_column in numeric_cols
                else 0,
                key=f"editor_line_y_{viz_id}",
            )

        col3, col4 = st.columns(2)

        with col3:
            current_agg = current_config.aggregation if current_config else "sum"
            aggregation = st.selectbox(
                "Aggregation",
                aggregations,
                index=aggregations.index(current_agg)
                if current_agg in aggregations
                else 0,
                key=f"editor_line_agg_{viz_id}",
            )

        with col4:
            color_column = st.selectbox(
                "Group by (Optional)",
                [None] + all_cols,
                index=0
                if not current_config or not current_config.color_column
                else ([None] + all_cols).index(current_config.color_column),
                key=f"editor_line_color_{viz_id}",
            )

        if st.button("✓ Apply Changes", key=f"apply_line_{viz_id}", type="primary"):
            config = VisualizationConfig(
                visualization_type=viz_type,
                title=title,
                x_column=x_column,
                y_column=y_column,
                aggregation=aggregation,
                color_column=color_column,
            )

    elif viz_type == VisualizationType.AREA_CHART:
        st.markdown("**Area Chart Configuration**")

        col1, col2 = st.columns(2)

        with col1:
            x_column = st.selectbox(
                "X-Axis",
                all_cols,
                index=all_cols.index(current_config.x_column)
                if current_config and current_config.x_column in all_cols
                else 0,
                key=f"editor_area_x_{viz_id}",
            )

        with col2:
            y_column = st.selectbox(
                "Y-Axis (Numeric)",
                numeric_cols if numeric_cols else all_cols,
                index=numeric_cols.index(current_config.y_column)
                if current_config and current_config.y_column in numeric_cols
                else 0,
                key=f"editor_area_y_{viz_id}",
            )

        color_column = st.selectbox(
            "Group by (Optional)",
            [None] + all_cols,
            index=0
            if not current_config or not current_config.color_column
            else ([None] + all_cols).index(current_config.color_column),
            key=f"editor_area_color_{viz_id}",
        )

        if st.button("✓ Apply Changes", key=f"apply_area_{viz_id}", type="primary"):
            config = VisualizationConfig(
                visualization_type=viz_type,
                title=title,
                x_column=x_column,
                y_column=y_column,
                color_column=color_column,
                aggregation=current_config.aggregation if current_config else "sum",
            )

    elif viz_type == VisualizationType.SCATTER_PLOT:
        st.markdown("**Scatter Plot Configuration**")

        col1, col2 = st.columns(2)

        with col1:
            x_column = st.selectbox(
                "X-Axis (Numeric)",
                numeric_cols if numeric_cols else all_cols,
                index=numeric_cols.index(current_config.x_column)
                if current_config and current_config.x_column in numeric_cols
                else 0,
                key=f"editor_scatter_x_{viz_id}",
            )

        with col2:
            y_options = (
                [c for c in numeric_cols if c != x_column] if numeric_cols else all_cols
            )
            y_column = st.selectbox(
                "Y-Axis (Numeric)",
                y_options,
                index=y_options.index(current_config.y_column)
                if current_config and current_config.y_column in y_options
                else 0,
                key=f"editor_scatter_y_{viz_id}",
            )

        col3, col4 = st.columns(2)

        with col3:
            color_options = categorical_cols + numeric_cols
            color_column = st.selectbox(
                "Color by (Optional)",
                [None] + color_options,
                index=0
                if not current_config or not current_config.color_column
                else ([None] + color_options).index(current_config.color_column),
                key=f"editor_scatter_color_{viz_id}",
            )

        with col4:
            size_column = st.selectbox(
                "Size by (Optional)",
                [None] + numeric_cols,
                index=0
                if not current_config or not current_config.size_column
                else ([None] + numeric_cols).index(current_config.size_column),
                key=f"editor_scatter_size_{viz_id}",
            )

        if st.button("✓ Apply Changes", key=f"apply_scatter_{viz_id}", type="primary"):
            config = VisualizationConfig(
                visualization_type=viz_type,
                title=title,
                x_column=x_column,
                y_column=y_column,
                color_column=color_column,
                size_column=size_column,
            )

    elif viz_type == VisualizationType.HISTOGRAM:
        st.markdown("**Histogram Configuration**")

        x_column = st.selectbox(
            "Column (Numeric)",
            numeric_cols if numeric_cols else all_cols,
            index=numeric_cols.index(current_config.x_column)
            if current_config and current_config.x_column in numeric_cols
            else 0,
            key=f"editor_hist_x_{viz_id}",
        )

        color_column = st.selectbox(
            "Split by (Optional)",
            [None] + categorical_cols,
            index=0
            if not current_config or not current_config.color_column
            else ([None] + categorical_cols).index(current_config.color_column),
            key=f"editor_hist_color_{viz_id}",
        )

        if st.button("✓ Apply Changes", key=f"apply_hist_{viz_id}", type="primary"):
            config = VisualizationConfig(
                visualization_type=viz_type,
                title=title,
                x_column=x_column,
                color_column=color_column,
            )

    elif viz_type == VisualizationType.BOX_PLOT:
        st.markdown("**Box Plot Configuration**")

        col1, col2 = st.columns(2)

        with col1:
            y_column = st.selectbox(
                "Values (Numeric)",
                numeric_cols if numeric_cols else all_cols,
                index=numeric_cols.index(current_config.y_column)
                if current_config and current_config.y_column in numeric_cols
                else 0,
                key=f"editor_box_y_{viz_id}",
            )

        with col2:
            x_column = st.selectbox(
                "Group by (Optional)",
                [None] + categorical_cols,
                index=0
                if not current_config or not current_config.x_column
                else ([None] + categorical_cols).index(current_config.x_column),
                key=f"editor_box_x_{viz_id}",
            )

        color_column = st.selectbox(
            "Color by (Optional)",
            [None] + categorical_cols,
            index=0
            if not current_config or not current_config.color_column
            else ([None] + categorical_cols).index(current_config.color_column),
            key=f"editor_box_color_{viz_id}",
        )

        if st.button("✓ Apply Changes", key=f"apply_box_{viz_id}", type="primary"):
            config = VisualizationConfig(
                visualization_type=viz_type,
                title=title,
                x_column=x_column,
                y_column=y_column,
                color_column=color_column,
            )

    else:
        # Default configuration
        st.markdown("**Configuration**")

        col1, col2 = st.columns(2)

        with col1:
            x_column = st.selectbox(
                "X-Axis", all_cols, key=f"editor_default_x_{viz_id}"
            )

        with col2:
            y_column = st.selectbox(
                "Y-Axis",
                numeric_cols if numeric_cols else all_cols,
                key=f"editor_default_y_{viz_id}",
            )

        if st.button("✓ Apply Changes", key=f"apply_default_{viz_id}", type="primary"):
            config = VisualizationConfig(
                visualization_type=viz_type,
                title=title,
                x_column=x_column,
                y_column=y_column,
            )

    # Cancel button
    if st.button("✗ Cancel", key=f"cancel_edit_{viz_id}"):
        st.session_state.editing_viz_id = None
        st.rerun()

    return config


def render_table(viz: Visualization, df: pl.DataFrame) -> None:
    """Render a table visualization."""
    config = viz.config
    if not config:
        return

    if config.x_column and config.y_column:
        columns_to_show = [config.x_column, config.y_column]
        if config.color_column:
            columns_to_show.append(config.color_column)
    else:
        columns_to_show = df.columns[:10]

    valid_columns = [c for c in columns_to_show if c in df.columns]
    if valid_columns:
        table_df = df.select(valid_columns)
        st.dataframe(
            table_df.head(100).to_pandas(), use_container_width=True, height=300
        )
    else:
        st.warning("No valid columns selected")


def render_metric_card(viz: Visualization, df: pl.DataFrame) -> None:
    """Render a metric card visualization."""
    config = viz.config
    if not config or not config.y_column:
        st.warning("Please select a column for the metric")
        return

    if config.y_column not in df.columns:
        st.warning(f"Column '{config.y_column}' not found in data")
        return

    col = df[config.y_column]

    if config.aggregation == "mean":
        value = col.mean()
        label = "Average"
    elif config.aggregation == "sum":
        value = col.sum()
        label = "Total"
    elif config.aggregation == "count":
        value = col.count()
        label = "Count"
    elif config.aggregation == "min":
        value = col.min()
        label = "Minimum"
    elif config.aggregation == "max":
        value = col.max()
        label = "Maximum"
    else:
        value = col.sum()
        label = "Total"

    if isinstance(value, float):
        if abs(value) >= 1_000_000:
            formatted_value = f"{value / 1_000_000:.2f}M"
        elif abs(value) >= 1_000:
            formatted_value = f"{value / 1_000:.2f}K"
        else:
            formatted_value = f"{value:.2f}"
    else:
        formatted_value = f"{value:,}"

    st.markdown(
        f"""
    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px; padding: 30px; color: white; text-align: center; margin: 10px 0;'>
        <h1 style='margin: 0; font-size: 48px;'>{formatted_value}</h1>
        <p style='margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;'>{config.title or f"{label} of {config.y_column}"}</p>
    </div>
    """,
        unsafe_allow_html=True,
    )


def render_slide_navigator(
    slides: List[Slide],
    current_slide_id: str,
    on_slide_change: Callable,
    on_add_slide: Callable,
    on_delete_slide: Callable,
) -> None:
    """Render the slide navigation bar."""
    st.markdown("---")

    col1, col2, col3 = st.columns([1, 3, 1])

    with col1:
        if st.button("➕ New Slide", use_container_width=True):
            on_add_slide()
            st.rerun()

    with col2:
        if slides:
            cols = st.columns(min(len(slides), 8))
            for i, slide in enumerate(slides):
                with cols[i % 8]:
                    is_current = slide.id == current_slide_id
                    title = (
                        slide.title[:10] + "..."
                        if len(slide.title) > 10
                        else slide.title
                    )

                    if st.button(
                        f"{i + 1}. {title}",
                        key=f"nav_slide_{slide.id}",
                        use_container_width=True,
                        type="primary" if is_current else "secondary",
                    ):
                        on_slide_change(slide.id)
                        st.rerun()

    with col3:
        if len(slides) > 1:
            if st.button("🗑️ Delete Slide", use_container_width=True):
                on_delete_slide(current_slide_id)
                st.rerun()
