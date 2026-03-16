"""
Widget Palette Component - Secondary sidebar for visualization widgets.
Implements the drag-and-drop schema mapping functionality shown in interface_principal.png.
"""

from typing import Callable, Optional, List, Any
import streamlit as st

from domain.entities import DataSchema, ColumnType, VisualizationType


def render_widget_palette(
    data_schema: Optional[DataSchema],
    on_add_visualization: Callable[[VisualizationType], None],
    collapsed: bool = False,
) -> None:
    """
    Render the widget palette for adding visualizations.
    This appears as a secondary sidebar when an analysis is active.

    Args:
        data_schema: Schema of the loaded data
        on_add_visualization: Callback when a visualization type is selected
        collapsed: Whether to show only icons (collapsed mode)
    """
    # Header
    if collapsed:
        st.markdown(
            """
            <div style='
                font-size: 11px;
                font-weight: 600;
                color: #64748B;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                text-align: center;
                padding: 8px 0;
            '>📊</div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div style='
                font-size: 11px;
                font-weight: 600;
                color: #64748B;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                margin-bottom: 16px;
            '>Visualizações</div>
            """,
            unsafe_allow_html=True,
        )

    # If no data, show placeholder
    if not data_schema:
        st.markdown(
            """
            <div style='
                text-align: center;
                padding: 40px 20px;
                background: #F8FAFC;
                border-radius: 12px;
                border: 1px dashed #CBD5E1;
            '>
                <div style='font-size: 32px; margin-bottom: 12px;'>📁</div>
                <p style='color: #64748B; margin: 0; font-size: 13px;'>
                    Carregue um arquivo XLSX<br>para adicionar visualizações
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    # Visualization type buttons
    chart_types = [
        ("📊", "Barras", VisualizationType.BAR_CHART, "Gráfico de barras"),
        ("📈", "Linhas", VisualizationType.LINE_CHART, "Gráfico de linhas"),
        ("🥧", "Pizza", VisualizationType.PIE_CHART, "Gráfico de pizza"),
        ("📉", "Área", VisualizationType.AREA_CHART, "Gráfico de área"),
        ("⚬", "Dispersão", VisualizationType.SCATTER_PLOT, "Gráfico de dispersão"),
        ("▊", "Histograma", VisualizationType.HISTOGRAM, "Histograma"),
        ("📦", "Box Plot", VisualizationType.BOX_PLOT, "Box plot"),
        ("🔥", "Heatmap", VisualizationType.HEATMAP, "Mapa de calor"),
        ("📋", "Tabela", VisualizationType.TABLE, "Tabela de dados"),
        ("💳", "Métrica", VisualizationType.METRIC_CARD, "Cartão de métrica"),
    ]

    # Create grid of buttons
    cols = st.columns(2 if collapsed else 3)

    for i, (icon, name, viz_type, tooltip) in enumerate(chart_types):
        col_idx = i % len(cols)
        with cols[col_idx]:
            button_label = icon if collapsed else f"{icon}\n{name}"
            if st.button(
                button_label,
                key=f"widget_btn_{viz_type.value}",
                use_container_width=True,
                help=tooltip,
            ):
                on_add_visualization(viz_type)

    if not collapsed:
        st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

        # Data preview section
        st.markdown(
            """
            <div style='
                font-size: 11px;
                font-weight: 600;
                color: #64748B;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                margin-bottom: 12px;
            '>Dados</div>
            """,
            unsafe_allow_html=True,
        )

        with st.expander("📁 Visualizar Dados", expanded=False):
            render_data_preview(data_schema)


def render_data_preview(data_schema: DataSchema) -> None:
    """
    Render a preview of the loaded data schema.

    Args:
        data_schema: Schema to display
    """
    st.markdown(
        f"""
        <div style='background: #F8FAFC; border-radius: 8px; padding: 12px; margin-bottom: 16px;'>
            <div style='font-weight: 600; color: #1E293B;'>{data_schema.file_name}</div>
            <div style='color: #64748B; font-size: 12px; margin-top: 4px;'>
                {data_schema.row_count:,} linhas • {len(data_schema.columns)} colunas
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("**Colunas:**")

    for col in data_schema.columns:
        type_icon = {
            ColumnType.NUMERIC: "🔢",
            ColumnType.CATEGORICAL: "📝",
            ColumnType.DATETIME: "📅",
            ColumnType.TEXT: "📄",
            ColumnType.BOOLEAN: "✓",
            ColumnType.UNKNOWN: "❓",
        }.get(col.data_type, "❓")

        with st.expander(f"{type_icon} {col.name}", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Tipo", col.data_type.value)
            with col2:
                st.metric("Únicos", col.unique_count)

            if col.data_type == ColumnType.NUMERIC and col.statistics:
                st.markdown("**Estatísticas:**")
                stats = col.statistics
                stat_cols = st.columns(3)
                stat_cols[0].metric("Mín", f"{stats.get('min', 0):.2f}")
                stat_cols[1].metric("Média", f"{stats.get('mean', 0):.2f}")
                stat_cols[2].metric("Máx", f"{stats.get('max', 0):.2f}")

            if col.data_type == ColumnType.CATEGORICAL and col.statistics:
                top_values = col.statistics.get("top_values", [])
                if top_values:
                    st.markdown("**Top Valores:**")
                    for tv in top_values[:5]:
                        st.write(
                            f"• {tv.get(data_schema.columns[0].name, tv)}: {tv.get('count', 0)}"
                        )

            if col.sample_values:
                st.markdown(f"**Amostra:** `{col.sample_values[:5]}`")


def render_column_mapping(
    data_schema: DataSchema,
    viz_type: VisualizationType,
    on_map: Callable[[dict], None],
    on_cancel: Callable[[], None],
) -> None:
    """
    Render the column mapping interface for a visualization.

    Args:
        data_schema: Schema of the data
        viz_type: Type of visualization being configured
        on_map: Callback when mapping is complete
        on_cancel: Callback when cancelled
    """
    numeric_cols = data_schema.get_numeric_columns()
    categorical_cols = data_schema.get_categorical_columns()
    datetime_cols = data_schema.get_datetime_columns()
    all_cols = data_schema.get_column_names()

    st.markdown("### 🎯 Configurar Visualização")

    # Title input
    title = st.text_input(
        "Título",
        value=f"Novo {viz_type.value.replace('_', ' ').title()}",
        key="mapping_title",
    )

    config = {
        "visualization_type": viz_type,
        "title": title,
    }

    # Column selectors based on visualization type
    if viz_type == VisualizationType.TABLE:
        st.markdown("**Colunas para exibir:**")
        selected_cols = st.multiselect(
            "Colunas", all_cols, default=all_cols[:5], key="mapping_table_cols"
        )
        config["x_column"] = selected_cols[0] if selected_cols else None
        config["y_column"] = selected_cols[1] if len(selected_cols) > 1 else None

    elif viz_type == VisualizationType.METRIC_CARD:
        col1, col2 = st.columns(2)
        with col1:
            config["y_column"] = st.selectbox(
                "Coluna de Valor",
                numeric_cols if numeric_cols else all_cols,
                key="mapping_metric_y",
            )
        with col2:
            config["aggregation"] = st.selectbox(
                "Agregação",
                ["sum", "mean", "count", "min", "max"],
                key="mapping_metric_agg",
            )

    elif viz_type == VisualizationType.PIE_CHART:
        col1, col2 = st.columns(2)
        with col1:
            config["x_column"] = st.selectbox(
                "Rótulos (Categorias)",
                categorical_cols if categorical_cols else all_cols,
                key="mapping_pie_x",
            )
        with col2:
            config["y_column"] = st.selectbox(
                "Valores",
                numeric_cols if numeric_cols else all_cols,
                key="mapping_pie_y",
            )

    elif viz_type in [
        VisualizationType.BAR_CHART,
        VisualizationType.LINE_CHART,
        VisualizationType.AREA_CHART,
    ]:
        col1, col2 = st.columns(2)
        with col1:
            config["x_column"] = st.selectbox(
                "Eixo X (Categorias)",
                categorical_cols + datetime_cols if categorical_cols else all_cols,
                key="mapping_chart_x",
            )
        with col2:
            config["y_column"] = st.selectbox(
                "Eixo Y (Valores)",
                numeric_cols if numeric_cols else all_cols,
                key="mapping_chart_y",
            )

        col3, col4 = st.columns(2)
        with col3:
            config["aggregation"] = st.selectbox(
                "Agregação",
                ["sum", "mean", "count", "min", "max"],
                key="mapping_chart_agg",
            )
        with col4:
            config["color_column"] = st.selectbox(
                "Agrupar por (Opcional)", [None] + all_cols, key="mapping_chart_color"
            )

    elif viz_type == VisualizationType.SCATTER_PLOT:
        col1, col2 = st.columns(2)
        with col1:
            config["x_column"] = st.selectbox(
                "Eixo X",
                numeric_cols if numeric_cols else all_cols,
                key="mapping_scatter_x",
            )
        with col2:
            remaining_cols = [c for c in numeric_cols if c != config.get("x_column")]
            config["y_column"] = st.selectbox(
                "Eixo Y",
                remaining_cols if remaining_cols else all_cols,
                key="mapping_scatter_y",
            )

        col3, col4 = st.columns(2)
        with col3:
            config["color_column"] = st.selectbox(
                "Cor por (Opcional)",
                [None] + categorical_cols,
                key="mapping_scatter_color",
            )
        with col4:
            config["size_column"] = st.selectbox(
                "Tamanho por (Opcional)",
                [None] + numeric_cols,
                key="mapping_scatter_size",
            )

    elif viz_type == VisualizationType.HISTOGRAM:
        config["x_column"] = st.selectbox(
            "Coluna", numeric_cols if numeric_cols else all_cols, key="mapping_hist_x"
        )
        config["color_column"] = st.selectbox(
            "Dividir por (Opcional)",
            [None] + categorical_cols,
            key="mapping_hist_color",
        )

    elif viz_type == VisualizationType.BOX_PLOT:
        col1, col2 = st.columns(2)
        with col1:
            config["y_column"] = st.selectbox(
                "Valores",
                numeric_cols if numeric_cols else all_cols,
                key="mapping_box_y",
            )
        with col2:
            config["x_column"] = st.selectbox(
                "Agrupar por (Opcional)", [None] + categorical_cols, key="mapping_box_x"
            )

    else:
        # Default configuration
        col1, col2 = st.columns(2)
        with col1:
            config["x_column"] = st.selectbox(
                "Eixo X", all_cols, key="mapping_default_x"
            )
        with col2:
            config["y_column"] = st.selectbox(
                "Eixo Y",
                numeric_cols if numeric_cols else all_cols,
                key="mapping_default_y",
            )

    # Action buttons
    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        if st.button(
            "✓ Adicionar", type="primary", use_container_width=True, key="mapping_add"
        ):
            on_map(config)

    with col2:
        if st.button("✗ Cancelar", use_container_width=True, key="mapping_cancel"):
            on_cancel()
