"""
Enhanced Report Generator with AI Summary and Advanced Insights
Generates comprehensive, professional PDF reports
"""

import io
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether, ListFlowable, ListItem, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.lineplots import LinePlot
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import FocusGroup, Project
from app.services.discussion_summarizer import DiscussionSummarizerService
from app.services.metrics_explainer import MetricsExplainerService
from app.services.advanced_insights_service import AdvancedInsightsService
from app.services.insight_service import InsightService


class EnhancedReportGenerator:
    """Generate enhanced PDF reports with AI summaries and advanced analytics"""

    def __init__(self):
        self.insight_service = InsightService()
        self.metrics_explainer = MetricsExplainerService()

    def _create_styles(self):
        """Create custom professional styles"""
        styles = getSampleStyleSheet()

        styles.add(ParagraphStyle(
            name='ReportTitle',
            parent=styles['Heading1'],
            fontSize=32,
            textColor=colors.HexColor('#0f172a'),
            spaceAfter=8,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
        ))

        styles.add(ParagraphStyle(
            name='ReportSubtitle',
            parent=styles['Normal'],
            fontSize=14,
            textColor=colors.HexColor('#64748b'),
            spaceAfter=40,
            alignment=TA_CENTER,
        ))

        styles.add(ParagraphStyle(
            name='SectionHeading',
            parent=styles['Heading2'],
            fontSize=20,
            textColor=colors.HexColor('#1e293b'),
            spaceAfter=14,
            spaceBefore=24,
            fontName='Helvetica-Bold',
        ))

        styles.add(ParagraphStyle(
            name='Subsection',
            parent=styles['Heading3'],
            fontSize=16,
            textColor=colors.HexColor('#475569'),
            spaceAfter=10,
            spaceBefore=14,
            fontName='Helvetica-Bold',
        ))

        body = styles['BodyText']
        body.fontSize = 11
        body.textColor = colors.HexColor('#334155')
        body.spaceAfter = 12
        body.alignment = TA_JUSTIFY
        body.leading = 16

        styles.add(ParagraphStyle(
            name='AIInsight',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#0369a1'),
            leftIndent=20,
            rightIndent=20,
            spaceAfter=12,
            borderPadding=12,
            backColor=colors.HexColor('#e0f2fe'),
            borderColor=colors.HexColor('#0ea5e9'),
            borderWidth=1,
            leading=16,
        ))

        styles.add(ParagraphStyle(
            name='Recommendation',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#065f46'),
            leftIndent=20,
            rightIndent=20,
            spaceAfter=12,
            borderPadding=12,
            backColor=colors.HexColor('#d1fae5'),
            borderColor=colors.HexColor('#10b981'),
            borderWidth=1,
            leading=16,
        ))

        return styles

    async def generate_enhanced_pdf_report(
        self,
        db: AsyncSession,
        focus_group_id: UUID,
        include_ai_summary: bool = True,
        include_advanced_insights: bool = True,
        use_pro_model: bool = False,
    ) -> bytes:
        """
        Generate comprehensive PDF report with AI summary and advanced insights
        """
        # Fetch data
        result = await db.execute(
            select(FocusGroup).where(FocusGroup.id == focus_group_id)
        )
        focus_group = result.scalar_one_or_none()
        if not focus_group:
            raise ValueError("Focus group not found")

        result = await db.execute(
            select(Project).where(Project.id == focus_group.project_id)
        )
        project = result.scalar_one_or_none()

        # Get basic insights
        insights_data = await self.insight_service.generate_focus_group_insights(
            db=db, focus_group_id=str(focus_group_id)
        )

        # Get metric explanations
        explanations = self.metrics_explainer.explain_all_metrics(insights_data)
        health = self.metrics_explainer.get_overall_health_assessment(insights_data)

        # Get AI summary (optional)
        ai_summary = None
        if include_ai_summary:
            try:
                summarizer = DiscussionSummarizerService(use_pro_model=use_pro_model)
                ai_summary = await summarizer.generate_discussion_summary(
                    db=db,
                    focus_group_id=str(focus_group_id),
                    include_demographics=True,
                    include_recommendations=True,
                )
            except Exception as e:
                print(f"Failed to generate AI summary: {e}")

        # Get advanced insights (optional)
        advanced_insights = None
        if include_advanced_insights:
            try:
                advanced_service = AdvancedInsightsService()
                advanced_insights = await advanced_service.generate_advanced_insights(
                    db=db, focus_group_id=str(focus_group_id)
                )
            except Exception as e:
                print(f"Failed to generate advanced insights: {e}")

        # Create PDF
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
        styles = self._create_styles()

        # ========== COVER PAGE ==========
        story.append(Spacer(1, 1.5 * inch))
        story.append(Paragraph(
            "Focus Group Analysis Report",
            styles['ReportTitle']
        ))
        story.append(Paragraph(
            f"Enhanced Insights Report • Generated {datetime.now().strftime('%B %d, %Y')}",
            styles['ReportSubtitle']
        ))

        # Project info box
        overview_data = [
            ['Project', project.name if project else 'Unknown'],
            ['Focus Group', focus_group.name],
            ['Participants', str(len(focus_group.persona_ids))],
            ['Questions', str(len(focus_group.questions))],
            ['Status', focus_group.status.upper()],
            ['Health Score', f"{health['health_score']:.1f}/100 - {health['status_label']}"],
        ]
        t = Table(overview_data, colWidths=[2.2*inch, 4.5*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f1f5f9')),
            ('BACKGROUND', (1, 0), (1, -1), colors.white),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1e293b')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
            ('PADDING', (0, 0), (-1, -1), 14),
        ]))
        story.append(t)
        story.append(PageBreak())

        # ========== AI EXECUTIVE SUMMARY ==========
        if ai_summary:
            story.append(Paragraph("🤖 AI Executive Summary", styles['SectionHeading']))
            story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#3b82f6')))
            story.append(Spacer(1, 0.15 * inch))

            # Executive summary text
            exec_summary = ai_summary.get('executive_summary', '')
            if exec_summary:
                story.append(Paragraph(exec_summary, styles['AIInsight']))
                story.append(Spacer(1, 0.2 * inch))

            # Key Insights
            key_insights = ai_summary.get('key_insights', [])
            if key_insights:
                story.append(Paragraph("💡 Key Insights", styles['Subsection']))
                items = [
                    ListItem(Paragraph(insight, styles['BodyText']), bulletColor=colors.HexColor('#0ea5e9'))
                    for insight in key_insights
                ]
                story.append(ListFlowable(
                    items,
                    bulletType='bullet',
                    start='circle',
                ))
                story.append(Spacer(1, 0.2 * inch))

            # Recommendations
            recommendations = ai_summary.get('recommendations', [])
            if recommendations:
                story.append(Paragraph("🎯 Strategic Recommendations", styles['Subsection']))
                for idx, rec in enumerate(recommendations, 1):
                    story.append(Paragraph(f"<b>{idx}.</b> {rec}", styles['Recommendation']))

            story.append(PageBreak())

        # ========== METRICS WITH EXPLANATIONS ==========
        story.append(Paragraph("📊 Key Metrics & Explanations", styles['SectionHeading']))
        story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#3b82f6')))
        story.append(Spacer(1, 0.15 * inch))

        # Health assessment
        health_color = {
            'healthy': colors.HexColor('#10b981'),
            'good': colors.HexColor('#3b82f6'),
            'fair': colors.HexColor('#f59e0b'),
            'poor': colors.HexColor('#ef4444'),
        }.get(health['status'], colors.HexColor('#64748b'))

        health_data = [
            ['Overall Health', f"{health['health_score']:.1f}/100", health['status_label']],
        ]
        health_table = Table(health_data, colWidths=[2*inch, 1.5*inch, 3.2*inch])
        health_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#f8fafc')),
            ('BACKGROUND', (1, 0), (1, 0), health_color),
            ('BACKGROUND', (2, 0), (2, 0), colors.HexColor('#f8fafc')),
            ('TEXTCOLOR', (1, 0), (1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 14),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('PADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 2, colors.HexColor('#cbd5e1')),
        ]))
        story.append(health_table)
        story.append(Spacer(1, 0.3 * inch))

        # Individual metrics with explanations
        for key in ['idea_score', 'consensus', 'sentiment']:
            if key in explanations:
                exp = explanations[key]
                story.append(Paragraph(f"<b>{exp.name}</b>", styles['Subsection']))

                metric_data = [
                    ['Value', exp.value],
                    ['Interpretation', exp.interpretation],
                    ['Recommended Action', exp.action],
                ]
                if exp.benchmark:
                    metric_data.append(['Benchmark', exp.benchmark])

                metric_table = Table(metric_data, colWidths=[2*inch, 4.7*inch])
                metric_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f1f5f9')),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                    ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
                    ('PADDING', (0, 0), (-1, -1), 10),
                ]))
                story.append(metric_table)
                story.append(Spacer(1, 0.15 * inch))

        story.append(PageBreak())

        # ========== ADVANCED INSIGHTS ==========
        if advanced_insights:
            story.append(Paragraph("📈 Advanced Analytics", styles['SectionHeading']))
            story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#3b82f6')))
            story.append(Spacer(1, 0.15 * inch))

            # Demographic Correlations
            correlations = advanced_insights.get('demographic_correlations', {})
            if correlations:
                story.append(Paragraph("Demographic-Sentiment Correlations", styles['Subsection']))

                for key, corr_data in correlations.items():
                    if isinstance(corr_data, dict) and 'interpretation' in corr_data:
                        story.append(Paragraph(
                            f"<b>{key.replace('_', ' ').title()}:</b> {corr_data['interpretation']}",
                            styles['BodyText']
                        ))

                story.append(Spacer(1, 0.2 * inch))

            # Behavioral Segments
            segments = advanced_insights.get('behavioral_segments', {}).get('segments', [])
            if segments:
                story.append(Paragraph("Behavioral Segments", styles['Subsection']))

                for segment in segments[:5]:  # Top 5 segments
                    seg_data = [
                        ['Segment', segment['label']],
                        ['Size', f"{segment['size']} participants ({segment['percentage']:.1f}%)"],
                        ['Avg Sentiment', f"{segment['characteristics']['avg_sentiment']:.2f}"],
                        ['Avg Response Length', f"{segment['characteristics']['avg_response_length']:.0f} chars"],
                    ]

                    seg_table = Table(seg_data, colWidths=[2*inch, 4.7*inch])
                    seg_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dbeafe')),
                        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 10),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
                        ('PADDING', (0, 0), (-1, -1), 8),
                    ]))
                    story.append(seg_table)
                    story.append(Spacer(1, 0.1 * inch))

                story.append(Spacer(1, 0.2 * inch))

            # Quality Metrics
            quality = advanced_insights.get('quality_metrics', {})
            if quality:
                story.append(Paragraph("Response Quality Analysis", styles['Subsection']))

                quality_data = [
                    ['Overall Quality', f"{quality.get('overall_quality', 0):.2f}"],
                    ['Depth Score', f"{quality.get('depth_score', 0):.2f}"],
                    ['Constructiveness', f"{quality.get('constructiveness_score', 0):.2f}"],
                    ['Specificity', f"{quality.get('specificity_score', 0):.2f}"],
                ]

                quality_table = Table(quality_data, colWidths=[3*inch, 3.7*inch])
                quality_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f1f5f9')),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
                    ('PADDING', (0, 0), (-1, -1), 10),
                ]))
                story.append(quality_table)

        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
