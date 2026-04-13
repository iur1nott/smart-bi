"""
Canvas Component - Main slide editing area.
"""

from typing import Optional, List, Callable
import streamlit as st
import polars as pl

from domain.entities import Slide, Visualization, VisualizationConfig, VisualizationType


def render_canvas(
    slide: Optional[Slide],
    data_service,
    analysis_id: str,
    on_update_visualization: Callable,
    on_delete_visualization: Callable,
    on_add_comment: Callable,
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
            <p>Add visualizations from the right panel to get started</p>
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
            )


def render_visualization(
    viz: Visualization,
    df: pl.DataFrame,
    chart_factory,
    index: int,
    slide_id: str,
    on_update: Callable,
    on_delete: Callable,
    on_add_comment: Callable,
) -> None:
    """Render a single visualization."""
    with st.container():
        # Header with title and actions
        col1, col2, col3 = st.columns([4, 1, 1])

        with col1:
            title = (
                viz.config.title
                if viz.config and viz.config.title
                else f"Visualization {index + 1}"
            )
            st.markdown(f"**{title}**")

        with col2:
            # Edit button - opens config dialog
            if st.button("✏️", key=f"edit_{viz.id}", help="Configure visualization"):
                st.session_state.editing_viz_id = viz.id
                st.session_state.editing_slide_id = slide_id

        with col3:
            # Delete button
            if st.button("🗑️", key=f"delete_{viz.id}", help="Delete visualization"):
                on_delete(slide_id, viz.id)
                st.rerun()

        # Show column info
        if viz.config:
            col_info = []
            if viz.config.x_column:
                col_info.append(f"X: {viz.config.x_column}")
            if viz.config.y_columns:
                col_info.append(f"Y: {viz.config.y_columns}")
            if viz.config.color_column:
                col_info.append(f"Color: {viz.config.color_column}")
            if col_info:
                st.caption(" | ".join(col_info))

        # Render the chart or table
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

        # Comment section
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

    table_df = df.select([c for c in columns_to_show if c in df.columns])

    # Apply aggregation if specified
    if config.x_column and config.y_column and config.aggregation:
        try:
            if config.aggregation == "mean":
                table_df = table_df.group_by(config.x_column).agg(
                    pl.col(config.y_column).mean().alias(config.y_column)
                )
            elif config.aggregation == "sum":
                table_df = table_df.group_by(config.x_column).agg(
                    pl.col(config.y_column).sum().alias(config.y_column)
                )
            elif config.aggregation == "count":
                table_df = table_df.group_by(config.x_column).agg(
                    pl.col(config.y_column).count().alias(config.y_column)
                )
        except:
            pass

    st.dataframe(table_df.head(100).to_pandas(), use_container_width=True, height=300)


def render_metric_card(viz: Visualization, df: pl.DataFrame) -> None:
    """Render a metric card visualization."""
    config = viz.config
    if not config or not config.y_column:
        st.warning("Please select a column for the metric")
        return

    try:
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
    except Exception as e:
        st.error(f"Error calculating metric: {str(e)}")


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
            if st.button("🗑️ Delete", use_container_width=True):
                on_delete_slide(current_slide_id)
                st.rerun()
