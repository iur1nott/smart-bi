"""
PDF Generator - Exportação da análise para PDF usando ReportLab.
Gera todos os visuais empilhados (gráficos, tabelas, métricas) com filtros aplicados.
"""

from typing import List, Dict, Any, Optional
import os
import io
from datetime import datetime

from domain.entities import Analysis, Visualization, VisualizationType
from domain.value_objects import ExportOptions


class PDFGenerator:
    def __init__(self, output_dir: str = "download"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_pdf(
        self,
        analysis: Analysis,
        options: ExportOptions,
        chart_images: Optional[Dict[str, bytes]] = None,
        table_data: Optional[Dict[str, Dict]] = None,
        metric_data: Optional[Dict[str, Dict]] = None,
    ) -> str:
        from reportlab.lib.pagesizes import A4, letter, legal
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.lib.units import mm
        from reportlab.lib.enums import TA_CENTER, TA_LEFT

        chart_images = chart_images or {}
        table_data = table_data or {}
        metric_data = metric_data or {}

        page_sizes = {"a4": A4, "letter": letter, "legal": legal}
        page_size = page_sizes.get(options.paper_size, A4)
        if options.orientation == "landscape":
            page_size = (page_size[1], page_size[0])

        output_filename = (
            f"{analysis.name.replace(' ', '_')}_"
            f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        )
        output_path = os.path.join(self.output_dir, output_filename)

        doc = SimpleDocTemplate(
            output_path,
            pagesize=page_size,
            rightMargin=options.margin_mm * mm,
            leftMargin=options.margin_mm * mm,
            topMargin=options.margin_mm * mm,
            bottomMargin=options.margin_mm * mm,
        )

        styles = getSampleStyleSheet()

        style_title = ParagraphStyle(
            "Title",
            parent=styles["Title"],
            fontSize=30,
            spaceAfter=8,
            spaceBefore=0,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#1E293B"),
            fontName="Helvetica-Bold",
        )
        style_subtitle = ParagraphStyle(
            "Subtitle",
            parent=styles["Normal"],
            fontSize=10,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#64748B"),
        )
        style_slide = ParagraphStyle(
            "SlideTitle",
            parent=styles["Heading1"],
            fontSize=15,
            spaceBefore=10,
            spaceAfter=8,
            textColor=colors.HexColor("#1E293B"),
            borderPad=4,
        )
        style_viz_title = ParagraphStyle(
            "VizTitle",
            parent=styles["Heading2"],
            fontSize=11,
            spaceBefore=14,
            spaceAfter=6,
            textColor=colors.HexColor("#334155"),
        )
        style_caption = ParagraphStyle(
            "Caption",
            parent=styles["Normal"],
            fontSize=9,
            textColor=colors.HexColor("#94A3B8"),
            alignment=TA_CENTER,
            spaceAfter=8,
        )
        style_comment = ParagraphStyle(
            "Comment",
            parent=styles["Italic"],
            fontSize=9,
            textColor=colors.HexColor("#64748B"),
            leftIndent=12,
            spaceAfter=8,
        )
        style_metric_label = ParagraphStyle(
            "MetricLabel",
            parent=styles["Normal"],
            fontSize=10,
            textColor=colors.HexColor("#64748B"),
            alignment=TA_CENTER,
            spaceAfter=4,
        )
        style_metric_value = ParagraphStyle(
            "MetricValue",
            parent=styles["Normal"],
            fontSize=28,
            textColor=colors.HexColor("#1E293B"),
            alignment=TA_CENTER,
            fontName="Helvetica-Bold",
            spaceAfter=16,
        )

        story = []

        # ── Capa ─────────────────────────────────────────────────────────────
        if options.header_text:
            story.append(Paragraph(options.header_text, style_caption))
            story.append(Spacer(1, 4 * mm))

        story.append(Spacer(1, 20 * mm))
        story.append(Paragraph(analysis.name, style_title))
        story.append(
            Paragraph(
                f"Exportado em {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                style_subtitle,
            )
        )

        total_vizs = sum(
            1 for s in analysis.slides
            for v in s.visualizations
            if v.config and v.config.visualization_type != VisualizationType.MEASURES
        )
        story.append(
            Paragraph(
                f"{len(analysis.slides)} slide(s) · {total_vizs} visualização(ões)",
                style_subtitle,
            )
        )
        story.append(Spacer(1, 10 * mm))

        # ── Slides ────────────────────────────────────────────────────────────
        for slide_idx, slide in enumerate(analysis.slides):
            vizs = [
                v for v in slide.visualizations
                if v.config and v.config.visualization_type != VisualizationType.MEASURES
            ]
            if not vizs:
                continue

            if slide_idx > 0:
                story.append(PageBreak())

            story.append(Paragraph(slide.title, style_slide))
            story.append(self._hr(doc, page_size, options.margin_mm * mm))
            story.append(Spacer(1, 4 * mm))

            for viz in vizs:
                vtype = viz.config.visualization_type
                viz_title = viz.config.title  # só mostra se o usuário definiu

                if viz_title:
                    story.append(Paragraph(viz_title, style_viz_title))

                if vtype == VisualizationType.METRIC_CARD and viz.id in metric_data:
                    story.extend(
                        self._build_metric(metric_data[viz.id], style_metric_value, style_metric_label)
                    )

                elif vtype == VisualizationType.TABLE and viz.id in table_data:
                    story.extend(
                        self._build_table(table_data[viz.id], doc, page_size, options.margin_mm * mm)
                    )

                elif viz.id in chart_images:
                    story.extend(
                        self._build_chart(chart_images[viz.id], doc, page_size, options.margin_mm * mm)
                    )

                else:
                    story.append(
                        Paragraph("[Visual não disponível]", style_caption)
                    )

                if options.include_comments and viz.comment:
                    story.append(Paragraph(f"💬 {viz.comment}", style_comment))

                story.append(Spacer(1, 4 * mm))

        # ── Rodapé ───────────────────────────────────────────────────────────
        if options.footer_text:
            story.append(Spacer(1, 8 * mm))
            story.append(Paragraph(options.footer_text, style_caption))

        doc.build(story)
        return output_path

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _hr(self, doc, page_size, margin):
        from reportlab.platypus import HRFlowable
        usable_width = page_size[0] - 2 * margin
        return HRFlowable(
            width=usable_width,
            thickness=0.5,
            color="#E2E8F0",
            spaceAfter=6,
        )

    def _build_chart(self, img_bytes: bytes, doc, page_size, margin) -> list:
        from reportlab.platypus import Image
        from reportlab.lib.units import inch

        usable_width = page_size[0] - 2 * margin
        max_height = page_size[1] * 0.45  # max 45% da página

        buf = io.BytesIO(img_bytes)
        img = Image(buf, width=usable_width, height=max_height, kind="proportional")
        return [img]

    def _build_table(self, tdata: dict, doc, page_size, margin) -> list:
        from reportlab.platypus import Table, TableStyle, Spacer
        from reportlab.lib import colors
        from reportlab.lib.units import mm

        cols = tdata.get("columns", [])
        rows = tdata.get("data", [])
        if not cols or not rows:
            return []

        usable_width = page_size[0] - 2 * margin
        col_w = usable_width / max(len(cols), 1)

        header = [str(c) for c in cols]
        body = [[str(r.get(c, ""))[:30] for c in cols] for r in rows[:60]]
        table_data = [header] + body

        t = Table(table_data, colWidths=[col_w] * len(cols), repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND",   (0, 0), (-1, 0),  colors.HexColor("#7BAFC8")),
            ("TEXTCOLOR",    (0, 0), (-1, 0),  colors.white),
            ("FONTNAME",     (0, 0), (-1, 0),  "Helvetica-Bold"),
            ("FONTSIZE",     (0, 0), (-1, 0),  9),
            ("BOTTOMPADDING",(0, 0), (-1, 0),  8),
            ("TOPPADDING",   (0, 0), (-1, 0),  8),
            ("BACKGROUND",   (0, 1), (-1, -1), colors.white),
            ("ROWBACKGROUNDS",(0, 1),(-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
            ("TEXTCOLOR",    (0, 1), (-1, -1), colors.HexColor("#334155")),
            ("FONTNAME",     (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE",     (0, 1), (-1, -1), 8),
            ("BOTTOMPADDING",(0, 1), (-1, -1), 6),
            ("TOPPADDING",   (0, 1), (-1, -1), 6),
            ("GRID",         (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ]))
        return [t, Spacer(1, 3 * mm)]

    def _build_metric(self, mdata: dict, style_value, style_label) -> list:
        from reportlab.platypus import Paragraph, Spacer, Table, TableStyle
        from reportlab.lib import colors
        from reportlab.lib.units import mm

        val = mdata.get("value")
        title = mdata.get("title", "")
        agg_labels = {"sum": "Total", "mean": "Média", "count": "Contagem",
                      "min": "Mínimo", "max": "Máximo"}
        agg_label = agg_labels.get(mdata.get("agg", "sum"), "")

        if val is None:
            return []

        if isinstance(val, float):
            if abs(val) >= 1_000_000:
                formatted = f"{val / 1_000_000:.2f}M"
            elif abs(val) >= 1_000:
                formatted = f"{val / 1_000:.2f}K"
            else:
                formatted = f"{val:.2f}"
        else:
            try:
                formatted = f"{int(val):,}"
            except Exception:
                formatted = str(val)

        inner = [
            [Paragraph(formatted, style_value)],
            [Paragraph(f"{agg_label} · {title}", style_label)],
        ]
        t = Table(inner, colWidths=["100%"])
        t.setStyle(TableStyle([
            ("BACKGROUND",   (0, 0), (-1, -1), colors.HexColor("#EFF6FF")),
            ("BOX",          (0, 0), (-1, -1), 1, colors.HexColor("#BFDBFE")),
            ("ROUNDEDCORNERS", [8]),
            ("TOPPADDING",   (0, 0), (-1, -1), 14),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 14),
            ("LEFTPADDING",  (0, 0), (-1, -1), 20),
            ("RIGHTPADDING", (0, 0), (-1, -1), 20),
        ]))
        return [t, Spacer(1, 4 * mm)]
