"""
Chart Factory - Creates visualization charts using Plotly.
Follows Factory Pattern for creating different chart types.
"""

from typing import Dict, Any, Optional, List
import polars as pl
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio

from domain.entities import VisualizationType, VisualizationConfig


class ChartFactory:
    """Factory class for creating different types of charts using Plotly."""

    COLOR_SCHEMES: Dict[str, list] = {
        "default": px.colors.qualitative.Plotly,
        "pastel":  px.colors.qualitative.Pastel,
        "dark":    px.colors.qualitative.Dark24,
        "vivid":   px.colors.qualitative.Vivid,
        "safe":    px.colors.qualitative.Safe,
        "d3":      px.colors.qualitative.D3,
        "set1":    px.colors.qualitative.Set1,
        "set2":    px.colors.qualitative.Set2,
    }

    def __init__(self, default_height: int = 400, default_width: int = 600):
        self.default_height = default_height
        self.default_width = default_width

    # ─────────────────────────────────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────────────────────────────────

    def create_chart(self, df: pl.DataFrame, config: VisualizationConfig) -> go.Figure:
        """Create a Plotly figure based on VisualizationConfig."""
        dispatch = {
            VisualizationType.COLUMN_CHART: self._create_column_chart,
            VisualizationType.BAR_CHART:    self._create_bar_chart,
            VisualizationType.LINE_CHART:   self._create_line_chart,
            VisualizationType.AREA_CHART:   self._create_area_chart,
            VisualizationType.PIE_CHART:    self._create_pie_chart,
            VisualizationType.SCATTER_PLOT: self._create_scatter_plot,
            VisualizationType.HISTOGRAM:    self._create_histogram,
            VisualizationType.BOX_PLOT:     self._create_box_plot,
            VisualizationType.HEATMAP:      self._create_heatmap,
        }
        method = dispatch.get(config.visualization_type)
        fig = method(df, config) if method else self._create_empty_figure(
            f"Tipo '{config.visualization_type.value}' não implementado"
        )
        self._apply_common_style(fig, config)
        return fig

    def export_figure_to_bytes(
        self, fig: go.Figure, format: str = "png", scale: float = 2.0
    ) -> bytes:
        return pio.to_image(fig, format=format, scale=scale)

    def export_figure_to_base64(
        self, fig: go.Figure, format: str = "png", scale: float = 2.0
    ) -> str:
        import base64
        return base64.b64encode(self.export_figure_to_bytes(fig, format, scale)).decode()

    def get_available_color_schemes(self) -> List[str]:
        return list(self.COLOR_SCHEMES.keys())

    # ─────────────────────────────────────────────────────────────────────────
    # Private helpers
    # ─────────────────────────────────────────────────────────────────────────

    def _colors(self, config: VisualizationConfig) -> list:
        return self.COLOR_SCHEMES.get(config.color_scheme, self.COLOR_SCHEMES["default"])

    def _agg_expr(self, col: str, agg: str) -> pl.Expr:
        return {
            "sum":   pl.col(col).sum(),
            "mean":  pl.col(col).mean(),
            "count": pl.col(col).count(),
            "min":   pl.col(col).min(),
            "max":   pl.col(col).max(),
        }.get(agg, pl.col(col).sum())

    def _aggregate(
        self,
        df: pl.DataFrame,
        x_col: str,
        y_cols: List[str],
        agg: str,
        group_col: Optional[str] = None,
    ) -> pl.DataFrame:
        """GroupBy x_col (+ group_col) and aggregate each y_col."""
        valid_y = [c for c in y_cols if c and c in df.columns]
        if not valid_y or x_col not in df.columns:
            return df

        group_keys = [x_col]
        if group_col and group_col in df.columns and group_col != x_col:
            group_keys.append(group_col)

        return (
            df.group_by(group_keys)
            .agg([self._agg_expr(c, agg) for c in valid_y])
            .sort(x_col)
        )

    def _fmt_values(self, values: list) -> List[str]:
        """Format a list of values for chart text labels."""
        out = []
        for v in values:
            if v is None:
                out.append("")
            elif isinstance(v, float):
                out.append(f"{v:,.2f}")
            else:
                out.append(str(v))
        return out

    def _y_cols_from_config(self, config: VisualizationConfig) -> List[str]:
        """Return the effective list of Y columns from config."""
        if config.y_columns:
            return [c for c in config.y_columns if c]
        if config.y_column:
            return [config.y_column]
        return []

    # ─────────────────────────────────────────────────────────────────────────
    # Chart builders
    # ─────────────────────────────────────────────────────────────────────────

    def _create_column_chart(
        self, df: pl.DataFrame, config: VisualizationConfig
    ) -> go.Figure:
        """Vertical bar (column) chart – supports multiple Y metrics."""
        y_cols = self._y_cols_from_config(config)
        if not y_cols or not config.x_column:
            return self._create_empty_figure("Selecione as colunas de Categoria e Valor")

        df_plot = self._aggregate(
            df, config.x_column, y_cols, config.aggregation, config.color_column
        )
        colors = self._colors(config)
        fig = go.Figure()

        for i, col in enumerate(y_cols):
            values = df_plot[col].to_list()
            fig.add_trace(
                go.Bar(
                    x=df_plot[config.x_column].to_list(),
                    y=values,
                    name=col,
                    marker_color=colors[i % len(colors)],
                    text=self._fmt_values(values) if config.show_values else None,
                    textposition="outside" if config.show_values else "none",
                )
            )

        fig.update_layout(
            barmode="group",
            xaxis_title=config.x_column,
            yaxis_title="Valor",
            hovermode="x unified",
        )
        return fig

    def _create_bar_chart(
        self, df: pl.DataFrame, config: VisualizationConfig
    ) -> go.Figure:
        """Horizontal bar chart – supports multiple Y metrics."""
        y_cols = self._y_cols_from_config(config)
        if not y_cols or not config.x_column:
            return self._create_empty_figure("Selecione as colunas de Categoria e Valor")

        df_plot = self._aggregate(df, config.x_column, y_cols, config.aggregation)
        colors = self._colors(config)
        fig = go.Figure()

        for i, col in enumerate(y_cols):
            values = df_plot[col].to_list()
            fig.add_trace(
                go.Bar(
                    y=df_plot[config.x_column].to_list(),
                    x=values,
                    name=col,
                    orientation="h",
                    marker_color=colors[i % len(colors)],
                    text=self._fmt_values(values) if config.show_values else None,
                    textposition="outside" if config.show_values else "none",
                )
            )

        fig.update_layout(
            barmode="group",
            xaxis_title="Valor",
            yaxis_title=config.x_column,
            hovermode="y unified",
        )
        return fig

    def _create_line_chart(
        self, df: pl.DataFrame, config: VisualizationConfig
    ) -> go.Figure:
        """Line chart with optional aggregation and value labels."""
        x_col = config.x_column
        y_col = config.y_column
        if not x_col or not y_col:
            return self._create_empty_figure("Selecione colunas X e Y")

        df_plot = self._aggregate(df, x_col, [y_col], config.aggregation, config.color_column)
        pdf = df_plot.to_pandas()
        grp = config.color_column if config.color_column and config.color_column in pdf.columns else None

        fig = px.line(
            pdf, x=x_col, y=y_col, color=grp,
            color_discrete_sequence=self._colors(config),
            markers=True,
        )

        if config.show_values:
            fig.update_traces(
                text=pdf[y_col].round(2).astype(str).tolist(),
                textposition="top center",
                mode="lines+markers+text",
            )

        return fig

    def _create_area_chart(
        self, df: pl.DataFrame, config: VisualizationConfig
    ) -> go.Figure:
        """Area chart with optional aggregation and value labels."""
        x_col = config.x_column
        y_col = config.y_column
        if not x_col or not y_col:
            return self._create_empty_figure("Selecione colunas X e Y")

        df_plot = self._aggregate(df, x_col, [y_col], config.aggregation, config.color_column)
        pdf = df_plot.to_pandas()
        grp = config.color_column if config.color_column and config.color_column in pdf.columns else None

        fig = px.area(
            pdf, x=x_col, y=y_col, color=grp,
            color_discrete_sequence=self._colors(config),
        )

        if config.show_values:
            fig.update_traces(
                text=pdf[y_col].round(2).astype(str).tolist(),
                textposition="top center",
                mode="lines+markers+text",
            )

        return fig

    def _create_pie_chart(
        self, df: pl.DataFrame, config: VisualizationConfig
    ) -> go.Figure:
        """Pie chart with real aggregation."""
        x_col = config.x_column
        y_col = config.y_column or (config.y_columns[0] if config.y_columns else None)
        if not x_col or not y_col:
            return self._create_empty_figure("Selecione colunas de Categoria e Valor")

        df_plot = self._aggregate(df, x_col, [y_col], config.aggregation)
        pdf = df_plot.to_pandas()

        fig = px.pie(
            pdf, names=x_col, values=y_col,
            color_discrete_sequence=self._colors(config),
        )
        fig.update_traces(
            textinfo="value+percent+label" if config.show_values else "percent+label"
        )
        return fig

    def _create_scatter_plot(
        self, df: pl.DataFrame, config: VisualizationConfig
    ) -> go.Figure:
        """Scatter plot (raw data, no aggregation)."""
        x_col = config.x_column
        y_col = config.y_column
        if not x_col or not y_col:
            return self._create_empty_figure("Selecione colunas X e Y")

        pdf = df.to_pandas()
        fig = px.scatter(
            pdf, x=x_col, y=y_col,
            color=config.color_column if config.color_column else None,
            size=config.size_column if config.size_column else None,
            color_discrete_sequence=self._colors(config),
            opacity=0.7,
        )

        if config.show_values:
            fig.update_traces(
                text=pdf[y_col].astype(str).tolist(),
                textposition="top center",
            )

        return fig

    def _create_histogram(
        self, df: pl.DataFrame, config: VisualizationConfig
    ) -> go.Figure:
        """Histogram (distribution of one column)."""
        x_col = config.x_column
        if not x_col:
            return self._create_empty_figure("Selecione uma coluna para o histograma")

        pdf = df.to_pandas()
        fig = px.histogram(
            pdf, x=x_col,
            color=config.color_column if config.color_column else None,
            barmode="overlay",
            opacity=0.75,
            color_discrete_sequence=self._colors(config),
        )

        if config.show_values:
            fig.update_traces(texttemplate="%{y}", textposition="outside")

        return fig

    def _create_box_plot(
        self, df: pl.DataFrame, config: VisualizationConfig
    ) -> go.Figure:
        """Box plot (raw data)."""
        y_col = config.y_column
        if not y_col:
            return self._create_empty_figure("Selecione a coluna de valores para o box plot")

        pdf = df.to_pandas()
        fig = px.box(
            pdf,
            x=config.x_column if config.x_column else None,
            y=y_col,
            color=config.color_column if config.color_column else None,
            color_discrete_sequence=self._colors(config),
        )
        return fig

    def _create_heatmap(
        self, df: pl.DataFrame, config: VisualizationConfig
    ) -> go.Figure:
        """Heatmap with pivot aggregation."""
        x_col = config.x_column
        y_col = config.y_column
        if not x_col or not y_col:
            return self._create_empty_figure("Selecione colunas X e Y para o heatmap")

        value_col = config.color_column or y_col
        pivot_pandas = (
            df.group_by([x_col, y_col])
            .agg(self._agg_expr(value_col, config.aggregation).alias("value"))
            .to_pandas()
            .pivot(index=y_col, columns=x_col, values="value")
        )

        fig = px.imshow(
            pivot_pandas,
            color_continuous_scale="Blues",
            aspect="auto",
            text_auto=config.show_values,
        )
        return fig

    # ─────────────────────────────────────────────────────────────────────────
    # Shared utilities
    # ─────────────────────────────────────────────────────────────────────────

    def _create_empty_figure(self, message: str = "Sem dados") -> go.Figure:
        fig = go.Figure()
        fig.add_annotation(
            text=message,
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=14, color="gray"),
        )
        fig.update_xaxes(showgrid=False, showticklabels=False)
        fig.update_yaxes(showgrid=False, showticklabels=False)
        return fig

    def _apply_common_style(
        self, fig: go.Figure, config: VisualizationConfig
    ) -> None:
        fig.update_layout(
            title=config.title or "",
            height=self.default_height,
            width=self.default_width,
            showlegend=config.show_legend,
            paper_bgcolor="rgba(255,255,255,1)",
            plot_bgcolor="rgba(248,248,248,1)",
            font=dict(family="Arial, sans-serif", size=12),
            title_font=dict(size=16),
            margin=dict(l=60, r=40, t=60, b=60),
        )

        if config.show_grid:
            fig.update_xaxes(
                showgrid=True, gridwidth=1, gridcolor="rgba(200,200,200,0.5)"
            )
            fig.update_yaxes(
                showgrid=True, gridwidth=1, gridcolor="rgba(200,200,200,0.5)"
            )
        else:
            fig.update_xaxes(showgrid=False)
            fig.update_yaxes(showgrid=False)
