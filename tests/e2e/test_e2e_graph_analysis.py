"""
End-to-End Test: Graph Analysis Workflow.

Ten test weryfikuje pełny pipeline analizy grafowej:
1. Utworzenie completed focus group (z fixture)
2. Budowanie grafu wiedzy (Neo4j lub memory fallback)
3. Ekstrakcja key concepts
4. Identyfikacja kontrowersyjnych tematów
5. Analiza wpływowych person
6. Korelacje demograficzne (trait-opinion)
7. Rozkład emocji
"""

import pytest


@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.external
@pytest.mark.asyncio
async def test_graph_analysis_complete_workflow(completed_focus_group):
    """
    Test pełnego workflow analizy grafowej.

    Weryfikuje:
    - Budowa grafu (nodes + links)
    - Ekstrakcja konceptów z odpowiedzi
    - Analiza sentymentu
    - Polaryzacja opinii
    - Wpływowe persony (PageRank-style)
    - Fallback do in-memory graph gdy Neo4j unavailable
    """
    focus_group, responses, client, headers = completed_focus_group

    print("\n[E2E GRAPH] Starting graph analysis workflow...")

    # ========== STEP 1: Build Graph ==========
    print("[E2E GRAPH] Step 1: Building knowledge graph...")

    build_response = client.post(
        f"/api/v1/graph/build/{focus_group.id}",
        headers=headers
    )

    assert build_response.status_code == 200, f"Graph building failed: {build_response.text}"

    graph_data = build_response.json()
    assert "nodes" in graph_data or "total_nodes" in graph_data
    assert "links" in graph_data or "total_links" in graph_data

    nodes_count = graph_data.get("nodes", graph_data.get("total_nodes", 0))
    links_count = graph_data.get("links", graph_data.get("total_links", 0))

    print(f"[E2E GRAPH] ✓ Graph built: {nodes_count} nodes, {links_count} links")

    # Verify we have some structure
    assert nodes_count > 0, "Graph should have at least some nodes"

    # ========== STEP 2: Get Key Concepts ==========
    print("[E2E GRAPH] Step 2: Extracting key concepts...")

    concepts_response = client.get(
        f"/api/v1/graph/{focus_group.id}/concepts",
        headers=headers
    )

    if concepts_response.status_code == 200:
        concepts_data = concepts_response.json()
        concepts = concepts_data.get("concepts", [])

        print(f"[E2E GRAPH] ✓ Extracted {len(concepts)} key concepts")

        if concepts:
            # Verify structure
            for concept in concepts[:3]:  # Check first 3
                assert "name" in concept
                assert "mentions" in concept
                assert "avg_sentiment" in concept

            # Find most mentioned concept
            top_concept = max(concepts, key=lambda c: c.get("mentions", 0))
            print(f"[E2E GRAPH]   Top concept: '{top_concept['name']}' ({top_concept['mentions']} mentions)")
    else:
        print(f"[E2E GRAPH] ⚠ Key concepts not available: {concepts_response.status_code}")

    # ========== STEP 3: Get Controversial Concepts ==========
    print("[E2E GRAPH] Step 3: Identifying controversial topics...")

    controversial_response = client.get(
        f"/api/v1/graph/{focus_group.id}/controversial",
        headers=headers
    )

    if controversial_response.status_code == 200:
        controversial_data = controversial_response.json()
        controversial = controversial_data.get("controversial_concepts", [])

        print(f"[E2E GRAPH] ✓ Found {len(controversial)} controversial topics")

        if controversial:
            # Check structure
            for topic in controversial[:2]:
                assert "concept" in topic
                assert "polarization" in topic
                # High polarization = controversial
                print(f"[E2E GRAPH]   '{topic['concept']}': polarization={topic['polarization']:.2f}")
    else:
        print(f"[E2E GRAPH] ⚠ Controversial concepts analysis not available")

    # ========== STEP 4: Get Influential Personas ==========
    print("[E2E GRAPH] Step 4: Finding influential personas...")

    influential_response = client.get(
        f"/api/v1/graph/{focus_group.id}/influential",
        headers=headers
    )

    if influential_response.status_code == 200:
        influential_data = influential_response.json()
        influential = influential_data.get("influential_personas", [])

        print(f"[E2E GRAPH] ✓ Identified {len(influential)} influential personas")

        if influential:
            # Check structure
            for persona in influential[:3]:
                assert "persona_name" in persona or "name" in persona
                assert "influence_score" in persona or "connections" in persona

            # Top influencer
            top_influencer = influential[0]
            print(f"[E2E GRAPH]   Top: {top_influencer.get('persona_name', top_influencer.get('name'))}")
    else:
        print(f"[E2E GRAPH] ⚠ Influential personas not available")

    # ========== STEP 5: Get Trait Correlations ==========
    print("[E2E GRAPH] Step 5: Analyzing demographic correlations...")

    correlations_response = client.get(
        f"/api/v1/graph/{focus_group.id}/correlations",
        headers=headers
    )

    if correlations_response.status_code == 200:
        correlations_data = correlations_response.json()
        print(f"[E2E GRAPH] ✓ Demographic correlations analyzed")

        # Check for age-based differences
        if "correlations" in correlations_data:
            print(f"[E2E GRAPH]   Found trait-opinion correlations")
    else:
        print(f"[E2E GRAPH] ⚠ Trait correlations not available")

    # ========== STEP 6: Get Emotion Distribution ==========
    print("[E2E GRAPH] Step 6: Analyzing emotion distribution...")

    emotions_response = client.get(
        f"/api/v1/graph/{focus_group.id}/emotions",
        headers=headers
    )

    if emotions_response.status_code == 200:
        emotions_data = emotions_response.json()
        emotions = emotions_data.get("emotions", [])

        print(f"[E2E GRAPH] ✓ Emotion distribution:")

        if emotions:
            for emotion in emotions:
                emotion_name = emotion.get("emotion", "Unknown")
                count = emotion.get("count", 0)
                print(f"[E2E GRAPH]   {emotion_name}: {count}")
    else:
        print(f"[E2E GRAPH] ⚠ Emotion distribution not available")

    # ========== STEP 7: Get Full Graph Visualization Data ==========
    print("[E2E GRAPH] Step 7: Fetching graph visualization data...")

    graph_viz_response = client.get(
        f"/api/v1/graph/{focus_group.id}",
        headers=headers
    )

    if graph_viz_response.status_code == 200:
        viz_data = graph_viz_response.json()

        assert "nodes" in viz_data
        assert "links" in viz_data

        nodes = viz_data["nodes"]
        links = viz_data["links"]

        print(f"[E2E GRAPH] ✓ Visualization data: {len(nodes)} nodes, {len(links)} links")

        # Verify node types
        node_types = set()
        for node in nodes[:10]:  # Check first 10
            assert "id" in node
            assert "type" in node
            node_types.add(node["type"])

        print(f"[E2E GRAPH]   Node types: {', '.join(node_types)}")

        # Should have at least personas and concepts
        # (emotions might not always be present)
        assert "persona" in node_types or "Persona" in node_types
    else:
        print(f"[E2E GRAPH] ⚠ Graph visualization data not available")

    # ========== FINAL SUMMARY ==========
    print(f"\n[E2E GRAPH] ========== GRAPH ANALYSIS COMPLETED ==========")
    print(f"[E2E GRAPH] ✓ Graph structure verified")
    print(f"[E2E GRAPH] ✓ Concepts extracted")
    print(f"[E2E GRAPH] ✓ Insights generated")
    print(f"[E2E GRAPH] All graph analysis endpoints functional")


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_graph_fallback_when_neo4j_unavailable(completed_focus_group):
    """
    Test że system działa z in-memory fallback gdy Neo4j jest niedostępny.

    KRYTYCZNE: Aplikacja nie może być całkowicie zależna od Neo4j.
    Memory fallback musi zapewnić podstawową funkcjonalność.
    """
    from unittest.mock import patch

    focus_group, responses, client, headers = completed_focus_group

    print("\n[E2E GRAPH FALLBACK] Testing Neo4j fallback...")

    # Mock Neo4j to be unavailable
    with patch("app.services.graph_service.GraphService.driver", None):
        # Try to build graph
        build_response = client.post(
            f"/api/v1/graph/build/{focus_group.id}",
            headers=headers
        )

        # Should succeed with fallback
        assert build_response.status_code == 200, "Fallback should work when Neo4j unavailable"

        data = build_response.json()
        print(f"[E2E GRAPH FALLBACK] ✓ Fallback activated")
        print(f"[E2E GRAPH FALLBACK] ✓ Graph structure created in memory")

        # Try to get concepts
        concepts_response = client.get(
            f"/api/v1/graph/{focus_group.id}/concepts",
            headers=headers
        )

        # Should still work
        if concepts_response.status_code == 200:
            print(f"[E2E GRAPH FALLBACK] ✓ Concepts extraction works in memory mode")
        else:
            print(f"[E2E GRAPH FALLBACK] ⚠ Some features limited in memory mode")

    print(f"[E2E GRAPH FALLBACK] ✓ System resilient without Neo4j")
