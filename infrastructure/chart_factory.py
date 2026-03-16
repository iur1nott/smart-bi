"""
Chart Factory - Creates Plotly charts from visualization configurations.
Provides a unified interface for all chart types.
"""

from typing import Dict, Any, Optional
import polars as pl
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io

from domain.entities import VisualizationConfig, VisualizationType
from domain.value_objects import ChartColors


class ChartFactory:
    """
    Factory for creating Plotly charts from visualization configurations.
    Implements the Factory Pattern for chart creation.
    """

    def __init__(self):
        """Initialize the chart factory with color palette."""
        self.colors = ChartColors()

    def create_chart(self, df: pl.DataFrame, config: VisualizationConfig) -> go.Figure:
        """
        Create a chart based on visualization configuration.

        Args:
            df: Polars DataFrame with the data
            config: Visualization configuration

        Returns:
            Plotly Figure object
        """
        chart_creators = {
            VisualizationType.BAR_CHART: self._create_bar_chart,
            VisualizationType.LINE_CHART: self._create_line_chart,
            VisualizationType.PIE_CHART: self._create_pie_chart,
            VisualizationType.AREA_CHART: self._create_area_chart,
            VisualizationType.SCATTER_PLOT: self._create_scatter_plot,
            VisualizationType.HISTOGRAM: self._create_histogram,
            VisualizationType.BOX_PLOT: self._create_box_plot,
            VisualizationType.HEATMAP: self._create_heatmap,
        }

        creator = chart_creators.get(config.visualization_type, self._create_bar_chart)

        fig = creator(df, config)

        fig.update_layout(
            title={
                "text": config.title,
                "x": 0.5,
                "xanchor": "center",
            },
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font={"family": "Inter, sans-serif", "color": "#1E293B"},
            margin={"l": 60, "r": 40, "t": 60, "b": 60},
        )

        fig.update_xaxes(
            gridcolor="#E2E8F0",
            linecolor="#CBD5E1",
        )
        fig.update_yaxes(
            gridcolor="#E2E8F0",
            linecolor="#CBD5E1",
        )

        return fig

    def _prepare_aggregated_data(
        self, df: pl.DataFrame, config: VisualizationConfig
    ) -> pl.DataFrame:
        """Prepare aggregated data for charts."""
        if not config.x_column or not config.y_column:
            return df

        if config.aggregation == "sum":
            agg_expr = pl.col(config.y_column).sum()
        elif config.aggregation == "mean":
            agg_expr = pl.col(config.y_column).mean()
        elif config.aggregation == "count":
            agg_expr = pl.col(config.y_column).count()
        elif config.aggregation == "min":
            agg_expr = pl.col(config.y_column).min()
        elif config.aggregation == "max":
            agg_expr = pl.col(config.y_column).max()
        else:
            agg_expr = pl.col(config.y_column).sum()

        group_cols = [config.x_column]
        if config.color_column and config.color_column in df.columns:
            group_cols.append(config.color_column)

        result = df.group_by(group_cols).agg(agg_expr.alias(config.y_column))
        return result.sort(config.x_column)

    def _create_bar_chart(
        self, df: pl.DataFrame, config: VisualizationConfig
    ) -> go.Figure:
        """Create a bar chart."""
        agg_df = self._prepare_aggregated_data(df, config)
        pandas_df = agg_df.to_pandas()

        if config.color_column and config.color_column in pandas_df.columns:
            fig = px.bar(
                pandas_df,
                x=config.x_column,
                y=config.y_column,
                color=config.color_column,
                color_discrete_sequence=self.colors.palette,
                barmode="group",
            )
        else:
            fig = px.bar(
                pandas_df,
                x=config.x_column,
                y=config.y_column,
                color_discrete_sequence=[self.colors.primary],
            )

        fig.update_traces(
            marker_line_width=0,
            marker_opacity=0.9,
        )

        return fig

    def _create_line_chart(
        self, df: pl.DataFrame, config: VisualizationConfig
    ) -> go.Figure:
        """Create a line chart."""
        agg_df = self._prepare_aggregated_data(df, config)
        pandas_df = agg_df.to_pandas()

        if config.color_column and config.color_column in pandas_df.columns:
            fig = px.line(
                pandas_df,
                x=config.x_column,
                y=config.y_column,
                color=config.color_column,
                color_discrete_sequence=self.colors.palette,
                markers=True,
            )
        else:
            fig = px.line(
                pandas_df,
                x=config.x_column,
                y=config.y_column,
                color_discrete_sequence=[self.colors.primary],
                markers=True,
            )

        fig.update_traces(
            line_width=2,
            marker_size=6,
        )

        return fig

    def _create_pie_chart(
        self, df: pl.DataFrame, config: VisualizationConfig
    ) -> go.Figure:
        """Create a pie chart."""
        agg_df = self._prepare_aggregated_data(df, config)
        pandas_df = agg_df.to_pandas()

        fig = px.pie(
            pandas_df,
            names=config.x_column,
            values=config.y_column,
            color_discrete_sequence=self.colors.palette,
        )

        fig.update_traces(
            textinfo="percent+label",
            textposition="outside",
            marker_line_width=1,
            marker_line_color="white",
        )

        return fig

    def _create_area_chart(
        self, df: pl.DataFrame, config: VisualizationConfig
    ) -> go.Figure:
        """Create an area chart."""
        agg_df = self._prepare_aggregated_data(df, config)
        pandas_df = agg_df.to_pandas()

        if config.color_column and config.color_column in pandas_df.columns:
            fig = px.area(
                pandas_df,
                x=config.x_column,
                y=config.y_column,
                color=config.color_column,
                color_discrete_sequence=self.colors.palette,
            )
        else:
            fig = px.area(
                pandas_df,
                x=config.x_column,
                y=config.y_column,
                color_discrete_sequence=[self.colors.primary],
            )

        fig.update_traces(
            line_width=2,
            opacity=0.7,
        )

        return fig

    def _create_scatter_plot(
        self, df: pl.DataFrame, config: VisualizationConfig
    ) -> go.Figure:
        """Create a scatter plot."""
        pandas_df = df.to_pandas()

        if not config.x_column or not config.y_column:
            raise ValueError("Scatter plot requires both x and y columns")

        size_col = (
            config.size_column if config.size_column in pandas_df.columns else None
        )
        color_col = (
            config.color_column if config.color_column in pandas_df.columns else None
        )

        fig = px.scatter(
            pandas_df,
            x=config.x_column,
            y=config.y_column,
            color=color_col,
            size=size_col,
            color_discrete_sequence=self.colors.palette,
            opacity=0.7,
        )

        fig.update_traces(
            marker_line_width=1,
            marker_line_color="white",
        )

        return fig

    def _create_histogram(
        self, df: pl.DataFrame, config: VisualizationConfig
    ) -> go.Figure:
        """Create a histogram."""
        pandas_df = df.to_pandas()

        if not config.x_column:
            raise ValueError("Histogram requires an x column")

        color_col = (
            config.color_column if config.color_column in pandas_df.columns else None
        )

        fig = px.histogram(
            pandas_df,
            x=config.x_column,
            color=color_col,
            color_discrete_sequence=self.colors.palette,
            nbins=30,
            opacity=0.8,
        )

        fig.update_traces(
            marker_line_width=1,
            marker_line_color="white",
        )

        return fig

    def _create_box_plot(
        self, df: pl.DataFrame, config: VisualizationConfig
    ) -> go.Figure:
        """Create a box plot."""
        pandas_df = df.to_pandas()

        if not config.y_column:
            raise ValueError("Box plot requires a y column")

        x_col = config.x_column if config.x_column in pandas_df.columns else None

        fig = px.box(
            pandas_df,
            x=x_col,
            y=config.y_column,
            color=x_col,
            color_discrete_sequence=self.colors.palette,
        )

        return fig

    def _create_heatmap(
        self, df: pl.DataFrame, config: VisualizationConfig
    ) -> go.Figure:
        """Create a heatmap."""
        if not config.x_column or not config.y_column:
            raise ValueError("Heatmap requires x and y columns")

        agg_df = df.group_by(
            [config.x_column, config.color_column or config.x_column]
        ).agg(pl.col(config.y_column).sum().alias(config.y_column))

        pivot_df = agg_df.pivot(
            values=config.y_column,
            index=config.x_column,
            columns=config.color_column or config.x_column,
        )

        data = pivot_df.drop(config.x_column).to_numpy()

        fig = go.Figure(
            data=go.Heatmap(
                z=data,
                x=pivot_df.columns[1:],
                y=pivot_df[config.x_column].to_list(),
                colorscale="Viridis",
            )
        )

        return fig

    def export_figure_to_bytes(
        self,
        fig: go.Figure,
        format: str = "png",
        width: int = 1200,
        height: int = 800,
        scale: float = 2.0,
    ) -> bytes:
        """
        Export a figure to bytes.

        Args:
            fig: Plotly Figure object
            format: Output format (png, jpeg, svg, pdf)
            width: Width in pixels
            height: Height in pixels
            scale: Scale factor for resolution

        Returns:
            Image bytes
        """
        return fig.to_image(
            format=format,
            width=width,
            height=height,
            scale=scale,
        )

    def export_figure_to_file(
        self,
        fig: go.Figure,
        filepath: str,
        format: Optional[str] = None,
        width: int = 1200,
        height: int = 800,
        scale: float = 2.0,
    ) -> str:
        """
        Export a figure to a file.

        Args:
            fig: Plotly Figure object
            filepath: Path for output file
            format: Output format (inferred from extension if not provided)
            width: Width in pixels
            height: Height in pixels
            scale: Scale factor for resolution

        Returns:
            Path to the saved file
        """
        if format is None:
            format = filepath.split(".")[-1]

        img_bytes = self.export_figure_to_bytes(fig, format, width, height, scale)

        with open(filepath, "wb") as f:
            f.write(img_bytes)

        return filepath
