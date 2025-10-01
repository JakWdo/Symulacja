"""Service for generating analysis reports in various formats."""

import io
from datetime import datetime
from typing import Any, Dict, List
from uuid import UUID

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import FocusGroup, Project


class ReportGenerator:
    """Generate reports in PDF and CSV formats."""

    async def generate_pdf_report(
        self,
        db: AsyncSession,
        focus_group_id: UUID,
        analysis_data: Dict[str, Any]
    ) -> bytes:
        """Generate a PDF report for focus group analysis."""

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
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = []

        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1e293b'),
            spaceAfter=30,
            alignment=TA_CENTER,
        )
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#334155'),
            spaceAfter=12,
        )
        normal_style = styles['Normal']

        # Title
        story.append(Paragraph("Focus Group Analysis Report", title_style))
        story.append(Spacer(1, 0.2 * inch))

        # Project & Focus Group Info
        story.append(Paragraph("Project Information", heading_style))
        project_data = [
            ['Project:', project.name if project else 'Unknown'],
            ['Focus Group:', focus_group.name],
            ['Description:', focus_group.description or 'N/A'],
            ['Mode:', focus_group.mode],
            ['Status:', focus_group.status],
            ['Generated:', datetime.now().strftime('%Y-%m-%d %H:%M')],
        ]
        t = Table(project_data, colWidths=[2*inch, 4*inch])
        t.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#475569')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.3 * inch))

        # Analysis Results
        story.append(Paragraph("Analysis Results", heading_style))

        # Polarization Score
        polarization_score = analysis_data.get('overall_polarization', 0)
        score_data = [
            ['Overall Polarization Score:', f"{polarization_score:.2%}"],
        ]
        t = Table(score_data, colWidths=[3*inch, 2*inch])
        t.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 14),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#0f172a')),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f1f5f9')),
            ('PADDING', (0, 0), (-1, -1), 12),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.2 * inch))

        # Opinion Clusters
        if 'clusters' in analysis_data:
            story.append(Paragraph("Opinion Clusters", heading_style))

            cluster_data = [['Cluster', 'Size', 'Avg Sentiment', 'Representative Response']]
            for cluster in analysis_data['clusters']:
                cluster_data.append([
                    f"#{cluster.get('cluster_id', 0) + 1}",
                    str(cluster.get('size', 0)),
                    f"{cluster.get('avg_sentiment', 0):.2f}",
                    cluster.get('representative_response', '')[:80] + '...'
                        if len(cluster.get('representative_response', '')) > 80
                        else cluster.get('representative_response', '')
                ])

            t = Table(cluster_data, colWidths=[0.8*inch, 0.8*inch, 1.2*inch, 3.5*inch])
            t.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#334155')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('ALIGN', (0, 1), (2, -1), 'CENTER'),
                ('ALIGN', (3, 1), (3, -1), 'LEFT'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('PADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(t)
            story.append(Spacer(1, 0.3 * inch))

        # Question-level Analysis
        if 'questions' in analysis_data:
            story.append(Paragraph("Question-Level Polarization", heading_style))

            question_data = [['Question', 'Polarization', 'Clusters', 'Responses']]
            for q in analysis_data['questions'][:10]:  # Limit to first 10
                question_text = q.get('question', '')[:60] + '...' if len(q.get('question', '')) > 60 else q.get('question', '')
                question_data.append([
                    question_text,
                    f"{q.get('polarization_score', 0):.1%}",
                    str(q.get('num_clusters', 0)),
                    str(q.get('num_responses', 0)),
                ])

            t = Table(question_data, colWidths=[3.5*inch, 1.2*inch, 1*inch, 1*inch])
            t.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#334155')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('PADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(t)

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
        """Generate a CSV report for focus group analysis."""

        # Prepare data for CSV
        rows = []

        # Add overall metrics
        rows.append(['Metric', 'Value'])
        rows.append(['Overall Polarization', f"{analysis_data.get('overall_polarization', 0):.4f}"])
        rows.append([''])

        # Add cluster data
        if 'clusters' in analysis_data:
            rows.append(['Cluster Analysis'])
            rows.append(['Cluster ID', 'Size', 'Avg Sentiment', 'Representative Response'])
            for cluster in analysis_data['clusters']:
                rows.append([
                    cluster.get('cluster_id', 0) + 1,
                    cluster.get('size', 0),
                    f"{cluster.get('avg_sentiment', 0):.4f}",
                    cluster.get('representative_response', '')
                ])
            rows.append([''])

        # Add question-level data
        if 'questions' in analysis_data:
            rows.append(['Question-Level Analysis'])
            rows.append(['Question', 'Polarization Score', 'Num Clusters', 'Num Responses'])
            for q in analysis_data['questions']:
                rows.append([
                    q.get('question', ''),
                    f"{q.get('polarization_score', 0):.4f}",
                    q.get('num_clusters', 0),
                    q.get('num_responses', 0),
                ])

        # Convert to DataFrame and then to CSV
        df = pd.DataFrame(rows)
        buffer = io.StringIO()
        df.to_csv(buffer, index=False, header=False)
        return buffer.getvalue().encode('utf-8')
