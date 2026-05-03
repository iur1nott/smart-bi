"""
Canvas Component - Main dashboard editing area with visualization rendering.
Full port of dev-03 interactive features adapted to the supabase data model.
"""

from typing import Any, Callable, List, Optional
import re

import polars as pl
import streamlit as st

from domain.entities import (
    FileSheet,
    Visualization,
    VisualizationConfig,
    VisualizationType,
)


# ── viz_type string → VisualizationType enum ────────────────────────────────
_VIZ_TYPE_MAP = {
    "bar":          VisualizationType.BAR,
    "column":       VisualizationType.COLUMN_CHART,
    "column_chart": VisualizationType.COLUMN_CHART,
    "bar_chart":    VisualizationType.BAR_CHART,
    "line":         VisualizationType.LINE,
    "line_chart":   VisualizationType.LINE_CHART,
    "pie":          VisualizationType.PIE,
    "pie_chart":    VisualizationType.PIE_CHART,
    "area":         VisualizationType.AREA,
    "area_chart":   VisualizationType.AREA_CHART,
    "scatter":      VisualizationType.SCATTER,
    "scatter_plot": VisualizationType.SCATTER_PLOT,
    "histogram":    VisualizationType.HISTOGRAM,
    "box":          VisualizationType.BOX,
    "box_plot":     VisualizationType.BOX_PLOT,
    "heatmap":      VisualizationType.HEATMAP,
    "table":        VisualizationType.TABLE,
    "metric_card":  VisualizationType.METRIC_CARD,
    "measures":     VisualizationType.MEASURES,
}

_SORTABLE_TYPES   = {"bar", "column", "pie", "column_chart", "bar_chart", "pie_chart"}
_SEARCHABLE_TYPES = {
    "bar", "column", "line", "area", "scatter", "pie", "table", "histogram", "box",
    "column_chart", "bar_chart", "line_chart", "area_chart", "scatter_plot", "pie_chart",
}

_SORT_OPTS = {
    "none":       "Sem ordenação",
    "x_asc":      "Categoria A→Z",
    "x_desc":     "Categoria Z→A",
    "value_asc":  "Valor ↑",
    "value_desc": "Valor ↓",
}

_SORTABLE = {
    VisualizationType.COLUMN_CHART,
    VisualizationType.BAR_CHART,
    VisualizationType.PIE_CHART,
    VisualizationType.BAR,
    VisualizationType.PIE,
}

_SEARCHABLE = {
    VisualizationType.COLUMN_CHART,
    VisualizationType.BAR_CHART,
    VisualizationType.PIE_CHART,
    VisualizationType.LINE_CHART,
    VisualizationType.AREA_CHART,
    VisualizationType.SCATTER_PLOT,
    VisualizationType.TABLE,
    VisualizationType.BAR,
    VisualizationType.LINE,
    VisualizationType.PIE,
    VisualizationType.AREA,
    VisualizationType.SCATTER,
}


# ── Filter helpers ───────────────────────────────────────────────────────────

def _cast_filter_val(df: pl.DataFrame, col: str, val):
    """Cast a raw filter value to the column's native Polars dtype."""
    dtype = df.schema.get(col)
    if dtype in (pl.Int64, pl.Int32, pl.Int16, pl.Int8, pl.UInt64, pl.UInt32):
        try:
            return int(float(val))
        except (ValueError, TypeError):
            return val
    if dtype in (pl.Float64, pl.Float32):
        try:
            return float(val)
        except (ValueError, TypeError):
            return val
    return val


def render_viz_filters(viz_id: str, df: pl.DataFrame) -> pl.DataFrame:
    """Per-visualization filter panel; returns the filtered dataframe."""
    key = f"filters_{viz_id}"
    if key not in st.session_state:
        st.session_state[key] = []

    filters: list = st.session_state[key]
    n = len(filters)
    label = f"🔍 Filtros ({n} ativo{'s' if n != 1 else ''})" if n else "🔍 Filtros"

    with st.expander(label, expanded=n > 0):
        if st.button("➕ Adicionar filtro", key=f"add_f_{viz_id}"):
            filters.append({"col": df.columns[0], "op": "eq", "val": ""})
            st.rerun()

        to_remove = []
        for i, f in enumerate(filters):
            c1, c2, c3, c4 = st.columns([3, 2, 4, 1])

            with c1:
                idx = df.columns.index(f["col"]) if f["col"] in df.columns else 0
                col_sel = st.selectbox(
                    "col", df.columns, index=idx,
                    key=f"f_col_{viz_id}_{i}", label_visibility="collapsed",
                )
                filters[i]["col"] = col_sel

            dtype = df.schema.get(col_sel)
            is_numeric = dtype in (
                pl.Float64, pl.Float32, pl.Int64, pl.Int32,
                pl.Int16, pl.Int8, pl.UInt64, pl.UInt32,
            )
            is_date = dtype in (pl.Date, pl.Datetime)

            with c2:
                if is_numeric or is_date:
                    ops = {"eq": "=", "ne": "≠", "gt": ">", "lt": "<",
                           "gte": ">=", "lte": "<=",
                           "is_null": "é nulo", "is_not_null": "não é nulo"}
                else:
                    ops = {"eq": "=", "ne": "≠", "contains": "contém",
                           "in": "está em", "starts_with": "começa com",
                           "is_null": "é nulo", "is_not_null": "não é nulo"}
                cur_op = f["op"] if f["op"] in ops else list(ops)[0]
                op_sel = st.selectbox(
                    "op", list(ops.keys()),
                    index=list(ops.keys()).index(cur_op),
                    format_func=lambda k: ops[k],
                    key=f"f_op_{viz_id}_{i}", label_visibility="collapsed",
                )
                filters[i]["op"] = op_sel

            with c3:
                needs_val = op_sel not in ("is_null", "is_not_null")
                if needs_val:
                    if op_sel == "in":
                        val_input = st.text_input(
                            "val", value=str(f["val"]) if f["val"] != "" else "",
                            placeholder="val1, val2, val3",
                            key=f"f_val_{viz_id}_{i}", label_visibility="collapsed",
                        )
                    elif is_numeric:
                        try:
                            cur_num = float(f["val"]) if f["val"] != "" else 0.0
                        except (ValueError, TypeError):
                            cur_num = 0.0
                        val_input = st.number_input(
                            "val", value=cur_num,
                            key=f"f_val_{viz_id}_{i}", label_visibility="collapsed",
                        )
                    else:
                        unique_vals = df[col_sel].drop_nulls().unique().sort().to_list()
                        cur_sel = f["val"] if isinstance(f["val"], list) else []
                        val_input = st.multiselect(
                            "val", unique_vals,
                            default=[v for v in cur_sel if v in unique_vals],
                            key=f"f_val_{viz_id}_{i}", label_visibility="collapsed",
                        )
                    filters[i]["val"] = val_input
                else:
                    st.empty()
                    filters[i]["val"] = ""

            with c4:
                if st.button("❌", key=f"f_rm_{viz_id}_{i}"):
                    to_remove.append(i)

        if to_remove:
            st.session_state[key] = [f for j, f in enumerate(filters) if j not in to_remove]
            st.rerun()

    # ── Apply filters ────────────────────────────────────────────────────────
    result = df
    for f in st.session_state.get(key, []):
        col, op, val = f["col"], f["op"], f["val"]
        if col not in result.columns:
            continue
        try:
            c = pl.col(col)
            if op == "is_null":
                result = result.filter(c.is_null())
            elif op == "is_not_null":
                result = result.filter(c.is_not_null())
            elif op == "in":
                vals = [v.strip() for v in str(val).split(",") if v.strip()]
                result = result.filter(c.cast(pl.String).is_in(vals))
            elif op == "contains":
                result = result.filter(c.cast(pl.String).str.contains(str(val), literal=True))
            elif op == "starts_with":
                result = result.filter(c.cast(pl.String).str.starts_with(str(val)))
            elif op == "eq":
                if isinstance(val, list):
                    result = result.filter(c.cast(pl.String).is_in([str(v) for v in val]))
                else:
                    result = result.filter(c == _cast_filter_val(result, col, val))
            elif op == "ne":
                result = result.filter(c != _cast_filter_val(result, col, val))
            elif op == "gt":
                result = result.filter(c > _cast_filter_val(result, col, val))
            elif op == "lt":
                result = result.filter(c < _cast_filter_val(result, col, val))
            elif op == "gte":
                result = result.filter(c >= _cast_filter_val(result, col, val))
            elif op == "lte":
                result = result.filter(c <= _cast_filter_val(result, col, val))
        except Exception:
            pass

    return result


def render_interactive_controls(
    viz_id: str,
    df: pl.DataFrame,
    viz_type_or_config,
    config: Optional[VisualizationConfig] = None,
) -> tuple:
    """
    Search bar + sort dropdown. Returns (filtered_df, sort_by_str).
    Accepts either (viz_id, df, config) from dev-03 or
    (viz_id, df, viz_type_str, config) from merge code.
    """
    # Normalise arguments: if viz_type_or_config is a string it's a viz_type str
    if isinstance(viz_type_or_config, str):
        viz_type_str = viz_type_or_config
        effective_config = config
        vtype = _VIZ_TYPE_MAP.get(viz_type_str)
    else:
        effective_config = viz_type_or_config
        vtype = getattr(effective_config, "visualization_type", None) if effective_config else None

    if vtype not in _SEARCHABLE:
        return df, "none"

    has_sort = vtype in _SORTABLE
    c_search, c_sort = st.columns([5, 3])

    with c_search:
        search = st.text_input(
            "busca", placeholder="🔍 Buscar na visualização...",
            key=f"search_{viz_id}", label_visibility="collapsed",
        )

    sort_by = "none"
    with c_sort:
        if has_sort:
            sort_by = st.selectbox(
                "ordenar", options=list(_SORT_OPTS.keys()),
                format_func=lambda k: _SORT_OPTS[k],
                key=f"sort_{viz_id}", label_visibility="collapsed",
            )
        else:
            st.empty()

    if search and effective_config:
        try:
            if vtype == VisualizationType.TABLE:
                str_cols = [c for c in df.columns
                            if df.schema.get(c) in (pl.Utf8, pl.String)]
                if str_cols:
                    mask = pl.lit(False)
                    for col in str_cols:
                        mask = mask | (
                            pl.col(col).cast(pl.String).str.to_lowercase()
                            .str.contains(search.lower(), literal=True)
                        )
                    df = df.filter(mask)
            elif effective_config.x_column and effective_config.x_column in df.columns:
                df = df.filter(
                    pl.col(effective_config.x_column).cast(pl.String).str.to_lowercase()
                    .str.contains(search.lower(), literal=True)
                )
        except Exception:
            pass

    return df, sort_by


# ── Measures ─────────────────────────────────────────────────────────────────

def _apply_measures(df: pl.DataFrame, measures: list) -> pl.DataFrame:
    """Add computed columns from measure expressions like [col1] + [col2]."""
    for m in measures:
        name = m.get("name", "")
        expr_str = m.get("expression", "")
        if not name or not expr_str:
            continue
        try:
            tokens = re.split(r"\s*([+\-*/])\s*", expr_str)
            polars_expr = None
            pending_op = None
            for tok in tokens:
                tok = tok.strip()
                if not tok:
                    continue
                if tok in ("+", "-", "*", "/"):
                    pending_op = tok
                    continue
                col_match = re.match(r"^\[(.+)\]$", tok)
                if col_match:
                    col_name = col_match.group(1)
                    if col_name not in df.columns:
                        continue
                    term = pl.col(col_name).cast(pl.Float64, strict=False)
                else:
                    try:
                        term = pl.lit(float(tok))
                    except ValueError:
                        continue
                if polars_expr is None:
                    polars_expr = term
                elif pending_op == "+":
                    polars_expr = polars_expr + term
                elif pending_op == "-":
                    polars_expr = polars_expr - term
                elif pending_op == "*":
                    polars_expr = polars_expr * term
                elif pending_op == "/":
                    polars_expr = polars_expr / term
                pending_op = None
            if polars_expr is not None:
                df = df.with_columns(polars_expr.alias(name))
        except Exception:
            pass
    return df


def render_measures_panel(
    viz_id: str,
    analysis_or_dashboard_id,
    on_update_measures: Optional[Any],
    df: Optional[pl.DataFrame] = None,
) -> None:
    """Builder UI for calculated measures; works with both dev-03 analysis and merge dashboard_id."""
    # Support both calling conventions:
    # dev-03: render_measures_panel(viz_id, analysis_obj, callback, df=df)
    # merge:  render_measures_panel(viz_id, dashboard_id_str, callback, df=df)
    if isinstance(analysis_or_dashboard_id, str):
        # merge mode: state stored by dashboard_id
        key = f"measures_{analysis_or_dashboard_id}"
        if key not in st.session_state:
            st.session_state[key] = []
        measures: list = st.session_state[key]
    else:
        # dev-03 mode: measures stored on analysis object
        analysis = analysis_or_dashboard_id
        measures: list = list(getattr(analysis, "measures", None) or [])

    all_cols: list = list(df.columns) if df is not None else []
    default_col = all_cols[0] if all_cols else ""
    _OPS = ["+", "-", "*", "/"]
    parts_key = f"mparts_{viz_id}"

    st.markdown("**📐 Medidas Calculadas**")
    st.caption(
        "Combine colunas com `+  −  ×  ÷`. "
        "As medidas ficam disponíveis como colunas em todos os gráficos."
    )

    to_del = []
    for i, m in enumerate(measures):
        c1, c2, c3 = st.columns([3, 6, 1])
        with c1:
            st.text_input("Nome", value=m.get("name", ""),
                          key=f"mname_{viz_id}_{i}", disabled=True,
                          label_visibility="collapsed")
        with c2:
            st.text_input("Expr", value=m.get("expression", ""),
                          key=f"mexpr_{viz_id}_{i}", disabled=True,
                          label_visibility="collapsed")
        with c3:
            if st.button("❌", key=f"mdel_{viz_id}_{i}"):
                to_del.append(i)

    if to_del:
        updated = [m for j, m in enumerate(measures) if j not in to_del]
        if isinstance(analysis_or_dashboard_id, str):
            st.session_state[key] = updated
        if on_update_measures:
            on_update_measures(updated)
        st.rerun()

    st.markdown("---")
    st.markdown("**➕ Nova Medida**")

    if parts_key not in st.session_state:
        st.session_state[parts_key] = [
            {"op": "", "col": default_col},
            {"op": "/", "col": default_col},
        ]

    parts: list = st.session_state[parts_key]
    new_name = st.text_input("Nome da Medida", placeholder="ex: Ticket Médio",
                              key=f"mnew_name_{viz_id}")

    to_rm_parts = []
    for i, part in enumerate(parts):
        if i == 0:
            c_val, c_rm = st.columns([8, 1])
        else:
            c_op, c_val, c_rm = st.columns([1, 7, 1])
            with c_op:
                cur_op = part["op"] if part["op"] in _OPS else "/"
                parts[i]["op"] = st.selectbox(
                    "op", _OPS, index=_OPS.index(cur_op),
                    key=f"mop_{viz_id}_{i}", label_visibility="collapsed",
                )
        with c_val:
            if all_cols:
                cur_col = part["col"] if part["col"] in all_cols else default_col
                parts[i]["col"] = st.selectbox(
                    "col", all_cols, index=all_cols.index(cur_col),
                    key=f"mcol_{viz_id}_{i}", label_visibility="collapsed",
                )
        with c_rm:
            if len(parts) > 1 and st.button("❌", key=f"mrm_{viz_id}_{i}"):
                to_rm_parts.append(i)

    if to_rm_parts:
        st.session_state[parts_key] = [p for j, p in enumerate(parts) if j not in to_rm_parts]
        st.rerun()

    if st.button("➕ Adicionar campo", key=f"madd_{viz_id}"):
        parts.append({"op": "+", "col": default_col})
        st.rerun()

    tokens = []
    for i, part in enumerate(parts):
        col = part.get("col", "")
        if not col:
            continue
        if i > 0 and tokens:
            tokens.append(part.get("op", "+"))
        tokens.append(f"[{col}]")
    expr = " ".join(tokens)
    if expr:
        st.caption(f"**Expressão:** `{expr}`")

    if st.button("💾 Adicionar Medida", key=f"msave_{viz_id}", type="primary"):
        name = new_name.strip()
        if name and expr:
            measures.append({"name": name, "expression": expr})
            if isinstance(analysis_or_dashboard_id, str):
                st.session_state[key] = measures
            if on_update_measures:
                on_update_measures(measures)
            if parts_key in st.session_state:
                del st.session_state[parts_key]
            st.success(f"Medida '{name}' adicionada!")
            st.rerun()
        else:
            st.warning("Preencha o nome e defina ao menos um campo.")


# ── Canvas + visualization rendering ────────────────────────────────────────

def render_canvas(
    visualizations: Optional[List] = None,
    data_service: Any = None,
    sheet_id: str = "",
    on_update_visualization: Any = None,
    on_delete_visualization: Any = None,
    on_add_comment: Any = None,
    sheet: Optional[FileSheet] = None,
    dashboard_id: str = "",
    on_update_measures: Optional[Any] = None,
    # dev-03 parameters
    slide: Optional[Any] = None,
    analysis_id: str = "",
    analysis: Any = None,
) -> None:
    """
    Render the main canvas with all visualizations.
    Supports both merge (dashboard + visualizations list) and dev-03 (slide) modes.
    """
    from infrastructure.chart_factory import ChartFactory
    chart_factory = ChartFactory()

    # ── dev-03 mode: slide-based ──────────────────────────────────────────────
    if slide is not None:
        col1, col2 = st.columns([5, 1])
        with col1:
            new_title = st.text_input(
                "Título do slide", value=slide.title, key=f"slide_title_{slide.id}",
                label_visibility="collapsed", placeholder="Título do slide…",
            )
        with col2:
            st.caption(f"{len(slide.visualizations)} visual{'is' if len(slide.visualizations) != 1 else ''}")

        df = data_service.get_cached_data(analysis_id)
        if df is None:
            st.warning("⚠️ No data loaded. Please upload an XLSX file.")
            return

        measures = getattr(analysis, "measures", None) or []
        if measures:
            try:
                df = data_service.compute_measures(df, measures)
            except Exception:
                pass

        if not slide.visualizations:
            st.markdown(
                """
            <div style='border: 2px dashed #CBD5E1; border-radius: 12px; padding: 64px 32px;
                        text-align: center; color: #94A3B8; margin: 24px 0;
                        background: #F8FAFC;'>
                <div style='font-size: 2.5rem; margin-bottom: 12px;'>📊</div>
                <div style='font-size: 1.1rem; font-weight: 600; color: #64748B; margin-bottom: 6px;'>
                    Slide vazio
                </div>
                <div style='font-size: 0.875rem;'>
                    Use o painel à direita para adicionar gráficos, tabelas e métricas
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )
            return

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
                analysis=analysis,
                on_update_measures=on_update_measures,
            )
        return

    # ── merge mode: dashboard visualizations list ────────────────────────────
    df = data_service.get_cached_sheet(sheet_id)

    if df is None:
        st.markdown(
            """
            <div style='background:linear-gradient(135deg,#FEF3C7 0%,#FDE68A 100%);
                        border-radius:12px;padding:24px;text-align:center;margin:20px 0;'>
                <div style='font-size:32px;margin-bottom:10px;'>⚠️</div>
                <h4 style='color:#92400E;margin:0;'>Nenhum dado carregado</h4>
                <p style='color:#B45309;margin-top:8px;'>Faça upload de um arquivo XLSX para começar</p>
            </div>""",
            unsafe_allow_html=True,
        )
        return

    measures = st.session_state.get(f"measures_{dashboard_id}", [])
    if measures:
        df = _apply_measures(df, measures)

    if not visualizations:
        st.markdown(
            """<div style='border:2px dashed #CBD5E1;border-radius:16px;padding:60px;
                           text-align:center;margin:20px 0;background:#F8FAFC;'>
                 <div style='font-size:48px;margin-bottom:16px;'>📈</div>
                 <h3 style='color:#475569;margin:0;'>Dashboard Vazio</h3>
                 <p style='color:#94A3B8;margin-top:8px;'>Adicione visualizações usando o painel à direita</p>
               </div>""",
            unsafe_allow_html=True,
        )
        return

    n = len(visualizations)
    st.markdown(
        f"""<div style='background:white;border-radius:12px;padding:16px 20px;
                        margin-bottom:16px;border:1px solid #E2E8F0;'>
              <h3 style='margin:0;color:#1E293B;'>📊 Dashboard</h3>
              <span style='color:#64748B;font-size:14px;'>{n} visualizaç{'ão' if n==1 else 'ões'}</span>
            </div>""",
        unsafe_allow_html=True,
    )

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
            dashboard_id=dashboard_id,
            on_update_measures=on_update_measures,
        )


def render_visualization(
    viz: Any,
    df: pl.DataFrame,
    chart_factory: Any,
    index: int,
    on_update: Any = None,
    on_delete: Any = None,
    on_add_comment: Any = None,
    # merge params
    sheet: Optional[FileSheet] = None,
    dashboard_id: str = "",
    # dev-03 params
    slide_id: str = "",
    analysis: Any = None,
    on_update_measures: Optional[Any] = None,
) -> None:
    """Render one visualization card with filters, sort, and comment."""
    # Detect model type (merge Visualization vs dev-03 SlideVisualization)
    is_dev03 = hasattr(viz, "id") and not hasattr(viz, "viz_id")
    viz_id = viz.id if is_dev03 else viz.viz_id

    # Determine if this is a measures panel
    if is_dev03:
        is_measures = (
            viz.config is not None
            and viz.config.visualization_type == VisualizationType.MEASURES
        )
    else:
        is_measures = getattr(viz, "viz_type", "") == "measures"

    title = (viz.config.title if viz.config and viz.config.title else
             f"Visualização {index + 1}")

    st.markdown('<div class="viz-card">', unsafe_allow_html=True)

    col_title, col_actions = st.columns([6, 1])
    with col_title:
        st.markdown(f'<p class="viz-card-title">{title}</p>', unsafe_allow_html=True)
    with col_actions:
        if is_dev03:
            btn_cols = st.columns(2) if not is_measures else st.columns(1)
            if not is_measures:
                with btn_cols[0]:
                    if st.button("✏️", key=f"edit_{viz_id}", help="Configurar"):
                        st.session_state.editing_viz_id = viz_id
                        st.session_state.editing_slide_id = slide_id
                with btn_cols[1]:
                    if st.button("🗑", key=f"delete_{viz_id}", help="Excluir"):
                        if on_delete:
                            on_delete(slide_id, viz_id)
                        st.rerun()
            else:
                with btn_cols[0]:
                    if st.button("🗑", key=f"delete_{viz_id}", help="Excluir"):
                        if on_delete:
                            on_delete(slide_id, viz_id)
                        st.rerun()
        else:
            if not is_measures:
                b1, b2, b3 = st.columns(3)
                with b1:
                    if st.button("✏️", key=f"edit_{viz_id}", help="Configurar"):
                        st.session_state.editing_viz_id = viz_id
                        st.rerun()
                with b2:
                    if st.button("💬", key=f"cmt_{viz_id}", help="Comentário"):
                        st.session_state.commenting_viz_id = viz_id
                with b3:
                    if st.button("🗑️", key=f"del_{viz_id}", help="Excluir"):
                        if on_delete:
                            on_delete(viz_id)
                        st.rerun()
            else:
                if st.button("🗑️", key=f"del_{viz_id}", help="Excluir"):
                    if on_delete:
                        on_delete(viz_id)
                    st.rerun()

    if is_measures:
        render_measures_panel(
            viz_id,
            analysis if is_dev03 else dashboard_id,
            on_update_measures,
            df=df,
        )
    elif viz.config:
        df_filtered = render_viz_filters(viz_id, df)

        if is_dev03:
            df_filtered, sort_by = render_interactive_controls(
                viz_id, df_filtered, viz.config
            )
        else:
            df_filtered, sort_by = render_interactive_controls(
                viz_id, df_filtered, viz.viz_type, viz.config
            )

        try:
            if is_dev03:
                vtype = viz.config.visualization_type
                if vtype == VisualizationType.TABLE:
                    render_table(viz, df_filtered)
                elif vtype == VisualizationType.METRIC_CARD:
                    render_metric_card(viz, df_filtered)
                else:
                    fig = chart_factory.create_chart(
                        df_filtered, viz.config, sort_by=sort_by
                    )
                    st.plotly_chart(fig, width='stretch', key=f"chart_{viz_id}")
            else:
                if viz.viz_type == "table":
                    render_table(viz, df_filtered)
                elif viz.viz_type == "metric_card":
                    render_metric_card(viz, df_filtered)
                else:
                    render_chart(viz, df_filtered, chart_factory, sort_by)
        except Exception as e:
            st.error(f"Erro ao renderizar: {e}")

        if viz.comment:
            st.caption(f"💬 {viz.comment}")
        with st.expander("💬 Comentário", expanded=False):
            comment = st.text_area(
                "Comentário", value=viz.comment or "",
                key=f"comment_{viz_id}", height=60,
                label_visibility="collapsed",
            )
            if st.button("Salvar", key=f"save_comment_{viz_id}"):
                if on_add_comment:
                    if is_dev03:
                        on_add_comment(slide_id, viz_id, comment)
                    else:
                        on_add_comment(viz_id, comment)
                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


def render_chart(
    viz: Any,
    df: pl.DataFrame,
    chart_factory: Any,
    sort_by: str = "none",
) -> None:
    config = viz.config
    if not config:
        return
    viz_type = _VIZ_TYPE_MAP.get(viz.viz_type, VisualizationType.BAR)
    try:
        fig = chart_factory.create_chart(df, config, viz_type, sort_by=sort_by)
        st.plotly_chart(fig, use_container_width=True, key=f"chart_{viz.viz_id}")
    except Exception as e:
        st.error(f"Erro ao criar gráfico: {e}")


def render_table(viz: Any, df: pl.DataFrame) -> None:
    config = viz.config
    if not config:
        return
    if config.y_columns:
        cols = [c for c in config.y_columns if c in df.columns]
    elif config.x_column or config.y_column:
        cols = [c for c in [config.x_column, config.y_column, config.color_column]
                if c and c in df.columns]
    else:
        cols = list(df.columns[:10])
    if not cols:
        st.warning("Nenhuma coluna válida.")
        return
    table_df = df.select(cols)
    st.dataframe(table_df.head(200).to_pandas(), use_container_width=True, height=300)


def render_metric_card(viz: Any, df: pl.DataFrame) -> None:
    config = viz.config
    if not config or not config.y_column:
        st.warning("Selecione uma coluna para a métrica")
        return
    try:
        col = df[config.y_column]
        agg_map = {"mean": (col.mean, "Média"), "sum": (col.sum, "Total"),
                   "count": (col.count, "Contagem"), "min": (col.min, "Mínimo"),
                   "max": (col.max, "Máximo")}
        fn, label = agg_map.get(config.aggregation, (col.sum, "Total"))
        value = fn()
        if isinstance(value, float):
            if abs(value) >= 1_000_000:
                fmt = f"{value / 1_000_000:.2f}M"
            elif abs(value) >= 1_000:
                fmt = f"{value / 1_000:.2f}K"
            else:
                fmt = f"{value:.2f}"
        else:
            fmt = f"{value:,}"
        st.markdown(
            f"""<div style='background:linear-gradient(135deg,#3B82F6 0%,#1D4ED8 100%);
                            border-radius:12px;padding:28px 24px;color:white;
                            text-align:center;margin:8px 0;
                            box-shadow:0 4px 16px rgba(59,130,246,.35);'>
                  <div style='font-size:2.6rem;font-weight:800;letter-spacing:-1px;margin-bottom:6px;'>{fmt}</div>
                  <div style='font-size:.9rem;opacity:.85;font-weight:500;'>
                    {config.title or f"{label} — {config.y_column}"}
                  </div>
                </div>""",
            unsafe_allow_html=True,
        )
    except Exception as e:
        st.error(f"Erro ao calcular métrica: {e}")


def render_slide_navigator(
    slides: List[Any],
    current_slide_id: str,
    on_slide_change: Callable,
    on_add_slide: Callable,
    on_delete_slide: Callable,
) -> None:
    """Barra de navegação de slides em estilo tab bar."""
    st.markdown(
        "<hr style='border:none;border-top:1px solid #E2E8F0;margin:24px 0 12px;'/>",
        unsafe_allow_html=True,
    )

    n = len(slides)
    col_widths = [3] * min(n, 8) + [1]
    cols = st.columns(col_widths)

    for i, slide in enumerate(slides[:8]):
        with cols[i]:
            is_current = slide.id == current_slide_id
            short = slide.title[:14] + "…" if len(slide.title) > 14 else slide.title
            label = f"**{i+1}. {short}**" if is_current else f"{i+1}. {short}"
            if st.button(
                label,
                key=f"nav_slide_{slide.id}",
                width='stretch',
                type="primary" if is_current else "secondary",
            ):
                on_slide_change(slide.id)
                st.rerun()

    with cols[-1]:
        if st.button("＋", width='stretch', help="Novo slide"):
            on_add_slide()
            st.rerun()

    if n > 1:
        _, col_del = st.columns([6, 1])
        with col_del:
            if st.button(
                "🗑 Deletar slide",
                width='stretch',
                help="Remover slide atual",
            ):
                on_delete_slide(current_slide_id)
                st.rerun()
