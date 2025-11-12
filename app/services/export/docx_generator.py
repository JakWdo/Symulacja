"""
Serwis generowania raportów DOCX (Microsoft Word).
Używa python-docx do tworzenia dokumentów .docx.
"""
import io
import logging
from datetime import datetime
from typing import Dict, Any, List

from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT

logger = logging.getLogger(__name__)


class DOCXGenerator:
    """Generator raportów DOCX dla person, grup fokusowych i ankiet."""

    def __init__(self):
        """Inicjalizacja generatora."""
        pass

    async def generate_persona_docx(
        self,
        persona_data: Dict[str, Any],
        user_tier: str = "free",
        include_reasoning: bool = True,
    ) -> bytes:
        """
        Generuje raport DOCX dla persony.

        Args:
            persona_data: Dane persony
            user_tier: Tier użytkownika ('free', 'pro', 'enterprise')
            include_reasoning: Czy dołączyć reasoning

        Returns:
            bytes: Zawartość pliku DOCX
        """
        logger.info(f"Generowanie DOCX dla persony: {persona_data.get('name', 'Unknown')}")

        doc = Document()

        # Watermark dla free tier
        if user_tier == "free":
            self._add_watermark(doc, "SIGHT FREE TIER")

        # Tytuł
        title = doc.add_heading(f"Raport Persony: {persona_data.get('name', 'Unknown')}", level=1)
        title.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

        # Metadata
        metadata = doc.add_paragraph()
        metadata.add_run(f"Wygenerowano: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n").italic = True
        metadata.add_run("Platform: Sight AI Focus Groups").italic = True

        # Dane podstawowe
        doc.add_heading("Dane Podstawowe", level=2)
        table = doc.add_table(rows=6, cols=2)
        table.style = "Light Grid Accent 1"

        fields = [
            ("Imię", persona_data.get("name", "N/A")),
            ("Wiek", str(persona_data.get("age", "N/A"))),
            ("Zawód", persona_data.get("occupation", "N/A")),
            ("Wykształcenie", persona_data.get("education", "N/A")),
            ("Dochód", persona_data.get("income", "N/A")),
            ("Lokalizacja", persona_data.get("location", "N/A")),
        ]

        for i, (label, value) in enumerate(fields):
            table.rows[i].cells[0].text = label
            table.rows[i].cells[1].text = str(value)

        # Profil psychologiczny
        doc.add_heading("Profil Psychologiczny", level=2)

        if persona_data.get("values"):
            p = doc.add_paragraph()
            p.add_run("Wartości: ").bold = True
            p.add_run(", ".join(persona_data["values"]))

        if persona_data.get("interests"):
            p = doc.add_paragraph()
            p.add_run("Zainteresowania: ").bold = True
            p.add_run(", ".join(persona_data["interests"]))

        # Potrzeby
        if persona_data.get("needs"):
            doc.add_heading("Potrzeby", level=2)
            for need in persona_data["needs"]:
                p = doc.add_paragraph(style="List Bullet")
                p.add_run(f"{need.get('category', 'N/A')}: ").bold = True
                p.add_run(f"{need.get('description', 'N/A')} ")
                p.add_run(f"(priorytet: {need.get('priority', 'N/A')})").italic = True

        # Reasoning (jeśli include_reasoning)
        if include_reasoning and persona_data.get("reasoning"):
            doc.add_heading("Uzasadnienie Generacji", level=2)
            reasoning = persona_data["reasoning"]

            if reasoning.get("orchestration_brief"):
                doc.add_paragraph(reasoning["orchestration_brief"])

            if reasoning.get("graph_insights"):
                doc.add_heading("Insighty z Graph RAG", level=3)
                doc.add_paragraph(reasoning["graph_insights"])

        # Konwertuj do bytes
        docx_buffer = io.BytesIO()
        doc.save(docx_buffer)
        docx_bytes = docx_buffer.getvalue()

        logger.info(f"DOCX wygenerowany, rozmiar: {len(docx_bytes)} bytes")
        return docx_bytes

    async def generate_focus_group_docx(
        self,
        focus_group_data: Dict[str, Any],
        user_tier: str = "free",
        include_discussion: bool = True,
    ) -> bytes:
        """
        Generuje raport DOCX dla grupy fokusowej.

        Args:
            focus_group_data: Dane grupy fokusowej
            user_tier: Tier użytkownika
            include_discussion: Czy dołączyć transkrypcję

        Returns:
            bytes: Zawartość pliku DOCX
        """
        logger.info(f"Generowanie DOCX dla grupy fokusowej: {focus_group_data.get('name', 'Unknown')}")

        doc = Document()

        if user_tier == "free":
            self._add_watermark(doc, "SIGHT FREE TIER")

        # Tytuł
        title = doc.add_heading(f"Raport Grupy Fokusowej: {focus_group_data.get('name', 'Unknown')}", level=1)
        title.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

        # Metadata
        metadata = doc.add_paragraph()
        metadata.add_run(f"Wygenerowano: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n").italic = True
        metadata.add_run("Platform: Sight AI Focus Groups").italic = True

        # Informacje podstawowe
        doc.add_heading("Informacje Podstawowe", level=2)
        p = doc.add_paragraph()
        p.add_run("Nazwa: ").bold = True
        p.add_run(focus_group_data.get("name", "N/A"))

        personas_count = len(focus_group_data.get("personas", []))
        p = doc.add_paragraph()
        p.add_run("Liczba uczestników: ").bold = True
        p.add_run(str(personas_count))

        # Podsumowanie
        if focus_group_data.get("summary"):
            doc.add_heading("Podsumowanie", level=2)
            summary = focus_group_data["summary"]

            if summary.get("main_insights"):
                doc.add_paragraph(summary["main_insights"])

            if summary.get("key_themes"):
                doc.add_heading("Kluczowe Tematy", level=3)
                for theme in summary["key_themes"]:
                    doc.add_paragraph(theme, style="List Bullet")

        # Transkrypcja dyskusji
        if include_discussion and focus_group_data.get("discussion"):
            doc.add_heading("Transkrypcja Dyskusji", level=2)

            for message in focus_group_data["discussion"]:
                p = doc.add_paragraph()
                p.add_run(f"{message.get('persona_name', 'Unknown')}: ").bold = True
                p.add_run(message.get("content", ""))

        # Konwertuj do bytes
        docx_buffer = io.BytesIO()
        doc.save(docx_buffer)
        docx_bytes = docx_buffer.getvalue()

        logger.info(f"DOCX wygenerowany, rozmiar: {len(docx_bytes)} bytes")
        return docx_bytes

    async def generate_survey_docx(
        self,
        survey_data: Dict[str, Any],
        user_tier: str = "free",
    ) -> bytes:
        """
        Generuje raport DOCX dla ankiety.

        Args:
            survey_data: Dane ankiety z odpowiedziami
            user_tier: Tier użytkownika

        Returns:
            bytes: Zawartość pliku DOCX
        """
        logger.info(f"Generowanie DOCX dla ankiety: {survey_data.get('title', 'Unknown')}")

        doc = Document()

        if user_tier == "free":
            self._add_watermark(doc, "SIGHT FREE TIER")

        # Tytuł
        title = doc.add_heading(f"Raport Ankiety: {survey_data.get('title', 'Unknown')}", level=1)
        title.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

        # Metadata
        metadata = doc.add_paragraph()
        metadata.add_run(f"Wygenerowano: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n").italic = True
        metadata.add_run("Platform: Sight AI Focus Groups").italic = True

        # Pytania i odpowiedzi
        doc.add_heading("Pytania i Odpowiedzi", level=2)

        for i, question in enumerate(survey_data.get("questions", []), 1):
            # Pytanie
            doc.add_heading(f"Pytanie {i}: {question.get('text', 'N/A')}", level=3)

            # Odpowiedzi
            if survey_data.get("responses"):
                for response in survey_data["responses"]:
                    if response.get("question_id") == question.get("id"):
                        p = doc.add_paragraph(style="List Bullet")
                        p.add_run(f"{response.get('persona_name', 'Unknown')}: ").bold = True
                        p.add_run(response.get("answer", ""))

        # Konwertuj do bytes
        docx_buffer = io.BytesIO()
        doc.save(docx_buffer)
        docx_bytes = docx_buffer.getvalue()

        logger.info(f"DOCX wygenerowany, rozmiar: {len(docx_bytes)} bytes")
        return docx_bytes

    def _add_watermark(self, doc: Document, text: str):
        """
        Dodaje watermark do dokumentu DOCX.

        Note: python-docx nie ma natywnej obsługi watermarks,
        więc dodajemy jako header z szarym tekstem.
        """
        section = doc.sections[0]
        header = section.header
        watermark_para = header.paragraphs[0] if header.paragraphs else header.add_paragraph()
        watermark_para.text = text
        watermark_para.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

        # Stylizacja watermark
        run = watermark_para.runs[0]
        run.font.size = Pt(48)
        run.font.color.rgb = RGBColor(200, 200, 200)  # Szary
        run.font.bold = True
