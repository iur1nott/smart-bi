"""
Chart Factory - Creates Plotly charts from visualization configurations.
Provides a unified interface for all chart types with Polars DataFrame support.
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

        # Apply common layout settings
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

        # Apply grid settings
        if config.show_grid:
            fig.update_xaxes(gridcolor="#E2E8F0", linecolor="#CBD5E1")
            fig.update_yaxes(gridcolor="#E2E8F0", linecolor="#CBD5E1")
        else:
            fig.update_xaxes(showgrid=False)
            fig.update_yaxes(showgrid=False)

        # Apply legend settings
        fig.update_layout(showlegend=config.show_legend)

        return fig

    def export_figure_to_bytes(
        self, fig: go.Figure, format: str = "png", scale: float = 2.0
    ) -> bytes:
        """
        Export a figure to bytes.

        Args:
            fig: Plotly Figure object
            format: Output format (png, jpg, svg, pdf)
            scale: Image scale factor

        Returns:
            Image bytes
        """
        img_bytes = fig.to_image(format=format, scale=scale)
        return img_bytes

    def _prepare_aggregated_data(
        self, df: pl.DataFrame, config: VisualizationConfig
    ) -> pl.DataFrame:
        """Prepare aggregated data for charts."""
        if not config.x_column or not config.y_column:
            return df

        # Determine aggregation expression
        agg_name = f"{config.y_column}_{config.aggregation}"

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

        # Build group columns
        group_cols = [config.x_column]
        if config.color_column and config.color_column in df.columns:
            # Avoid duplicate group columns
            if config.color_column != config.x_column:
                group_cols.append(config.color_column)

        # Aggregate and use a unique name for the aggregated column
        result = df.group_by(group_cols).agg(agg_expr.alias(agg_name))
        result = result.sort(config.x_column)

        # Rename back to y_column for plotting (but avoid duplicate)
        if agg_name != config.y_column and config.y_column not in result.columns:
            result = result.rename({agg_name: config.y_column})

        return result

    def _create_bar_chart(
        self, df: pl.DataFrame, config: VisualizationConfig
    ) -> go.Figure:
        """Create a bar chart."""
        if config.x_column and config.y_column:
            df = self._prepare_aggregated_data(df, config)

        # Convert to pandas for Plotly Express
        pdf = df.to_pandas()

        if config.color_column and config.color_column in pdf.columns:
            fig = px.bar(
                pdf,
                x=config.x_column,
                y=config.y_column,
                color=config.color_column,
                color_discrete_sequence=self.colors.palette,
                barmode="group",
            )
        else:
            fig = px.bar(
                pdf,
                x=config.x_column,
                y=config.y_column,
                color_discrete_sequence=[self.colors.primary],
            )

        return fig

    def _create_line_chart(
        self, df: pl.DataFrame, config: VisualizationConfig
    ) -> go.Figure:
        """Create a line chart."""
        if config.x_column and config.y_column:
            df = self._prepare_aggregated_data(df, config)

        pdf = df.to_pandas()

        if config.color_column and config.color_column in pdf.columns:
            fig = px.line(
                pdf,
                x=config.x_column,
                y=config.y_column,
                color=config.color_column,
                color_discrete_sequence=self.colors.palette,
                markers=True,
            )
        else:
            fig = px.line(
                pdf,
                x=config.x_column,
                y=config.y_column,
                color_discrete_sequence=[self.colors.primary],
                markers=True,
            )

        return fig

    def _create_pie_chart(
        self, df: pl.DataFrame, config: VisualizationConfig
    ) -> go.Figure:
        """Create a pie chart."""
        if not config.x_column or not config.y_column:
            # Return empty figure
            return go.Figure()

        df = self._prepare_aggregated_data(df, config)
        pdf = df.to_pandas()

        fig = px.pie(
            pdf,
            names=config.x_column,
            values=config.y_column,
            color_discrete_sequence=self.colors.palette,
        )

        fig.update_traces(textposition="inside", textinfo="percent+label")

        return fig

    def _create_area_chart(
        self, df: pl.DataFrame, config: VisualizationConfig
    ) -> go.Figure:
        """Create an area chart."""
        if config.x_column and config.y_column:
            df = self._prepare_aggregated_data(df, config)

        pdf = df.to_pandas()

        if config.color_column and config.color_column in pdf.columns:
            fig = px.area(
                pdf,
                x=config.x_column,
                y=config.y_column,
                color=config.color_column,
                color_discrete_sequence=self.colors.palette,
            )
        else:
            fig = px.area(
                pdf,
                x=config.x_column,
                y=config.y_column,
                color_discrete_sequence=[self.colors.primary],
            )

        return fig

    def _create_scatter_plot(
        self, df: pl.DataFrame, config: VisualizationConfig
    ) -> go.Figure:
        """Create a scatter plot."""
        pdf = df.to_pandas()

        scatter_kwargs = {
            "x": config.x_column,
            "y": config.y_column,
            "color_discrete_sequence": [self.colors.primary],
        }

        if config.color_column and config.color_column in pdf.columns:
            scatter_kwargs["color"] = config.color_column
            scatter_kwargs["color_discrete_sequence"] = self.colors.palette

        if config.size_column and config.size_column in pdf.columns:
            scatter_kwargs["size"] = config.size_column

        fig = px.scatter(pdf, **scatter_kwargs)

        return fig

    def _create_histogram(
        self, df: pl.DataFrame, config: VisualizationConfig
    ) -> go.Figure:
        """Create a histogram."""
        if not config.x_column:
            return go.Figure()

        pdf = df.to_pandas()

        fig = px.histogram(
            pdf,
            x=config.x_column,
            color=config.color_column if config.color_column else None,
            color_discrete_sequence=self.colors.palette,
            nbins=30,
        )

        return fig

    def _create_box_plot(
        self, df: pl.DataFrame, config: VisualizationConfig
    ) -> go.Figure:
        """Create a box plot."""
        pdf = df.to_pandas()

        if config.x_column and config.y_column:
            fig = px.box(
                pdf,
                x=config.x_column,
                y=config.y_column,
                color=config.color_column if config.color_column else None,
                color_discrete_sequence=self.colors.palette,
            )
        elif config.y_column:
            fig = px.box(
                pdf,
                y=config.y_column,
                color_discrete_sequence=[self.colors.primary],
            )
        else:
            return go.Figure()

        return fig

    def _create_heatmap(
        self, df: pl.DataFrame, config: VisualizationConfig
    ) -> go.Figure:
        """Create a heatmap."""
        if not config.x_column or not config.y_column:
            return go.Figure()

        # Prepare aggregated data
        agg_col = config.color_column or config.y_column
        agg_df = df.group_by([config.x_column, config.y_column]).agg(
            pl.col(agg_col).sum().alias("value")
        )

        pdf = agg_df.to_pandas()

        # Pivot for heatmap
        pivot_df = pdf.pivot(
            index=config.y_column,
            columns=config.x_column,
            values="value",
        ).fillna(0)

        fig = go.Figure(
            data=go.Heatmap(
                z=pivot_df.values,
                x=pivot_df.columns,
                y=pivot_df.index,
                colorscale="Viridis",
            )
        )

        return fig
