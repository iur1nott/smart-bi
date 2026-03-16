"""
Canvas Component - Main slide editing area with visualization rendering.
Implements the main content area shown in interface_principal.png.
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
        title = (
            viz.config.title
            if viz.config and viz.config.title
            else f"Visualização {index + 1}"
        )
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

    # Show configuration editor if editing
    if st.session_state.get("editing_viz_id") == viz.id and data_schema:
        st.markdown("---")
        new_config = render_visualization_editor(viz.config, data_schema, viz.id)
        if new_config:
            on_update(slide_id, viz.id, new_config)
            st.session_state.editing_viz_id = None
            st.rerun()

    # Show comment editor
    if st.session_state.get("commenting_viz_id") == viz.id:
        st.markdown("---")
        comment = st.text_area(
            "Comentário", value=viz.comment, key=f"comment_input_{viz.id}", height=80
        )
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("✓ Salvar", key=f"save_comment_{viz.id}", type="primary"):
                on_add_comment(slide_id, viz.id, comment)
                st.session_state.commenting_viz_id = None
                st.rerun()
        with col_b:
            if st.button("✗ Cancelar", key=f"cancel_comment_{viz.id}"):
                st.session_state.commenting_viz_id = None
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


def render_visualization_editor(
    current_config: VisualizationConfig, data_schema: DataSchema, viz_id: str
) -> Optional[VisualizationConfig]:
    """Render an editor for visualization configuration."""
    st.markdown("### ⚙️ Configurar Visualização")

    numeric_cols = data_schema.get_numeric_columns()
    categorical_cols = data_schema.get_categorical_columns()
    all_cols = data_schema.get_column_names()

    title = st.text_input(
        "Título",
        value=current_config.title if current_config else "",
        key=f"editor_title_{viz_id}",
    )

    config = None
    viz_type = (
        current_config.visualization_type
        if current_config
        else VisualizationType.BAR_CHART
    )
    aggregations = ["sum", "mean", "count", "min", "max"]

    if viz_type == VisualizationType.TABLE:
        st.markdown("**Configuração da Tabela**")
        default_cols = []
        if current_config:
            if current_config.x_column:
                default_cols.append(current_config.x_column)
            if current_config.y_column and current_config.y_column not in default_cols:
                default_cols.append(current_config.y_column)
        if not default_cols:
            default_cols = all_cols[:5]

        selected_cols = st.multiselect(
            "Colunas para exibir",
            all_cols,
            default=default_cols,
            key=f"editor_table_cols_{viz_id}",
        )

        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("✓ Aplicar", key=f"apply_table_{viz_id}", type="primary"):
                config = VisualizationConfig(
                    visualization_type=viz_type,
                    title=title,
                    x_column=selected_cols[0] if selected_cols else None,
                    y_column=selected_cols[1] if len(selected_cols) > 1 else None,
                    color_column=selected_cols[2] if len(selected_cols) > 2 else None,
                )
        with col_b:
            if st.button("✗ Cancelar", key=f"cancel_table_{viz_id}"):
                st.session_state.editing_viz_id = None
                st.rerun()

    elif viz_type == VisualizationType.METRIC_CARD:
        st.markdown("**Configuração do Cartão de Métrica**")

        col1, col2 = st.columns(2)
        with col1:
            y_column = st.selectbox(
                "Coluna de Valor",
                numeric_cols if numeric_cols else all_cols,
                index=numeric_cols.index(current_config.y_column)
                if current_config and current_config.y_column in numeric_cols
                else 0,
                key=f"editor_metric_y_{viz_id}",
            )
        with col2:
            current_agg = current_config.aggregation if current_config else "sum"
            aggregation = st.selectbox(
                "Agregação",
                aggregations,
                index=aggregations.index(current_agg)
                if current_agg in aggregations
                else 0,
                key=f"editor_metric_agg_{viz_id}",
            )

        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("✓ Aplicar", key=f"apply_metric_{viz_id}", type="primary"):
                config = VisualizationConfig(
                    visualization_type=viz_type,
                    title=title,
                    y_column=y_column,
                    aggregation=aggregation,
                )
        with col_b:
            if st.button("✗ Cancelar", key=f"cancel_metric_{viz_id}"):
                st.session_state.editing_viz_id = None
                st.rerun()

    elif viz_type == VisualizationType.PIE_CHART:
        st.markdown("**Configuração do Gráfico de Pizza**")

        col1, col2 = st.columns(2)
        with col1:
            label_cols = categorical_cols if categorical_cols else all_cols
            x_column = st.selectbox(
                "Rótulos (Categorias)",
                label_cols,
                index=label_cols.index(current_config.x_column)
                if current_config and current_config.x_column in label_cols
                else 0,
                key=f"editor_pie_x_{viz_id}",
            )
        with col2:
            y_column = st.selectbox(
                "Valores",
                numeric_cols if numeric_cols else all_cols,
                index=numeric_cols.index(current_config.y_column)
                if current_config and current_config.y_column in numeric_cols
                else 0,
                key=f"editor_pie_y_{viz_id}",
            )

        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("✓ Aplicar", key=f"apply_pie_{viz_id}", type="primary"):
                config = VisualizationConfig(
                    visualization_type=viz_type,
                    title=title,
                    x_column=x_column,
                    y_column=y_column,
                )
        with col_b:
            if st.button("✗ Cancelar", key=f"cancel_pie_{viz_id}"):
                st.session_state.editing_viz_id = None
                st.rerun()

    else:
        # Generic chart configuration
        st.markdown(f"**Configuração do {viz_type.value.replace('_', ' ').title()}**")

        col1, col2 = st.columns(2)
        with col1:
            x_cols = categorical_cols if categorical_cols else all_cols
            x_column = st.selectbox(
                "Eixo X (Categorias)",
                x_cols,
                index=x_cols.index(current_config.x_column)
                if current_config and current_config.x_column in x_cols
                else 0,
                key=f"editor_chart_x_{viz_id}",
            )
        with col2:
            y_column = st.selectbox(
                "Eixo Y (Valores)",
                numeric_cols if numeric_cols else all_cols,
                index=numeric_cols.index(current_config.y_column)
                if current_config and current_config.y_column in numeric_cols
                else 0,
                key=f"editor_chart_y_{viz_id}",
            )

        col3, col4 = st.columns(2)
        with col3:
            current_agg = current_config.aggregation if current_config else "sum"
            aggregation = st.selectbox(
                "Agregação",
                aggregations,
                index=aggregations.index(current_agg)
                if current_agg in aggregations
                else 0,
                key=f"editor_chart_agg_{viz_id}",
            )
        with col4:
            color_column = st.selectbox(
                "Agrupar por (Opcional)",
                [None] + all_cols,
                index=0
                if not current_config or not current_config.color_column
                else ([None] + all_cols).index(current_config.color_column),
                key=f"editor_chart_color_{viz_id}",
            )

        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("✓ Aplicar", key=f"apply_chart_{viz_id}", type="primary"):
                config = VisualizationConfig(
                    visualization_type=viz_type,
                    title=title,
                    x_column=x_column,
                    y_column=y_column,
                    aggregation=aggregation,
                    color_column=color_column,
                )
        with col_b:
            if st.button("✗ Cancelar", key=f"cancel_chart_{viz_id}"):
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
        st.dataframe(table_df.head(100).to_pandas(), use_container_width=True)
    else:
        st.warning("Nenhuma coluna válida selecionada")


def render_metric_card(viz: Visualization, df: pl.DataFrame) -> None:
    """Render a metric card visualization."""
    config = viz.config
    if not config or not config.y_column:
        st.warning("Selecione uma coluna para a métrica")
        return

    if config.y_column not in df.columns:
        st.warning(f"Coluna '{config.y_column}' não encontrada")
        return

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
            formatted_value = f"{value:,.2f}"
    else:
        formatted_value = f"{value:,}"

    st.markdown(
        f"""
        <div style='
            background: linear-gradient(135deg, #10B981 0%, #059669 100%);
            border-radius: 16px;
            padding: 32px;
            color: white;
            text-align: center;
            margin: 16px 0;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        '>
            <h1 style='margin: 0; font-size: 52px; font-weight: 700;'>{formatted_value}</h1>
            <p style='margin: 12px 0 0 0; font-size: 16px; opacity: 0.9;'>{config.title or f"{label} de {config.y_column}"}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_slide_navigator(
    slides: List[Slide],
    current_slide_id: str,
    on_slide_change: Callable[[str], None],
    on_add_slide: Callable[[], None],
    on_delete_slide: Callable[[str], None],
) -> None:
    """Render the slide navigation bar at bottom."""
    st.markdown("---")

    col1, col2, col3 = st.columns([1, 4, 1])

    with col1:
        if st.button("➕ Novo Slide", type="primary", use_container_width=True):
            on_add_slide()

    with col2:
        if slides:
            slide_cols = st.columns(min(len(slides), 10))
            for i, slide in enumerate(slides):
                with slide_cols[i % 10]:
                    is_current = slide.id == current_slide_id
                    title = (
                        slide.title[:8] + "..." if len(slide.title) > 8 else slide.title
                    )

                    btn_type = "primary" if is_current else "secondary"
                    if st.button(
                        f"{i + 1}. {title}",
                        key=f"nav_slide_{slide.id}",
                        use_container_width=True,
                        type=btn_type,
                    ):
                        on_slide_change(slide.id)

    with col3:
        if len(slides) > 1:
            if st.button("🗑️ Excluir", use_container_width=True):
                on_delete_slide(current_slide_id)
