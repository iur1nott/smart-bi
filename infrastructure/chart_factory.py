"""
Chart Factory - Creates visualization charts using Plotly.
Follows Factory Pattern for creating different chart types.
"""

from typing import Dict, Any, Optional, List
import polars as pl
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio
import io

from domain.entities import VisualizationType, VisualizationConfig


class ChartFactory:
    """
    Factory class for creating different types of charts.
    Uses Plotly for interactive visualizations.
    """

    # Default color schemes
    COLOR_SCHEMES = {
        "default": px.colors.qualitative.Plotly,
        "pastel": px.colors.qualitative.Pastel,
        "dark": px.colors.qualitative.Dark24,
        "light": px.colors.qualitative.Light24,
        "vivid": px.colors.qualitative.Vivid,
        "safe": px.colors.qualitative.Safe,
        "d3": px.colors.qualitative.D3,
        "alphabet": px.colors.qualitative.Alphabet,
    }

    def __init__(self, default_height: int = 400, default_width: int = 600):
        """Initialize the chart factory with default dimensions."""
        self.default_height = default_height
        self.default_width = default_width
        self.current_theme = "default"

    def create_chart(self, df: pl.DataFrame, config: VisualizationConfig) -> go.Figure:
        """
        Create a chart based on configuration.

        Args:
            df: Polars DataFrame with data
            config: Visualization configuration

        Returns:
            Plotly Figure object
        """
        chart_methods = {
            VisualizationType.LINE_CHART: self._create_line_chart,
            VisualizationType.BAR_CHART: self._create_bar_chart,
            VisualizationType.PIE_CHART: self._create_pie_chart,
            VisualizationType.SCATTER_PLOT: self._create_scatter_plot,
            VisualizationType.HISTOGRAM: self._create_histogram,
            VisualizationType.AREA_CHART: self._create_area_chart,
            VisualizationType.BOX_PLOT: self._create_box_plot,
            VisualizationType.HEATMAP: self._create_heatmap,
        }

        method = chart_methods.get(config.visualization_type)
        if method:
            fig = method(df, config)
        else:
            fig = go.Figure()
            fig.add_annotation(
                text=f"Chart type '{config.visualization_type.value}' not implemented",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
            )

        # Apply common styling
        self._apply_common_style(fig, config)

        return fig

    def _create_line_chart(
        self, df: pl.DataFrame, config: VisualizationConfig
    ) -> go.Figure:
        """Create a line chart."""
        pandas_df = df.to_pandas()
        x_col = config.x_column
        y_col = config.y_column

        if not x_col or not y_col:
            return self._create_empty_figure("Please select X and Y columns")

        color_col = config.color_column

        if color_col and color_col in df.columns:
            fig = px.line(
                pandas_df,
                x=x_col,
                y=y_col,
                color=color_col,
                color_discrete_sequence=self.COLOR_SCHEMES.get(
                    config.color_scheme, self.COLOR_SCHEMES["default"]
                ),
            )
        else:
            fig = px.line(
                pandas_df,
                x=x_col,
                y=y_col,
                color_discrete_sequence=self.COLOR_SCHEMES.get(
                    config.color_scheme, self.COLOR_SCHEMES["default"]
                ),
            )

        return fig

    def _create_bar_chart(
        self, df: pl.DataFrame, config: VisualizationConfig
    ) -> go.Figure:
        """Create a bar chart."""
        pandas_df = df.to_pandas()
        x_col = config.x_column
        y_col = config.y_column

        if not x_col:
            return self._create_empty_figure("Please select X column")

        color_col = config.color_column

        if y_col:
            if color_col and color_col in df.columns:
                fig = px.bar(
                    pandas_df,
                    x=x_col,
                    y=y_col,
                    color=color_col,
                    barmode="group",
                    color_discrete_sequence=self.COLOR_SCHEMES.get(
                        config.color_scheme, self.COLOR_SCHEMES["default"]
                    ),
                )
            else:
                fig = px.bar(
                    pandas_df,
                    x=x_col,
                    y=y_col,
                    color_discrete_sequence=self.COLOR_SCHEMES.get(
                        config.color_scheme, self.COLOR_SCHEMES["default"]
                    ),
                )
        else:
            # Count plot
            counts = pandas_df[x_col].value_counts().reset_index()
            counts.columns = [x_col, "count"]
            fig = px.bar(
                counts,
                x=x_col,
                y="count",
                color_discrete_sequence=self.COLOR_SCHEMES.get(
                    config.color_scheme, self.COLOR_SCHEMES["default"]
                ),
            )

        return fig

    def _create_pie_chart(
        self, df: pl.DataFrame, config: VisualizationConfig
    ) -> go.Figure:
        """Create a pie chart."""
        pandas_df = df.to_pandas()
        names_col = config.x_column
        values_col = config.y_column

        if not names_col:
            return self._create_empty_figure("Please select a column for categories")

        if values_col:
            fig = px.pie(
                pandas_df,
                names=names_col,
                values=values_col,
                color_discrete_sequence=self.COLOR_SCHEMES.get(
                    config.color_scheme, self.COLOR_SCHEMES["default"]
                ),
            )
        else:
            # Count occurrences
            counts = pandas_df[names_col].value_counts().reset_index()
            counts.columns = [names_col, "count"]
            fig = px.pie(
                counts,
                names=names_col,
                values="count",
                color_discrete_sequence=self.COLOR_SCHEMES.get(
                    config.color_scheme, self.COLOR_SCHEMES["default"]
                ),
            )

        return fig

    def _create_scatter_plot(
        self, df: pl.DataFrame, config: VisualizationConfig
    ) -> go.Figure:
        """Create a scatter plot."""
        pandas_df = df.to_pandas()
        x_col = config.x_column
        y_col = config.y_column

        if not x_col or not y_col:
            return self._create_empty_figure("Please select X and Y columns")

        color_col = config.color_column
        size_col = config.size_column

        fig = px.scatter(
            pandas_df,
            x=x_col,
            y=y_col,
            color=color_col if color_col else None,
            size=size_col if size_col else None,
            color_discrete_sequence=self.COLOR_SCHEMES.get(
                config.color_scheme, self.COLOR_SCHEMES["default"]
            ),
            opacity=0.7,
        )

        return fig

    def _create_histogram(
        self, df: pl.DataFrame, config: VisualizationConfig
    ) -> go.Figure:
        """Create a histogram."""
        pandas_df = df.to_pandas()
        x_col = config.x_column

        if not x_col:
            return self._create_empty_figure("Please select a column for histogram")

        color_col = config.color_column

        if color_col and color_col in df.columns:
            fig = px.histogram(
                pandas_df,
                x=x_col,
                color=color_col,
                barmode="overlay",
                opacity=0.7,
                color_discrete_sequence=self.COLOR_SCHEMES.get(
                    config.color_scheme, self.COLOR_SCHEMES["default"]
                ),
            )
        else:
            fig = px.histogram(
                pandas_df,
                x=x_col,
                color_discrete_sequence=self.COLOR_SCHEMES.get(
                    config.color_scheme, self.COLOR_SCHEMES["default"]
                ),
            )

        return fig

    def _create_area_chart(
        self, df: pl.DataFrame, config: VisualizationConfig
    ) -> go.Figure:
        """Create an area chart."""
        pandas_df = df.to_pandas()
        x_col = config.x_column
        y_col = config.y_column

        if not x_col or not y_col:
            return self._create_empty_figure("Please select X and Y columns")

        color_col = config.color_column

        if color_col and color_col in df.columns:
            fig = px.area(
                pandas_df,
                x=x_col,
                y=y_col,
                color=color_col,
                color_discrete_sequence=self.COLOR_SCHEMES.get(
                    config.color_scheme, self.COLOR_SCHEMES["default"]
                ),
            )
        else:
            fig = px.area(
                pandas_df,
                x=x_col,
                y=y_col,
                color_discrete_sequence=self.COLOR_SCHEMES.get(
                    config.color_scheme, self.COLOR_SCHEMES["default"]
                ),
            )

        return fig

    def _create_box_plot(
        self, df: pl.DataFrame, config: VisualizationConfig
    ) -> go.Figure:
        """Create a box plot."""
        pandas_df = df.to_pandas()
        y_col = config.y_column
        x_col = config.x_column

        if not y_col:
            return self._create_empty_figure("Please select Y column for box plot")

        color_col = config.color_column

        fig = px.box(
            pandas_df,
            x=x_col if x_col else None,
            y=y_col,
            color=color_col if color_col else None,
            color_discrete_sequence=self.COLOR_SCHEMES.get(
                config.color_scheme, self.COLOR_SCHEMES["default"]
            ),
        )

        return fig

    def _create_heatmap(
        self, df: pl.DataFrame, config: VisualizationConfig
    ) -> go.Figure:
        """Create a heatmap."""
        if not config.x_column or not config.y_column:
            return self._create_empty_figure(
                "Please select X and Y columns for heatmap"
            )

        x_col = config.x_column
        y_col = config.y_column
        value_col = config.color_column or config.y_column

        # Create pivot table
        pivot_df = df.group_by([x_col, y_col]).agg(
            pl.col(value_col).sum().alias("value")
        )

        pivot_pandas = pivot_df.to_pandas()
        pivot_table = pivot_pandas.pivot(index=y_col, columns=x_col, values="value")

        fig = px.imshow(pivot_table, color_continuous_scale="Blues", aspect="auto")

        return fig

    def _create_empty_figure(self, message: str = "No data") -> go.Figure:
        """Create an empty figure with a message."""
        fig = go.Figure()
        fig.add_annotation(
            text=message,
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=16, color="gray"),
        )
        fig.update_xaxes(showgrid=False, showticklabels=False)
        fig.update_yaxes(showgrid=False, showticklabels=False)
        return fig

    def _apply_common_style(self, fig: go.Figure, config: VisualizationConfig) -> None:
        """Apply common styling to the figure."""
        title = config.title if config.title else ""

        fig.update_layout(
            title=title,
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

    def export_figure_to_bytes(
        self, fig: go.Figure, format: str = "png", scale: float = 2.0
    ) -> bytes:
        """
        Export figure to image bytes.

        Args:
            fig: Plotly Figure object
            format: Image format (png, jpeg, svg, pdf)
            scale: Scale factor for higher resolution

        Returns:
            Image as bytes
        """
        img_bytes = pio.to_image(fig, format=format, scale=scale)
        return img_bytes

    def export_figure_to_base64(
        self, fig: go.Figure, format: str = "png", scale: float = 2.0
    ) -> str:
        """
        Export figure to base64 encoded string.

        Args:
            fig: Plotly Figure object
            format: Image format
            scale: Scale factor

        Returns:
            Base64 encoded image string
        """
        import base64

        img_bytes = self.export_figure_to_bytes(fig, format, scale)
        return base64.b64encode(img_bytes).decode("utf-8")

    def get_available_chart_types(self) -> List[Dict[str, str]]:
        """Get list of available chart types with display names."""
        return [
            {
                "id": VisualizationType.BAR_CHART.value,
                "name": "Bar Chart",
                "icon": "📊",
            },
            {
                "id": VisualizationType.LINE_CHART.value,
                "name": "Line Chart",
                "icon": "📈",
            },
            {
                "id": VisualizationType.PIE_CHART.value,
                "name": "Pie Chart",
                "icon": "🥧",
            },
            {
                "id": VisualizationType.AREA_CHART.value,
                "name": "Area Chart",
                "icon": "📉",
            },
            {
                "id": VisualizationType.SCATTER_PLOT.value,
                "name": "Scatter Plot",
                "icon": "⚬",
            },
            {"id": VisualizationType.HISTOGRAM.value, "name": "Histogram", "icon": "▊"},
            {"id": VisualizationType.BOX_PLOT.value, "name": "Box Plot", "icon": "📦"},
            {"id": VisualizationType.HEATMAP.value, "name": "Heatmap", "icon": "🔥"},
            {"id": VisualizationType.TABLE.value, "name": "Table", "icon": "📋"},
            {
                "id": VisualizationType.METRIC_CARD.value,
                "name": "Metric Card",
                "icon": "💳",
            },
        ]

    def get_available_color_schemes(self) -> List[str]:
        """Get list of available color schemes."""
        return list(self.COLOR_SCHEMES.keys())
