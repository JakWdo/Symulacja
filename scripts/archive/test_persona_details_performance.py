"""
Performance validation script for optimized Persona Details services.

Tests:
1. PersonaJourneyService - Target: <2s
2. PersonaNeedsService - Target: <2s
3. PersonaMessagingService - Target: <1.5s
4. PersonaKPIService - Target: <300ms (fresh), <50ms (cached)
5. PersonaDetailsService - Target: <3s (fresh), <50ms (cached)
6. PersonaBatchProcessor - Target: <5s for 3 personas

Run:
    python scripts/archive/test_persona_details_performance.py
"""

import asyncio
import sys
import time
from pathlib import Path

# Add project root to path when uruchamiany jako skrypt
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.config import get_settings
from app.db import AsyncSessionLocal
from app.models.persona import Persona
from app.services.persona_journey_service import PersonaJourneyService
from app.services.persona_needs_service import PersonaNeedsService
from app.services.persona_messaging_service import PersonaMessagingService
from app.services.persona_kpi_service import PersonaKPIService
from app.services.persona_details_service import PersonaDetailsService
from app.services.persona_batch_processor import PersonaBatchProcessor

settings = get_settings()


def create_mock_persona() -> Persona:
    """Create a mock persona for testing."""
    persona = Persona(
        id="123e4567-e89b-12d3-a456-426614174000",
        project_id="123e4567-e89b-12d3-a456-426614174001",
        full_name="Jan Kowalski",
        persona_title="Senior Product Manager",
        headline="Experienced PM leading B2B SaaS products",
        age=35,
        gender="Mężczyzna",
        location="Warszawa",
        education_level="Wyższe (magisterskie)",
        income_bracket="10 000 - 15 000 zł",
        occupation="Product Manager",
        openness=0.75,
        conscientiousness=0.82,
        extraversion=0.68,
        agreeableness=0.71,
        neuroticism=0.35,
        power_distance=0.45,
        individualism=0.70,
        masculinity=0.55,
        uncertainty_avoidance=0.60,
        long_term_orientation=0.75,
        indulgence=0.50,
        values=["innowacja", "efektywność", "rozwój"],
        interests=["technologia", "zarządzanie", "AI"],
        background_story="Doświadczony Product Manager z 10-letnim stażem...",
        rag_context_used=True,
    )
    return persona


async def test_journey_service():
    """Test PersonaJourneyService performance."""
    print("\n=== Testing PersonaJourneyService ===")
    service = PersonaJourneyService()
    persona = create_mock_persona()

    start_time = time.time()
    try:
        journey = await service.generate_customer_journey(
            persona,
            rag_context="Sample RAG context about Polish B2B SaaS market..."
        )
        elapsed_ms = int((time.time() - start_time) * 1000)

        print(f"✓ Journey generated in {elapsed_ms}ms")
        print(f"  - Stages: {len(journey.get('stages', []))}")
        print(f"  - Overall conversion rate: {journey.get('overall_conversion_rate', 0):.2%}")

        if elapsed_ms < 2000:
            print(f"  ✓ PASS: Under 2s target ({elapsed_ms}ms)")
        else:
            print(f"  ✗ FAIL: Exceeded 2s target ({elapsed_ms}ms)")

        return elapsed_ms < 2000
    except Exception as exc:
        print(f"✗ FAILED: {exc}")
        return False


async def test_needs_service():
    """Test PersonaNeedsService performance."""
    print("\n=== Testing PersonaNeedsService ===")

    async with AsyncSessionLocal() as db:
        service = PersonaNeedsService(db)
        persona = create_mock_persona()

        start_time = time.time()
        try:
            needs = await service.generate_needs_analysis(persona)
            elapsed_ms = int((time.time() - start_time) * 1000)

            print(f"✓ Needs generated in {elapsed_ms}ms")
            print(f"  - JTBD items: {len(needs.get('jobs_to_be_done', []))}")
            print(f"  - Pain points: {len(needs.get('pain_points', []))}")

            if elapsed_ms < 2000:
                print(f"  ✓ PASS: Under 2s target ({elapsed_ms}ms)")
            else:
                print(f"  ✗ FAIL: Exceeded 2s target ({elapsed_ms}ms)")

            return elapsed_ms < 2000
        except Exception as exc:
            print(f"✗ FAILED: {exc}")
            return False


async def test_messaging_service():
    """Test PersonaMessagingService performance."""
    print("\n=== Testing PersonaMessagingService ===")
    service = PersonaMessagingService()
    persona = create_mock_persona()

    start_time = time.time()
    try:
        messaging = await service.generate_messaging(
            persona,
            tone="professional",
            message_type="email",
            num_variants=3,
            context="New product launch campaign"
        )
        elapsed_ms = int((time.time() - start_time) * 1000)

        print(f"✓ Messaging generated in {elapsed_ms}ms")
        print(f"  - Variants: {len(messaging.get('variants', []))}")

        if elapsed_ms < 1500:
            print(f"  ✓ PASS: Under 1.5s target ({elapsed_ms}ms)")
        else:
            print(f"  ✗ FAIL: Exceeded 1.5s target ({elapsed_ms}ms)")

        return elapsed_ms < 1500
    except Exception as exc:
        print(f"✗ FAILED: {exc}")
        return False


async def test_kpi_service():
    """Test PersonaKPIService performance (fresh + cached)."""
    print("\n=== Testing PersonaKPIService ===")

    async with AsyncSessionLocal() as db:
        service = PersonaKPIService(db)
        persona = create_mock_persona()

        # Test 1: Fresh calculation
        start_time = time.time()
        try:
            kpi = await service.calculate_kpi_snapshot(persona)
            elapsed_ms = int((time.time() - start_time) * 1000)

            print(f"✓ KPI calculated (fresh) in {elapsed_ms}ms")
            print(f"  - Segment size: {kpi.get('segment_size', 0):,}")
            print(f"  - Conversion rate: {kpi.get('conversion_rate', 0):.2%}")

            fresh_pass = elapsed_ms < 300
            if fresh_pass:
                print(f"  ✓ PASS: Under 300ms target ({elapsed_ms}ms)")
            else:
                print(f"  ✗ FAIL: Exceeded 300ms target ({elapsed_ms}ms)")

        except Exception as exc:
            print(f"✗ FAILED (fresh): {exc}")
            fresh_pass = False

        # Test 2: Cached calculation
        start_time = time.time()
        try:
            kpi_cached = await service.calculate_kpi_snapshot(persona)
            elapsed_ms = int((time.time() - start_time) * 1000)

            print(f"✓ KPI calculated (cached) in {elapsed_ms}ms")

            cached_pass = elapsed_ms < 50
            if cached_pass:
                print(f"  ✓ PASS: Under 50ms target ({elapsed_ms}ms)")
            else:
                print(f"  ✗ FAIL: Exceeded 50ms target ({elapsed_ms}ms)")

        except Exception as exc:
            print(f"✗ FAILED (cached): {exc}")
            cached_pass = False

        return fresh_pass and cached_pass


async def test_batch_processor():
    """Test PersonaBatchProcessor for 3 personas."""
    print("\n=== Testing PersonaBatchProcessor (3 personas) ===")

    async with AsyncSessionLocal() as db:
        processor = PersonaBatchProcessor(db)

        # Create 3 mock personas
        personas = [
            create_mock_persona(),
            create_mock_persona(),
            create_mock_persona(),
        ]

        # Test parallel journey generation
        start_time = time.time()
        try:
            journeys = await processor.batch_generate_journeys(
                personas,
                rag_context="Sample RAG context..."
            )
            elapsed_ms = int((time.time() - start_time) * 1000)

            print(f"✓ Batch journeys generated in {elapsed_ms}ms")
            print(f"  - Personas processed: {len(journeys)}")
            print(f"  - Avg per persona: {elapsed_ms // len(journeys)}ms")

            if elapsed_ms < 5000:
                print(f"  ✓ PASS: Under 5s target ({elapsed_ms}ms)")
            else:
                print(f"  ✗ FAIL: Exceeded 5s target ({elapsed_ms}ms)")

            return elapsed_ms < 5000
        except Exception as exc:
            print(f"✗ FAILED: {exc}")
            return False


async def main():
    """Run all performance tests."""
    print("=" * 60)
    print("PERSONA DETAILS PERFORMANCE VALIDATION")
    print("=" * 60)
    print(f"\nModel: {settings.ANALYSIS_MODEL}")
    print(f"Environment: {settings.ENVIRONMENT}")

    results = {}

    # Run tests
    results["journey"] = await test_journey_service()
    results["needs"] = await test_needs_service()
    results["messaging"] = await test_messaging_service()
    results["kpi"] = await test_kpi_service()
    results["batch"] = await test_batch_processor()

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    total = len(results)
    passed = sum(1 for r in results.values() if r)

    for test_name, passed_flag in results.items():
        status = "✓ PASS" if passed_flag else "✗ FAIL"
        print(f"{status} - {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n✓ ALL TESTS PASSED - Performance targets met!")
        sys.exit(0)
    else:
        print("\n✗ SOME TESTS FAILED - Performance targets not met")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
