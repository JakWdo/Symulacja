"""Service for generating analysis reports in various formats."""

import io
from datetime import datetime
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

        # Key Themes
        key_themes = analysis_data.get('key_themes', [])
        if key_themes:
            story.append(Paragraph("Key Themes & Signals", styles['Subsection']))
            theme_items = []
            for theme in key_themes:
                keyword = theme.get('keyword', '')
                mentions = theme.get('mentions', 0)
                quote = theme.get('representative_quote') or '—'
                bullet = (
                    f"<b>{keyword.title()}</b> ({mentions} mentions) — "
                    f"<i>{quote}</i>"
                )
                theme_items.append(ListItem(Paragraph(bullet, styles['BodyText']), bulletColor=colors.HexColor('#0f172a')))

            story.append(
                ListFlowable(
                    theme_items,
                    bulletType='bullet',
                    start='circle',
                    bulletFontName='Helvetica',
                    bulletFontSize=8,
                )
            )
            story.append(Spacer(1, 0.3 * inch))

        # Question breakdown
        question_breakdown = analysis_data.get('question_breakdown', [])
        if question_breakdown:
            story.append(Paragraph("Question Breakdown", styles['Subsection']))

            question_table_data = [[
                'Question',
                'Idea Score',
                'Consensus',
                'Avg Sentiment',
                'Responses',
            ]]

            for entry in question_breakdown[:10]:
                question_text = entry.get('question', '')
                if len(question_text) > 70:
                    question_text = question_text[:67] + '...'
                question_table_data.append(
                    [
                        question_text,
                        f"{entry.get('idea_score', 0.0):.1f}",
                        f"{entry.get('consensus', 0.0) * 100:.0f}%",
                        f"{entry.get('avg_sentiment', 0.0):+.2f}",
                        str(entry.get('response_count', 0)),
                    ]
                )

            question_table = Table(question_table_data, colWidths=[3.5*inch, 1*inch, 1*inch, 1*inch, 0.8*inch])
            question_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f172a')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
                ('ALIGN', (0, 1), (0, -1), 'LEFT'),
                ('GRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#94a3b8')),
                ('PADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(question_table)
            story.append(Spacer(1, 0.3 * inch))

        # Persona engagement
        persona_engagement = analysis_data.get('persona_engagement', [])
        if persona_engagement:
            story.append(Paragraph("Persona Engagement", styles['Subsection']))
            persona_table_data = [[
                'Persona ID',
                'Contributions',
                'Avg Sentiment',
                'Avg Response Time (ms)',
                'Last Activity',
            ]]

            for persona in persona_engagement[:12]:
                persona_table_data.append(
                    [
                        persona.get('persona_id'),
                        str(persona.get('contribution_count', 0)),
                        f"{persona.get('avg_sentiment', 0.0):+.2f}",
                        f"{persona.get('average_response_time_ms', 0.0):.0f}",
                        persona.get('last_activity', '—'),
                    ]
                )

            persona_table = Table(persona_table_data, colWidths=[2.2*inch, 1*inch, 1.2*inch, 1.8*inch, 1.4*inch])
            persona_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f1f5f9')),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
                ('ALIGN', (0, 1), (0, -1), 'LEFT'),
                ('GRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#cbd5e1')),
                ('PADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(persona_table)

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

            question_breakdown = analysis_data.get('question_breakdown', [])
            if question_breakdown:
                questions_df = pd.DataFrame([
                    {
                        'Question': item.get('question'),
                        'Idea Score': item.get('idea_score'),
                        'Consensus': item.get('consensus'),
                        'Average Sentiment': item.get('avg_sentiment'),
                        'Responses': item.get('response_count'),
                    }
                    for item in question_breakdown
                ])
                questions_df.to_excel(writer, sheet_name='Question Breakdown', index=False)

            key_themes = analysis_data.get('key_themes', [])
            if key_themes:
                themes_df = pd.DataFrame([
                    {
                        'Keyword': theme.get('keyword'),
                        'Mentions': theme.get('mentions'),
                        'Representative Quote': theme.get('representative_quote'),
                    }
                    for theme in key_themes
                ])
                themes_df.to_excel(writer, sheet_name='Key Themes', index=False)

            persona_engagement = analysis_data.get('persona_engagement', [])
            if persona_engagement:
                personas_df = pd.DataFrame([
                    {
                        'Persona ID': persona.get('persona_id'),
                        'Contributions': persona.get('contribution_count'),
                        'Average Sentiment': persona.get('avg_sentiment'),
                        'Average Response Time (ms)': persona.get('average_response_time_ms'),
                        'Last Activity': persona.get('last_activity'),
                    }
                    for persona in persona_engagement
                ])
                personas_df.to_excel(writer, sheet_name='Persona Engagement', index=False)

        output.seek(0)
        return output.getvalue()
