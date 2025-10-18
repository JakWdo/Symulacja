#!/usr/bin/env python3
"""
Backfill script - Generate needs_and_pains for existing personas with NULL needs.

Usage:
    # Dry run (show what would be done)
    python scripts/backfill_persona_needs.py --dry-run

    # Backfill all personas (limit 10)
    python scripts/backfill_persona_needs.py --limit 10

    # Backfill specific project
    python scripts/backfill_persona_needs.py --project-id <UUID>

    # Backfill all personas (no limit, use with caution!)
    python scripts/backfill_persona_needs.py --limit -1

Performance:
    - ~2-3s per persona (LLM generation)
    - For 100 personas: ~3-5 minutes
    - Uses parallel processing (concurrency=5) for speed

Example output:
    🔍 Found 15 personas with NULL needs_and_pains
    ✅ Generated needs for persona 1/15 (Anna Kowalska)
    ✅ Generated needs for persona 2/15 (Piotr Nowak)
    ...
    ✅ Backfill complete: 15/15 personas updated
"""

import asyncio
import argparse
import logging
import sys
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

# Add parent directory to path for imports
sys.path.insert(0, str(__file__ + "/../../"))

from app.db import AsyncSessionLocal
from app.models import Persona
from app.services.personas.persona_needs_service import PersonaNeedsService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def count_null_needs(db: AsyncSession, project_id: Optional[UUID] = None) -> int:
    """Count personas with NULL needs_and_pains."""
    query = select(func.count(Persona.id)).where(
        Persona.is_active == True,
        Persona.deleted_at.is_(None),
        Persona.needs_and_pains.is_(None),
    )
    if project_id:
        query = query.where(Persona.project_id == project_id)

    result = await db.execute(query)
    return result.scalar() or 0


async def fetch_personas_without_needs(
    db: AsyncSession,
    limit: int = 10,
    project_id: Optional[UUID] = None,
) -> List[Persona]:
    """Fetch personas with NULL needs_and_pains."""
    query = select(Persona).where(
        Persona.is_active == True,
        Persona.deleted_at.is_(None),
        Persona.needs_and_pains.is_(None),
    )

    if project_id:
        query = query.where(Persona.project_id == project_id)

    if limit > 0:
        query = query.limit(limit)

    result = await db.execute(query)
    return list(result.scalars().all())


async def generate_needs_for_persona(
    persona: Persona,
    db: AsyncSession,
    dry_run: bool = False,
) -> bool:
    """Generate needs_and_pains for a single persona."""
    try:
        # Extract RAG context from persona
        rag_context = None
        if persona.rag_context_details:
            details = persona.rag_context_details
            orch = details.get("orchestration_reasoning") or {}
            rag_context = (
                orch.get("segment_social_context")
                or orch.get("overall_context")
                or details.get("graph_context")
            )

        logger.info(
            f"{'[DRY RUN] ' if dry_run else ''}Generating needs for persona: "
            f"{persona.full_name} (ID: {persona.id})"
        )

        if dry_run:
            # Dry run - don't actually generate
            return True

        # Generate needs with RAG context
        needs_service = PersonaNeedsService(db)
        needs_data = await needs_service.generate_needs_analysis(
            persona,
            rag_context=rag_context,
        )

        # Update persona
        persona.needs_and_pains = needs_data
        await db.commit()

        logger.info(
            f"✅ Generated needs for {persona.full_name}: "
            f"{len(needs_data.get('jobs_to_be_done', []))} jobs, "
            f"{len(needs_data.get('pain_points', []))} pains"
        )

        return True

    except Exception as e:
        logger.error(
            f"❌ Failed to generate needs for {persona.full_name} (ID: {persona.id}): {e}",
            exc_info=True,
        )
        await db.rollback()
        return False


async def backfill_persona_needs(
    limit: int = 10,
    project_id: Optional[UUID] = None,
    dry_run: bool = False,
    concurrency: int = 5,
):
    """
    Backfill needs_and_pains for personas with NULL needs.

    Args:
        limit: Max number of personas to process (-1 for all)
        project_id: Optional project UUID to filter
        dry_run: If True, only show what would be done
        concurrency: Number of parallel LLM calls (default 5)
    """
    async with AsyncSessionLocal() as db:
        # Count total personas needing backfill
        total_count = await count_null_needs(db, project_id)

        if total_count == 0:
            logger.info("✅ All personas already have needs_and_pains generated!")
            return

        logger.info(
            f"🔍 Found {total_count} personas with NULL needs_and_pains"
        )

        if dry_run:
            logger.info("[DRY RUN MODE] - No changes will be made")

        # Fetch personas to process
        personas = await fetch_personas_without_needs(db, limit, project_id)

        if not personas:
            logger.info("No personas to process")
            return

        logger.info(
            f"📋 Processing {len(personas)} personas "
            f"(limit: {limit if limit > 0 else 'all'})"
        )

        # Process personas with controlled concurrency
        semaphore = asyncio.Semaphore(concurrency)
        success_count = 0
        fail_count = 0

        async def process_with_semaphore(persona: Persona, idx: int):
            async with semaphore:
                logger.info(f"Processing persona {idx+1}/{len(personas)}...")
                async with AsyncSessionLocal() as session:
                    # Refresh persona in new session
                    result = await session.execute(
                        select(Persona).where(Persona.id == persona.id)
                    )
                    fresh_persona = result.scalars().first()
                    if not fresh_persona:
                        logger.warning(f"Persona {persona.id} not found - skipping")
                        return False

                    return await generate_needs_for_persona(
                        fresh_persona,
                        session,
                        dry_run=dry_run,
                    )

        # Process all personas in parallel (with concurrency limit)
        tasks = [
            asyncio.create_task(process_with_semaphore(persona, i))
            for i, persona in enumerate(personas)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Count results
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Task failed with exception: {result}")
                fail_count += 1
            elif result:
                success_count += 1
            else:
                fail_count += 1

        # Summary
        logger.info("\n" + "=" * 60)
        logger.info(
            f"{'[DRY RUN] ' if dry_run else ''}Backfill complete: "
            f"{success_count}/{len(personas)} personas updated"
        )
        if fail_count > 0:
            logger.warning(f"⚠️  {fail_count} personas failed")

        remaining = total_count - len(personas)
        if remaining > 0:
            logger.info(
                f"ℹ️  {remaining} personas remaining "
                f"(increase --limit to process more)"
            )
        logger.info("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Backfill needs_and_pains for personas with NULL needs"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Max personas to process (-1 for all). Default: 10",
    )
    parser.add_argument(
        "--project-id",
        type=str,
        help="Optional: Only process personas from specific project (UUID)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run - show what would be done without making changes",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=5,
        help="Number of parallel LLM calls. Default: 5",
    )

    args = parser.parse_args()

    project_id = None
    if args.project_id:
        try:
            project_id = UUID(args.project_id)
        except ValueError:
            logger.error(f"Invalid project UUID: {args.project_id}")
            sys.exit(1)

    # Run backfill
    asyncio.run(
        backfill_persona_needs(
            limit=args.limit,
            project_id=project_id,
            dry_run=args.dry_run,
            concurrency=args.concurrency,
        )
    )


if __name__ == "__main__":
    main()
