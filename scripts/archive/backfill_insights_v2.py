#!/usr/bin/env python
"""
Backfill Script - Re-klasyfikacja i re-ekstrakcja koncepcji dla istniejących insightów

Ten skrypt ponownie przetwarza wszystkie InsightEvidence w bazie danych, używając:
1. Nowej klasyfikacji typu insight (z polskimi słowami kluczowymi)
2. Nowej ekstrakcji koncepcji (z polskimi stopwords i n-gramami)

Uruchomienie:
    # Dry run (tylko wyświetl zmiany, nie zapisuj)
    python scripts/archive/backfill_insights_v2.py --dry-run

    # Produkcyjny run (zapisz zmiany)
    python scripts/archive/backfill_insights_v2.py

    # Z limitem (dla testów)
    python scripts/archive/backfill_insights_v2.py --limit 100 --dry-run
"""

import argparse
import asyncio
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict

# Add project root to path when uruchamiany jako skrypt
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from tqdm.asyncio import tqdm

from app.core.config import get_settings
from app.models import InsightEvidence
from app.services.focus_groups.discussion_summarizer import DiscussionSummarizer


settings = get_settings()


class InsightBackfiller:
    """
    Backfiller dla re-klasyfikacji i re-ekstrakcji koncepcji insightów.
    """

    def __init__(self, dry_run: bool = False, batch_size: int = 500):
        self.dry_run = dry_run
        self.batch_size = batch_size

        # Statistics
        self.stats = {
            "total": 0,
            "processed": 0,
            "errors": 0,
            "type_changes": Counter(),
            "concepts_improved": 0,
        }

        # Create async engine for database
        self.engine = create_async_engine(
            settings.DATABASE_URL,
            echo=False,
            pool_size=5,
            max_overflow=10,
        )

        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

        # Create summarizer instance to access classification/extraction methods
        self.summarizer = DiscussionSummarizer()

    async def count_total_insights(self) -> int:
        """Count total number of InsightEvidence records."""
        async with self.async_session() as session:
            result = await session.execute(
                select(func.count(InsightEvidence.id))
            )
            return result.scalar() or 0

    async def fetch_insights_batch(
        self, offset: int, limit: int
    ) -> list[InsightEvidence]:
        """Fetch a batch of insights from database."""
        async with self.async_session() as session:
            result = await session.execute(
                select(InsightEvidence)
                .order_by(InsightEvidence.id)
                .offset(offset)
                .limit(limit)
            )
            return result.scalars().all()

    def classify_insight_type(self, insight_text: str) -> str:
        """Wrapper for _classify_insight_type from DiscussionSummarizer."""
        return self.summarizer._classify_insight_type(insight_text)

    def extract_concepts(self, text: str) -> list[str]:
        """Wrapper for _extract_concepts from DiscussionSummarizer."""
        return self.summarizer._extract_concepts(text)

    async def process_insight(
        self, insight: InsightEvidence, session: AsyncSession
    ) -> Dict[str, Any]:
        """
        Process a single insight: re-classify type and re-extract concepts.

        Returns:
            Dictionary with processing results
        """
        result = {
            "id": insight.id,
            "old_type": insight.insight_type,
            "new_type": None,
            "type_changed": False,
            "old_concepts_count": len(insight.concepts or []),
            "new_concepts_count": 0,
            "concepts_improved": False,
            "error": None,
        }

        try:
            # 1. Re-classify insight type
            insight_text = insight.insight or ""
            new_type = self.classify_insight_type(insight_text)
            result["new_type"] = new_type
            result["type_changed"] = new_type != insight.insight_type

            # 2. Re-extract concepts
            # Build text from insight + evidence for better concept extraction
            text_sources = [insight_text]
            if insight.evidence:
                for evidence_item in insight.evidence:
                    if isinstance(evidence_item, dict):
                        text_sources.append(evidence_item.get("text", ""))

            combined_text = " ".join(text_sources)
            new_concepts = self.extract_concepts(combined_text)
            result["new_concepts_count"] = len(new_concepts)
            result["concepts_improved"] = len(new_concepts) > result["old_concepts_count"]

            # 3. Update database (if not dry run)
            if not self.dry_run:
                insight.insight_type = new_type
                insight.concepts = new_concepts
                session.add(insight)

        except Exception as e:
            result["error"] = str(e)

        return result

    async def backfill(self, limit: int | None = None):
        """
        Main backfill logic: process all insights in batches.

        Args:
            limit: Optional limit on number of insights to process (for testing)
        """
        print("\n" + "=" * 80)
        print("INSIGHT BACKFILL - Re-classification & Concept Re-extraction")
        print("=" * 80)
        print(f"Mode: {'DRY RUN (no changes will be saved)' if self.dry_run else 'PRODUCTION (changes will be saved)'}")
        print(f"Batch size: {self.batch_size}")

        # Count total insights
        total_count = await self.count_total_insights()
        if limit:
            total_count = min(total_count, limit)

        print(f"Total insights to process: {total_count}")
        print("=" * 80 + "\n")

        if total_count == 0:
            print("No insights found. Exiting.")
            return

        # Process in batches with progress bar
        self.stats["total"] = total_count

        with tqdm(total=total_count, desc="Processing insights") as pbar:
            offset = 0
            while offset < total_count:
                # Fetch batch
                batch_limit = min(self.batch_size, total_count - offset)
                insights = await self.fetch_insights_batch(offset, batch_limit)

                if not insights:
                    break

                # Process batch
                async with self.async_session() as session:
                    for insight in insights:
                        result = await self.process_insight(insight, session)

                        # Update statistics
                        self.stats["processed"] += 1
                        if result["error"]:
                            self.stats["errors"] += 1
                            tqdm.write(f"ERROR [ID {result['id']}]: {result['error']}")
                        else:
                            if result["type_changed"]:
                                self.stats["type_changes"][
                                    f"{result['old_type']} -> {result['new_type']}"
                                ] += 1
                            if result["concepts_improved"]:
                                self.stats["concepts_improved"] += 1

                        pbar.update(1)

                    # Commit batch (if not dry run)
                    if not self.dry_run:
                        await session.commit()

                offset += batch_limit

        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print backfill summary statistics."""
        print("\n" + "=" * 80)
        print("BACKFILL SUMMARY")
        print("=" * 80)
        print(f"Total insights: {self.stats['total']}")
        print(f"Processed: {self.stats['processed']}")
        print(f"Errors: {self.stats['errors']}")
        print(f"Success rate: {(self.stats['processed'] - self.stats['errors']) / self.stats['processed'] * 100:.1f}%")
        print()

        print("TYPE CHANGES:")
        if self.stats["type_changes"]:
            for change, count in self.stats["type_changes"].most_common():
                print(f"  {change}: {count}")
        else:
            print("  No type changes")
        print()

        print("CONCEPT EXTRACTION:")
        print(f"  Insights with improved concepts: {self.stats['concepts_improved']}")
        print(f"  Improvement rate: {self.stats['concepts_improved'] / self.stats['processed'] * 100:.1f}%")
        print()

        if self.dry_run:
            print("⚠️  DRY RUN MODE - No changes were saved to database")
        else:
            print("✓ Changes committed to database")

        print("=" * 80 + "\n")

    async def close(self):
        """Close database connections."""
        await self.engine.dispose()


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Backfill insights with new Polish NLP classification and concept extraction"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run mode: show changes but don't save to database",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of insights to process (for testing)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=500,
        help="Batch size for database operations (default: 500)",
    )

    args = parser.parse_args()

    # Create backfiller
    backfiller = InsightBackfiller(
        dry_run=args.dry_run,
        batch_size=args.batch_size,
    )

    try:
        # Run backfill
        await backfiller.backfill(limit=args.limit)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user. Exiting gracefully...")
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await backfiller.close()


if __name__ == "__main__":
    asyncio.run(main())
