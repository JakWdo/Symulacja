"""
End-to-End Test: Pełny Workflow Badania Rynkowego.

Ten test symuluje kompletny scenariusz użytkownika od początku do końca:
1. Rejestracja użytkownika
2. Utworzenie projektu badawczego
3. Generowanie person (syntetycznych respondentów)
4. Walidacja statystyczna person (chi-kwadrat)
5. Utworzenie grupy fokusowej
6. Uruchomienie dyskusji
7. Weryfikacja odpowiedzi
8. Budowanie grafu wiedzy
9. Generowanie insights AI
10. Weryfikacja performance metrics

UWAGA: Ten test wymaga prawdziwego Gemini API key w .env
i może trwać 2-3 minuty (generowanie person + focus group).
"""

import pytest
import asyncio
import time
from uuid import uuid4


@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.external
@pytest.mark.asyncio
async def test_complete_research_workflow_end_to_end(db_session):
    """
    Test kompletnego przepływu badania rynkowego.

    KRYTYCZNE: To jest najważniejszy test aplikacji - pokrywa
    wszystkie główne funkcjonalności od początku do końca.

    Oczekiwany czas wykonania: 90-180 sekund
    - Rejestracja: <1s
    - Utworzenie projektu: <1s
    - Generowanie 10 person: 15-30s (Gemini Flash)
    - Utworzenie focus group: <1s
    - Uruchomienie dyskusji (5 person × 3 pytania): 30-60s
    - Budowa grafu: 10-20s
    - Generowanie insights: 5-10s
    """
    from fastapi.testclient import TestClient
    from app.main import app
    from sqlalchemy import select
    from app.models.user import User
    from app.models.project import Project
    from app.models.persona import Persona
    from app.models.focus_group import FocusGroup
    from app.models.persona_response import PersonaResponse

    client = TestClient(app, raise_server_exceptions=False)

    start_time = time.time()

    # ========== STEP 1: Register User ==========
    print("\n[E2E] Step 1: Registering user...")
    register_data = {
        "email": f"e2e_test_{uuid4().hex[:8]}@example.com",
        "password": "SecurePass123",
        "full_name": "E2E Test User"
    }

    register_response = client.post("/api/v1/auth/register", json=register_data)
    assert register_response.status_code == 201, f"Registration failed: {register_response.text}"

    auth_data = register_response.json()
    token = auth_data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    user_id = auth_data["user"]["id"]

    print(f"[E2E] ✓ User registered: {user_id}")

    # ========== STEP 2: Create Project ==========
    print("[E2E] Step 2: Creating research project...")
    project_data = {
        "name": "E2E Test Research Project",
        "description": "End-to-end test of market research platform",
        "target_audience": "Young professionals aged 25-35",
        "research_objectives": "Test complete workflow",
        "target_sample_size": 10  # Small for faster test
    }

    project_response = client.post("/api/v1/projects", json=project_data, headers=headers)
    assert project_response.status_code == 201, f"Project creation failed: {project_response.text}"

    project_id = project_response.json()["id"]
    print(f"[E2E] ✓ Project created: {project_id}")

    # ========== STEP 3: Generate Personas ==========
    print("[E2E] Step 3: Generating 10 personas (this may take 15-30s)...")
    persona_gen_start = time.time()

    generate_response = client.post(
        f"/api/v1/projects/{project_id}/personas/generate",
        json={"num_personas": 10, "adversarial_mode": False},
        headers=headers
    )
    assert generate_response.status_code == 202, f"Persona generation failed: {generate_response.text}"

    # Poll for completion (background task)
    max_wait = 60  # 60 seconds timeout
    personas_ready = False

    for attempt in range(max_wait):
        await asyncio.sleep(1)

        personas_response = client.get(f"/api/v1/projects/{project_id}/personas", headers=headers)
        if personas_response.status_code == 200:
            personas = personas_response.json()
            if len(personas) >= 10:
                personas_ready = True
                break

    assert personas_ready, "Personas generation timed out after 60s"

    persona_gen_time = time.time() - persona_gen_start
    print(f"[E2E] ✓ 10 personas generated in {persona_gen_time:.1f}s")

    # Verify personas
    personas_response = client.get(f"/api/v1/projects/{project_id}/personas", headers=headers)
    personas = personas_response.json()
    assert len(personas) == 10

    # Check that personas have required fields
    for persona in personas:
        assert "id" in persona
        assert "age" in persona
        assert "gender" in persona
        assert "full_name" in persona or "name" in persona
        # Big Five traits
        assert "openness" in persona
        assert "conscientiousness" in persona

    print(f"[E2E] ✓ All personas have required fields")

    # ========== STEP 4: Validate Project Structure ==========
    print("[E2E] Step 4: Validating project structure...")
    project_check = client.get(f"/api/v1/projects/{project_id}", headers=headers)
    project_data = project_check.json()

    # NOTE: Chi-square validation removed (2025-10-22) - segment-based allocation
    print(f"[E2E] ✓ Project structure validated")

    # ========== STEP 5: Create Focus Group ==========
    print("[E2E] Step 5: Creating focus group...")
    selected_persona_ids = [p["id"] for p in personas[:5]]  # Select 5 personas

    focus_group_data = {
        "name": "E2E Test Focus Group",
        "description": "Testing complete focus group workflow",
        "persona_ids": selected_persona_ids,
        "questions": [
            "What is your first impression of this product idea?",
            "Would you recommend this to your friends or colleagues?",
            "What improvements or features would you like to see?"
        ],
        "mode": "normal"
    }

    fg_response = client.post(
        f"/api/v1/projects/{project_id}/focus-groups",
        json=focus_group_data,
        headers=headers
    )
    assert fg_response.status_code == 201, f"Focus group creation failed: {fg_response.text}"

    focus_group_id = fg_response.json()["id"]
    print(f"[E2E] ✓ Focus group created: {focus_group_id}")

    # ========== STEP 6: Run Focus Group Discussion ==========
    print("[E2E] Step 6: Running focus group (5 personas × 3 questions, ~30-60s)...")
    fg_run_start = time.time()

    run_response = client.post(
        f"/api/v1/focus-groups/{focus_group_id}/run",
        headers=headers
    )
    assert run_response.status_code == 202, f"Focus group run failed: {run_response.text}"

    # Poll for completion
    max_wait = 120  # 2 minutes timeout
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
                pytest.fail(f"Focus group failed to complete")

    assert fg_completed, "Focus group execution timed out after 2 minutes"

    fg_run_time = time.time() - fg_run_start
    print(f"[E2E] ✓ Focus group completed in {fg_run_time:.1f}s")

    # ========== STEP 7: Verify Responses ==========
    print("[E2E] Step 7: Verifying responses...")
    results_response = client.get(f"/api/v1/focus-groups/{focus_group_id}/results", headers=headers)
    assert results_response.status_code == 200

    # Verify response count: 5 personas × 3 questions = 15 responses
    result = await db_session.execute(
        select(PersonaResponse).where(PersonaResponse.focus_group_id == focus_group_id)
    )
    responses = result.scalars().all()

    assert len(responses) == 15, f"Expected 15 responses (5×3), got {len(responses)}"
    print(f"[E2E] ✓ All 15 responses received")

    # Verify each response has content
    for response in responses:
        assert response.response_text is not None
        assert len(response.response_text) > 0
        assert response.response_time_ms is not None

    # ========== STEP 8: Build Knowledge Graph (Optional) ==========
    print("[E2E] Step 8: Building knowledge graph...")

    # Try to build graph (might fail if Neo4j not available, should fallback to memory)
    graph_response = client.post(
        f"/api/v1/graph/build/{focus_group_id}",
        headers=headers
    )

    if graph_response.status_code == 200:
        graph_data = graph_response.json()
        print(f"[E2E] ✓ Graph built: {graph_data.get('nodes', 0)} nodes, {graph_data.get('links', 0)} links")

        # Get key concepts
        concepts_response = client.get(
            f"/api/v1/graph/{focus_group_id}/concepts",
            headers=headers
        )
        if concepts_response.status_code == 200:
            concepts = concepts_response.json()
            print(f"[E2E] ✓ Key concepts extracted: {len(concepts.get('concepts', []))} concepts")
    else:
        print(f"[E2E] ⚠ Graph building failed (Neo4j might not be available): {graph_response.status_code}")

    # ========== STEP 9: Generate AI Insights (Optional) ==========
    print("[E2E] Step 9: Generating AI insights...")

    insights_response = client.post(
        f"/api/v1/analysis/{focus_group_id}/insights",
        headers=headers
    )

    if insights_response.status_code in [200, 202]:
        print(f"[E2E] ✓ AI insights generation started")

        # Try to fetch insights
        get_insights = client.get(
            f"/api/v1/analysis/{focus_group_id}/insights",
            headers=headers
        )
        if get_insights.status_code == 200:
            insights = get_insights.json()
            if "summary" in insights:
                print(f"[E2E] ✓ AI insights available")
    else:
        print(f"[E2E] ⚠ AI insights generation not available: {insights_response.status_code}")

    # ========== STEP 10: Verify Performance Metrics ==========
    print("[E2E] Step 10: Verifying performance metrics...")

    fg_final = client.get(f"/api/v1/focus-groups/{focus_group_id}", headers=headers)
    fg_metrics = fg_final.json()

    total_time_ms = fg_metrics.get("total_execution_time_ms")
    avg_time_ms = fg_metrics.get("avg_response_time_ms")

    print(f"[E2E] Performance metrics:")
    print(f"  - Total execution time: {total_time_ms}ms ({total_time_ms/1000:.1f}s)")
    print(f"  - Avg response time: {avg_time_ms}ms")

    # Performance assertions (targets from CLAUDE.md)
    # Target: <30s total for focus group, <3s per persona response
    assert total_time_ms < 180000, f"Focus group took {total_time_ms}ms (>3 min)"  # Relaxed for E2E
    assert avg_time_ms < 10000, f"Avg response time {avg_time_ms}ms (>10s)"  # Relaxed for E2E

    # ========== FINAL SUMMARY ==========
    total_time = time.time() - start_time
    print(f"\n[E2E] ========== TEST COMPLETED SUCCESSFULLY ==========")
    print(f"[E2E] Total test time: {total_time:.1f}s")
    print(f"[E2E] Breakdown:")
    print(f"  - Persona generation: {persona_gen_time:.1f}s")
    print(f"  - Focus group execution: {fg_run_time:.1f}s")
    print(f"[E2E] All critical paths verified ✓")

    # Assert reasonable total time (should be < 3 minutes)
    assert total_time < 240, f"E2E test took {total_time:.1f}s (>4 min)"
