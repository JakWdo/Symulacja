"""
Serwis generowania raportów PDF z HTML templates.
Używa WeasyPrint do konwersji HTML→PDF.
"""
import io
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML, CSS
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)


class PDFGenerator:
    """Generator raportów PDF dla person, grup fokusowych i ankiet."""

    def __init__(self):
        """Inicjalizacja generatora z Jinja2 environment."""
        # Ścieżka do templates
        self.templates_dir = Path(__file__).parent / "templates"
        self.templates_dir.mkdir(exist_ok=True)

        # Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=select_autoescape(["html", "xml"]),
        )

        # CSS dla PDF
        self.base_css = """
            @page {
                size: A4;
                margin: 2.5cm;
                @bottom-right {
                    content: "Strona " counter(page) " z " counter(pages);
                    font-size: 9pt;
                    color: #666;
                }
            }
            body {
                font-family: 'DejaVu Sans', Arial, sans-serif;
                font-size: 11pt;
                line-height: 1.6;
                color: #333;
            }
            h1 {
                color: #2563eb;
                font-size: 24pt;
                margin-bottom: 0.5em;
                border-bottom: 2px solid #2563eb;
                padding-bottom: 0.3em;
            }
            h2 {
                color: #1e40af;
                font-size: 18pt;
                margin-top: 1.5em;
                margin-bottom: 0.8em;
            }
            h3 {
                color: #1e3a8a;
                font-size: 14pt;
                margin-top: 1em;
                margin-bottom: 0.5em;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin: 1em 0;
            }
            th, td {
                padding: 8px;
                text-align: left;
                border: 1px solid #ddd;
            }
            th {
                background-color: #f3f4f6;
                font-weight: bold;
            }
            .watermark {
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%) rotate(-45deg);
                font-size: 72pt;
                color: rgba(0, 0, 0, 0.05);
                z-index: -1;
                white-space: nowrap;
            }
            .metadata {
                font-size: 9pt;
                color: #666;
                margin-bottom: 2em;
            }
        """

    async def generate_persona_pdf(
        self,
        persona_data: Dict[str, Any],
        user_tier: str = "free",
        include_reasoning: bool = True,
    ) -> bytes:
        """
        Generuje raport PDF dla persony.

        Args:
            persona_data: Dane persony (dict z polami: name, age, occupation, etc.)
            user_tier: Tier użytkownika ('free', 'pro', 'enterprise')
            include_reasoning: Czy dołączyć reasoning/uzasadnienie

        Returns:
            bytes: Zawartość pliku PDF
        """
        logger.info(f"Generowanie PDF dla persony: {persona_data.get('name', 'Unknown')}")

        # Przygotuj kontekst dla template
        context = {
            "persona": persona_data,
            "include_reasoning": include_reasoning,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "show_watermark": user_tier == "free",
        }

        # Renderuj HTML
        try:
            template = self.env.get_template("persona_report.html")
        except Exception:
            # Jeśli template nie istnieje, użyj prostego fallback
            template_html = self._get_fallback_persona_template()
            template = self.env.from_string(template_html)

        html_content = template.render(**context)

        # Konwertuj do PDF
        pdf_bytes = await self._html_to_pdf(html_content, user_tier)

        logger.info(f"PDF wygenerowany, rozmiar: {len(pdf_bytes)} bytes")
        return pdf_bytes

    async def generate_focus_group_pdf(
        self,
        focus_group_data: Dict[str, Any],
        user_tier: str = "free",
        include_discussion: bool = True,
    ) -> bytes:
        """
        Generuje raport PDF dla grupy fokusowej.

        Args:
            focus_group_data: Dane grupy (dict z polami: name, personas, discussion, summary)
            user_tier: Tier użytkownika
            include_discussion: Czy dołączyć pełną transkrypcję dyskusji

        Returns:
            bytes: Zawartość pliku PDF
        """
        logger.info(f"Generowanie PDF dla grupy fokusowej: {focus_group_data.get('name', 'Unknown')}")

        context = {
            "focus_group": focus_group_data,
            "include_discussion": include_discussion,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "show_watermark": user_tier == "free",
        }

        try:
            template = self.env.get_template("focus_group_report.html")
        except Exception:
            template_html = self._get_fallback_focus_group_template()
            template = self.env.from_string(template_html)

        html_content = template.render(**context)
        pdf_bytes = await self._html_to_pdf(html_content, user_tier)

        logger.info(f"PDF wygenerowany, rozmiar: {len(pdf_bytes)} bytes")
        return pdf_bytes

    async def generate_survey_pdf(
        self,
        survey_data: Dict[str, Any],
        user_tier: str = "free",
    ) -> bytes:
        """
        Generuje raport PDF dla ankiety z odpowiedziami.

        Args:
            survey_data: Dane ankiety (dict z polami: title, questions, responses)
            user_tier: Tier użytkownika

        Returns:
            bytes: Zawartość pliku PDF
        """
        logger.info(f"Generowanie PDF dla ankiety: {survey_data.get('title', 'Unknown')}")

        context = {
            "survey": survey_data,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "show_watermark": user_tier == "free",
        }

        try:
            template = self.env.get_template("survey_report.html")
        except Exception:
            template_html = self._get_fallback_survey_template()
            template = self.env.from_string(template_html)

        html_content = template.render(**context)
        pdf_bytes = await self._html_to_pdf(html_content, user_tier)

        logger.info(f"PDF wygenerowany, rozmiar: {len(pdf_bytes)} bytes")
        return pdf_bytes

    async def _html_to_pdf(self, html_content: str, user_tier: str) -> bytes:
        """
        Konwertuje HTML do PDF używając WeasyPrint.

        Args:
            html_content: Zawartość HTML
            user_tier: Tier użytkownika (dla watermark)

        Returns:
            bytes: PDF
        """
        # WeasyPrint jest synchroniczny, ale opakowujemy w async dla spójności
        css = CSS(string=self.base_css)
        html_obj = HTML(string=html_content)

        # Generuj PDF do BytesIO
        pdf_buffer = io.BytesIO()
        html_obj.write_pdf(pdf_buffer, stylesheets=[css])

        return pdf_buffer.getvalue()

    def _get_fallback_persona_template(self) -> str:
        """Prosty fallback template dla persony (gdy brak pliku template)."""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Raport Persony</title>
        </head>
        <body>
            {% if show_watermark %}
            <div class="watermark">SIGHT FREE TIER</div>
            {% endif %}

            <h1>Raport Persony: {{ persona.name }}</h1>

            <div class="metadata">
                Wygenerowano: {{ generated_at }}<br>
                Platform: Sight AI Focus Groups
            </div>

            <h2>Dane Podstawowe</h2>
            <table>
                <tr><th>Pole</th><th>Wartość</th></tr>
                <tr><td>Imię</td><td>{{ persona.name }}</td></tr>
                <tr><td>Wiek</td><td>{{ persona.age }}</td></tr>
                <tr><td>Zawód</td><td>{{ persona.occupation }}</td></tr>
                <tr><td>Wykształcenie</td><td>{{ persona.education }}</td></tr>
                <tr><td>Dochód</td><td>{{ persona.income }}</td></tr>
            </table>

            <h2>Profil Psychologiczny</h2>
            <p><strong>Wartości:</strong> {{ persona.values|join(', ') if persona.values else 'N/A' }}</p>
            <p><strong>Zainteresowania:</strong> {{ persona.interests|join(', ') if persona.interests else 'N/A' }}</p>

            {% if persona.needs %}
            <h2>Potrzeby</h2>
            <ul>
            {% for need in persona.needs %}
                <li><strong>{{ need.category }}:</strong> {{ need.description }} (priorytet: {{ need.priority }})</li>
            {% endfor %}
            </ul>
            {% endif %}

            {% if include_reasoning and persona.reasoning %}
            <h2>Uzasadnienie Generacji</h2>
            <p>{{ persona.reasoning.orchestration_brief }}</p>

            {% if persona.reasoning.graph_insights %}
            <h3>Insighty z Graph RAG</h3>
            <p>{{ persona.reasoning.graph_insights }}</p>
            {% endif %}
            {% endif %}
        </body>
        </html>
        """

    def _get_fallback_focus_group_template(self) -> str:
        """Prosty fallback template dla grupy fokusowej."""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Raport Grupy Fokusowej</title>
        </head>
        <body>
            {% if show_watermark %}
            <div class="watermark">SIGHT FREE TIER</div>
            {% endif %}

            <h1>Raport Grupy Fokusowej: {{ focus_group.name }}</h1>

            <div class="metadata">
                Wygenerowano: {{ generated_at }}<br>
                Platform: Sight AI Focus Groups
            </div>

            <h2>Informacje Podstawowe</h2>
            <p><strong>Nazwa:</strong> {{ focus_group.name }}</p>
            <p><strong>Liczba uczestników:</strong> {{ focus_group.personas|length if focus_group.personas else 0 }}</p>

            {% if focus_group.summary %}
            <h2>Podsumowanie</h2>
            <p>{{ focus_group.summary.main_insights }}</p>

            {% if focus_group.summary.key_themes %}
            <h3>Kluczowe Tematy</h3>
            <ul>
            {% for theme in focus_group.summary.key_themes %}
                <li>{{ theme }}</li>
            {% endfor %}
            </ul>
            {% endif %}
            {% endif %}

            {% if include_discussion and focus_group.discussion %}
            <h2>Transkrypcja Dyskusji</h2>
            {% for message in focus_group.discussion %}
            <p><strong>{{ message.persona_name }}:</strong> {{ message.content }}</p>
            {% endfor %}
            {% endif %}
        </body>
        </html>
        """

    def _get_fallback_survey_template(self) -> str:
        """Prosty fallback template dla ankiety."""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Raport Ankiety</title>
        </head>
        <body>
            {% if show_watermark %}
            <div class="watermark">SIGHT FREE TIER</div>
            {% endif %}

            <h1>Raport Ankiety: {{ survey.title }}</h1>

            <div class="metadata">
                Wygenerowano: {{ generated_at }}<br>
                Platform: Sight AI Focus Groups
            </div>

            <h2>Pytania i Odpowiedzi</h2>
            {% for question in survey.questions %}
            <h3>Pytanie {{ loop.index }}: {{ question.text }}</h3>
            {% if survey.responses %}
            <ul>
            {% for response in survey.responses %}
                {% if response.question_id == question.id %}
                <li><strong>{{ response.persona_name }}:</strong> {{ response.answer }}</li>
                {% endif %}
            {% endfor %}
            </ul>
            {% endif %}
            {% endfor %}
        </body>
        </html>
        """
