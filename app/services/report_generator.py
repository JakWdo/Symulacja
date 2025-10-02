"""Service for generating analysis reports in various formats."""

import io
from datetime import datetime
from html import escape
from typing import Any, Dict, List
from uuid import UUID

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, KeepTogether, ListFlowable, ListItem
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import FocusGroup, Project


class ReportGenerator:
    """Generate reports in PDF and CSV formats."""

    def _create_styles(self):
        """Create custom styles for the report."""
        styles = getSampleStyleSheet()

        styles.add(ParagraphStyle(
            name='ReportTitle',
            parent=styles['Heading1'],
            fontSize=28,
            textColor=colors.HexColor('#0f172a'),
            spaceAfter=6,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
        ))

        styles.add(ParagraphStyle(
            name='ReportSubtitle',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#64748b'),
            spaceAfter=30,
            alignment=TA_CENTER,
        ))

        styles.add(ParagraphStyle(
            name='SectionHeading',
            parent=styles['Heading2'],
            fontSize=18,
            textColor=colors.HexColor('#1e293b'),
            spaceAfter=12,
            spaceBefore=20,
            fontName='Helvetica-Bold',
            borderPadding=(0, 0, 8, 0),
            borderColor=colors.HexColor('#3b82f6'),
            borderWidth=3,
        ))

        styles.add(ParagraphStyle(
            name='Subsection',
            parent=styles['Heading3'],
            fontSize=14,
            textColor=colors.HexColor('#475569'),
            spaceAfter=8,
            spaceBefore=12,
            fontName='Helvetica-Bold',
        ))

        # Reuse the built-in BodyText style instead of redefining (avoids duplicate key)
        body = styles['BodyText']
        body.fontSize = 11
        body.textColor = colors.HexColor('#334155')
        body.spaceAfter = 12
        body.alignment = TA_JUSTIFY

        styles.add(ParagraphStyle(
            name='Insight',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#0f766e'),
            leftIndent=20,
            rightIndent=20,
            spaceAfter=10,
            borderPadding=10,
            backColor=colors.HexColor('#f0fdfa'),
            borderColor=colors.HexColor('#14b8a6'),
            borderWidth=1,
            borderRadius=5,
        ))

        return styles

    def _create_polarization_chart(self, polarization_score: float) -> Drawing:
        """Create a pie chart showing polarization level."""
        drawing = Drawing(200, 200)

        # Create pie chart
        pie = Pie()
        pie.x = 50
        pie.y = 50
        pie.width = 100
        pie.height = 100

        # Data: polarized vs unified
        pie.data = [polarization_score * 100, (1 - polarization_score) * 100]
        pie.labels = ['Polarized', 'Unified']
        pie.slices[0].fillColor = colors.HexColor('#ef4444')
        pie.slices[1].fillColor = colors.HexColor('#22c55e')

        drawing.add(pie)
        return drawing

    def _create_cluster_chart(self, clusters: List[Dict[str, Any]]) -> Drawing:
        """Create a bar chart showing cluster sizes."""
        drawing = Drawing(400, 200)

        bc = VerticalBarChart()
        bc.x = 50
        bc.y = 50
        bc.height = 125
        bc.width = 300
        bc.data = [[cluster['size'] for cluster in clusters[:5]]]  # Max 5 clusters
        bc.categoryAxis.categoryNames = [f"Cluster {i+1}" for i in range(len(clusters[:5]))]
        bc.valueAxis.valueMin = 0
        bc.bars[0].fillColor = colors.HexColor('#3b82f6')

        drawing.add(bc)
        return drawing

    async def generate_pdf_report(
        self,
        db: AsyncSession,
        focus_group_id: UUID,
        analysis_data: Dict[str, Any]
    ) -> bytes:
        """Generate a comprehensive PDF report for focus group analysis."""

        # Fetch focus group data
        result = await db.execute(
            select(FocusGroup).where(FocusGroup.id == focus_group_id)
        )
        focus_group = result.scalar_one_or_none()

        if not focus_group:
            raise ValueError("Focus group not found")

        # Fetch project data
        result = await db.execute(
            select(Project).where(Project.id == focus_group.project_id)
        )
        project = result.scalar_one_or_none()

        # Create PDF buffer
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch,
        )
        story = []

        # Get custom styles
        styles = self._create_styles()

        # ========== COVER PAGE ==========
        story.append(Spacer(1, 1.5 * inch))
        story.append(Paragraph("Focus Group Analysis Report", styles['ReportTitle']))
        story.append(Paragraph(
            f"Generated on {datetime.now().strftime('%B %d, %Y')}",
            styles['ReportSubtitle']
        ))
        story.append(Spacer(1, 0.5 * inch))

        # Project overview box
        overview_data = [
            ['Project', project.name if project else 'Unknown'],
            ['Focus Group', focus_group.name],
            ['Participants', str(len(focus_group.persona_ids))],
            ['Questions', str(len(focus_group.questions))],
            ['Status', focus_group.status.upper()],
        ]
        t = Table(overview_data, colWidths=[2*inch, 4*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f1f5f9')),
            ('BACKGROUND', (1, 0), (1, -1), colors.white),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1e293b')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
            ('PADDING', (0, 0), (-1, -1), 12),
        ]))
        story.append(t)
        story.append(PageBreak())

        # ========== EXECUTIVE SUMMARY ==========
        story.append(Paragraph("Executive Summary", styles['SectionHeading']))
        story.append(Spacer(1, 0.1 * inch))

        idea_score = analysis_data.get('idea_score', 0.0)
        idea_grade = analysis_data.get('idea_grade', 'N/A')
        metrics = analysis_data.get('metrics', {})
        sentiment_summary = metrics.get('sentiment_summary', {})
        engagement = metrics.get('engagement', {})

        story.append(Paragraph(
            f"<b>Overall Idea Score:</b> {idea_score:.1f}/100 — {idea_grade}.",
            styles['BodyText']
        ))

        story.append(Paragraph(
            "The score blends participant sentiment and consensus to gauge whether the concept "
            "resonates with the simulated audience.",
            styles['BodyText']
        ))

        metric_rows = [
            ["Consensus", f"{metrics.get('consensus', 0.0) * 100:.1f}%"],
            ["Average Sentiment", f"{metrics.get('average_sentiment', 0.0):+.2f}"],
            ["Positive Responses", f"{sentiment_summary.get('positive_ratio', 0.0) * 100:.1f}%"],
            ["Negative Responses", f"{sentiment_summary.get('negative_ratio', 0.0) * 100:.1f}%"],
            [
                "Completion Rate",
                f"{engagement.get('completion_rate', 0.0) * 100:.1f}%",
            ],
            [
                "Avg Response Time",
                f"{engagement.get('average_response_time_ms') or 0:.0f} ms",
            ],
            [
                "Consistency Score",
                f"{engagement.get('consistency_score', 0.0):.2f}" if engagement.get('consistency_score') is not None else "N/A",
            ],
        ]

        metrics_table = Table(metric_rows, colWidths=[2.5 * inch, 3.5 * inch])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e0f2fe')),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5f5')),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(metrics_table)
        story.append(Spacer(1, 0.3 * inch))

        signal_breakdown = analysis_data.get('signal_breakdown', {})

        def _render_signal_section(entries: List[Dict[str, Any]], heading: str) -> None:
            if not entries:
                return
            story.append(Paragraph(heading, styles['Subsection']))
            items: List[ListItem] = []
            for entry in entries:
                title = escape(str(entry.get('title', 'Insight')))
                summary = escape(str(entry.get('summary', '')))
                evidence = entry.get('evidence')
                evidence_text = escape(str(evidence)) if evidence else ''
                bullet_text = f"<b>{title}</b> — {summary}"
                if evidence_text:
                    bullet_text += f"<br/><font size=9 color='#475569'><i>{evidence_text}</i></font>"
                items.append(
                    ListItem(
                        Paragraph(bullet_text, styles['BodyText']),
                        bulletColor=colors.HexColor('#0f172a'),
                    )
                )

            story.append(
                ListFlowable(
                    items,
                    bulletType='bullet',
                    start='circle',
                    bulletFontName='Helvetica',
                    bulletFontSize=8,
                )
            )
            story.append(Spacer(1, 0.2 * inch))

        _render_signal_section(signal_breakdown.get('strengths', []), "Najsilniejsze sygnały")
        _render_signal_section(signal_breakdown.get('opportunities', []), "Szanse do wykorzystania")
        _render_signal_section(signal_breakdown.get('risks', []), "Ryzyka i bariery")

        persona_patterns = analysis_data.get('persona_patterns', [])
        if persona_patterns:
            story.append(Paragraph("Persona Patterns", styles['Subsection']))
            persona_table_data = [[
                'Persona ID',
                'Klasyfikacja',
                'Avg Sentiment',
                'Contributions',
                'Last Activity',
                'Podsumowanie',
            ]]

            classification_labels = {
                'champion': 'Champion',
                'detractor': 'Detraktor',
                'low_engagement': 'Niska aktywność',
                'neutral': 'Neutralny',
            }

            for pattern in persona_patterns[:12]:
                persona_table_data.append(
                    [
                        pattern.get('persona_id'),
                        classification_labels.get(pattern.get('classification'), 'Neutralny'),
                        f"{pattern.get('avg_sentiment', 0.0):+.2f}",
                        str(pattern.get('contribution_count', 0)),
                        pattern.get('last_activity', '—') or '—',
                        pattern.get('summary', ''),
                    ]
                )

            persona_table = Table(persona_table_data, colWidths=[1.4*inch, 1.2*inch, 1*inch, 1*inch, 1.4*inch, 2*inch])
            persona_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f1f5f9')),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('ALIGN', (2, 1), (3, -1), 'CENTER'),
                ('ALIGN', (0, 1), (1, -1), 'LEFT'),
                ('ALIGN', (4, 1), (5, -1), 'LEFT'),
                ('GRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#cbd5e1')),
                ('PADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(persona_table)
            story.append(Spacer(1, 0.2 * inch))

        evidence_feed = analysis_data.get('evidence_feed', {})
        positives = evidence_feed.get('positives', [])
        negatives = evidence_feed.get('negatives', [])
        if positives or negatives:
            story.append(Paragraph("Evidence Highlights", styles['Subsection']))

            negative_style = ParagraphStyle(
                name='NegativeInsight',
                parent=styles['Insight'],
                textColor=colors.HexColor('#991b1b'),
                backColor=colors.HexColor('#fef2f2'),
                borderColor=colors.HexColor('#fee2e2'),
            )

            def _format_quote(sample: Dict[str, Any], tone: str) -> Paragraph:
                persona_id = escape(str(sample.get('persona_id', '—') or '—'))
                sentiment = sample.get('sentiment', 0.0)
                question_raw = sample.get('question', '') or ''
                question = escape(question_raw[:200]) if question_raw else ''
                quote = escape(str(sample.get('response', '')))
                meta = f"Persona: {persona_id} • Sentiment: {sentiment:+.2f}"
                if question:
                    meta += f" • Question: {question[:80]}"
                text = (
                    f"<b>{quote}</b><br/><font size=9 color='#475569'>{meta}</font>"
                )
                style = styles['Insight'] if tone == 'positive' else styles['BodyText']
                if tone == 'negative':
                    style = negative_style
                return Paragraph(text, style)

            if positives:
                story.append(Paragraph("Pozytywne sygnały", styles['BodyText']))
                for sample in positives[:5]:
                    story.append(_format_quote(sample, 'positive'))

            if negatives:
                story.append(Paragraph("Ostrzeżenia / bariery", styles['BodyText']))
                for sample in negatives[:5]:
                    story.append(_format_quote(sample, 'negative'))

        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()

    async def generate_csv_report(
        self,
        db: AsyncSession,
        focus_group_id: UUID,
        analysis_data: Dict[str, Any]
    ) -> bytes:
        """Generate an Excel workbook summarizing insight metrics."""

        result = await db.execute(
            select(FocusGroup).where(FocusGroup.id == focus_group_id)
        )
        focus_group = result.scalar_one_or_none()
        if not focus_group:
            raise ValueError("Focus group not found")

        output = io.BytesIO()
        metrics = analysis_data.get('metrics', {})
        sentiment_summary = metrics.get('sentiment_summary', {})
        engagement = metrics.get('engagement', {})

        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            summary_data = {
                'Metric': [
                    'Focus Group Name',
                    'Total Participants',
                    'Total Questions',
                    'Idea Score',
                    'Idea Grade',
                    'Consensus',
                    'Average Sentiment',
                    'Positive Responses',
                    'Negative Responses',
                    'Completion Rate',
                    'Average Response Time (ms)',
                    'Consistency Score',
                    'Analysis Date',
                ],
                'Value': [
                    focus_group.name,
                    len(focus_group.persona_ids),
                    len(focus_group.questions),
                    f"{analysis_data.get('idea_score', 0.0):.1f}",
                    analysis_data.get('idea_grade', 'N/A'),
                    f"{metrics.get('consensus', 0.0) * 100:.1f}%",
                    f"{metrics.get('average_sentiment', 0.0):+.2f}",
                    f"{sentiment_summary.get('positive_ratio', 0.0) * 100:.1f}%",
                    f"{sentiment_summary.get('negative_ratio', 0.0) * 100:.1f}%",
                    f"{engagement.get('completion_rate', 0.0) * 100:.1f}%",
                    f"{engagement.get('average_response_time_ms') or 0:.0f}",
                    (
                        f"{engagement.get('consistency_score', 0.0):.2f}"
                        if engagement.get('consistency_score') is not None
                        else 'N/A'
                    ),
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                ],
            }
            pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)

            signal_breakdown = analysis_data.get('signal_breakdown', {})
            signals_rows: List[Dict[str, Any]] = []
            for category, entries in signal_breakdown.items():
                for entry in entries or []:
                    signals_rows.append(
                        {
                            'Category': category,
                            'Title': entry.get('title'),
                            'Summary': entry.get('summary'),
                            'Evidence': entry.get('evidence'),
                        }
                    )
            if signals_rows:
                pd.DataFrame(signals_rows).to_excel(writer, sheet_name='Signals', index=False)

            persona_patterns = analysis_data.get('persona_patterns', [])
            if persona_patterns:
                persona_pattern_rows = [
                    {
                        'Persona ID': item.get('persona_id'),
                        'Classification': item.get('classification'),
                        'Average Sentiment': item.get('avg_sentiment'),
                        'Contributions': item.get('contribution_count'),
                        'Last Activity': item.get('last_activity'),
                        'Summary': item.get('summary'),
                    }
                    for item in persona_patterns
                ]
                pd.DataFrame(persona_pattern_rows).to_excel(writer, sheet_name='Persona Patterns', index=False)

            evidence_feed = analysis_data.get('evidence_feed', {})
            evidence_rows: List[Dict[str, Any]] = []
            for tone, entries in evidence_feed.items():
                for entry in entries or []:
                    evidence_rows.append(
                        {
                            'Tone': tone,
                            'Persona ID': entry.get('persona_id'),
                            'Question': entry.get('question'),
                            'Response': entry.get('response'),
                            'Sentiment': entry.get('sentiment'),
                            'Consistency Score': entry.get('consistency_score'),
                            'Created At': entry.get('created_at'),
                        }
                    )
            if evidence_rows:
                pd.DataFrame(evidence_rows).to_excel(writer, sheet_name='Evidence', index=False)

        output.seek(0)
        return output.getvalue()
