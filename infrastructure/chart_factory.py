"""
Chart Factory - Creates Plotly charts from visualization configurations.
Provides a unified interface for all chart types with Polars DataFrame support.
"""

from typing import Dict, List, Optional
import polars as pl
import plotly.express as px
import plotly.graph_objects as go

from domain.entities import VisualizationConfig, VisualizationType
from domain.value_objects import ChartColors

# Plotly color-sequence presets mapped to our scheme names
_COLOR_SEQUENCES: Dict[str, List[str]] = {
    "default": px.colors.qualitative.Plotly,
    "pastel":  px.colors.qualitative.Pastel,
    "dark":    px.colors.qualitative.Dark24,
    "vivid":   px.colors.qualitative.Vivid,
    "safe":    px.colors.qualitative.Safe,
    "d3":      px.colors.qualitative.D3,
    "set1":    px.colors.qualitative.Set1,
    "set2":    px.colors.qualitative.Set2,
}


class ChartFactory:
    """
    Factory for creating Plotly charts from visualization configurations.
    Implements the Factory Pattern for chart creation.
    """

    def __init__(self):
        self.colors = ChartColors()

    # ── Public API ───────────────────────────────────────────────────────────

    def create_chart(
        self,
        df: pl.DataFrame,
        config: VisualizationConfig,
        viz_type: VisualizationType,
        sort_by: str = "none",
    ) -> go.Figure:
        """
        Create a chart based on visualization configuration.

        Args:
            df: Polars DataFrame with the data.
            config: Visualization configuration.
            viz_type: Type of visualization to render.
            sort_by: Sorting mode — "none" | "x_asc" | "x_desc" |
                "value_asc" | "value_desc". Applied after aggregation.
        """
        chart_creators = {
            VisualizationType.BAR:       self._create_bar_chart,
            VisualizationType.LINE:      self._create_line_chart,
            VisualizationType.PIE:       self._create_pie_chart,
            VisualizationType.AREA:      self._create_area_chart,
            VisualizationType.SCATTER:   self._create_scatter_plot,
            VisualizationType.HISTOGRAM: self._create_histogram,
            VisualizationType.BOX:       self._create_box_plot,
            VisualizationType.HEATMAP:   self._create_heatmap,
        }

        creator = chart_creators.get(viz_type, self._create_bar_chart)
        fig = creator(df, config, sort_by)

        palette = self._palette(config)
        fig.update_layout(
            title={"text": config.title, "x": 0.5, "xanchor": "center"},
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font={"family": "Inter, sans-serif", "color": "#1E293B"},
            margin={"l": 60, "r": 40, "t": 60, "b": 60},
            showlegend=config.show_legend,
            colorway=palette,
        )

        if config.show_grid:
            fig.update_xaxes(gridcolor="#E2E8F0", linecolor="#CBD5E1")
            fig.update_yaxes(gridcolor="#E2E8F0", linecolor="#CBD5E1")
        else:
            fig.update_xaxes(showgrid=False)
            fig.update_yaxes(showgrid=False)

        return fig

    def export_figure_to_bytes(
        self, fig: go.Figure, format: str = "png", scale: float = 2.0
    ) -> bytes:
        """Export a figure to bytes (PNG/JPG/SVG)."""
        return fig.to_image(format=format, scale=scale)

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _palette(self, config: VisualizationConfig) -> List[str]:
        scheme = getattr(config, "color_scheme", "default") or "default"
        return _COLOR_SEQUENCES.get(scheme, _COLOR_SEQUENCES["default"])

    def _agg_expr(self, col: str, agg: str):
        """Return a Polars aggregation expression."""
        c = pl.col(col)
        if agg == "sum":    return c.sum()
        if agg == "mean":   return c.mean()
        if agg == "count":  return c.count()
        if agg == "min":    return c.min()
        if agg == "max":    return c.max()
        if agg == "median": return c.median()
        return c.sum()

    def _aggregate_single(
        self, df: pl.DataFrame, config: VisualizationConfig, y_col: str
    ) -> pl.DataFrame:
        """Aggregate df by x_column (+ optional color_column) for one y column."""
        if not config.x_column or not y_col:
            return df
        agg_alias = f"_agg_{y_col}"
        group_cols = [config.x_column]
        if config.color_column and config.color_column in df.columns and \
                config.color_column != config.x_column:
            group_cols.append(config.color_column)
        result = df.group_by(group_cols).agg(
            self._agg_expr(y_col, config.aggregation).alias(agg_alias)
        )
        # Rename aggregated alias back to original column name
        if agg_alias != y_col:
            result = result.rename({agg_alias: y_col})
        return result

    def _sort(
        self, df: pl.DataFrame, x_col: Optional[str], y_col: Optional[str],
        sort_by: str
    ) -> pl.DataFrame:
        """Apply sort_by logic to an already-aggregated frame."""
        if sort_by == "none" or not x_col:
            return df
        try:
            if sort_by == "x_asc":
                return df.sort(x_col)
            if sort_by == "x_desc":
                return df.sort(x_col, descending=True)
            if sort_by == "value_asc" and y_col and y_col in df.columns:
                return df.sort(y_col)
            if sort_by == "value_desc" and y_col and y_col in df.columns:
                return df.sort(y_col, descending=True)
        except Exception:
            pass
        return df

    def _y_columns(self, config: VisualizationConfig) -> List[str]:
        """Return effective list of Y columns (multi-Y or single fallback)."""
        if config.y_columns:
            return list(config.y_columns)
        if config.y_column:
            return [config.y_column]
        return []

    # ── Chart creators ───────────────────────────────────────────────────────

    def _create_bar_chart(
        self, df: pl.DataFrame, config: VisualizationConfig, sort_by: str = "none"
    ) -> go.Figure:
        """Bar chart — horizontal (VisualizationType.BAR) or vertical ('column')."""
        y_cols = self._y_columns(config)
        palette = self._palette(config)

        if not config.x_column or not y_cols:
            return go.Figure()

        # Aggregate each y column and merge results
        frames = []
        for yc in y_cols:
            if yc not in df.columns:
                continue
            agg = self._aggregate_single(df, config, yc)
            agg = self._sort(agg, config.x_column, yc, sort_by)
            frames.append((yc, agg))

        if not frames:
            return go.Figure()

        # Build figure with multiple traces for multi-Y
        pdf = frames[0][1].to_pandas()
        first_y = frames[0][0]

        if config.color_column and config.color_column in pdf.columns and len(y_cols) == 1:
            fig = px.bar(
                pdf, x=config.x_column, y=first_y,
                color=config.color_column,
                color_discrete_sequence=palette, barmode="group",
                text_auto=config.show_values,
            )
        else:
            # Merge all y-frames into one wide dataframe
            if len(frames) > 1:
                wide = frames[0][1].select([config.x_column, frames[0][0]])
                for yc, agg_df in frames[1:]:
                    wide = wide.join(
                        agg_df.select([config.x_column, yc]),
                        on=config.x_column, how="outer_coalesce",
                    )
                pdf = wide.to_pandas()

            fig = px.bar(
                pdf, x=config.x_column, y=[f[0] for f in frames],
                color_discrete_sequence=palette, barmode="group",
                text_auto=config.show_values,
            )

        return fig

    def _create_line_chart(
        self, df: pl.DataFrame, config: VisualizationConfig, sort_by: str = "none"
    ) -> go.Figure:
        y_cols = self._y_columns(config)
        palette = self._palette(config)
        if not config.x_column or not y_cols:
            return go.Figure()

        agg = self._aggregate_single(df, config, y_cols[0] if y_cols else config.y_column or "")
        agg = self._sort(agg, config.x_column, y_cols[0] if y_cols else None, sort_by)
        pdf = agg.to_pandas()

        if config.color_column and config.color_column in pdf.columns and len(y_cols) == 1:
            fig = px.line(
                pdf, x=config.x_column, y=y_cols[0],
                color=config.color_column,
                color_discrete_sequence=palette, markers=True,
            )
        else:
            fig = px.line(
                pdf, x=config.x_column, y=y_cols if len(y_cols) > 1 else y_cols[0],
                color_discrete_sequence=palette, markers=True,
            )

        if config.show_values:
            fig.update_traces(text=pdf[y_cols[0]] if y_cols else None, textposition="top center")

        return fig

    def _create_pie_chart(
        self, df: pl.DataFrame, config: VisualizationConfig, sort_by: str = "none"
    ) -> go.Figure:
        if not config.x_column or not config.y_column:
            return go.Figure()
        palette = self._palette(config)
        agg = self._aggregate_single(df, config, config.y_column)
        agg = self._sort(agg, config.x_column, config.y_column, sort_by)
        pdf = agg.to_pandas()

        text_info = "percent+label" if config.show_values else "percent"
        fig = px.pie(
            pdf, names=config.x_column, values=config.y_column,
            color_discrete_sequence=palette,
        )
        fig.update_traces(textposition="inside", textinfo=text_info)
        return fig

    def _create_area_chart(
        self, df: pl.DataFrame, config: VisualizationConfig, sort_by: str = "none"
    ) -> go.Figure:
        palette = self._palette(config)
        if not config.x_column or not config.y_column:
            return go.Figure()
        agg = self._aggregate_single(df, config, config.y_column)
        agg = self._sort(agg, config.x_column, config.y_column, sort_by)
        pdf = agg.to_pandas()

        if config.color_column and config.color_column in pdf.columns:
            fig = px.area(
                pdf, x=config.x_column, y=config.y_column,
                color=config.color_column, color_discrete_sequence=palette,
            )
        else:
            fig = px.area(
                pdf, x=config.x_column, y=config.y_column,
                color_discrete_sequence=palette,
            )
        return fig

    def _create_scatter_plot(
        self, df: pl.DataFrame, config: VisualizationConfig, sort_by: str = "none"
    ) -> go.Figure:
        palette = self._palette(config)
        pdf = df.to_pandas()
        kwargs: dict = {
            "x": config.x_column,
            "y": config.y_column,
            "color_discrete_sequence": palette,
        }
        if config.color_column and config.color_column in pdf.columns:
            kwargs["color"] = config.color_column
        if config.size_column and config.size_column in pdf.columns:
            kwargs["size"] = config.size_column
        return px.scatter(pdf, **kwargs)

    def _create_histogram(
        self, df: pl.DataFrame, config: VisualizationConfig, sort_by: str = "none"
    ) -> go.Figure:
        if not config.x_column:
            return go.Figure()
        palette = self._palette(config)
        pdf = df.to_pandas()
        return px.histogram(
            pdf, x=config.x_column,
            color=config.color_column if config.color_column else None,
            color_discrete_sequence=palette, nbins=30,
        )

    def _create_box_plot(
        self, df: pl.DataFrame, config: VisualizationConfig, sort_by: str = "none"
    ) -> go.Figure:
        palette = self._palette(config)
        pdf = df.to_pandas()
        if config.x_column and config.y_column:
            return px.box(
                pdf, x=config.x_column, y=config.y_column,
                color=config.color_column if config.color_column else None,
                color_discrete_sequence=palette,
            )
        elif config.y_column:
            return px.box(pdf, y=config.y_column, color_discrete_sequence=palette)
        return go.Figure()

    def _create_heatmap(
        self, df: pl.DataFrame, config: VisualizationConfig, sort_by: str = "none"
    ) -> go.Figure:
        if not config.x_column or not config.y_column:
            return go.Figure()
        agg_col = config.color_column or config.y_column
        try:
            agg_df = df.group_by([config.x_column, config.y_column]).agg(
                pl.col(agg_col).sum().alias("value")
            )
            pdf = agg_df.to_pandas()
            pivot_df = pdf.pivot(
                index=config.y_column, columns=config.x_column, values="value"
            ).fillna(0)
        except Exception:
            return go.Figure()

        return go.Figure(data=go.Heatmap(
            z=pivot_df.values,
            x=list(pivot_df.columns),
            y=list(pivot_df.index),
            colorscale="Viridis",
        ))
