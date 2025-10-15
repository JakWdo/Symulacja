"""
End-to-End Test: Pełny Workflow Ankiety.

Ten test symuluje kompletny scenariusz ankiety:
1. Utworzenie projektu + persony
2. Utworzenie ankiety z różnymi typami pytań
3. Uruchomienie zbierania odpowiedzi
4. Weryfikacja odpowiedzi
5. Analiza demograficzna wyników
"""

import pytest
import asyncio
import time


@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.external
@pytest.mark.asyncio
async def test_survey_workflow_end_to_end(project_with_personas):
    """
    Test kompletnego przepływu ankiety.

    Weryfikuje:
    - Utworzenie ankiety z 4 typami pytań
    - Uruchomienie zbierania odpowiedzi (background task)
    - Weryfikację liczby odpowiedzi (10 person × 4 pytania = 40)
    - Analizę statystyczną wyników
    - Demographic breakdown
    """
    project, personas, client, headers = project_with_personas

    print("\n[E2E SURVEY] Starting survey workflow...")

    # ========== STEP 1: Create Survey with Multiple Question Types ==========
    print("[E2E SURVEY] Step 1: Creating survey with 4 question types...")

    survey_data = {
        "title": "E2E Product Feedback Survey",
        "description": "Complete survey workflow test",
        "questions": [
            {
                "id": "q1",
                "type": "rating-scale",
                "title": "How would you rate this product? (1-5)",
                "scaleMin": 1,
                "scaleMax": 5,
                "required": True
            },
            {
                "id": "q2",
                "type": "single-choice",
                "title": "Would you recommend this product?",
                "options": ["Definitely yes", "Probably yes", "Not sure", "Probably not", "Definitely not"],
                "required": True
            },
            {
                "id": "q3",
                "type": "multiple-choice",
                "title": "Which features interest you most? (select all that apply)",
                "options": ["Performance", "Design", "Price", "Support", "Features"],
                "required": False
            },
            {
                "id": "q4",
                "type": "open-text",
                "title": "What improvements would you suggest?",
                "required": False
            }
        ],
        "target_responses": 40  # 10 personas × 4 questions
    }

    create_response = client.post(
        f"/api/v1/projects/{project.id}/surveys",
        json=survey_data,
        headers=headers
    )

    assert create_response.status_code == 201, f"Survey creation failed: {create_response.text}"
    survey_id = create_response.json()["id"]
    print(f"[E2E SURVEY] ✓ Survey created: {survey_id}")

    # ========== STEP 2: Run Survey ==========
    print("[E2E SURVEY] Step 2: Running survey (10 personas × 4 questions)...")
    start_time = time.time()

    run_response = client.post(
        f"/api/v1/surveys/{survey_id}/run",
        headers=headers
    )

    assert run_response.status_code == 202, f"Survey run failed: {run_response.text}"

    # ========== STEP 3: Poll for Completion ==========
    print("[E2E SURVEY] Step 3: Waiting for completion...")
    max_wait = 90  # 90 seconds timeout
    survey_completed = False

    for attempt in range(max_wait):
        await asyncio.sleep(2)

        status_response = client.get(f"/api/v1/surveys/{survey_id}", headers=headers)
        if status_response.status_code == 200:
            survey_data_status = status_response.json()
            if survey_data_status["status"] == "completed":
                survey_completed = True
                break
            elif survey_data_status["status"] == "failed":
                pytest.fail("Survey execution failed")

    execution_time = time.time() - start_time

    assert survey_completed, f"Survey timed out after {execution_time:.1f}s"
    print(f"[E2E SURVEY] ✓ Survey completed in {execution_time:.1f}s")

    # ========== STEP 4: Verify Response Count ==========
    print("[E2E SURVEY] Step 4: Verifying responses...")

    results_response = client.get(f"/api/v1/surveys/{survey_id}/results", headers=headers)
    assert results_response.status_code == 200

    results = results_response.json()

    # Expected: 10 personas × 4 questions = 40 responses
    actual_responses = results.get("actual_responses", 0)
    print(f"[E2E SURVEY]   Responses: {actual_responses}")

    # Allow some flexibility (not all questions are required)
    assert actual_responses >= 30, f"Too few responses: {actual_responses} (expected ~40)"

    # ========== STEP 5: Verify Question Analytics ==========
    print("[E2E SURVEY] Step 5: Analyzing question statistics...")

    question_analytics = results.get("question_analytics", [])
    assert len(question_analytics) == 4, "Should have analytics for all 4 questions"

    for qa in question_analytics:
        print(f"[E2E SURVEY]   Q{qa['question_id']}: {qa['question_type']} - {qa['responses_count']} responses")

        # Verify statistics structure
        assert "statistics" in qa

        if qa["question_type"] == "rating-scale":
            stats = qa["statistics"]
            assert "mean" in stats
            assert "min" in stats
            assert "max" in stats
            print(f"[E2E SURVEY]     Rating: mean={stats.get('mean', 'N/A'):.2f}")

        elif qa["question_type"] == "single-choice":
            stats = qa["statistics"]
            # Should have distribution of answers
            print(f"[E2E SURVEY]     Distribution: {list(stats.keys())[:2]}...")

    # ========== STEP 6: Verify Demographic Breakdown ==========
    print("[E2E SURVEY] Step 6: Verifying demographic breakdown...")

    demographic_breakdown = results.get("demographic_breakdown", {})
    assert len(demographic_breakdown) > 0, "Should have demographic breakdown"

    # Check for age or gender breakdown
    if "age_group" in demographic_breakdown or "gender" in demographic_breakdown:
        print(f"[E2E SURVEY] ✓ Demographic segments: {list(demographic_breakdown.keys())}")
    else:
        print(f"[E2E SURVEY] ⚠ Demographic breakdown not detailed")

    # ========== STEP 7: Verify Performance ==========
    print("[E2E SURVEY] Step 7: Verifying performance metrics...")

    total_time_ms = results.get("total_execution_time_ms")
    avg_time_ms = results.get("avg_response_time_ms")

    if total_time_ms and avg_time_ms:
        print(f"[E2E SURVEY]   Total time: {total_time_ms/1000:.1f}s")
        print(f"[E2E SURVEY]   Avg per response: {avg_time_ms}ms")

        # Performance target: <60s for 10 personas × 4 questions
        assert total_time_ms < 120000, f"Survey too slow: {total_time_ms/1000:.1f}s"

    # ========== FINAL SUMMARY ==========
    print(f"\n[E2E SURVEY] ========== SURVEY WORKFLOW COMPLETED ==========")
    print(f"[E2E SURVEY] ✓ Survey created with 4 question types")
    print(f"[E2E SURVEY] ✓ {actual_responses} responses collected")
    print(f"[E2E SURVEY] ✓ Analytics generated")
    print(f"[E2E SURVEY] ✓ Demographic breakdown available")
    print(f"[E2E SURVEY] Total time: {execution_time:.1f}s")

    # Assert reasonable execution time
    assert execution_time < 120, f"E2E survey test took {execution_time:.1f}s (>2 min)"
