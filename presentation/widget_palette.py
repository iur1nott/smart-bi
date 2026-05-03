"""
Widget Palette Component - Secondary sidebar for visualization widgets.
Full port of dev-03 config dialogs adapted to supabase FileSheet/SheetColumn.
"""

from typing import Callable, Optional, List, Any, Dict
import polars as pl
import streamlit as st

from domain.entities import FileSheet, SheetColumn, VisualizationConfig

_COLOR_SCHEMES = ["default", "pastel", "dark", "vivid", "safe", "d3", "set1", "set2"]
_AGG_OPTIONS = {
    "sum": "Soma", "mean": "Média", "count": "Contagem",
    "min": "Mínimo", "max": "Máximo",
}


# ── Column-type helpers ───────────────────────────────────────────────────────

def get_numeric_columns(sheet: FileSheet) -> List[str]:
    return [c.column_name for c in sheet.columns if c.data_type in ("Int64", "Float64")]

def get_categorical_columns(sheet: FileSheet) -> List[str]:
    return [c.column_name for c in sheet.columns if c.data_type == "String"]

def get_datetime_columns(sheet: FileSheet) -> List[str]:
    return [c.column_name for c in sheet.columns if c.data_type in ("Date", "Datetime", "Time")]

def get_all_columns(sheet: FileSheet) -> List[str]:
    return [c.column_name for c in sheet.columns]


# ── Widget palette ────────────────────────────────────────────────────────────

_WIDGET_GROUPS = [
    ("Medidas", [("📐 Medidas", "measures")]),
    ("Gráficos", [
        ("📊 Barras", "bar"), ("📉 Colunas", "column"),
        ("📈 Linha", "line"), ("🏔 Área", "area"),
        ("🥧 Pizza", "pie"), ("⚬ Dispersão", "scatter"),
        ("▊ Histograma", "histogram"), ("📦 Box Plot", "box"),
        ("🔥 Mapa de calor", "heatmap"),
    ]),
    ("Tabelas", [("📋 Tabela", "table"), ("💳 Métrica", "metric_card")]),
]

_VIZ_ICONS = {
    "measures": "📐", "bar": "📊", "column": "📉", "line": "📈",
    "area": "🏔", "pie": "🥧", "scatter": "⚬", "histogram": "▊",
    "box": "📦", "heatmap": "🔥", "table": "📋", "metric_card": "💳",
}

def render_widget_palette(
    sheet: Optional[FileSheet],
    on_add_visualization: Callable[[str], None],
    collapsed: bool = False,
) -> None:
    """
    Render the widget palette for adding visualizations — grouped by category.
    """
    if not sheet:
        st.markdown(
            """<div style='text-align:center;padding:40px 20px;background:#F8FAFC;
                           border-radius:12px;border:1px dashed #CBD5E1;'>
                 <div style='font-size:32px;margin-bottom:12px;'>📁</div>
                 <p style='color:#64748B;margin:0;font-size:13px;'>
                     Carregue um arquivo XLSX<br>para adicionar visualizações
                 </p>
               </div>""",
            unsafe_allow_html=True,
        )
        return

    for group_label, items in _WIDGET_GROUPS:
        st.markdown(
            f"<div style='font-size:.68rem;color:#94A3B8;font-weight:600;"
            f"text-transform:uppercase;letter-spacing:.06em;margin:10px 0 4px;'>"
            f"{group_label}</div>",
            unsafe_allow_html=True,
        )
        for label, viz_type in items:
            if st.button(label, key=f"wbtn_{viz_type}", use_container_width=True):
                on_add_visualization(viz_type)

    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
    st.markdown(
        "<div style='font-size:.68rem;color:#94A3B8;font-weight:600;"
        "text-transform:uppercase;letter-spacing:.06em;margin:10px 0 4px;'>"
        "Dados</div>",
        unsafe_allow_html=True,
    )
    with st.expander("📋 Visualizar colunas", expanded=False):
        render_column_preview(sheet)


def render_column_preview(sheet: FileSheet) -> None:
    """Render column list with type icons."""
    st.markdown(
        f"<div style='background:#F8FAFC;border-radius:8px;padding:12px;margin-bottom:12px;'>"
        f"<div style='font-weight:600;color:#1E293B;'>{sheet.sheet_name}</div>"
        f"<div style='color:#64748B;font-size:12px;'>{len(sheet.columns)} colunas</div>"
        f"</div>",
        unsafe_allow_html=True,
    )
    _TYPE_ICON = {"Int64": "🔢", "Float64": "🔢", "String": "📝",
                  "Boolean": "✓", "Date": "📅", "Datetime": "📅", "Time": "🕐"}
    for col in sheet.columns:
        icon = _TYPE_ICON.get(col.data_type, "❓")
        st.markdown(f"{icon} **{col.column_name}** `{col.data_type}`")


def render_data_preview(sheet: FileSheet, df: Optional[pl.DataFrame] = None) -> None:
    """Column list + optional data sample and numeric stats."""
    render_column_preview(sheet)
    if df is not None:
        numeric_cols = get_numeric_columns(sheet)
        if numeric_cols:
            with st.expander("📈 Estatísticas numéricas", expanded=False):
                for col in numeric_cols[:5]:
                    if col in df.columns:
                        try:
                            s = df[col]
                            st.caption(
                                f"**{col}** — min {s.min():.2g}, "
                                f"máx {s.max():.2g}, média {s.mean():.2g}"
                            )
                        except Exception:
                            pass
        with st.expander("📊 Amostra dos dados", expanded=False):
            st.dataframe(df.head(10).to_pandas(), use_container_width=True)


# ── Column-type editor (post-upload mapper) ─────────────────────────────────
# Display labels shown to the user, mapped to supabase storage data_types.
# We intentionally collapse the supabase set ("Int64", "Float64", "Datetime",
# "Date", "Time", "Boolean", "String") into a smaller, friendlier set the way
# dev-03 did it. The user sees 4 categories; we cast to a sensible polars type.
_COLUMN_TYPE_LABELS = ["Numérico", "Inteiro", "Data/Hora", "Categoria", "Texto"]

_LABEL_TO_DATA_TYPE = {
    "Numérico":  "Float64",
    "Inteiro":   "Int64",
    "Data/Hora": "Datetime",
    "Categoria": "String",
    "Texto":     "String",
}

_DATA_TYPE_TO_LABEL = {
    "Int64":    "Inteiro",
    "Float64":  "Numérico",
    "Datetime": "Data/Hora",
    "Date":     "Data/Hora",
    "Time":     "Data/Hora",
    "Boolean":  "Categoria",
    "String":   "Texto",
}

_LABEL_ICONS = {
    "Numérico":  "🔢",
    "Inteiro":   "🔢",
    "Data/Hora": "📅",
    "Categoria": "🏷️",
    "Texto":     "📝",
}

_LABEL_COLORS = {
    "Numérico":  ("#EFF6FF", "#BFDBFE"),
    "Inteiro":   ("#EFF6FF", "#BFDBFE"),
    "Data/Hora": ("#F0FDF4", "#BBF7D0"),
    "Categoria": ("#FFF7ED", "#FED7AA"),
    "Texto":     ("#F8FAFC", "#E2E8F0"),
}


def render_column_mapper(
    sheet: FileSheet, df: Optional[pl.DataFrame] = None
) -> Dict[str, str]:
    """
    Render a card per column showing the detected type plus a dropdown for
    the user to override it. Returns ``{column_name: data_type_str}`` where
    ``data_type_str`` is the supabase storage type ("Int64", "Float64",
    "String", "Datetime").

    Args:
        sheet: FileSheet whose columns drive the mapper. ``data_type`` on
            each ``SheetColumn`` is used as the initially-selected option.
        df: Optional DataFrame; when present, three sample values per column
            are rendered to help the user pick the right type.
    """
    mapping: Dict[str, str] = {}
    cols_ui = st.columns(2)

    for i, col in enumerate(sheet.columns):
        detected_label = _DATA_TYPE_TO_LABEL.get(col.data_type, "Texto")
        try:
            initial_index = _COLUMN_TYPE_LABELS.index(detected_label)
        except ValueError:
            initial_index = _COLUMN_TYPE_LABELS.index("Texto")

        sample_str = "—"
        if df is not None and col.column_name in df.columns:
            try:
                samples = (
                    df[col.column_name]
                    .drop_nulls()
                    .head(3)
                    .cast(pl.String)
                    .to_list()
                )
                if samples:
                    sample_str = " · ".join(str(s)[:18] for s in samples)
            except Exception:
                sample_str = "—"

        bg, border = _LABEL_COLORS.get(detected_label, ("#F8FAFC", "#E2E8F0"))
        icon = _LABEL_ICONS.get(detected_label, "📄")

        with cols_ui[i % 2]:
            st.markdown(
                f"""
                <div style='background:{bg};border:1px solid {border};
                            border-radius:8px;padding:10px 12px 4px;
                            margin-bottom:4px;'>
                    <div style='font-size:.82rem;font-weight:600;color:#1E293B;'>
                        {icon} {col.column_name}
                    </div>
                    <div style='font-size:.72rem;color:#94A3B8;margin-bottom:6px;
                                white-space:nowrap;overflow:hidden;
                                text-overflow:ellipsis;'>
                        {sample_str}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            choice_label = st.selectbox(
                col.column_name,
                _COLUMN_TYPE_LABELS,
                index=initial_index,
                key=f"col_map_{col.column_id}",
                label_visibility="collapsed",
            )
            mapping[col.column_name] = _LABEL_TO_DATA_TYPE[choice_label]

    return mapping


# ── Visualization config dialog ───────────────────────────────────────────────

@st.dialog("Configurar Visualização", width="large")
def render_viz_config_dialog(
    viz_type: str,
    sheet: FileSheet,
    existing_config: Optional[VisualizationConfig] = None,
    on_save: Optional[Callable] = None,
    on_cancel: Optional[Callable] = None,
    is_new: bool = False,
) -> None:
    """Modal dialog for creating or editing a visualization. Adapted to supabase model."""
    num_cols   = get_numeric_columns(sheet)
    cat_cols   = get_categorical_columns(sheet)
    dt_cols    = get_datetime_columns(sheet)
    all_cols   = get_all_columns(sheet)

    icon  = _VIZ_ICONS.get(viz_type, "📊")
    verb  = "Novo" if is_new else "Editar"
    label = viz_type.replace("_", " ").title()
    st.markdown(
        f"<span style='font-size:1.05rem;font-weight:600;color:#1E293B;'>"
        f"{icon} {verb} — {label}</span>",
        unsafe_allow_html=True,
    )
    st.markdown("---")

    existing = existing_config
    title = st.text_input(
        "Título", value=existing.title if existing else "",
        placeholder="Dê um título a esta visualização…", key="cfg_title",
    )

    config: Optional[VisualizationConfig] = None

    if viz_type == "table":
        config = _cfg_table(title, all_cols, existing)
    elif viz_type == "metric_card":
        config = _cfg_metric(title, num_cols, existing)
    elif viz_type == "pie":
        config = _cfg_pie(title, all_cols, num_cols, cat_cols, existing)
    elif viz_type in ("bar", "column"):
        config = _cfg_bar(title, sheet, existing)
    elif viz_type == "line":
        config = _cfg_line(title, all_cols, num_cols, cat_cols, dt_cols, existing)
    elif viz_type == "area":
        config = _cfg_area(title, all_cols, num_cols, cat_cols, existing)
    elif viz_type == "scatter":
        config = _cfg_scatter(title, num_cols, all_cols, existing)
    elif viz_type == "histogram":
        config = _cfg_histogram(title, num_cols, cat_cols, existing)
    elif viz_type == "box":
        config = _cfg_box(title, num_cols, cat_cols, existing)
    elif viz_type == "heatmap":
        config = _cfg_heatmap(title, all_cols, num_cols, existing)
    else:
        config = _cfg_default(title, all_cols, num_cols, existing)

    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("✓ Aplicar", type="primary", use_container_width=True):
            if on_save and config:
                on_save(config)
    with c2:
        if st.button("✗ Cancelar", use_container_width=True):
            if on_cancel:
                on_cancel()


def _sel(label, options, existing_val, key, **kw):
    """Safe selectbox that handles missing current value gracefully."""
    opts = list(options) if options else [""]
    try:
        idx = opts.index(existing_val) if existing_val in opts else 0
    except (ValueError, TypeError):
        idx = 0
    return st.selectbox(label, opts, index=idx, key=key, **kw)


def _cfg_table(title, all_cols, existing):
    existing_cols = (existing.y_columns if existing and existing.y_columns
                     else ([existing.x_column, existing.y_column] if existing else []))
    default_sel = [c for c in existing_cols if c in all_cols] or all_cols[:5]
    selected = st.multiselect("📋 Colunas a exibir", all_cols,
                              default=default_sel, key="cfg_table_cols")
    return VisualizationConfig(
        title=title or "Tabela",
        y_columns=selected,
        x_column=selected[0] if selected else None,
    )


def _cfg_metric(title, num_cols, existing):
    if not num_cols:
        st.warning("Sem colunas numéricas.")
        return VisualizationConfig(title=title or "Métrica")
    y = _sel("📊 Coluna de Valor", num_cols,
              existing.y_column if existing else None, "cfg_metric_y")
    agg = _sel("📐 Agregação", list(_AGG_OPTIONS.keys()),
               existing.aggregation if existing else "sum", "cfg_metric_agg",
               format_func=lambda k: _AGG_OPTIONS[k])
    return VisualizationConfig(title=title or f"{agg} de {y}", y_column=y, aggregation=agg)


def _cfg_pie(title, all_cols, num_cols, cat_cols, existing):
    label_cols = cat_cols or all_cols
    c1, c2 = st.columns(2)
    with c1:
        x = _sel("🏷️ Rótulos", label_cols,
                 existing.x_column if existing else None, "cfg_pie_x")
    with c2:
        y = _sel("📊 Valores", num_cols or all_cols,
                 existing.y_column if existing else None, "cfg_pie_y")
    c3, c4 = st.columns(2)
    with c3:
        agg = _sel("📐 Agregação", list(_AGG_OPTIONS.keys()),
                   existing.aggregation if existing else "sum", "cfg_pie_agg",
                   format_func=lambda k: _AGG_OPTIONS[k])
    with c4:
        scheme = _sel("🎨 Paleta", _COLOR_SCHEMES,
                      existing.color_scheme if existing else "default", "cfg_pie_scheme")
    c5, c6 = st.columns(2)
    with c5:
        show_vals = st.checkbox("Mostrar valores",
                                value=existing.show_values if existing else False,
                                key="cfg_pie_vals")
    with c6:
        show_leg = st.checkbox("Legenda",
                               value=existing.show_legend if existing else True,
                               key="cfg_pie_leg")
    return VisualizationConfig(
        title=title or f"Distribuição de {x}",
        x_column=x, y_column=y, aggregation=agg,
        color_scheme=scheme, show_values=show_vals, show_legend=show_leg,
    )


def _cfg_bar(title, sheet, existing):
    num_cols = get_numeric_columns(sheet)
    cat_cols = get_categorical_columns(sheet)
    all_cols = get_all_columns(sheet)
    x_opts = cat_cols or all_cols
    x = _sel("📋 Categoria (Eixo X)", x_opts,
             existing.x_column if existing else None, "cfg_bar_x")
    default_y = (existing.y_columns if existing and existing.y_columns
                 else ([existing.y_column] if existing and existing.y_column else []))
    y_cols = st.multiselect("📈 Métricas", num_cols or all_cols,
                            default=[c for c in default_y if c in (num_cols or all_cols)],
                            key="cfg_bar_y")
    c1, c2 = st.columns(2)
    with c1:
        agg = _sel("📐 Agregação", list(_AGG_OPTIONS.keys()),
                   existing.aggregation if existing else "sum", "cfg_bar_agg",
                   format_func=lambda k: _AGG_OPTIONS[k])
    with c2:
        grp = _sel("🎨 Agrupar por", [None] + cat_cols,
                   existing.color_column if existing else None, "cfg_bar_grp")
    scheme = _sel("🎨 Paleta", _COLOR_SCHEMES,
                  existing.color_scheme if existing else "default", "cfg_bar_scheme")
    c3, c4, c5 = st.columns(3)
    with c3:
        sv = st.checkbox("Valores", value=existing.show_values if existing else False, key="cfg_bar_sv")
    with c4:
        sl = st.checkbox("Legenda", value=existing.show_legend if existing else True, key="cfg_bar_sl")
    with c5:
        sg = st.checkbox("Grade", value=existing.show_grid if existing else True, key="cfg_bar_sg")
    return VisualizationConfig(
        title=title or (f"{', '.join(y_cols)} por {x}" if y_cols else ""),
        x_column=x, y_columns=y_cols,
        y_column=y_cols[0] if y_cols else None,
        color_column=grp, aggregation=agg, color_scheme=scheme,
        show_values=sv, show_legend=sl, show_grid=sg,
    )


def _cfg_line(title, all_cols, num_cols, cat_cols, dt_cols, existing):
    x_opts = list(dict.fromkeys(dt_cols + cat_cols + all_cols))
    c1, c2 = st.columns(2)
    with c1:
        x = _sel("📊 Eixo X", x_opts,
                 existing.x_column if existing else None, "cfg_line_x")
    with c2:
        y = _sel("📈 Eixo Y", num_cols or all_cols,
                 existing.y_column if existing else None, "cfg_line_y")
    c3, c4 = st.columns(2)
    with c3:
        agg = _sel("📐 Agregação", list(_AGG_OPTIONS.keys()),
                   existing.aggregation if existing else "sum", "cfg_line_agg",
                   format_func=lambda k: _AGG_OPTIONS[k])
    with c4:
        grp = _sel("🎨 Agrupar por", [None] + all_cols,
                   existing.color_column if existing else None, "cfg_line_grp")
    scheme = _sel("🎨 Paleta", _COLOR_SCHEMES,
                  existing.color_scheme if existing else "default", "cfg_line_scheme")
    c5, c6, c7 = st.columns(3)
    with c5:
        sv = st.checkbox("Valores", value=existing.show_values if existing else False, key="cfg_line_sv")
    with c6:
        sl = st.checkbox("Legenda", value=existing.show_legend if existing else True, key="cfg_line_sl")
    with c7:
        sg = st.checkbox("Grade", value=existing.show_grid if existing else True, key="cfg_line_sg")
    return VisualizationConfig(
        title=title or f"{y} por {x}",
        x_column=x, y_column=y, color_column=grp, aggregation=agg,
        color_scheme=scheme, show_values=sv, show_legend=sl, show_grid=sg,
    )


def _cfg_area(title, all_cols, num_cols, cat_cols, existing):
    c1, c2 = st.columns(2)
    with c1:
        x = _sel("📊 Eixo X", all_cols, existing.x_column if existing else None, "cfg_area_x")
    with c2:
        y = _sel("📈 Eixo Y", num_cols or all_cols,
                 existing.y_column if existing else None, "cfg_area_y")
    c3, c4 = st.columns(2)
    with c3:
        agg = _sel("📐 Agregação", list(_AGG_OPTIONS.keys()),
                   existing.aggregation if existing else "sum", "cfg_area_agg",
                   format_func=lambda k: _AGG_OPTIONS[k])
    with c4:
        grp = _sel("🎨 Agrupar por", [None] + all_cols,
                   existing.color_column if existing else None, "cfg_area_grp")
    return VisualizationConfig(
        title=title or f"{y} por {x}",
        x_column=x, y_column=y, color_column=grp, aggregation=agg,
    )


def _cfg_scatter(title, num_cols, all_cols, existing):
    c1, c2 = st.columns(2)
    with c1:
        x = _sel("📊 Eixo X", num_cols or all_cols,
                 existing.x_column if existing else None, "cfg_sc_x")
    with c2:
        y_opts = num_cols or all_cols
        y_def = (existing.y_column if existing and existing.y_column in y_opts
                 else (y_opts[1] if len(y_opts) > 1 else y_opts[0] if y_opts else None))
        y = _sel("📈 Eixo Y", y_opts, y_def, "cfg_sc_y")
    c3, c4 = st.columns(2)
    with c3:
        grp = _sel("🎨 Cor por", [None] + all_cols,
                   existing.color_column if existing else None, "cfg_sc_grp")
    with c4:
        sz = _sel("📐 Tamanho por", [None] + (num_cols or []),
                  existing.size_column if existing else None, "cfg_sc_sz")
    return VisualizationConfig(
        title=title or f"{y} vs {x}",
        x_column=x, y_column=y, color_column=grp, size_column=sz,
    )


def _cfg_histogram(title, num_cols, cat_cols, existing):
    if not num_cols:
        st.warning("Sem colunas numéricas.")
        return VisualizationConfig(title=title or "Histograma")
    x = _sel("📊 Coluna", num_cols, existing.x_column if existing else None, "cfg_hist_x")
    grp = _sel("🎨 Dividir por", [None] + cat_cols,
               existing.color_column if existing else None, "cfg_hist_grp")
    return VisualizationConfig(title=title or f"Distribuição de {x}",
                               x_column=x, color_column=grp)


def _cfg_box(title, num_cols, cat_cols, existing):
    if not num_cols:
        st.warning("Sem colunas numéricas.")
        return VisualizationConfig(title=title or "Box Plot")
    c1, c2 = st.columns(2)
    with c1:
        y = _sel("📊 Valores", num_cols, existing.y_column if existing else None, "cfg_box_y")
    with c2:
        x = _sel("📦 Agrupar por", [None] + cat_cols,
                 existing.x_column if existing else None, "cfg_box_x")
    return VisualizationConfig(title=title or f"Distribuição de {y}",
                               x_column=x, y_column=y)


def _cfg_heatmap(title, all_cols, num_cols, existing):
    c1, c2 = st.columns(2)
    with c1:
        x = _sel("📊 Eixo X", all_cols, existing.x_column if existing else None, "cfg_heat_x")
    with c2:
        y_opts = [c for c in all_cols if c != x] or all_cols
        y = _sel("📈 Eixo Y", y_opts, existing.y_column if existing else None, "cfg_heat_y")
    v = _sel("🎨 Valores", num_cols or all_cols,
             existing.color_column if existing else None, "cfg_heat_v")
    return VisualizationConfig(title=title or "Mapa de Calor",
                               x_column=x, y_column=y, color_column=v)


def _cfg_default(title, all_cols, num_cols, existing):
    c1, c2 = st.columns(2)
    with c1:
        x = _sel("📊 Eixo X", all_cols, existing.x_column if existing else None, "cfg_def_x")
    with c2:
        y = _sel("📈 Eixo Y", num_cols or all_cols,
                 existing.y_column if existing else None, "cfg_def_y")
    return VisualizationConfig(title=title, x_column=x, y_column=y)


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
