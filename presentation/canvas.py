"""
Canvas Component - Main slide editing area with visualization rendering.
"""

from typing import Optional, List, Callable, Any, Dict
import streamlit as st
import polars as pl

from domain.entities import (
    Slide,
    Visualization,
    VisualizationType,
    VisualizationConfig,
    DataSchema,
)


def render_canvas(
    slide: Optional[Slide],
    data_service: Any,
    analysis_id: str,
    on_update_visualization: Callable[[str, str, VisualizationConfig], None],
    on_delete_visualization: Callable[[str, str], None],
    on_add_comment: Callable[[str, str, str], None],
    data_schema: Optional[DataSchema] = None,
) -> None:
    """
    Render the main canvas for slide editing.

    Args:
        slide: Current slide to render
        data_service: Service for data operations
        analysis_id: ID of the current analysis
        on_update_visualization: Callback when visualization is updated
        on_delete_visualization: Callback when visualization is deleted
        on_add_comment: Callback when comment is added
        data_schema: Schema of the loaded data
    """
    if not slide:
        st.markdown(
            """
            <div style='
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                height: 400px;
                text-align: center;
            '>
                <div style='font-size: 64px; margin-bottom: 20px;'>📊</div>
                <h3 style='color: #1E293B; margin: 0;'>Nenhum slide selecionado</h3>
                <p style='color: #64748B; margin-top: 10px;'>Selecione ou crie um slide para começar</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    df = data_service.get_cached_data(analysis_id)

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

    # Render slide header
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
            <h3 style='margin: 0; color: #1E293B;'>📄 {slide.title}</h3>
            <span style='color: #64748B; font-size: 14px;'>{len(slide.visualizations)} visualizações</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not slide.visualizations:
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
                <h3 style='color: #475569; margin: 0;'>Slide Vazio</h3>
                <p style='color: #94A3B8; margin-top: 8px;'>Adicione visualizações usando o painel à direita</p>
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
    on_update: Callable[[str, str, VisualizationConfig], None],
    on_delete: Callable[[str, str], None],
    on_add_comment: Callable[[str, str, str], None],
    data_schema: Optional[DataSchema] = None,
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
        title = viz.config.title if viz.config and viz.config.title else f"Visualização {index + 1}"
        st.markdown(f"**{title}**")

    with col2:
        if st.button("✏️", key=f"edit_{viz.id}", help="Editar visualização"):
            st.session_state.editing_viz_id = viz.id

    with col3:
        if st.button("💬", key=f"comment_btn_{viz.id}", help="Adicionar comentário"):
            st.session_state.commenting_viz_id = viz.id

    with col4:
        if st.button("🗑️", key=f"delete_{viz.id}", help="Excluir visualização"):
            on_delete(slide_id, viz.id)
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
                st.plotly_chart(fig, use_container_width=True, key=f"chart_{viz.id}")
        except Exception as e:
            st.error(f"Erro ao renderizar: {str(e)}")

    # Show existing comment
    if viz.comment:
        st.info(f"💬 {viz.comment}")

    st.markdown("</div>", unsafe_allow_html=True)


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


def render_slide_navigator(
    slides: List[Slide],
    current_slide_id: Optional[str],
    on_slide_change: Callable[[str], None],
    on_add_slide: Callable[[], None],
    on_delete_slide: Callable[[str], None],
) -> None:
    """Render the slide navigation bar."""
    st.markdown("---")

    col1, col2, col3 = st.columns([1, 3, 1])

    with col1:
        if st.button("➕ Novo Slide", use_container_width=True):
            on_add_slide()
            st.rerun()

    with col2:
        if slides:
            cols = st.columns(min(len(slides), 8))
            for i, slide in enumerate(slides):
                with cols[i % 8]:
                    is_current = slide.id == current_slide_id
                    title = slide.title[:10] + "..." if len(slide.title) > 10 else slide.title

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
            if st.button("🗑️ Excluir", use_container_width=True):
                on_delete_slide(current_slide_id)
                st.rerun()
