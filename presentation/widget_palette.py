"""
Widget Palette Component - Secondary sidebar for visualization widgets.
Updated for new schema with FileSheet and SheetColumn.
"""

from typing import Callable, Optional, List, Any, Dict
import streamlit as st

from domain.entities import FileSheet, SheetColumn, VisualizationConfig


def render_widget_palette(
    sheet: Optional[FileSheet],
    on_add_visualization: Callable[[str], None],
    collapsed: bool = False,
) -> None:
    """
    Render the widget palette for adding visualizations.

    Args:
        sheet: Current sheet with column metadata
        on_add_visualization: Callback when a visualization type is selected
        collapsed: Whether to show only icons (collapsed mode)
    """
    # Header
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

    if not sheet:
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
        ("📊", "Barras", "bar"),
        ("📈", "Linhas", "line"),
        ("🥧", "Pizza", "pie"),
        ("📉", "Área", "area"),
        ("⚬", "Dispersão", "scatter"),
        ("📊", "Histograma", "histogram"),
        ("📦", "Box Plot", "box"),
        ("📋", "Tabela", "table"),
        ("💳", "Métrica", "metric_card"),
    ]

    cols = st.columns(3)
    for i, (icon, name, viz_type) in enumerate(chart_types):
        with cols[i % 3]:
            if st.button(
                f"{icon}\n{name}", key=f"widget_btn_{viz_type}", width="stretch"
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

    with st.expander("📁 Visualizar Colunas", expanded=False):
        render_column_preview(sheet)


def render_column_preview(sheet: FileSheet) -> None:
    """Render a preview of the sheet columns."""
    st.markdown(
        f"""
    <div style='background: #F8FAFC; border-radius: 8px; padding: 12px; margin-bottom: 16px;'>
        <div style='font-weight: 600; color: #1E293B;'>{sheet.sheet_name}</div>
        <div style='color: #64748B; font-size: 12px; margin-top: 4px;'>
            {len(sheet.columns)} colunas
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    st.markdown("**Colunas:**")
    for col in sheet.columns:
        type_icon = {
            "Int64": "🔢",
            "Float64": "🔢",
            "String": "📝",
            "Boolean": "✓",
            "Date": "📅",
            "Datetime": "📅",
            "Time": "🕐",
        }.get(col.data_type, "❓")

        st.markdown(f"{type_icon} **{col.column_name}** `{col.data_type}`")


def get_numeric_columns(sheet: FileSheet) -> List[str]:
    """Get list of numeric column names."""
    numeric_types = ["Int64", "Float64"]
    return [col.column_name for col in sheet.columns if col.data_type in numeric_types]


def get_categorical_columns(sheet: FileSheet) -> List[str]:
    """Get list of categorical (string) column names."""
    return [col.column_name for col in sheet.columns if col.data_type == "String"]


def render_column_mapping(
    sheet: FileSheet,
    viz_type: str,
    on_map: Callable[[Dict[str, Any]], None],
    on_cancel: Callable[[], None],
) -> None:
    """
    Render the column mapping dialog for new visualizations.

    Args:
        sheet: Sheet with column metadata
        viz_type: Type of visualization to configure
        on_map: Callback when mapping is complete
        on_cancel: Callback when mapping is cancelled
    """
    st.markdown("### ⚙️ Configurar Visualização")

    numeric_cols = get_numeric_columns(sheet)
    categorical_cols = get_categorical_columns(sheet)
    all_cols = sheet.get_column_names()

    # Title input
    title = st.text_input(
        "Título da Visualização",
        placeholder="Digite um título opcional",
        key="column_mapping_title",
    )

    config: Dict[str, Any] = {
        "viz_type": viz_type,
        "title": title,
    }

    # Configure based on visualization type
    if viz_type == "table":
        st.markdown("**Colunas para exibir:**")
        selected_cols = st.multiselect(
            "Selecione as colunas",
            all_cols,
            default=all_cols[:5],
            key="table_cols_select",
        )
        config["x_column"] = selected_cols[0] if selected_cols else None
        config["y_column"] = selected_cols[1] if len(selected_cols) > 1 else None
        config["color_column"] = selected_cols[2] if len(selected_cols) > 2 else None

    elif viz_type == "metric_card":
        col1, col2 = st.columns(2)
        with col1:
            config["y_column"] = st.selectbox(
                "Coluna de Valor",
                numeric_cols if numeric_cols else all_cols,
                key="metric_value_col",
            )
        with col2:
            config["aggregation"] = st.selectbox(
                "Agregação",
                ["sum", "mean", "count", "min", "max"],
                key="metric_agg",
            )

    elif viz_type == "pie":
        col1, col2 = st.columns(2)
        with col1:
            config["x_column"] = st.selectbox(
                "Rótulos (Categoria)",
                categorical_cols + all_cols,
                key="pie_label_col",
            )
        with col2:
            config["y_column"] = st.selectbox(
                "Valores",
                numeric_cols if numeric_cols else all_cols,
                key="pie_value_col",
            )

    elif viz_type == "histogram":
        config["x_column"] = st.selectbox(
            "Coluna para Histograma",
            numeric_cols if numeric_cols else all_cols,
            key="hist_col",
        )

    elif viz_type == "box":
        col1, col2 = st.columns(2)
        with col1:
            config["x_column"] = st.selectbox(
                "Coluna X (Categoria)",
                categorical_cols + all_cols,
                key="box_x_col",
            )
        with col2:
            config["y_column"] = st.selectbox(
                "Coluna Y (Valores)",
                numeric_cols if numeric_cols else all_cols,
                key="box_y_col",
            )

    else:
        # Default configuration for bar, line, area, scatter charts
        col1, col2 = st.columns(2)
        with col1:
            config["x_column"] = st.selectbox(
                "Eixo X",
                all_cols,
                key="chart_x_col",
            )
        with col2:
            config["y_column"] = st.selectbox(
                "Eixo Y",
                numeric_cols if numeric_cols else all_cols,
                key="chart_y_col",
            )

        col1, col2 = st.columns(2)
        with col1:
            config["color_column"] = st.selectbox(
                "Cor/Agrupamento (opcional)",
                [None] + categorical_cols,
                key="chart_color_col",
            )
        with col2:
            config["aggregation"] = st.selectbox(
                "Agregação",
                ["sum", "mean", "count", "min", "max"],
                key="chart_agg",
            )

    # Action buttons
    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("✓ Criar Visualização", type="primary", use_container_width=True):
            on_map(config)

    with col2:
        if st.button("✗ Cancelar", use_container_width=True):
            on_cancel()
