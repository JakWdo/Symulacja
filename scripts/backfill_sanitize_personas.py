#!/usr/bin/env python3
"""
Backfill script do sanityzacji pól tekstowych w tabeli personas

Problem: LLM generuje pola tekstowe z nadmiarowymi znakami nowej linii (\\n\\n),
         co powoduje błędy wyświetlania w UI (np. "Zawód\\n\\nJuż" zamiast "Zawód Już")

Rozwiązanie: Sanityzuje wszystkie pola tekstowe w istniejących personach:
- occupation, full_name, location, headline, persona_title
- communication_style, decision_making_style
- background_story (zachowując podział na akapity)

Funkcjonalności:
- --dry-run mode: Pokazuje co zostanie zmienione bez wykonywania update
- Batch processing: Przetwarza persony w paczkach po 100
- Detailed logging: Pokazuje przed/po dla każdej zmiany
- Progress tracking: Pokazuje postęp przetwarzania

Uruchomienie:
    # Dry-run (bezpieczny podgląd)
    python scripts/backfill_sanitize_personas.py --dry-run

    # Właściwy backfill
    python scripts/backfill_sanitize_personas.py

Wymaga:
    - Uruchomiona baza PostgreSQL (docker-compose up postgres)
    - Poprawna DATABASE_URL w .env
"""

import argparse
import asyncio
import re
import sys
import logging
from pathlib import Path
from typing import List, Tuple
from datetime import datetime

# Dodaj root directory do path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.models.persona import Persona

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def sanitize_text(text: str, preserve_paragraphs: bool = False) -> str:
    """
    Sanityzuj tekst wygenerowany przez LLM, usuwając nadmierne białe znaki

    Metoda ta usuwa:
    - Nadmiarowe znaki nowej linii (\\n\\n -> pojedyncza spacja lub akapit)
    - Nadmiarowe spacje (wiele spacji -> jedna spacja)
    - Leading/trailing whitespace

    Args:
        text: Tekst do sanityzacji
        preserve_paragraphs: Czy zachować podział na akapity (dla background_story)
                            Jeśli True, zachowuje podział na paragrafy (\\n\\n)
                            Jeśli False, zamienia wszystkie \\n na spacje

    Returns:
        Zsanityzowany tekst bez nadmiarowych białych znaków

    Przykłady:
        >>> sanitize_text("Zawód\\n\\nJuż")
        "Zawód Już"
        >>> sanitize_text("Tekst  z   wieloma    spacjami")
        "Tekst z wieloma spacjami"
        >>> sanitize_text("Para 1\\n\\nPara 2", preserve_paragraphs=True)
        "Para 1\\n\\nPara 2"
    """
    if not text:
        return text

    if preserve_paragraphs:
        # Dla background_story - zachowaj podział na akapity ale znormalizuj każdy akapit
        paragraphs = text.split('\n')
        paragraphs = [re.sub(r'\s+', ' ', p).strip() for p in paragraphs if p.strip()]
        return '\n\n'.join(paragraphs)
    else:
        # Dla pól jednoliniowych - usuń wszystkie \\n i znormalizuj spacje
        return re.sub(r'\s+', ' ', text).strip()


async def count_affected_personas(session: AsyncSession) -> Tuple[int, int]:
    """
    Zlicz ile person ma buggy text fields (z \\n lub nadmiarowymi spacjami)

    Args:
        session: AsyncSession do bazy danych

    Returns:
        Tuple (total_personas, affected_personas)
    """
    # Zlicz wszystkie persony
    total_result = await session.execute(select(func.count(Persona.id)))
    total_count = total_result.scalar()

    # Zlicz persony z \\n w occupation lub innych polach tekstowych
    # Używamy OR dla wielu pól
    affected_result = await session.execute(
        select(func.count(Persona.id)).where(
            (Persona.occupation.like('%\\n%')) |
            (Persona.full_name.like('%\\n%')) |
            (Persona.location.like('%\\n%')) |
            (Persona.headline.like('%\\n%')) |
            (Persona.persona_title.like('%\\n%')) |
            (Persona.background_story.like('%\\n%'))
        )
    )
    affected_count = affected_result.scalar()

    return total_count, affected_count


async def fetch_personas_batch(
    session: AsyncSession, offset: int, batch_size: int
) -> List[Persona]:
    """
    Pobierz paczkę person z bazy (dla batch processing)

    Args:
        session: AsyncSession do bazy danych
        offset: Offset dla paginacji
        batch_size: Rozmiar paczki

    Returns:
        Lista obiektów Persona
    """
    result = await session.execute(
        select(Persona)
        .order_by(Persona.created_at)
        .offset(offset)
        .limit(batch_size)
    )
    return list(result.scalars().all())


def should_sanitize_persona(persona: Persona) -> bool:
    """
    Sprawdź czy persona wymaga sanityzacji (ma \\n lub nadmiarowe spacje)

    Args:
        persona: Obiekt Persona do sprawdzenia

    Returns:
        True jeśli wymaga sanityzacji, False w przeciwnym razie
    """
    text_fields = [
        persona.occupation,
        persona.full_name,
        persona.location,
        persona.headline,
        persona.persona_title,
        persona.background_story,
    ]

    for field in text_fields:
        if field and ('\n' in field or '  ' in field):
            return True

    return False


def sanitize_persona(persona: Persona, dry_run: bool = False) -> bool:
    """
    Sanityzuj pola tekstowe persony

    Args:
        persona: Obiekt Persona do sanityzacji
        dry_run: Jeśli True, tylko loguj zmiany bez modyfikacji

    Returns:
        True jeśli dokonano zmian (lub dry-run wykrył zmiany), False w przeciwnym razie
    """
    changed = False

    # Pola jednoliniowe (usuń wszystkie \\n)
    single_line_fields = [
        'occupation', 'full_name', 'location', 'headline',
        'persona_title', 'communication_style', 'decision_making_style'
    ]

    for field_name in single_line_fields:
        original_value = getattr(persona, field_name, None)
        if original_value and isinstance(original_value, str):
            sanitized_value = sanitize_text(original_value, preserve_paragraphs=False)

            if original_value != sanitized_value:
                changed = True
                logger.info(
                    f"  [{field_name}] BEFORE: {repr(original_value[:100])}"
                )
                logger.info(
                    f"  [{field_name}] AFTER:  {repr(sanitized_value[:100])}"
                )

                if not dry_run:
                    setattr(persona, field_name, sanitized_value)

    # background_story (zachowaj podział na akapity)
    if persona.background_story and isinstance(persona.background_story, str):
        original_story = persona.background_story
        sanitized_story = sanitize_text(original_story, preserve_paragraphs=True)

        if original_story != sanitized_story:
            changed = True
            logger.info(
                f"  [background_story] BEFORE: {repr(original_story[:150])}"
            )
            logger.info(
                f"  [background_story] AFTER:  {repr(sanitized_story[:150])}"
            )

            if not dry_run:
                persona.background_story = sanitized_story

    return changed


async def sanitize_personas(dry_run: bool = False, batch_size: int = 100):
    """
    Główna funkcja sanityzacji person

    Args:
        dry_run: Jeśli True, tylko pokazuje co zostanie zmienione
        batch_size: Rozmiar paczki dla batch processing
    """
    start_time = datetime.now()
    logger.info("=" * 70)
    logger.info("PERSONA TEXT SANITIZATION BACKFILL")
    logger.info("=" * 70)
    logger.info(f"Mode: {'DRY-RUN (no changes)' if dry_run else 'LIVE (will update database)'}")
    logger.info(f"Batch size: {batch_size}")
    logger.info("")

    async with AsyncSessionLocal() as session:
        # Krok 1: Zlicz affected personas
        logger.info("📊 Step 1: Counting personas...")
        total_count, affected_count = await count_affected_personas(session)

        logger.info(f"Total personas in database: {total_count}")
        logger.info(f"Personas with \\n in text fields: {affected_count}")

        if affected_count == 0:
            logger.info("✅ No personas need sanitization. Exiting.")
            return

        logger.info("")
        logger.info(f"🔧 Step 2: Sanitizing {total_count} personas in batches of {batch_size}...")
        logger.info("")

        # Krok 2: Batch processing
        offset = 0
        total_processed = 0
        total_changed = 0

        while True:
            # Pobierz paczkę person
            personas = await fetch_personas_batch(session, offset, batch_size)

            if not personas:
                break  # Koniec danych

            logger.info(f"Processing batch {offset // batch_size + 1} (offset={offset}, count={len(personas)})...")

            # Sanityzuj każdą personę w paczce
            batch_changed = 0
            for persona in personas:
                if should_sanitize_persona(persona):
                    logger.info(f"  Sanitizing Persona {persona.id} ({persona.full_name})...")
                    if sanitize_persona(persona, dry_run=dry_run):
                        batch_changed += 1

            # Commit zmian (jeśli nie dry-run)
            if not dry_run and batch_changed > 0:
                try:
                    await session.commit()
                    logger.info(f"✅ Committed {batch_changed} changes for batch {offset // batch_size + 1}")
                except Exception as e:
                    await session.rollback()
                    logger.error(f"❌ ERROR committing batch {offset // batch_size + 1}: {e}")
                    raise

            total_processed += len(personas)
            total_changed += batch_changed
            offset += batch_size

            # Progress update
            progress_pct = (total_processed / total_count) * 100 if total_count > 0 else 0
            logger.info(f"Progress: {total_processed}/{total_count} ({progress_pct:.1f}%) | Changed: {total_changed}")
            logger.info("")

    # Podsumowanie
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    logger.info("=" * 70)
    logger.info("SUMMARY")
    logger.info("=" * 70)
    logger.info(f"Total personas processed: {total_processed}")
    logger.info(f"Personas changed: {total_changed}")
    logger.info(f"Duration: {duration:.2f} seconds")
    logger.info("")

    if dry_run:
        logger.info("🔍 DRY-RUN completed. No changes were made to the database.")
        logger.info("Run without --dry-run to apply changes.")
    else:
        logger.info("✅ Sanitization completed successfully!")
        logger.info(f"{total_changed} personas updated in database.")


async def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Sanitize persona text fields (remove excess \\n and whitespace)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without modifying the database"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Number of personas to process per batch (default: 100)"
    )

    args = parser.parse_args()

    try:
        await sanitize_personas(dry_run=args.dry_run, batch_size=args.batch_size)
    except Exception as e:
        logger.error(f"❌ FATAL ERROR: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
