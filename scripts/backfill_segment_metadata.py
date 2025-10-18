#!/usr/bin/env python3
"""
Backfill script ujednolicający metadane segmentów person

Zakres:
- Synchronizuje rag_context_details z aktualnym persona.segment_name / segment_id
- Uzupełnia opis i kontekst segmentu bazując na helperach z PersonaDetailsService

Użycie:
    # Podgląd zmian
    python scripts/backfill_segment_metadata.py --dry-run

    # Właściwy backfill
    python scripts/backfill_segment_metadata.py
"""

import argparse
import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import List

from sqlalchemy import select

# Dodaj root repo do sys.path (uruchamiamy ze scripts/)
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db.session import AsyncSessionLocal  # noqa: E402
from app.models.persona import Persona  # noqa: E402
from app.services.persona_details_service import _ensure_segment_metadata  # noqa: E402

logger = logging.getLogger(__name__)


async def fetch_personas(session, offset: int, limit: int) -> List[Persona]:
    result = await session.execute(
        select(Persona)
        .order_by(Persona.created_at)
        .offset(offset)
        .limit(limit)
    )
    return result.scalars().all()


async def backfill_metadata(dry_run: bool, batch_size: int) -> None:
    start = datetime.utcnow()
    total_processed = 0
    total_updated = 0

    async with AsyncSessionLocal() as session:
        offset = 0
        while True:
            personas = await fetch_personas(session, offset, batch_size)
            if not personas:
                break

            logger.info("Processing batch offset=%s count=%s", offset, len(personas))
            batch_updates = 0

            for persona in personas:
                details = _ensure_segment_metadata(persona)
                if details != persona.rag_context_details:
                    batch_updates += 1
                    total_updated += 1
                    logger.info(
                        "Persona %s (%s) metadata refreshed -> segment_name=%s",
                        persona.id,
                        persona.full_name,
                        details.get("segment_name") if isinstance(details, dict) else None,
                    )
                    if not dry_run:
                        persona.rag_context_details = details
                        persona.updated_at = datetime.utcnow()

            if not dry_run and batch_updates > 0:
                await session.commit()
            elif dry_run:
                await session.rollback()

            total_processed += len(personas)
            offset += batch_size

    duration = (datetime.utcnow() - start).total_seconds()
    logger.info("Processed %s personas in %.2fs (updated=%s)", total_processed, duration, total_updated)
    if dry_run:
        logger.info("DRY RUN: no changes were committed.")


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    parser = argparse.ArgumentParser(description="Backfill persona segment metadata.")
    parser.add_argument("--dry-run", action="store_true", help="Only preview changes without committing.")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size (default: 100).")
    args = parser.parse_args()
    await backfill_metadata(dry_run=args.dry_run, batch_size=args.batch_size)


if __name__ == "__main__":
    asyncio.run(main())
