"""
Widgets Component - Visualization palette for adding visualizations.
"""

from typing import Optional, Callable, Any
import streamlit as st

from domain.entities import DataSchema, ColumnType, VisualizationType


def render_widget_palette(
    data_schema: Optional[DataSchema],
    on_add_visualization: Callable[[VisualizationType], None],
) -> None:
    """Render the widget palette for adding visualizations."""

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

    chart_types = [
        ("📊", "Barras", VisualizationType.BAR_CHART),
        ("📈", "Linhas", VisualizationType.LINE_CHART),
        ("🥧", "Pizza", VisualizationType.PIE_CHART),
        ("📉", "Área", VisualizationType.AREA_CHART),
        ("⚬", "Dispersão", VisualizationType.SCATTER_PLOT),
        ("▊", "Histograma", VisualizationType.HISTOGRAM),
        ("📦", "Box Plot", VisualizationType.BOX_PLOT),
        ("📋", "Tabela", VisualizationType.TABLE),
        ("💳", "Métrica", VisualizationType.METRIC_CARD),
    ]

    cols = st.columns(3)
    for i, (icon, name, viz_type) in enumerate(chart_types):
        with cols[i % 3]:
            if st.button(
                f"{icon}\n{name}", key=f"widget_btn_{viz_type.value}", width="stretch"
            ):
                on_add_visualization(viz_type)

    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
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
        render_data_preview(data_schema, None)


def render_data_preview(data_schema: DataSchema, df: Any) -> None:
    """Render a preview of the loaded data."""
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

        st.markdown(f"{type_icon} **{col.name}** `{col.data_type.value}`")
