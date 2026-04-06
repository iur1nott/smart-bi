"""
PDF Generator - Generates PDF reports from analyses.
Creates professional export documents with charts and tables.
"""

from typing import Dict, Any, List, Optional, Tuple
import io
import os
from datetime import datetime
import logging

from domain.entities import Analysis, Slide, Visualization, VisualizationType
from domain.value_objects import ExportOptions

logger = logging.getLogger(__name__)

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, LETTER, LEGAL
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
        Image,
        PageBreak,
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT

    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False
    logger.warning("reportlab not installed. PDF export will be limited.")


class PDFGenerator:
    """
    Generates PDF documents from analysis data.
    Supports multiple paper sizes and orientations.
    """

    # Paper size mapping
    PAPER_SIZES = {
        "a4": A4 if HAS_REPORTLAB else None,
        "letter": LETTER if HAS_REPORTLAB else None,
        "legal": LEGAL if HAS_REPORTLAB else None,
    }

    def __init__(self):
        """Initialize the PDF generator."""
        self.styles = self._create_styles() if HAS_REPORTLAB else None

    def _create_styles(self) -> Dict[str, Any]:
        """Create custom styles for PDF documents."""
        styles = getSampleStyleSheet()

        # Custom title style
        styles.add(
            ParagraphStyle(
                name="CustomTitle",
                parent=styles["Heading1"],
                fontSize=24,
                spaceAfter=30,
                alignment=TA_CENTER,
                textColor=colors.HexColor("#1E293B"),
            )
        )

        # Custom heading style
        styles.add(
            ParagraphStyle(
                name="CustomHeading",
                parent=styles["Heading2"],
                fontSize=16,
                spaceAfter=12,
                spaceBefore=20,
                textColor=colors.HexColor("#334155"),
            )
        )

        # Custom body style
        styles.add(
            ParagraphStyle(
                name="CustomBody",
                parent=styles["Normal"],
                fontSize=11,
                spaceAfter=8,
                textColor=colors.HexColor("#475569"),
            )
        )

        # Comment style
        styles.add(
            ParagraphStyle(
                name="Comment",
                parent=styles["Normal"],
                fontSize=10,
                fontName="Helvetica-Oblique",
                textColor=colors.HexColor("#64748B"),
                leftIndent=10,
                rightIndent=10,
                spaceBefore=5,
                spaceAfter=10,
                backColor=colors.HexColor("#F8FAFC"),
                borderPadding=5,
            )
        )

        return styles

    def generate_pdf(
        self,
        analysis: Analysis,
        options: ExportOptions,
        chart_images: Dict[str, bytes],
        output_path: Optional[str] = None,
    ) -> Optional[str]:
        """
        Generate a PDF document from an analysis.

        Args:
            analysis: The analysis entity to export
            options: Export configuration options
            chart_images: Dictionary mapping visualization IDs to chart image bytes
            output_path: Optional output file path

        Returns:
            Path to the generated PDF file, or None on failure
        """
        if not HAS_REPORTLAB:
            logger.error("reportlab not installed. Cannot generate PDF.")
            return None

        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"exports/{analysis.name}_{timestamp}.pdf"

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

        try:
            # Get paper size
            paper_size = self.PAPER_SIZES.get(options.paper_size.lower(), A4)

            # Create document
            doc = SimpleDocTemplate(
                output_path,
                pagesize=paper_size,
                leftMargin=options.margin_mm * mm,
                rightMargin=options.margin_mm * mm,
                topMargin=options.margin_mm * mm,
                bottomMargin=options.margin_mm * mm,
            )

            # Build content
            story = []

            # Add title page if requested
            if options.title_page:
                story.extend(self._create_title_page(analysis, options))
                story.append(PageBreak())

            # Add header text if provided
            if options.header_text:
                story.append(Paragraph(options.header_text, self.styles["CustomBody"]))
                story.append(Spacer(1, 10))

            # Add slides
            for slide_idx, slide in enumerate(analysis.slides):
                slide_content = self._create_slide_content(
                    slide, slide_idx + 1, options, chart_images
                )
                story.extend(slide_content)

                # Add page break between slides (except last)
                if slide_idx < len(analysis.slides) - 1:
                    story.append(PageBreak())

            # Add footer text if provided
            if options.footer_text:
                story.append(Spacer(1, 20))
                story.append(Paragraph(options.footer_text, self.styles["CustomBody"]))

            # Build PDF
            doc.build(story)

            logger.info(f"PDF generated successfully: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Error generating PDF: {e}")
            return None

    def _create_title_page(self, analysis: Analysis, options: ExportOptions) -> List[Any]:
        """Create title page content."""
        content = []

        # Add spacer for vertical centering
        content.append(Spacer(1, 100))

        # Title
        content.append(Paragraph(analysis.name, self.styles["CustomTitle"]))

        # Subtitle with timestamp
        if options.include_timestamp:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            content.append(
                Paragraph(
                    f"Generated on {timestamp}",
                    self.styles["CustomBody"],
                )
            )

        # Data info
        if analysis.data_schema:
            schema = analysis.data_schema
            content.append(Spacer(1, 20))
            content.append(
                Paragraph(
                    f"Data: {schema.file_name}",
                    self.styles["CustomBody"],
                )
            )
            content.append(
                Paragraph(
                    f"Rows: {schema.row_count:,} | Columns: {len(schema.columns)}",
                    self.styles["CustomBody"],
                )
            )

        return content

    def _create_slide_content(
        self,
        slide: Slide,
        slide_number: int,
        options: ExportOptions,
        chart_images: Dict[str, bytes],
    ) -> List[Any]:
        """Create content for a single slide."""
        content = []

        # Slide title
        content.append(
            Paragraph(
                f"{slide_number}. {slide.title}",
                self.styles["CustomHeading"],
            )
        )

        # Add visualizations
        for viz in slide.visualizations:
            viz_content = self._create_visualization_content(viz, options, chart_images)
            content.extend(viz_content)

        return content

    def _create_visualization_content(
        self,
        viz: Visualization,
        options: ExportOptions,
        chart_images: Dict[str, bytes],
    ) -> List[Any]:
        """Create content for a single visualization."""
        content = []

        if not viz.config:
            return content

        # Visualization title
        if viz.config.title:
            content.append(
                Paragraph(
                    viz.config.title,
                    self.styles["CustomHeading"],
                )
            )

        # Add chart image if available
        if viz.id in chart_images:
            try:
                img_data = chart_images[viz.id]
                img = Image(io.BytesIO(img_data), width=150 * mm, height=100 * mm)
                content.append(img)
                content.append(Spacer(1, 10))
            except Exception as e:
                logger.warning(f"Could not add chart image: {e}")

        # Add comment if present and enabled
        if viz.comment and options.include_comments:
            content.append(Paragraph(f"Comment: {viz.comment}", self.styles["Comment"]))

        return content

    def create_table_from_data(
        self,
        headers: List[str],
        data: List[List[Any]],
        style_options: Optional[Dict[str, Any]] = None,
    ) -> Optional[Table]:
        """
        Create a formatted table for PDF.

        Args:
            headers: Column headers
            data: Table data as list of rows
            style_options: Optional styling options

        Returns:
            Formatted Table object
        """
        if not HAS_REPORTLAB:
            return None

        # Combine headers and data
        table_data = [headers] + data

        # Create table
        table = Table(table_data, repeatRows=1)

        # Default style
        default_style = [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#10B981")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
            ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F8FAFC")),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), ["#FFFFFF", "#F8FAFC"]),
        ]

        # Apply custom styles if provided
        if style_options:
            default_style.extend(style_options.get("extra_styles", []))

        table.setStyle(TableStyle(default_style))

        return table
