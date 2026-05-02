"""
Canvas Component - Main dashboard editing area with visualization rendering.
Updated for new schema with dashboards and visualizations.
"""

from typing import Any, Callable, Dict, List, Optional

import polars as pl
import streamlit as st

from domain.entities import (
    FileSheet,
    Visualization,
    VisualizationConfig,
    VisualizationType,
)


def render_canvas(
    visualizations: List[Visualization],
    data_service: Any,
    sheet_id: str,
    on_update_visualization: Callable[[str, VisualizationConfig], None],
    on_delete_visualization: Callable[[str], None],
    on_add_comment: Callable[[str, str], None],
    sheet: Optional[FileSheet] = None,
) -> None:
    """
    Render the main canvas for dashboard editing.

    Args:
        visualizations: List of visualizations to render
        data_service: Service for data operations
        sheet_id: ID of the current sheet for data
        on_update_visualization: Callback when visualization is updated
        on_delete_visualization: Callback when visualization is deleted
        on_add_comment: Callback when comment is added
        sheet: Current sheet metadata
    """
    df = data_service.get_cached_sheet(sheet_id)

    if df is None:
        st.markdown(
            """
            <div style='
                background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%);
                border-radius: 12px;
                padding: 24px;
                text-align: center;
                margin: 20px 0;
            '>
                <div style='font-size: 32px; margin-bottom: 10px;'>⚠️</div>
                <h4 style='color: #92400E; margin: 0;'>Nenhum dado carregado</h4>
                <p style='color: #B45309; margin-top: 8px;'>Faça upload de um arquivo XLSX para começar</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    # Render dashboard header
    st.markdown(
        f"""
        <div style='
            background: white;
            border-radius: 12px;
            padding: 16px 20px;
            margin-bottom: 16px;
            border: 1px solid #E2E8F0;
            display: flex;
            align-items: center;
            justify-content: space-between;
        '>
            <h3 style='margin: 0; color: #1E293B;'>📊 Dashboard</h3>
            <span style='color: #64748B; font-size: 14px;'>{len(visualizations)} visualizações</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not visualizations:
        st.markdown(
            """
            <div style='
                border: 2px dashed #CBD5E1;
                border-radius: 16px;
                padding: 60px;
                text-align: center;
                margin: 20px 0;
                background: #F8FAFC;
            '>
                <div style='font-size: 48px; margin-bottom: 16px;'>📈</div>
                <h3 style='color: #475569; margin: 0;'>Dashboard Vazio</h3>
                <p style='color: #94A3B8; margin-top: 8px;'>Adicione visualizações usando o painel à direita</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        from infrastructure.chart_factory import ChartFactory

        chart_factory = ChartFactory()

        for idx, viz in enumerate(visualizations):
            render_visualization(
                viz=viz,
                df=df,
                chart_factory=chart_factory,
                index=idx,
                on_update=on_update_visualization,
                on_delete=on_delete_visualization,
                on_add_comment=on_add_comment,
                sheet=sheet,
            )


def render_visualization(
    viz: Visualization,
    df: pl.DataFrame,
    chart_factory: Any,
    index: int,
    on_update: Callable[[str, VisualizationConfig], None],
    on_delete: Callable[[str], None],
    on_add_comment: Callable[[str, str], None],
    sheet: Optional[FileSheet] = None,
) -> None:
    """Render a single visualization with modern card design."""

    # Card container
    st.markdown(
        """
        <div style='
            background: white;
            border-radius: 12px;
            border: 1px solid #E2E8F0;
            margin-bottom: 16px;
            overflow: hidden;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        '>
        """,
        unsafe_allow_html=True,
    )

    # Card header
    col1, col2, col3, col4 = st.columns([5, 1, 1, 1])

    with col1:
        title = (
            viz.config.title
            if viz.config and viz.config.title
            else f"Visualização {index + 1}"
        )
        st.markdown(f"**{title}**")

    with col2:
        if st.button("✏️", key=f"edit_{viz.viz_id}", help="Editar visualização"):
            st.session_state.editing_viz_id = viz.viz_id

    with col3:
        if st.button(
            "💬", key=f"comment_btn_{viz.viz_id}", help="Adicionar comentário"
        ):
            st.session_state.commenting_viz_id = viz.viz_id

    with col4:
        if st.button("🗑️", key=f"delete_{viz.viz_id}", help="Excluir visualização"):
            on_delete(viz.viz_id)
            st.rerun()

    # Render the visualization
    if viz.config:
        try:
            if viz.viz_type == "table":
                render_table(viz, df)
            elif viz.viz_type == "metric_card":
                render_metric_card(viz, df)
            else:
                render_chart(viz, df, chart_factory)
        except Exception as e:
            st.error(f"Erro ao renderizar: {str(e)}")

    # Show existing comment
    if viz.comment:
        st.info(f"💬 {viz.comment}")

    st.markdown("</div>", unsafe_allow_html=True)


_VIZ_TYPE_MAP = {
    "bar": VisualizationType.BAR,
    "line": VisualizationType.LINE,
    "pie": VisualizationType.PIE,
    "area": VisualizationType.AREA,
    "scatter": VisualizationType.SCATTER,
    "histogram": VisualizationType.HISTOGRAM,
    "box": VisualizationType.BOX,
    "heatmap": VisualizationType.HEATMAP,
}


def render_chart(viz: Visualization, df: pl.DataFrame, chart_factory: Any) -> None:
    """Render a chart visualization through the ChartFactory."""
    config = viz.config
    if not config:
        return

    viz_type = _VIZ_TYPE_MAP.get(viz.viz_type, VisualizationType.BAR)

    try:
        fig = chart_factory.create_chart(df, config, viz_type)
        st.plotly_chart(fig, use_container_width=True, key=f"chart_{viz.viz_id}")
    except Exception as e:
        st.error(f"Erro ao criar gráfico: {str(e)}")


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
        except Exception:
            pass

    st.dataframe(table_df.head(100).to_pandas(), use_container_width=True, height=300)


def render_metric_card(viz: Visualization, df: pl.DataFrame) -> None:
    """Render a metric card visualization."""
    config = viz.config
    if not config or not config.y_column:
        st.warning("Selecione uma coluna para a métrica")
        return

    try:
        col = df[config.y_column]

        if config.aggregation == "mean":
            value = col.mean()
            label = "Média"
        elif config.aggregation == "sum":
            value = col.sum()
            label = "Total"
        elif config.aggregation == "count":
            value = col.count()
            label = "Contagem"
        elif config.aggregation == "min":
            value = col.min()
            label = "Mínimo"
        elif config.aggregation == "max":
            value = col.max()
            label = "Máximo"
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
        <div style='background: linear-gradient(135deg, #10B981 0%, #059669 100%); border-radius: 15px; padding: 30px; color: white; text-align: center; margin: 10px 0;'>
            <h1 style='margin: 0; font-size: 48px;'>{formatted_value}</h1>
            <p style='margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;'>{config.title or f"{label} de {config.y_column}"}</p>
        </div>
        """,
            unsafe_allow_html=True,
        )
    except Exception as e:
        st.error(f"Erro ao calcular métrica: {str(e)}")
