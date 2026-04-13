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

# ── Constantes de UI compartilhadas ──────────────────────────────────────────
_AGG_OPTIONS: dict = {
    "sum":   "Soma",
    "mean":  "Média",
    "count": "Contagem",
    "min":   "Mínimo",
    "max":   "Máximo",
}

_COLOR_SCHEMES: list = [
    "default", "pastel", "dark", "vivid", "safe", "d3", "set1", "set2"
]


def render_widget_palette(
    data_schema: Optional[DataSchema], on_add_visualization: Callable
) -> None:
    """Render the widget palette for adding visualizations."""
    st.markdown("### ➕ Add Visualization")

    if not data_schema:
        st.info("📁 Upload data first")
        return

    chart_types = [
        ("📊 Gráfico de Colunas", VisualizationType.COLUMN_CHART),
        ("📉 Barras Horizontais",  VisualizationType.BAR_CHART),
        ("📈 Linha",              VisualizationType.LINE_CHART),
        ("🥧 Pizza",              VisualizationType.PIE_CHART),
        ("🏔 Área",               VisualizationType.AREA_CHART),
        ("⚬ Dispersão",           VisualizationType.SCATTER_PLOT),
        ("▊ Histograma",          VisualizationType.HISTOGRAM),
        ("📦 Box Plot",           VisualizationType.BOX_PLOT),
        ("🔥 Mapa de Calor",      VisualizationType.HEATMAP),
        ("📋 Tabela",             VisualizationType.TABLE),
        ("💳 Cartão de Métrica",  VisualizationType.METRIC_CARD),
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

    elif viz_type in (VisualizationType.COLUMN_CHART, VisualizationType.BAR_CHART):
        config = _configure_bar_column_ui(
            title, viz_type, all_cols, numeric_cols, categorical_cols, existing_config
        )

    elif viz_type == VisualizationType.LINE_CHART:
        config = _configure_line_chart_ui(
            title, all_cols, numeric_cols, categorical_cols, datetime_cols, existing_config,
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

    col1, col2 = st.columns(2)
    with col1:
        _pie_agg = {"sum": "Soma", "mean": "Média", "count": "Contagem"}
        default_agg = existing.aggregation if existing else "sum"
        aggregation = st.selectbox(
            "📐 Agregação",
            options=list(_pie_agg.keys()),
            index=list(_pie_agg.keys()).index(default_agg) if default_agg in _pie_agg else 0,
            format_func=lambda k: _pie_agg[k],
            key="pie_agg",
        )
    with col2:
        default_scheme = existing.color_scheme if existing and existing.color_scheme in _COLOR_SCHEMES else "default"
        color_scheme = st.selectbox("🎨 Paleta", _COLOR_SCHEMES, index=_COLOR_SCHEMES.index(default_scheme), key="pie_scheme")

    col3, col4 = st.columns(2)
    with col3:
        show_values = st.checkbox("Mostrar valores", value=existing.show_values if existing else False, key="pie_showvals")
    with col4:
        show_legend = st.checkbox("Legenda", value=existing.show_legend if existing else True, key="pie_legend")

    return VisualizationConfig(
        visualization_type=VisualizationType.PIE_CHART,
        title=title if title else f"Distribuição de {x_column}",
        x_column=x_column,
        y_column=y_column,
        aggregation=aggregation,
        color_scheme=color_scheme,
        show_values=show_values,
        show_legend=show_legend,
    )


def _configure_bar_column_ui(
    title: str,
    viz_type: VisualizationType,
    all_cols: List[str],
    numeric_cols: List[str],
    categorical_cols: List[str],
    existing: Optional[VisualizationConfig],
) -> VisualizationConfig:
    """UI unificada para Gráfico de Colunas (vertical) e Barras Horizontais."""
    pfx = viz_type.value  # chave única por tipo
    is_column = viz_type == VisualizationType.COLUMN_CHART
    label = "Gráfico de Colunas" if is_column else "Barras Horizontais"
    icon = "📊" if is_column else "📉"
    st.markdown(f"**{icon} Configuração — {label}**")

    # Categoria (eixo X para colunas, eixo Y para barras horizontais)
    x_cols = categorical_cols if categorical_cols else all_cols
    default_x_idx = 0
    if existing and existing.x_column in x_cols:
        default_x_idx = x_cols.index(existing.x_column)
    x_column = st.selectbox(
        "📋 Categoria",
        x_cols,
        index=default_x_idx,
        key=f"{pfx}_x_select",
    )

    # Métricas (Y)
    if numeric_cols:
        default_y = (
            existing.y_columns
            if existing and existing.y_columns
            else [numeric_cols[0]]
        )
        y_columns = st.multiselect(
            "📈 Métricas (Eixo de Valor)",
            options=numeric_cols,
            default=[c for c in default_y if c in numeric_cols],
            key=f"{pfx}_y_select",
        )
    else:
        y_columns = []
        st.warning("⚠️ Nenhuma coluna numérica disponível")

    col1, col2 = st.columns(2)
    with col1:
        default_agg = existing.aggregation if existing else "sum"
        aggregation = st.selectbox(
            "📐 Agregação",
            options=list(_AGG_OPTIONS.keys()),
            index=list(_AGG_OPTIONS.keys()).index(default_agg)
            if default_agg in _AGG_OPTIONS else 0,
            format_func=lambda k: _AGG_OPTIONS[k],
            key=f"{pfx}_agg",
        )
    with col2:
        color_opts = [None] + categorical_cols
        default_color = 0
        if existing and existing.color_column and existing.color_column in categorical_cols:
            default_color = color_opts.index(existing.color_column)
        color_column = st.selectbox(
            "🎨 Agrupar por",
            color_opts,
            index=default_color,
            key=f"{pfx}_color",
            help="Divide as barras por categoria (melhor com uma única métrica)",
        )

    # Paleta de cores
    default_scheme = (
        existing.color_scheme
        if existing and existing.color_scheme in _COLOR_SCHEMES
        else "default"
    )
    color_scheme = st.selectbox(
        "🎨 Paleta de cores",
        _COLOR_SCHEMES,
        index=_COLOR_SCHEMES.index(default_scheme),
        key=f"{pfx}_scheme",
    )

    col3, col4, col5 = st.columns(3)
    with col3:
        show_values = st.checkbox(
            "Mostrar valores",
            value=existing.show_values if existing else False,
            key=f"{pfx}_showvals",
        )
    with col4:
        show_legend = st.checkbox(
            "Legenda",
            value=existing.show_legend if existing else True,
            key=f"{pfx}_legend",
        )
    with col5:
        show_grid = st.checkbox(
            "Grade",
            value=existing.show_grid if existing else True,
            key=f"{pfx}_grid",
        )

    auto_title = f"{', '.join(y_columns)} por {x_column}" if y_columns else ""
    return VisualizationConfig(
        visualization_type=viz_type,
        title=title if title else auto_title,
        x_column=x_column,
        y_columns=y_columns,
        color_column=color_column,
        aggregation=aggregation,
        color_scheme=color_scheme,
        show_values=show_values,
        show_legend=show_legend,
        show_grid=show_grid,
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
        default_agg = existing.aggregation if existing else "sum"
        aggregation = st.selectbox(
            "📐 Agregação",
            options=list(_AGG_OPTIONS.keys()),
            index=list(_AGG_OPTIONS.keys()).index(default_agg) if default_agg in _AGG_OPTIONS else 0,
            format_func=lambda k: _AGG_OPTIONS[k],
            key="line_agg",
        )

    with col2:
        color_options = [None] + all_cols
        default_color_idx = 0
        if existing and existing.color_column:
            if existing.color_column in all_cols:
                default_color_idx = color_options.index(existing.color_column)
        color_column = st.selectbox(
            "🎨 Agrupar por",
            color_options,
            index=default_color_idx,
            key="line_color",
            help="Cria linhas separadas por grupo",
        )

    default_scheme = existing.color_scheme if existing and existing.color_scheme in _COLOR_SCHEMES else "default"
    color_scheme = st.selectbox("🎨 Paleta de cores", _COLOR_SCHEMES, index=_COLOR_SCHEMES.index(default_scheme), key="line_scheme")

    col3, col4, col5 = st.columns(3)
    with col3:
        show_values = st.checkbox("Mostrar valores", value=existing.show_values if existing else False, key="line_showvals")
    with col4:
        show_legend = st.checkbox("Legenda", value=existing.show_legend if existing else True, key="line_legend")
    with col5:
        show_grid = st.checkbox("Grade", value=existing.show_grid if existing else True, key="line_grid")

    return VisualizationConfig(
        visualization_type=VisualizationType.LINE_CHART,
        title=title if title else f"{y_column} por {x_column}",
        x_column=x_column,
        y_column=y_column,
        color_column=color_column,
        aggregation=aggregation,
        color_scheme=color_scheme,
        show_values=show_values,
        show_legend=show_legend,
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

    col1, col2 = st.columns(2)
    with col1:
        default_agg = existing.aggregation if existing else "sum"
        aggregation = st.selectbox(
            "📐 Agregação",
            options=list(_AGG_OPTIONS.keys()),
            index=list(_AGG_OPTIONS.keys()).index(default_agg) if default_agg in _AGG_OPTIONS else 0,
            format_func=lambda k: _AGG_OPTIONS[k],
            key="area_agg",
        )
    with col2:
        color_options = [None] + all_cols
        default_color_idx = 0
        if existing and existing.color_column:
            if existing.color_column in all_cols:
                default_color_idx = color_options.index(existing.color_column)
        color_column = st.selectbox(
            "🎨 Agrupar por", color_options, index=default_color_idx, key="area_color"
        )

    default_scheme = existing.color_scheme if existing and existing.color_scheme in _COLOR_SCHEMES else "default"
    color_scheme = st.selectbox("🎨 Paleta de cores", _COLOR_SCHEMES, index=_COLOR_SCHEMES.index(default_scheme), key="area_scheme")

    col3, col4, col5 = st.columns(3)
    with col3:
        show_values = st.checkbox("Mostrar valores", value=existing.show_values if existing else False, key="area_showvals")
    with col4:
        show_legend = st.checkbox("Legenda", value=existing.show_legend if existing else True, key="area_legend")
    with col5:
        show_grid = st.checkbox("Grade", value=existing.show_grid if existing else True, key="area_grid")

    return VisualizationConfig(
        visualization_type=VisualizationType.AREA_CHART,
        title=title if title else f"{y_column} por {x_column}",
        x_column=x_column,
        y_column=y_column,
        color_column=color_column,
        aggregation=aggregation,
        color_scheme=color_scheme,
        show_values=show_values,
        show_legend=show_legend,
        show_grid=show_grid,
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

import streamlit as st

# Mapeia ColumnType detectado → rótulo exibido na tela de mapeamento
_COLUMN_TYPE_TO_LABEL = {
    ColumnType.NUMERIC: "Numérico",
    ColumnType.DATETIME: "Data/Hora",
    ColumnType.CATEGORICAL: "Categoria",
    ColumnType.TEXT: "Texto",
    ColumnType.BOOLEAN: "Numérico",
    ColumnType.UNKNOWN: "Texto",
}

_MAPPER_OPTIONS = ["Numérico", "Data/Hora", "Categoria", "Texto"]


def render_column_mapper(df, schema=None):
    """
    Interface para o usuário confirmar/ajustar o tipo de cada coluna.
    Usa os tipos já detectados pelo DataService como sugestão padrão.
    Retorna {nome_original: label_escolhido} para todas as colunas.
    """
    st.subheader("🛠️ Mapeamento de Colunas")
    st.info("Tipos detectados automaticamente pelo sistema. Ajuste se necessário.")

    # Monta índice {col_name: ColumnType} a partir do schema pré-detectado (se disponível)
    detected: dict = {}
    if schema is not None:
        for col_obj in schema.columns:
            detected[col_obj.name] = col_obj.data_type

    mapping = {}
    cols_ui = st.columns(2)

    for i, col in enumerate(df.columns):
        with cols_ui[i % 2]:
            # Determina o label padrão: usa o tipo detectado pelo DataService
            col_type = detected.get(col, ColumnType.UNKNOWN)
            label_detectado = _COLUMN_TYPE_TO_LABEL.get(col_type, "Texto")
            index_sugerido = _MAPPER_OPTIONS.index(label_detectado)

            choice = st.selectbox(
                col,
                _MAPPER_OPTIONS,
                index=index_sugerido,
                key=f"map_{col}",
                help=f"Tipo detectado automaticamente: **{label_detectado}**",
            )

            mapping[col] = choice

    return mapping