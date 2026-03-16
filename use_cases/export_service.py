"""
Export Service - Handles export operations to LaTeX and PDF.
Implements the export pipeline: Data -> LaTeX -> PDF.
"""

from typing import List, Dict, Any, Optional
import os
import tempfile
import subprocess
import base64
from pathlib import Path
from datetime import datetime
import logging

from domain.entities import Analysis, Slide, Visualization, VisualizationType
from domain.value_objects import ExportOptions

logger = logging.getLogger(__name__)


class LaTeXTemplateEngine:
    """
    Template engine for generating LaTeX documents.
    Handles the conversion of slides and visualizations to LaTeX code.
    """

    DOCUMENT_TEMPLATE = r"""
\documentclass[{paper_size}{orientation}]{{article}}
\usepackage[utf8]{{inputenc}}
\usepackage[T1]{{fontenc}}
\usepackage{{graphicx}}
\usepackage{{booktabs}}
\usepackage{{longtable}}
\usepackage{{geometry}}
\usepackage{{xcolor}}
\usepackage{{tikz}}
\usepackage{{pgfplots}}
\usepackage{{float}}
\usepackage{{caption}}
\usepackage{{hyperref}}
\pgfplotsset{{compat=1.18}}

\geometry{{margin={margin_mm}mm}}

{extra_packages}

\begin{{document}}

{header}

{content}

{footer}

\end{{document}}
"""

    SLIDE_TEMPLATE = r"""
\section*{{{title}}}

{content}

{comment}

\newpage
"""

    CHART_TEMPLATE = r"""
\begin{{figure}}[H]
\centering
{chart_content}
\caption{{{title}}}
\end{{figure}}
"""

    TABLE_TEMPLATE = r"""
\begin{{table}}[H]
\centering
\caption{{{title}}}
{table_content}
\end{{table}}
"""

    def __init__(self):
        """Initialize the template engine with color palette."""
        self.color_palette = {
            "primary": "#10B981",
            "secondary": "#3B82F6",
            "accent": "#F59E0B",
        }

    def generate_document(
        self, analysis: Analysis, options: ExportOptions, image_paths: Dict[str, str]
    ) -> str:
        """
        Generate a complete LaTeX document for an analysis.

        Args:
            analysis: The analysis to export
            options: Export options
            image_paths: Dictionary mapping visualization IDs to image paths

        Returns:
            Complete LaTeX document as string
        """
        paper_size = options.paper_size + "paper"
        orientation = "" if options.orientation == "portrait" else ",landscape"

        content_parts = []
        for slide in analysis.slides:
            slide_content = self._generate_slide_content(slide, image_paths, options)
            content_parts.append(slide_content)

        header = ""
        if options.header_text:
            header = f"\\textbf{{{self._escape_latex(options.header_text)}}}\n\\vspace{{1em}}\n\n"

        footer = ""
        if options.footer_text:
            footer = f"\\vfill\n\\textit{{{self._escape_latex(options.footer_text)}}}\n"
        if options.include_page_numbers:
            footer += "\\pagenumbering{arabic}\n"

        if options.title_page:
            title_content = self._generate_title_page(analysis, options)
            content_parts.insert(0, title_content)

        document = self.DOCUMENT_TEMPLATE.format(
            paper_size=paper_size,
            orientation=orientation,
            margin_mm=options.margin_mm,
            extra_packages="",
            header=header,
            content="\n".join(content_parts),
            footer=footer,
        )

        return document

    def _generate_title_page(self, analysis: Analysis, options: ExportOptions) -> str:
        """Generate a title page for the document."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        return f"""
\\begin{{titlepage}}
\\centering
\\vspace*{{2cm}}
\\Huge\\textbf{{{self._escape_latex(analysis.name)}}}
\\vspace{{2cm}}

\\Large Data Analysis Report
\\vspace{{1cm}}

\\normalsize Generated: {timestamp}
\\end{{titlepage}}

\\newpage
"""

    def _generate_slide_content(
        self, slide: Slide, image_paths: Dict[str, str], options: ExportOptions
    ) -> str:
        """Generate LaTeX content for a single slide."""
        content_parts = []

        for viz in slide.visualizations:
            if viz.config:
                if viz.config.visualization_type == VisualizationType.TABLE:
                    content = self._generate_table_latex(viz)
                else:
                    content = self._generate_chart_latex(viz, image_paths.get(viz.id))

                if content:
                    content_parts.append(content)

                if options.include_comments and viz.comment:
                    content_parts.append(
                        f"\\textit{{{self._escape_latex(viz.comment)}}}\n\\vspace{{1em}}\n"
                    )

        return self.SLIDE_TEMPLATE.format(
            title=self._escape_latex(slide.title),
            content="\n".join(content_parts),
            comment="",
        )

    def _generate_chart_latex(
        self, visualization: Visualization, image_path: Optional[str] = None
    ) -> str:
        """Generate LaTeX for a chart visualization."""
        if not visualization.config:
            return ""

        title = self._escape_latex(visualization.config.title or "Chart")

        if image_path:
            chart_content = f"\\includegraphics[width=0.9\\textwidth]{{{image_path}}}"
        else:
            chart_content = "% Chart placeholder - image not available"

        return self.CHART_TEMPLATE.format(chart_content=chart_content, title=title)

    def _generate_table_latex(self, visualization: Visualization) -> str:
        """Generate LaTeX for a table visualization."""
        if not visualization.config or not visualization.data_snapshot:
            return ""

        data = visualization.data_snapshot.get("data", [])
        columns = visualization.data_snapshot.get("columns", [])

        if not data or not columns:
            return ""

        title = self._escape_latex(visualization.config.title or "Table")

        num_cols = len(columns)
        col_spec = "|" + "|".join(["l"] * num_cols) + "|"

        header_row = " & ".join([self._escape_latex(str(col)) for col in columns]) + " \\\\\\hline"

        data_rows = []
        for row in data[:100]:
            row_values = [self._escape_latex(str(row.get(col, "")))[:50] for col in columns]
            data_rows.append(" & ".join(row_values) + " \\\\\\hline")

        table_content = (
            f"\\begin{{tabular}}{{{col_spec}}}\n\\hline\n{header_row}\n"
            + "\n".join(data_rows)
            + "\n\\end{tabular}"
        )

        return self.TABLE_TEMPLATE.format(title=title, table_content=table_content)

    def _escape_latex(self, text: str) -> str:
        """Escape special LaTeX characters."""
        if not text:
            return ""
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
        for char, replacement in replacements.items():
            text = text.replace(char, replacement)
        return text


class PDFCompiler:
    """
    Handles LaTeX to PDF compilation.
    Supports multiple compilation methods for maximum compatibility.
    """

    @staticmethod
    def compile_latex(tex_path: str, working_dir: str) -> Optional[str]:
        """
        Compile LaTeX file to PDF using pdflatex.

        Args:
            tex_path: Path to the LaTeX file
            working_dir: Working directory for compilation

        Returns:
            Path to the generated PDF or None if failed
        """
        try:
            result = subprocess.run(
                [
                    "pdflatex",
                    "-interaction=nonstopmode",
                    "-output-directory",
                    working_dir,
                    tex_path,
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )

            pdf_path = tex_path.replace(".tex", ".pdf")
            if os.path.exists(pdf_path):
                return pdf_path

        except FileNotFoundError:
            logger.info("pdflatex not found, using alternative method")
            return PDFCompiler._alternative_pdf_generation(tex_path, working_dir)
        except subprocess.TimeoutExpired:
            logger.error("LaTeX compilation timed out")
        except Exception as e:
            logger.error(f"LaTeX compilation error: {e}")

        return None

    @staticmethod
    def _alternative_pdf_generation(tex_path: str, working_dir: str) -> Optional[str]:
        """
        Alternative PDF generation using reportlab when pdflatex is not available.

        Args:
            tex_path: Path to the LaTeX file (for reference)
            working_dir: Working directory

        Returns:
            Path to the generated PDF or None if failed
        """
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import (
                SimpleDocTemplate,
                Paragraph,
                Spacer,
                PageBreak,
            )
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib.units import mm

            pdf_path = tex_path.replace(".tex", ".pdf")
            doc = SimpleDocTemplate(
                pdf_path,
                pagesize=A4,
                rightMargin=20 * mm,
                leftMargin=20 * mm,
                topMargin=20 * mm,
                bottomMargin=20 * mm,
            )

            styles = getSampleStyleSheet()
            story = [
                Paragraph("Dashboard Builder Export", styles["Title"]),
                Spacer(1, 20),
                Paragraph(
                    "PDF generated using alternative method (LaTeX not available)",
                    styles["Normal"],
                ),
            ]

            doc.build(story)
            return pdf_path

        except ImportError:
            logger.warning("reportlab not available for alternative PDF generation")
        except Exception as e:
            logger.error(f"Alternative PDF generation error: {e}")

        return None


class ExportService:
    """
    Service for exporting analyses to various formats.
    Supports PDF, LaTeX, and HTML output formats.
    """

    def __init__(self, output_dir: str = "download"):
        """Initialize the export service with output directory."""
        self.output_dir = output_dir
        self.template_engine = LaTeXTemplateEngine()
        os.makedirs(output_dir, exist_ok=True)

    def export_to_pdf(
        self,
        analysis: Analysis,
        options: Optional[ExportOptions] = None,
        chart_images: Optional[Dict[str, bytes]] = None,
    ) -> str:
        """
        Export an analysis to PDF format.

        Args:
            analysis: The analysis to export
            options: Export options
            chart_images: Dictionary mapping visualization IDs to chart image bytes

        Returns:
            Path to the generated PDF file
        """
        if options is None:
            options = ExportOptions(format="pdf")

        with tempfile.TemporaryDirectory() as temp_dir:
            image_paths = {}
            if chart_images:
                for viz_id, img_bytes in chart_images.items():
                    img_path = os.path.join(temp_dir, f"{viz_id}.png")
                    with open(img_path, "wb") as f:
                        f.write(img_bytes)
                    image_paths[viz_id] = img_path

            latex_content = self.template_engine.generate_document(analysis, options, image_paths)

            tex_path = os.path.join(temp_dir, "document.tex")
            with open(tex_path, "w", encoding="utf-8") as f:
                f.write(latex_content)

            pdf_path = PDFCompiler.compile_latex(tex_path, temp_dir)

            if pdf_path and os.path.exists(pdf_path):
                output_filename = f"{analysis.name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                output_path = os.path.join(self.output_dir, output_filename)
                os.rename(pdf_path, output_path)
                logger.info(f"Exported PDF: {output_path}")
                return output_path

        raise RuntimeError("Failed to generate PDF")

    def export_to_latex(
        self,
        analysis: Analysis,
        options: Optional[ExportOptions] = None,
        chart_images: Optional[Dict[str, bytes]] = None,
    ) -> str:
        """
        Export an analysis to LaTeX format.

        Args:
            analysis: The analysis to export
            options: Export options
            chart_images: Dictionary mapping visualization IDs to chart image bytes

        Returns:
            Path to the generated LaTeX file
        """
        if options is None:
            options = ExportOptions(format="latex")

        images_dir = os.path.join(self.output_dir, f"{analysis.id}_images")
        os.makedirs(images_dir, exist_ok=True)

        image_paths = {}
        if chart_images:
            for viz_id, img_bytes in chart_images.items():
                img_path = os.path.join(images_dir, f"{viz_id}.png")
                with open(img_path, "wb") as f:
                    f.write(img_bytes)
                image_paths[viz_id] = os.path.basename(img_path)

        latex_content = self.template_engine.generate_document(analysis, options, image_paths)

        output_filename = (
            f"{analysis.name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.tex"
        )
        output_path = os.path.join(self.output_dir, output_filename)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(latex_content)

        logger.info(f"Exported LaTeX: {output_path}")
        return output_path

    def export_to_html(
        self,
        analysis: Analysis,
        options: Optional[ExportOptions] = None,
        chart_images: Optional[Dict[str, bytes]] = None,
    ) -> str:
        """
        Export an analysis to HTML format.

        Args:
            analysis: The analysis to export
            options: Export options
            chart_images: Dictionary mapping visualization IDs to chart image bytes

        Returns:
            Path to the generated HTML file
        """
        if options is None:
            options = ExportOptions(format="html")

        html_content = self._generate_html(analysis, options, chart_images)

        output_filename = (
            f"{analysis.name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        )
        output_path = os.path.join(self.output_dir, output_filename)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        logger.info(f"Exported HTML: {output_path}")
        return output_path

    def _generate_html(
        self,
        analysis: Analysis,
        options: ExportOptions,
        chart_images: Optional[Dict[str, bytes]] = None,
    ) -> str:
        """Generate HTML content for an analysis."""
        slides_html = []

        for slide in analysis.slides:
            visualizations_html = []

            for viz in slide.visualizations:
                viz_html = ""

                if chart_images and viz.id in chart_images:
                    img_data = base64.b64encode(chart_images[viz.id]).decode("utf-8")
                    title = viz.config.title if viz.config else ""
                    viz_html = f'<img src="data:image/png;base64,{img_data}" alt="{title}" style="max-width: 100%;">'

                if viz.config:
                    title = viz.config.title or ""
                    comment_html = ""
                    if options.include_comments and viz.comment:
                        comment_html = f'<p class="comment">{viz.comment}</p>'
                    viz_html = f"""
                    <div class="visualization">
                        <h4>{title}</h4>
                        {viz_html}
                        {comment_html}
                    </div>
                    """

                visualizations_html.append(viz_html)

            slide_html = f"""
            <div class="slide">
                <h2>{slide.title}</h2>
                <div class="visualizations">
                    {"".join(visualizations_html)}
                </div>
            </div>
            """
            slides_html.append(slide_html)

        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{analysis.name}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f8fafc;
        }}
        .slide {{
            background-color: white;
            padding: 30px;
            margin-bottom: 30px;
            border-radius: 12px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .visualization {{
            margin: 20px 0;
        }}
        .comment {{
            font-style: italic;
            color: #64748b;
            margin-top: 10px;
            padding-left: 20px;
            border-left: 3px solid #10b981;
        }}
        img {{
            display: block;
            margin: 0 auto;
            max-width: 100%;
            border-radius: 8px;
        }}
        h1 {{
            color: #1e293b;
            text-align: center;
        }}
        h2 {{
            color: #10b981;
            border-bottom: 2px solid #10b981;
            padding-bottom: 10px;
        }}
        h4 {{
            color: #475569;
        }}
    </style>
</head>
<body>
    <h1>{analysis.name}</h1>
    {"".join(slides_html)}
</body>
</html>
        """

        return html

    def get_supported_formats(self) -> List[str]:
        """Get list of supported export formats."""
        return ["pdf", "latex", "html"]
