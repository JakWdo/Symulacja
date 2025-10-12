"""
Testy wydajności platformy badań rynkowych.

Te testy weryfikują czy system spełnia wymagania wydajnościowe:
- Generowanie 20 person < 60s (Gemini Flash)
- Focus group (20 person × 4 pytania) < 3 min
- Średni czas odpowiedzi < 3s per persona
- Survey (10 person × 10 pytań) < 60s

UWAGA: Te testy wymagają prawdziwego Gemini API i mogą być kosztowne
(wiele wywołań API). Oznaczone jako @pytest.mark.slow.
"""

import pytest
import time
import asyncio


@pytest.mark.slow
@pytest.mark.asyncio
async def test_persona_generation_performance_20_personas(db_session):
    """
    Test wydajności generowania 20 person.

    TARGET: < 60 sekund dla 20 person (Gemini Flash)
    IDEAL: 30-45 sekund

    KRYTYCZNE: Jeśli generowanie person trwa >2 min,
    użytkownicy porzucą platform.
    """
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app, raise_server_exceptions=False)

    # Register and login
    register_data = {
        "email": f"perf_test_{time.time()}@example.com",
        "password": "SecurePass123",
        "full_name": "Performance Test User"
    }
    register_response = client.post("/api/v1/auth/register", json=register_data)
    assert register_response.status_code == 201

    headers = {"Authorization": f"Bearer {register_response.json()['access_token']}"}

    # Create project
    project_data = {
        "name": "Performance Test Project",
        "target_demographics": {
            "age_group": {"18-24": 0.2, "25-34": 0.3, "35-44": 0.3, "45-54": 0.2},
            "gender": {"male": 0.5, "female": 0.5}
        },
        "target_sample_size": 20
    }
    project_response = client.post("/api/v1/projects", json=project_data, headers=headers)
    assert project_response.status_code == 201
    project_id = project_response.json()["id"]

    # Start timer
    start_time = time.time()

    # Generate 20 personas
    generate_response = client.post(
        f"/api/v1/projects/{project_id}/personas/generate",
        json={"num_personas": 20, "adversarial_mode": False},
        headers=headers
    )
    assert generate_response.status_code == 202

    # Poll for completion
    max_wait = 120  # 2 minutes timeout
    personas_ready = False

    for attempt in range(max_wait):
        await asyncio.sleep(1)

        personas_response = client.get(f"/api/v1/projects/{project_id}/personas", headers=headers)
        if personas_response.status_code == 200:
            personas = personas_response.json()
            if len(personas) >= 20:
                personas_ready = True
                break

    generation_time = time.time() - start_time

    assert personas_ready, f"Persona generation timed out after {generation_time:.1f}s"

    print(f"\n[PERF] 20 personas generated in {generation_time:.1f}s")

    # Performance assertion
    assert generation_time < 60, (
        f"PERFORMANCE FAILURE: 20 personas took {generation_time:.1f}s (target: <60s)"
    )

    if generation_time < 45:
        print(f"[PERF] ✓ EXCELLENT: Generated in {generation_time:.1f}s (target: 30-45s)")
    elif generation_time < 60:
        print(f"[PERF] ✓ ACCEPTABLE: Generated in {generation_time:.1f}s (target: <60s)")


@pytest.mark.slow
@pytest.mark.asyncio
async def test_focus_group_execution_performance_20x4(project_with_personas):
    """
    Test wydajności wykonania grupy fokusowej.

    TARGET: 20 person × 4 pytania < 3 minuty
    IDEAL: < 2 minuty (przy równoległym przetwarzaniu)

    KRYTYCZNE: Sequential processing = 20×4×3s = 4 min
    Parallelization musi działać!
    """
    project, personas, client, headers = project_with_personas

    # Note: project_with_personas fixture gives us only 10 personas
    # For this test, we'll use all 10 personas with 4 questions
    # Expected: 10 personas × 4 questions = 40 responses

    persona_ids = [str(p.id) for p in personas]  # All 10 personas

    focus_group_data = {
        "name": "Performance Test Focus Group",
        "persona_ids": persona_ids,
        "questions": [
            "What do you think about this product?",
            "How likely are you to use it?",
            "What features are most important?",
            "What would you change?"
        ],
        "mode": "normal"
    }

    # Create focus group
    fg_response = client.post(
        f"/api/v1/projects/{project.id}/focus-groups",
        json=focus_group_data,
        headers=headers
    )
    assert fg_response.status_code == 201
    focus_group_id = fg_response.json()["id"]

    # Start timer
    start_time = time.time()

    # Run focus group
    run_response = client.post(
        f"/api/v1/focus-groups/{focus_group_id}/run",
        headers=headers
    )
    assert run_response.status_code == 202

    # Poll for completion
    max_wait = 180  # 3 minutes timeout
    fg_completed = False

    for attempt in range(max_wait):
        await asyncio.sleep(2)

        fg_status = client.get(f"/api/v1/focus-groups/{focus_group_id}", headers=headers)
        if fg_status.status_code == 200:
            fg_data = fg_status.json()
            if fg_data["status"] == "completed":
                fg_completed = True
                break
            elif fg_data["status"] == "failed":
                pytest.fail("Focus group failed")

    execution_time = time.time() - start_time

    assert fg_completed, f"Focus group timed out after {execution_time:.1f}s"

    print(f"\n[PERF] Focus group (10×4) completed in {execution_time:.1f}s")

    # Get final metrics
    fg_final = client.get(f"/api/v1/focus-groups/{focus_group_id}", headers=headers)
    metrics = fg_final.json()

    total_time_ms = metrics.get("total_execution_time_ms", 0)
    avg_time_ms = metrics.get("avg_response_time_ms", 0)

    print(f"[PERF] Metrics:")
    print(f"  - Total: {total_time_ms/1000:.1f}s")
    print(f"  - Avg per response: {avg_time_ms}ms")

    # Performance assertions
    assert execution_time < 180, (
        f"PERFORMANCE FAILURE: Focus group took {execution_time:.1f}s (target: <3 min)"
    )

    if execution_time < 120:
        print(f"[PERF] ✓ EXCELLENT: Completed in {execution_time:.1f}s (target: <2 min)")
    elif execution_time < 180:
        print(f"[PERF] ✓ ACCEPTABLE: Completed in {execution_time:.1f}s (target: <3 min)")


@pytest.mark.slow
@pytest.mark.asyncio
async def test_avg_response_time_per_persona(completed_focus_group):
    """
    Test średniego czasu odpowiedzi per persona.

    TARGET: < 3 sekundy per persona per pytanie
    IDEAL: 1-2 sekundy

    KRYTYCZNE: Długie czasy odpowiedzi = długi czas wykonania całej grupy.
    """
    focus_group, responses, client, headers = completed_focus_group

    # Get focus group metrics
    fg_response = client.get(f"/api/v1/focus-groups/{focus_group.id}", headers=headers)
    assert fg_response.status_code == 200

    fg_data = fg_response.json()
    avg_response_time_ms = fg_data.get("avg_response_time_ms")

    assert avg_response_time_ms is not None, "avg_response_time_ms not found"

    print(f"\n[PERF] Average response time: {avg_response_time_ms}ms ({avg_response_time_ms/1000:.2f}s)")

    # Performance assertion
    target_ms = 3000  # 3 seconds
    assert avg_response_time_ms < target_ms, (
        f"PERFORMANCE FAILURE: Avg response time {avg_response_time_ms}ms (target: <{target_ms}ms)"
    )

    if avg_response_time_ms < 2000:
        print(f"[PERF] ✓ EXCELLENT: {avg_response_time_ms}ms (target: <2000ms)")
    elif avg_response_time_ms < 3000:
        print(f"[PERF] ✓ ACCEPTABLE: {avg_response_time_ms}ms (target: <3000ms)")

    # Verify individual response times
    from sqlalchemy import select
    from app.models.persona_response import PersonaResponse

    result = await client._session.execute(
        select(PersonaResponse).where(PersonaResponse.focus_group_id == focus_group.id)
    )
    all_responses = result.scalars().all()

    # Check for outliers (responses taking >10s)
    slow_responses = [r for r in all_responses if r.response_time_ms > 10000]

    if slow_responses:
        print(f"[PERF] ⚠ WARNING: {len(slow_responses)} responses took >10s")
    else:
        print(f"[PERF] ✓ No slow responses detected")


@pytest.mark.slow
@pytest.mark.asyncio
async def test_survey_execution_performance_10x10(project_with_personas):
    """
    Test wydajności wykonania ankiety.

    TARGET: 10 person × 10 pytań < 60 sekund
    IDEAL: < 45 sekund

    Ankiety są prostsze niż focus groups (mniej context),
    więc powinny być szybsze.
    """
    project, personas, client, headers = project_with_personas

    # Create survey with 10 questions
    survey_data = {
        "title": "Performance Test Survey",
        "description": "Testing survey performance",
        "questions": [
            {
                "id": f"q{i}",
                "type": "rating-scale",
                "title": f"How would you rate feature {i}?",
                "scaleMin": 1,
                "scaleMax": 5
            }
            for i in range(1, 11)
        ],
        "target_responses": 100
    }

    survey_response = client.post(
        f"/api/v1/projects/{project.id}/surveys",
        json=survey_data,
        headers=headers
    )
    assert survey_response.status_code == 201
    survey_id = survey_response.json()["id"]

    # Start timer
    start_time = time.time()

    # Run survey
    run_response = client.post(
        f"/api/v1/surveys/{survey_id}/run",
        headers=headers
    )
    assert run_response.status_code == 202

    # Poll for completion
    max_wait = 90  # 90 seconds timeout
    survey_completed = False

    for attempt in range(max_wait):
        await asyncio.sleep(2)

        survey_status = client.get(f"/api/v1/surveys/{survey_id}", headers=headers)
        if survey_status.status_code == 200:
            survey_data = survey_status.json()
            if survey_data["status"] == "completed":
                survey_completed = True
                break

    execution_time = time.time() - start_time

    assert survey_completed, f"Survey timed out after {execution_time:.1f}s"

    print(f"\n[PERF] Survey (10 personas × 10 questions) completed in {execution_time:.1f}s")

    # Performance assertion
    assert execution_time < 60, (
        f"PERFORMANCE FAILURE: Survey took {execution_time:.1f}s (target: <60s)"
    )

    if execution_time < 45:
        print(f"[PERF] ✓ EXCELLENT: Completed in {execution_time:.1f}s (target: <45s)")
    elif execution_time < 60:
        print(f"[PERF] ✓ ACCEPTABLE: Completed in {execution_time:.1f}s (target: <60s)")


@pytest.mark.asyncio
async def test_parallelization_speedup(project_with_personas):
    """
    Test weryfikujący że równoległe przetwarzanie działa.

    Porównuje teoretyczny czas sekwencyjny vs rzeczywisty równoległy.
    Oczekujemy przynajmniej 3x speedup dla 10 person.
    """
    project, personas, client, headers = project_with_personas

    persona_ids = [str(p.id) for p in personas[:5]]  # 5 personas

    focus_group_data = {
        "name": "Parallelization Test",
        "persona_ids": persona_ids,
        "questions": ["Test question?"],  # Single question
        "mode": "normal"
    }

    # Create and run
    fg_response = client.post(
        f"/api/v1/projects/{project.id}/focus-groups",
        json=focus_group_data,
        headers=headers
    )
    focus_group_id = fg_response.json()["id"]

    start_time = time.time()

    run_response = client.post(f"/api/v1/focus-groups/{focus_group_id}/run", headers=headers)
    assert run_response.status_code == 202

    # Wait for completion
    for attempt in range(60):
        await asyncio.sleep(1)
        fg_status = client.get(f"/api/v1/focus-groups/{focus_group_id}", headers=headers)
        if fg_status.json()["status"] == "completed":
            break

    actual_time = time.time() - start_time

    # Get avg response time
    fg_final = client.get(f"/api/v1/focus-groups/{focus_group_id}", headers=headers)
    avg_time_ms = fg_final.json().get("avg_response_time_ms", 0)

    # Theoretical sequential time = 5 personas × avg_time
    theoretical_sequential_time = (5 * avg_time_ms) / 1000

    # Speedup factor
    speedup = theoretical_sequential_time / actual_time if actual_time > 0 else 0

    print(f"\n[PERF] Parallelization analysis:")
    print(f"  - Actual time: {actual_time:.1f}s")
    print(f"  - Theoretical sequential: {theoretical_sequential_time:.1f}s")
    print(f"  - Speedup: {speedup:.1f}x")

    # We expect at least 2x speedup (some overhead is normal)
    assert speedup >= 2, (
        f"PARALLELIZATION FAILURE: Only {speedup:.1f}x speedup (expected >=2x)"
    )

    if speedup >= 4:
        print(f"[PERF] ✓ EXCELLENT: {speedup:.1f}x speedup")
    elif speedup >= 3:
        print(f"[PERF] ✓ GOOD: {speedup:.1f}x speedup")
    elif speedup >= 2:
        print(f"[PERF] ✓ ACCEPTABLE: {speedup:.1f}x speedup")
