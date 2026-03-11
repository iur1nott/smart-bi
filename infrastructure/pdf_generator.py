"""
PDF Generator - Alternative PDF generation using ReportLab.
Provides fallback when LaTeX compilation is not available.
"""

from typing import List, Dict, Any, Optional
import os
from datetime import datetime
import io
import base64

from domain.entities import Analysis, Slide, Visualization, VisualizationType
from domain.value_objects import ExportOptions


class PDFGenerator:
    """
    PDF generator using ReportLab library.
    Provides direct PDF generation without LaTeX dependency.
    """

    def __init__(self, output_dir: str = "download"):
        """Initialize PDF generator."""
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_pdf(
        self,
        analysis: Analysis,
        options: ExportOptions,
        chart_images: Optional[Dict[str, bytes]] = None,
    ) -> str:
        """
        Generate PDF from analysis using ReportLab.

        Args:
            analysis: Analysis to export
            options: Export options
            chart_images: Dictionary of visualization ID to image bytes

        Returns:
            Path to generated PDF file
        """
        from reportlab.lib.pagesizes import A4, letter, legal
        from reportlab.platypus import (
            SimpleDocTemplate,
            Paragraph,
            Spacer,
            Image,
            Table,
            TableStyle,
            PageBreak,
            KeepTogether,
        )
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.lib.units import mm, inch
        from reportlab.lib.enums import TA_CENTER, TA_LEFT

        # Determine page size
        page_sizes = {"a4": A4, "letter": letter, "legal": legal}
        page_size = page_sizes.get(options.paper_size, A4)

        # Adjust for orientation
        if options.orientation == "landscape":
            page_size = (page_size[1], page_size[0])

        # Create output file path
        output_filename = f"{analysis.name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        output_path = os.path.join(self.output_dir, output_filename)

        # Create document
        doc = SimpleDocTemplate(
            output_path,
            pagesize=page_size,
            rightMargin=options.margin_mm * mm,
            leftMargin=options.margin_mm * mm,
            topMargin=options.margin_mm * mm,
            bottomMargin=options.margin_mm * mm,
        )

        # Get styles
        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Title"],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
        )

        heading_style = ParagraphStyle(
            "CustomHeading",
            parent=styles["Heading2"],
            fontSize=16,
            spaceBefore=20,
            spaceAfter=10,
            textColor=colors.HexColor("#2c3e50"),
        )

        body_style = ParagraphStyle(
            "CustomBody",
            parent=styles["Normal"],
            fontSize=options.font_size,
            spaceAfter=12,
        )

        caption_style = ParagraphStyle(
            "Caption",
            parent=styles["Normal"],
            fontSize=10,
            textColor=colors.gray,
            alignment=TA_CENTER,
            spaceBefore=6,
            spaceAfter=12,
        )

        comment_style = ParagraphStyle(
            "Comment",
            parent=styles["Italic"],
            fontSize=10,
            textColor=colors.HexColor("#7f8c8d"),
            leftIndent=20,
            spaceAfter=12,
        )

        # Build content
        story = []

        # Add header if specified
        if options.header_text:
            header_para = Paragraph(options.header_text, body_style)
            story.append(header_para)
            story.append(Spacer(1, 20))

        # Document title
        story.append(Paragraph(analysis.name, title_style))
        story.append(Spacer(1, 20))

        # Add timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        story.append(Paragraph(f"Generated: {timestamp}", caption_style))
        story.append(Spacer(1, 30))

        # Process each slide
        for slide_index, slide in enumerate(analysis.slides):
            slide_content = []

            # Slide title
            slide_content.append(Paragraph(slide.title, heading_style))
            slide_content.append(Spacer(1, 10))

            # Process visualizations
            for viz in slide.visualizations:
                viz_elements = self._process_visualization(
                    viz, chart_images, styles, caption_style, comment_style, options
                )
                slide_content.extend(viz_elements)

            # Add slide content to story
            if slide_index < len(analysis.slides) - 1:
                slide_content.append(PageBreak())

            story.extend(slide_content)

        # Add footer if specified
        if options.footer_text:
            story.append(Spacer(1, 30))
            story.append(Paragraph(options.footer_text, caption_style))

        # Build PDF
        doc.build(story)

        return output_path

    def _process_visualization(
        self,
        visualization: Visualization,
        chart_images: Optional[Dict[str, bytes]],
        styles: Any,
        caption_style: Any,
        comment_style: Any,
        options: ExportOptions,
    ) -> List[Any]:
        """Process a single visualization into PDF elements."""
        from reportlab.platypus import Paragraph, Spacer, Image, Table, TableStyle
        from reportlab.lib import colors
        from reportlab.lib.units import inch, mm

        elements = []

        if not visualization.config:
            return elements

        config = visualization.config

        # Handle different visualization types
        if config.visualization_type == VisualizationType.TABLE:
            elements.extend(self._process_table(visualization, styles, caption_style))
        else:
            # Handle chart types
            elements.extend(
                self._process_chart(visualization, chart_images, caption_style, options)
            )

        # Add comment if enabled
        if options.include_comments and visualization.comment:
            elements.append(Paragraph(visualization.comment, comment_style))
            elements.append(Spacer(1, 10))

        return elements

    def _process_table(
        self, visualization: Visualization, styles: Any, caption_style: Any
    ) -> List[Any]:
        """Process a table visualization."""
        from reportlab.platypus import Paragraph, Spacer, Table, TableStyle
        from reportlab.lib import colors

        elements = []

        if not visualization.data_snapshot:
            return elements

        data = visualization.data_snapshot.get("data", [])
        columns = visualization.data_snapshot.get("columns", [])

        if not data or not columns:
            return elements

        # Build table data
        table_data = [columns]  # Header row

        # Limit rows for PDF
        max_rows = 50
        for row in data[:max_rows]:
            row_values = [str(row.get(col, ""))[:30] for col in columns]
            table_data.append(row_values)

        from reportlab.lib.units import inch

        # Create table
        col_widths = [1.5 * inch] * len(columns)
        table = Table(table_data, colWidths=col_widths)

        # Style the table
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#3498db")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                    ("TEXTCOLOR", (0, 1), (-1, -1), colors.black),
                    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 1), (-1, -1), 9),
                    ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#bdc3c7")),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [colors.white, colors.HexColor("#ecf0f1")],
                    ),
                ]
            )
        )

        elements.append(table)

        # Add caption
        if visualization.config.title:
            elements.append(Paragraph(visualization.config.title, caption_style))

        elements.append(Spacer(1, 15))

        return elements

    def _process_chart(
        self,
        visualization: Visualization,
        chart_images: Optional[Dict[str, bytes]],
        caption_style: Any,
        options: ExportOptions,
    ) -> List[Any]:
        """Process a chart visualization."""
        from reportlab.platypus import Paragraph, Spacer, Image
        from reportlab.lib.units import inch

        elements = []

        if not chart_images or visualization.id not in chart_images:
            elements.append(Paragraph("[Chart placeholder]", caption_style))
            return elements

        # Get image bytes
        img_bytes = chart_images[visualization.id]

        # Create image from bytes
        img_buffer = io.BytesIO(img_bytes)

        try:
            # Determine image size
            max_width = 6 * inch
            max_height = 4 * inch

            img = Image(
                img_buffer, width=max_width, height=max_height, kind="proportional"
            )

            elements.append(img)

            # Add caption
            if visualization.config and visualization.config.title:
                elements.append(Paragraph(visualization.config.title, caption_style))

            elements.append(Spacer(1, 15))

        except Exception as e:
            elements.append(Paragraph(f"[Image error: {str(e)}]", caption_style))

        return elements

    def merge_pdfs(self, pdf_paths: List[str], output_path: str) -> str:
        """Merge multiple PDFs into one."""
        from PyPDF2 import PdfMerger

        merger = PdfMerger()

        for path in pdf_paths:
            if os.path.exists(path):
                merger.append(path)

        merger.write(output_path)
        merger.close()

        return output_path
