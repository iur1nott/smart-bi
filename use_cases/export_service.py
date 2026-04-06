"""
Export Service - Handles export of analyses to various formats.
Supports PDF, LaTeX, and HTML export with chart embedding.
"""

from typing import Dict, Any, Optional, List
import os
from datetime import datetime
import logging

from domain.entities import Analysis, Slide, Visualization, VisualizationType
from domain.value_objects import ExportOptions
from infrastructure.pdf_generator import PDFGenerator

logger = logging.getLogger(__name__)


class ExportService:
    """
    Service responsible for exporting analyses to various formats.
    Supports PDF, HTML, and LaTeX formats.
    """

    def __init__(self, export_dir: str = "exports"):
        """
        Initialize the export service.

        Args:
            export_dir: Directory to store exported files
        """
        self.export_dir = export_dir
        self.pdf_generator = PDFGenerator()
        os.makedirs(export_dir, exist_ok=True)

    def export_to_pdf(
        self,
        analysis: Analysis,
        options: ExportOptions,
        chart_images: Dict[str, bytes],
    ) -> Optional[str]:
        """
        Export an analysis to PDF format.

        Args:
            analysis: The analysis to export
            options: Export configuration options
            chart_images: Dictionary mapping visualization IDs to chart images

        Returns:
            Path to the generated PDF file, or None on failure
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self._sanitize_filename(f"{analysis.name}_{timestamp}.pdf")
        output_path = os.path.join(self.export_dir, filename)

        return self.pdf_generator.generate_pdf(analysis, options, chart_images, output_path)

    def export_to_html(
        self,
        analysis: Analysis,
        options: ExportOptions,
        chart_images: Dict[str, bytes],
    ) -> Optional[str]:
        """
        Export an analysis to HTML format.

        Args:
            analysis: The analysis to export
            options: Export configuration options
            chart_images: Dictionary mapping visualization IDs to chart images

        Returns:
            Path to the generated HTML file, or None on failure
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self._sanitize_filename(f"{analysis.name}_{timestamp}.html")
        output_path = os.path.join(self.export_dir, filename)

        try:
            html_content = self._generate_html_content(analysis, options, chart_images)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html_content)

            logger.info(f"HTML export created: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Error exporting to HTML: {e}")
            return None

    def export_to_latex(
        self,
        analysis: Analysis,
        options: ExportOptions,
        chart_images: Dict[str, bytes],
    ) -> Optional[str]:
        """
        Export an analysis to LaTeX format.

        Args:
            analysis: The analysis to export
            options: Export configuration options
            chart_images: Dictionary mapping visualization IDs to chart images

        Returns:
            Path to the generated LaTeX file, or None on failure
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self._sanitize_filename(f"{analysis.name}_{timestamp}.tex")
        output_path = os.path.join(self.export_dir, filename)

        try:
            latex_content = self._generate_latex_content(analysis, options, chart_images)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(latex_content)

            logger.info(f"LaTeX export created: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Error exporting to LaTeX: {e}")
            return None

    def _generate_html_content(
        self,
        analysis: Analysis,
        options: ExportOptions,
        chart_images: Dict[str, bytes],
    ) -> str:
        """Generate HTML content for an analysis."""
        import base64

        html_parts = [
            "<!DOCTYPE html>",
            "<html lang='en'>",
            "<head>",
            f"<title>{self._escape_html(analysis.name)}</title>",
            "<meta charset='UTF-8'>",
            "<meta name='viewport' content='width=device-width, initial-scale=1.0'>",
            "<style>",
            self._get_html_styles(),
            "</style>",
            "</head>",
            "<body>",
        ]

        # Title
        html_parts.append(f"<h1>{self._escape_html(analysis.name)}</h1>")

        # Header text
        if options.header_text:
            html_parts.append(f"<p class='header'>{self._escape_html(options.header_text)}</p>")

        # Metadata
        if analysis.data_schema:
            schema = analysis.data_schema
            html_parts.append(
                f"<p class='meta'>Data: {self._escape_html(schema.file_name)} | "
                f"Rows: {schema.row_count:,} | Columns: {len(schema.columns)}</p>"
            )

        # Timestamp
        if options.include_timestamp:
            html_parts.append(
                f"<p class='meta'>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>"
            )

        # Slides
        for i, slide in enumerate(analysis.slides):
            html_parts.extend(self._generate_slide_html(slide, i + 1, options, chart_images))

        # Footer
        if options.footer_text:
            html_parts.append(f"<p class='footer'>{self._escape_html(options.footer_text)}</p>")

        html_parts.extend(["</body>", "</html>"])

        return "\n".join(html_parts)

    def _generate_slide_html(
        self,
        slide: Slide,
        slide_number: int,
        options: ExportOptions,
        chart_images: Dict[str, bytes],
    ) -> List[str]:
        """Generate HTML for a single slide."""
        import base64

        parts = [
            "<div class='slide'>",
            f"<h2>{slide_number}. {self._escape_html(slide.title)}</h2>",
        ]

        for viz in slide.visualizations:
            # Title
            if viz.config and viz.config.title:
                parts.append(f"<h3>{self._escape_html(viz.config.title)}</h3>")

            # Chart image
            if viz.id in chart_images:
                img_base64 = base64.b64encode(chart_images[viz.id]).decode()
                parts.append(
                    f"<img src='data:image/png;base64,{img_base64}' alt='Chart' class='chart'>"
                )

            # Comment
            if viz.comment and options.include_comments:
                parts.append(f"<p class='comment'>{self._escape_html(viz.comment)}</p>")

        parts.append("</div>")
        return parts

    def _get_html_styles(self) -> str:
        """Get CSS styles for HTML export."""
        return """
            body { font-family: 'Segoe UI', Arial, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; background: #f8fafc; }
            h1 { color: #10B981; text-align: center; border-bottom: 2px solid #10B981; padding-bottom: 10px; }
            h2 { color: #1E293B; border-left: 4px solid #10B981; padding-left: 10px; margin-top: 30px; }
            h3 { color: #334155; }
            .slide { background: white; padding: 20px; margin: 20px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .chart { max-width: 100%; height: auto; border-radius: 8px; margin: 15px 0; }
            .comment { font-style: italic; color: #64748B; background: #F8FAFC; padding: 10px; border-radius: 4px; border-left: 3px solid #CBD5E1; }
            .meta { color: #64748B; font-size: 14px; text-align: center; }
            .header { color: #475569; font-size: 16px; }
            .footer { color: #94A3B8; font-size: 14px; text-align: center; margin-top: 40px; }
        """

    def _generate_latex_content(
        self,
        analysis: Analysis,
        options: ExportOptions,
        chart_images: Dict[str, bytes],
    ) -> str:
        """Generate LaTeX content for an analysis."""
        latex_parts = [
            "\\documentclass{article}",
            "\\usepackage[utf8]{inputenc}",
            "\\usepackage{graphicx}",
            "\\usepackage{geometry}",
            "\\geometry{a4paper, margin=20mm}",
            "\\title{" + self._escape_latex(analysis.name) + "}",
            "\\date{" + datetime.now().strftime("%Y-%m-%d") + "}",
            "\\begin{document}",
            "\\maketitle",
        ]

        # Header text
        if options.header_text:
            latex_parts.append("\\section*{" + self._escape_latex(options.header_text) + "}")

        # Slides
        for i, slide in enumerate(analysis.slides):
            latex_parts.extend(self._generate_slide_latex(slide, i + 1, options, chart_images))

        # Footer
        if options.footer_text:
            latex_parts.append("\\vspace{1cm}")
            latex_parts.append("\\textit{" + self._escape_latex(options.footer_text) + "}")

        latex_parts.append("\\end{document}")

        return "\n".join(latex_parts)

    def _generate_slide_latex(
        self,
        slide: Slide,
        slide_number: int,
        options: ExportOptions,
        chart_images: Dict[str, bytes],
    ) -> List[str]:
        """Generate LaTeX for a single slide."""
        parts = [
            "\\section{" + f"{slide_number}. " + self._escape_latex(slide.title) + "}",
        ]

        for viz in slide.visualizations:
            if viz.config and viz.config.title:
                parts.append("\\subsection{" + self._escape_latex(viz.config.title) + "}")

            # Note: Chart images would need to be saved to files for LaTeX
            # This is a simplified version

            if viz.comment and options.include_comments:
                parts.append("\\textit{" + self._escape_latex(viz.comment) + "}")

        return parts

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize a filename for safe filesystem use."""
        # Replace spaces and special characters
        safe = "".join(c if c.isalnum() or c in "._-" else "_" for c in filename)
        return safe

    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        replacements = {
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#39;",
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        return text

    def _escape_latex(self, text: str) -> str:
        """Escape LaTeX special characters."""
        replacements = {
            "&": r"\&",
            "%": r"\%",
            "$": r"\$",
            "#": r"\#",
            "_": r"\_",
            "{": r"\{",
            "}": r"\}",
            "~": r"\textasciitilde{}",
            "^": r"\^{}",
            "\\": r"\textbackslash{}",
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        return text
