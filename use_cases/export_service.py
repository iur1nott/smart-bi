"""
Export Service - Dashboard export to PDF (pdflatex/reportlab), LaTeX, HTML.
Uses Jinja2 templates in templates/; falls back to reportlab if pdflatex
is not on PATH.
"""

from __future__ import annotations

import base64
import logging
import os
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from jinja2 import Environment, FileSystemLoader

from domain.entities import Dashboard, Visualization
from domain.value_objects import ExportOptions

logger = logging.getLogger(__name__)

_TEMPLATE_DIR = Path(__file__).parent.parent / "templates"


def _latex_escape(text: str) -> str:
    if not text:
        return ""
    for char, rep in [
        ("\\", r"\textbackslash{}"), ("&", r"\&"), ("%", r"\%"),
        ("$", r"\$"), ("#", r"\#"), ("_", r"\_"), ("{", r"\{"),
        ("}", r"\}"), ("~", r"\textasciitilde{}"), ("^", r"\^{}"),
    ]:
        text = text.replace(char, rep)
    return text


def _jinja_env() -> Environment:
    # Use standard Jinja2 delimiters.  Jinja2 processes and removes them before
    # pdflatex ever sees the file, so {% %} in the template never reaches LaTeX
    # and never triggers LaTeX's % comment behaviour.
    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATE_DIR)),
        trim_blocks=True,
        lstrip_blocks=True,
        autoescape=False,
    )
    env.filters["latex_escape"] = _latex_escape
    return env


def _build_viz_ctx(
    viz: Visualization,
    image_dir: str,
    chart_images: Dict[str, bytes],
    include_comments: bool,
) -> dict:
    ctx = {
        "title":      (viz.config.title if viz.config else "") or "Visualização",
        "comment":    viz.comment if include_comments else "",
        "image_path": "",
    }
    if viz.viz_id in chart_images:
        img_path = os.path.join(image_dir, f"{viz.viz_id}.png")
        with open(img_path, "wb") as f:
            f.write(chart_images[viz.viz_id])
        ctx["image_path"] = img_path
    return ctx


class ExportService:
    """
    Exports a Dashboard to PDF, LaTeX source, or HTML.

    PDF pipeline:
      1. Render Jinja2 LaTeX template (report.tex.j2 or slides.tex.j2).
      2. Compile with pdflatex (two passes).
      3. Fall back to reportlab if pdflatex is not available.
    """

    def __init__(self, output_dir: str = "exports"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    # ── Public ───────────────────────────────────────────────────────────────

    def export_to_pdf(
        self,
        dashboard: Dashboard,
        options: Optional[ExportOptions] = None,
        chart_images: Optional[Dict[str, bytes]] = None,
        use_slides: bool = False,
    ) -> Optional[bytes]:
        """Return raw PDF bytes, or None on failure."""
        options = options or ExportOptions()
        chart_images = chart_images or {}

        with tempfile.TemporaryDirectory() as tmp:
            image_dir = os.path.join(tmp, "images")
            os.makedirs(image_dir, exist_ok=True)

            latex_src = self._render_latex(
                dashboard, options, chart_images, image_dir, use_slides
            )
            tex_path = os.path.join(tmp, "document.tex")
            with open(tex_path, "w", encoding="utf-8") as f:
                f.write(latex_src)

            pdf_path = self._compile(tex_path, tmp)
            if pdf_path and os.path.exists(pdf_path):
                with open(pdf_path, "rb") as f:
                    return f.read()

        # pdflatex failed — try reportlab
        return self._reportlab(dashboard, chart_images, options)

    def export_to_latex(
        self,
        dashboard: Dashboard,
        options: Optional[ExportOptions] = None,
        chart_images: Optional[Dict[str, bytes]] = None,
        use_slides: bool = False,
    ) -> bytes:
        """Return rendered LaTeX source as bytes."""
        options = options or ExportOptions()
        with tempfile.TemporaryDirectory() as tmp:
            image_dir = os.path.join(tmp, "images")
            os.makedirs(image_dir, exist_ok=True)
            src = self._render_latex(
                dashboard, options, chart_images or {}, image_dir, use_slides
            )
        return src.encode("utf-8")

    def export_to_html(
        self,
        dashboard: Dashboard,
        options: Optional[ExportOptions] = None,
        chart_images: Optional[Dict[str, bytes]] = None,
    ) -> bytes:
        """Return self-contained HTML as bytes."""
        options = options or ExportOptions()
        return self._html(dashboard, options, chart_images or {}).encode("utf-8")

    # ── LaTeX rendering ───────────────────────────────────────────────────────

    def _render_latex(
        self,
        dashboard: Dashboard,
        options: ExportOptions,
        chart_images: Dict[str, bytes],
        image_dir: str,
        use_slides: bool,
    ) -> str:
        tpl_name = "slides.tex.j2" if use_slides else "report.tex.j2"
        try:
            tpl = _jinja_env().get_template(tpl_name)
        except Exception as e:
            logger.warning(f"Template not found ({e}); using minimal fallback")
            return self._minimal_latex(dashboard)

        viz_ctxs = [
            _build_viz_ctx(v, image_dir, chart_images, options.include_comments)
            for v in dashboard.visualizations
        ]
        ts = (
            datetime.now().strftime("%d/%m/%Y %H:%M")
            if options.include_timestamp else ""
        )
        return tpl.render(
            title=dashboard.title,
            paper_size=options.paper_size,
            landscape=(options.orientation == "landscape"),
            margin_mm=options.margin_mm,
            header_text=options.header_text,
            footer_text=options.footer_text,
            timestamp=ts,
            visualizations=viz_ctxs,
        )

    def _minimal_latex(self, dashboard: Dashboard) -> str:
        title = _latex_escape(dashboard.title)
        secs = "\n".join(
            f"\\subsection*{{{_latex_escape(v.config.title or '')}}}"
            for v in dashboard.visualizations if v.config
        )
        return (
            r"\documentclass{article}" "\n"
            r"\begin{document}" "\n"
            f"\\title{{{title}}}\n\\maketitle\n"
            f"{secs}\n"
            r"\end{document}"
        )

    def _compile(self, tex_path: str, work_dir: str) -> Optional[str]:
        cmd = [
            "pdflatex", "-interaction=nonstopmode", "-halt-on-error",
            f"-output-directory={work_dir}", tex_path,
        ]
        for _ in range(2):
            try:
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                if r.returncode != 0:
                    logger.warning(f"pdflatex exit {r.returncode}: {r.stdout[-800:]}")
            except FileNotFoundError:
                logger.info("pdflatex not on PATH — falling back to reportlab")
                return None
            except subprocess.TimeoutExpired:
                logger.error("pdflatex timed out")
                return None

        pdf = tex_path.replace(".tex", ".pdf")
        return pdf if os.path.exists(pdf) else None

    # ── reportlab fallback ────────────────────────────────────────────────────

    def _reportlab(
        self,
        dashboard: Dashboard,
        chart_images: Dict[str, bytes],
        options: ExportOptions,
    ) -> Optional[bytes]:
        try:
            from io import BytesIO
            from reportlab.lib.pagesizes import A4, landscape as rl_ls
            from reportlab.lib.units import mm
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib import colors
            from reportlab.platypus import (
                SimpleDocTemplate, Paragraph, Spacer, Image,
            )

            buf = BytesIO()
            psize = rl_ls(A4) if options.orientation == "landscape" else A4
            doc = SimpleDocTemplate(
                buf, pagesize=psize,
                rightMargin=options.margin_mm * mm,
                leftMargin=options.margin_mm * mm,
                topMargin=options.margin_mm * mm,
                bottomMargin=options.margin_mm * mm,
            )
            styles = getSampleStyleSheet()
            t_style = ParagraphStyle("T2", parent=styles["Title"], fontSize=20, spaceAfter=20)
            h_style = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=13, spaceAfter=8)
            c_style = ParagraphStyle(
                "Cmt", parent=styles["Normal"],
                fontSize=9, textColor=colors.grey, spaceAfter=12,
            )

            avail_w = psize[0] - (options.margin_mm * 2) * mm
            story: list = [Paragraph(dashboard.title, t_style), Spacer(1, 6 * mm)]

            for viz in dashboard.visualizations:
                title = viz.config.title if viz.config else ""
                if title:
                    story.append(Paragraph(title, h_style))
                if viz.viz_id in chart_images:
                    from io import BytesIO as BIO
                    img = Image(BIO(chart_images[viz.viz_id]),
                                width=avail_w, height=avail_w * 0.6)
                    story.append(img)
                    story.append(Spacer(1, 4 * mm))
                if options.include_comments and viz.comment:
                    story.append(Paragraph(viz.comment, c_style))
                story.append(Spacer(1, 8 * mm))

            doc.build(story)
            return buf.getvalue()
        except ImportError:
            logger.error("reportlab unavailable; cannot produce PDF without pdflatex")
            return None
        except Exception as e:
            logger.error(f"reportlab fallback failed: {e}")
            return None

    # ── HTML export ───────────────────────────────────────────────────────────

    def _html(
        self,
        dashboard: Dashboard,
        options: ExportOptions,
        chart_images: Dict[str, bytes],
    ) -> str:
        ts = datetime.now().strftime("%d/%m/%Y %H:%M")
        blocks = []
        for viz in dashboard.visualizations:
            title = viz.config.title if viz.config else ""
            img_tag = ""
            if viz.viz_id in chart_images:
                b64 = base64.b64encode(chart_images[viz.viz_id]).decode()
                img_tag = (
                    f'<img src="data:image/png;base64,{b64}" '
                    f'alt="{title}" style="max-width:100%;border-radius:8px;">'
                )
            comment = ""
            if options.include_comments and viz.comment:
                comment = (
                    f'<p style="font-style:italic;color:#64748B;">💬 {viz.comment}</p>'
                )
            blocks.append(f"""
  <section style="background:white;border-radius:12px;padding:24px;
                  margin-bottom:24px;box-shadow:0 1px 4px rgba(0,0,0,.08);">
    <h2 style="margin:0 0 16px;color:#1E293B;font-size:1.1rem;">{title}</h2>
    {img_tag}{comment}
  </section>""")

        return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="UTF-8"><title>{dashboard.title}</title>
<style>
body{{font-family:Inter,Arial,sans-serif;background:#F8FAFC;
     max-width:960px;margin:0 auto;padding:32px 16px;color:#1E293B;}}
h1{{font-size:1.8rem;margin-bottom:4px;}}
.meta{{color:#64748B;font-size:.85rem;margin-bottom:32px;}}
</style></head>
<body>
<h1>{dashboard.title}</h1>
<p class="meta">Exportado em {ts}</p>
{"".join(blocks)}
</body></html>"""
