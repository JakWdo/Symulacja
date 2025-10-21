"""Testy dla analityki grafowej (Graph Analytics).

Ten moduł testuje zaawansowane analizy grafu wiedzy:
- Key concepts extraction (frequency, sentiment)
- Controversial concepts (high polarization)
- Influential personas (PageRank-like)
- Emotion distribution
- Trait-opinion correlations
- Natural language queries (answer_question)

Dokumentacja: app/services/graph_service.py (metody get_*)
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from statistics import mean, pstdev


class TestKeyConceptsExtraction:
    """Testy dla ekstrakcji kluczowych konceptów."""

    async def test_get_key_concepts_returns_top_concepts(
        self, graph_service_with_mocks, db_session
    ):
        """
        Test: get_key_concepts zwraca top 10 concepts sorted by frequency.

        Returns:
        [
            {
                "name": "Quality",
                "frequency": 15,
                "sentiment": 0.7,
                "personas": ["Anna", "Bob", ...]
            }
        ]
        """
        service = await graph_service_with_mocks
        service.driver = None  # Use memory fallback

        # Populate memory cache with test data
        focus_group_id = "fg123"
        GraphService._memory_metrics_cache[focus_group_id] = {
            "concept_aggregates": {
                "Quality": {
                    "mentions": 15,
                    "sentiments": [0.7, 0.8, 0.6],
                    "personas": {"p1", "p2", "p3"}
                },
                "Design": {
                    "mentions": 10,
                    "sentiments": [0.5, 0.6],
                    "personas": {"p1", "p4"}
                },
                "Price": {
                    "mentions": 8,
                    "sentiments": [-0.3, -0.2],
                    "personas": {"p2"}
                }
            },
            "persona_metadata": {
                "p1": {"name": "Anna"},
                "p2": {"name": "Bob"},
                "p3": {"name": "Carol"},
                "p4": {"name": "David"}
            }
        }

        # Execute
        concepts = await service.get_key_concepts(focus_group_id, db=db_session)

        # Verify
        assert len(concepts) >= 2
        assert concepts[0]["name"] == "Quality"  # Highest frequency
        assert concepts[0]["frequency"] == 15
        assert concepts[0]["sentiment"] == mean([0.7, 0.8, 0.6])
        assert len(concepts[0]["personas"]) == 3

    async def test_key_concepts_sorted_by_frequency(
        self, graph_service_with_mocks, db_session
    ):
        """
        Test: Key concepts są sorted descending by frequency.

        Najpopularniejsze koncepty na początku.
        """
        service = await graph_service_with_mocks
        service.driver = None

        focus_group_id = "fg123"
        GraphService._memory_metrics_cache[focus_group_id] = {
            "concept_aggregates": {
                "A": {"mentions": 5, "sentiments": [0.5], "personas": set()},
                "B": {"mentions": 20, "sentiments": [0.5], "personas": set()},
                "C": {"mentions": 10, "sentiments": [0.5], "personas": set()}
            },
            "persona_metadata": {}
        }

        concepts = await service.get_key_concepts(focus_group_id, db=db_session)

        # Verify sorting
        frequencies = [c["frequency"] for c in concepts]
        assert frequencies == sorted(frequencies, reverse=True)
        assert concepts[0]["name"] == "B"  # Highest (20)


class TestControversialConcepts:
    """Testy dla identyfikacji kontrowersyjnych konceptów."""

    async def test_get_controversial_concepts_high_polarization(
        self, graph_service_with_mocks, db_session
    ):
        """
        Test: Controversial concepts mają high sentiment variance (std dev > 0.4).

        Polarization = standard deviation of sentiments.
        Controversial = jedni kochają, inni nienawidzą (high variance).
        """
        service = await graph_service_with_mocks
        service.driver = None

        focus_group_id = "fg123"
        GraphService._memory_metrics_cache[focus_group_id] = {
            "concept_aggregates": {
                "Price": {
                    "mentions": 5,
                    "sentiments": [0.9, -0.8, 0.7, -0.9, 0.8],  # High variance
                    "personas": {"p1", "p2", "p3"}
                },
                "Quality": {
                    "mentions": 5,
                    "sentiments": [0.7, 0.8, 0.6, 0.7, 0.75],  # Low variance
                    "personas": {"p1", "p2"}
                }
            },
            "persona_concepts": {
                "p1": {"Price": [0.9], "Quality": [0.7]},
                "p2": {"Price": [-0.8], "Quality": [0.8]},
                "p3": {"Price": [0.7], "Quality": [0.6]}
            },
            "persona_metadata": {
                "p1": {"name": "Anna"},
                "p2": {"name": "Bob"},
                "p3": {"name": "Carol"}
            }
        }

        # Execute
        controversial = await service.get_controversial_concepts(
            focus_group_id, db=db_session
        )

        # Verify
        assert len(controversial) >= 1
        # Price powinno być pierwsze (highest polarization)
        price_concept = next(c for c in controversial if c["concept"] == "Price")
        assert price_concept["polarization"] > 0.4
        assert len(price_concept["supporters"]) > 0
        assert len(price_concept["critics"]) > 0

    async def test_controversial_concepts_supporters_vs_critics(
        self, graph_service_with_mocks, db_session
    ):
        """
        Test: Controversial concepts mają identified supporters i critics.

        Supporters: personas z sentiment > 0.5
        Critics: personas z sentiment < -0.3
        """
        service = await graph_service_with_mocks
        service.driver = None

        focus_group_id = "fg123"
        GraphService._memory_metrics_cache[focus_group_id] = {
            "concept_aggregates": {
                "Feature": {
                    "mentions": 4,
                    "sentiments": [0.9, 0.8, -0.7, -0.6],
                    "personas": {"p1", "p2", "p3", "p4"}
                }
            },
            "persona_concepts": {
                "p1": {"Feature": [0.9]},  # Supporter
                "p2": {"Feature": [0.8]},  # Supporter
                "p3": {"Feature": [-0.7]},  # Critic
                "p4": {"Feature": [-0.6]}   # Critic
            },
            "persona_metadata": {
                "p1": {"name": "Anna"},
                "p2": {"name": "Bob"},
                "p3": {"name": "Carol"},
                "p4": {"name": "David"}
            }
        }

        controversial = await service.get_controversial_concepts(
            focus_group_id, db=db_session
        )

        feature_concept = controversial[0]
        assert len(feature_concept["supporters"]) == 2  # Anna, Bob
        assert len(feature_concept["critics"]) == 2  # Carol, David

    async def test_controversial_concepts_min_mentions_filter(
        self, graph_service_with_mocks, db_session
    ):
        """
        Test: Controversial concepts wymagają min 3 mentions.

        Edge case: Concept z 1-2 mentions nie jest controversial (za mało danych).
        """
        service = await graph_service_with_mocks
        service.driver = None

        focus_group_id = "fg123"
        GraphService._memory_metrics_cache[focus_group_id] = {
            "concept_aggregates": {
                "RareConcept": {
                    "mentions": 2,
                    "sentiments": [0.9, -0.9],  # High variance but tylko 2 mentions
                    "personas": {"p1", "p2"}
                }
            },
            "persona_concepts": {},
            "persona_metadata": {}
        }

        controversial = await service.get_controversial_concepts(
            focus_group_id, db=db_session
        )

        # Verify: RareConcept nie powinno być w wynikach (< 3 mentions)
        assert len(controversial) == 0


class TestInfluentialPersonas:
    """Testy dla identyfikacji wpływowych person."""

    async def test_get_influential_personas_by_connections(
        self, graph_service_with_mocks, db_session
    ):
        """
        Test: Influential personas mają most connections w grafie.

        Connections = concept mentions + emotion expressions + persona edges.
        Influence score = min(100, connections * 5)
        """
        service = await graph_service_with_mocks
        service.driver = None

        focus_group_id = "fg123"
        GraphService._memory_metrics_cache[focus_group_id] = {
            "persona_metadata": {
                "p1": {"name": "Anna", "age": 30},
                "p2": {"name": "Bob", "age": 40},
                "p3": {"name": "Carol", "age": 25}
            },
            "persona_connections": {
                "p1": 20,  # Most connections
                "p2": 10,
                "p3": 5
            },
            "persona_sentiments": {
                "p1": 0.7,
                "p2": 0.5,
                "p3": 0.3
            }
        }

        # Execute
        influential = await service.get_influential_personas(
            focus_group_id, db=db_session
        )

        # Verify
        assert len(influential) >= 2
        # Anna powinna być pierwsza (most connections)
        assert influential[0]["name"] == "Anna"
        assert influential[0]["connections"] == 20
        assert influential[0]["influence"] == min(100, 20 * 5)

    async def test_influential_personas_sorted_by_influence(
        self, graph_service_with_mocks, db_session
    ):
        """
        Test: Influential personas są sorted descending by influence score.
        """
        service = await graph_service_with_mocks
        service.driver = None

        focus_group_id = "fg123"
        GraphService._memory_metrics_cache[focus_group_id] = {
            "persona_metadata": {
                "p1": {"name": "A"},
                "p2": {"name": "B"},
                "p3": {"name": "C"}
            },
            "persona_connections": {"p1": 5, "p2": 15, "p3": 10},
            "persona_sentiments": {"p1": 0.5, "p2": 0.5, "p3": 0.5}
        }

        influential = await service.get_influential_personas(
            focus_group_id, db=db_session
        )

        # Verify: B → C → A (sorted by connections)
        assert influential[0]["name"] == "B"
        assert influential[1]["name"] == "C"
        assert influential[2]["name"] == "A"


class TestEmotionDistribution:
    """Testy dla rozkładu emocji w dyskusji."""

    async def test_get_emotion_distribution(
        self, graph_service_with_mocks, db_session
    ):
        """
        Test: get_emotion_distribution zwraca distribution emocji.

        Returns:
        [
            {
                "emotion": "Satisfied",
                "personas_count": 3,
                "avg_intensity": 0.75,
                "percentage": 60.0
            }
        ]
        """
        service = await graph_service_with_mocks
        service.driver = None

        focus_group_id = "fg123"
        GraphService._memory_metrics_cache[focus_group_id] = {
            "emotion_aggregates": {
                "Satisfied": {
                    "count": 10,
                    "intensities": [0.7, 0.8, 0.75],
                    "personas": {"p1", "p2", "p3"}
                },
                "Excited": {
                    "count": 5,
                    "intensities": [0.9, 0.85],
                    "personas": {"p1", "p4"}
                }
            }
        }

        # Execute
        distribution = await service.get_emotion_distribution(
            focus_group_id, db=db_session
        )

        # Verify
        assert len(distribution) == 2
        satisfied = next(e for e in distribution if e["emotion"] == "Satisfied")
        assert satisfied["personas_count"] == 3
        assert satisfied["avg_intensity"] == mean([0.7, 0.8, 0.75])
        assert satisfied["percentage"] == (3 / (3 + 2)) * 100  # 60%

    async def test_emotion_distribution_percentage_calculation(
        self, graph_service_with_mocks, db_session
    ):
        """
        Test: Emotion percentage calculation.

        Percentage = (personas_count for emotion / total_personas) * 100
        """
        service = await graph_service_with_mocks
        service.driver = None

        focus_group_id = "fg123"
        GraphService._memory_metrics_cache[focus_group_id] = {
            "emotion_aggregates": {
                "Satisfied": {
                    "count": 1,
                    "intensities": [0.5],
                    "personas": {"p1", "p2"}  # 2 personas
                },
                "Frustrated": {
                    "count": 1,
                    "intensities": [0.3],
                    "personas": {"p3"}  # 1 persona
                }
            }
        }

        distribution = await service.get_emotion_distribution(
            focus_group_id, db=db_session
        )

        # Total personas = 3 (p1, p2, p3)
        satisfied = next(e for e in distribution if e["emotion"] == "Satisfied")
        frustrated = next(e for e in distribution if e["emotion"] == "Frustrated")

        assert satisfied["percentage"] == pytest.approx((2/3) * 100, rel=0.01)  # ~66.7%
        assert frustrated["percentage"] == pytest.approx((1/3) * 100, rel=0.01)  # ~33.3%


class TestTraitOpinionCorrelations:
    """Testy dla korelacji między cechami demograficznymi a opiniami."""

    async def test_get_trait_opinion_correlations_by_age(
        self, graph_service_with_mocks, db_session
    ):
        """
        Test: Korelacje pokazują różnice w opiniach między grupami wiekowymi.

        Age groups:
        - young (<30): avg sentiment dla concept
        - mid (30-50): avg sentiment
        - senior (50+): avg sentiment

        Age gap = |young_sentiment - senior_sentiment|
        Significant jeśli age_gap > 0.3
        """
        service = await graph_service_with_mocks
        service.driver = None

        focus_group_id = "fg123"
        GraphService._memory_metrics_cache[focus_group_id] = {
            "concept_aggregates": {
                "Innovation": {
                    "mentions": 5,
                    "sentiments": [0.9, 0.8, -0.3, -0.4, 0.5],
                    "personas": {"p1", "p2", "p3", "p4", "p5"}
                }
            },
            "persona_concepts": {
                "p1": {"Innovation": [0.9]},  # Young (25)
                "p2": {"Innovation": [0.8]},  # Young (28)
                "p3": {"Innovation": [-0.3]},  # Senior (55)
                "p4": {"Innovation": [-0.4]},  # Senior (60)
                "p5": {"Innovation": [0.5]}   # Mid (40)
            },
            "persona_metadata": {
                "p1": {"name": "Anna", "age": 25},
                "p2": {"name": "Bob", "age": 28},
                "p3": {"name": "Carol", "age": 55},
                "p4": {"name": "David", "age": 60},
                "p5": {"name": "Eve", "age": 40}
            }
        }

        # Execute
        correlations = await service.get_trait_opinion_correlations(
            focus_group_id, db=db_session
        )

        # Verify
        assert len(correlations) >= 1
        innovation_corr = correlations[0]
        assert innovation_corr["concept"] == "Innovation"

        # Young sentiment = (0.9 + 0.8) / 2 = 0.85
        # Senior sentiment = (-0.3 + -0.4) / 2 = -0.35
        # Age gap = |0.85 - (-0.35)| = 1.2
        assert innovation_corr["age_gap"] > 0.3
        assert innovation_corr["young_sentiment"] > 0.5
        assert innovation_corr["senior_sentiment"] < 0.0

    async def test_trait_correlations_min_mentions_filter(
        self, graph_service_with_mocks, db_session
    ):
        """
        Test: Korelacje wymagają min 3 mentions.

        Edge case: Concept z 1-2 mentions nie jest reliable dla correlation.
        """
        service = await graph_service_with_mocks
        service.driver = None

        focus_group_id = "fg123"
        GraphService._memory_metrics_cache[focus_group_id] = {
            "concept_aggregates": {
                "RareConcept": {
                    "mentions": 2,  # Too few
                    "sentiments": [0.9, -0.9],
                    "personas": {"p1", "p2"}
                }
            },
            "persona_concepts": {},
            "persona_metadata": {}
        }

        correlations = await service.get_trait_opinion_correlations(
            focus_group_id, db=db_session
        )

        # Verify: RareConcept nie powinno być w wynikach
        assert len(correlations) == 0


class TestNaturalLanguageQueries:
    """Testy dla answer_question (natural language interface)."""

    async def test_answer_question_about_influence(
        self, graph_service_with_mocks, db_session
    ):
        """
        Test: Query "Who influences the most?" zwraca influential personas.

        Heuristics: Detect keywords "who", "influence", "influential"
        → Call get_influential_personas()
        """
        service = await graph_service_with_mocks
        service.driver = None

        focus_group_id = "fg123"
        GraphService._memory_metrics_cache[focus_group_id] = {
            "persona_metadata": {"p1": {"name": "Anna"}},
            "persona_connections": {"p1": 15},
            "persona_sentiments": {"p1": 0.7}
        }

        # Execute
        result = await service.answer_question(
            focus_group_id,
            "Who influences others the most?",
            db=db_session
        )

        # Verify
        assert "answer" in result
        assert "insights" in result
        assert "Anna" in result["answer"]  # Most influential
        assert "influence" in result["answer"].lower()

    async def test_answer_question_about_controversial_topics(
        self, graph_service_with_mocks, db_session
    ):
        """
        Test: Query "controversial topics" zwraca polarized concepts.

        Heuristics: Keywords "controversial", "disagree", "polarized"
        → Call get_controversial_concepts()
        """
        service = await graph_service_with_mocks
        service.driver = None

        focus_group_id = "fg123"
        GraphService._memory_metrics_cache[focus_group_id] = {
            "concept_aggregates": {
                "Price": {
                    "mentions": 5,
                    "sentiments": [0.9, -0.8, 0.7, -0.9],
                    "personas": {"p1", "p2", "p3"}
                }
            },
            "persona_concepts": {
                "p1": {"Price": [0.9]},
                "p2": {"Price": [-0.8]},
                "p3": {"Price": [0.7]}
            },
            "persona_metadata": {
                "p1": {"name": "Anna"},
                "p2": {"name": "Bob"},
                "p3": {"name": "Carol"}
            }
        }

        result = await service.answer_question(
            focus_group_id,
            "Show me controversial topics",
            db=db_session
        )

        # Verify
        assert "Price" in result["answer"]  # Controversial concept
        assert "polariz" in result["answer"].lower() or "controvers" in result["answer"].lower()

    async def test_answer_question_about_emotions(
        self, graph_service_with_mocks, db_session
    ):
        """
        Test: Query "emotions" zwraca emotion distribution.

        Heuristics: Keywords "emotion", "feel", "feeling"
        → Call get_emotion_distribution()
        """
        service = await graph_service_with_mocks
        service.driver = None

        focus_group_id = "fg123"
        GraphService._memory_metrics_cache[focus_group_id] = {
            "emotion_aggregates": {
                "Satisfied": {
                    "count": 5,
                    "intensities": [0.7],
                    "personas": {"p1", "p2"}
                }
            },
            "persona_metadata": {},
            "persona_concepts": {},
            "persona_emotions": {}
        }

        result = await service.answer_question(
            focus_group_id,
            "Which emotions dominate?",
            db=db_session
        )

        # Verify
        assert "Satisfied" in result["answer"]
        assert "emotion" in result["answer"].lower()

    async def test_answer_question_default_summary(
        self, graph_service_with_mocks, db_session
    ):
        """
        Test: Generic query zwraca comprehensive summary.

        Fallback jeśli query nie pasuje do żadnej heurystyki:
        - Top concept
        - Most influential persona
        - Any negative concepts (risks)
        """
        service = await graph_service_with_mocks
        service.driver = None

        focus_group_id = "fg123"
        GraphService._memory_metrics_cache[focus_group_id] = {
            "concept_aggregates": {
                "Quality": {"mentions": 10, "sentiments": [0.7], "personas": set()}
            },
            "persona_metadata": {"p1": {"name": "Anna"}},
            "persona_connections": {"p1": 10},
            "persona_sentiments": {"p1": 0.7},
            "persona_concepts": {},
            "persona_emotions": {}
        }

        result = await service.answer_question(
            focus_group_id,
            "Tell me about this focus group",
            db=db_session
        )

        # Verify: Summary zawiera key insights
        assert "answer" in result
        assert len(result["answer"]) > 50  # Non-trivial answer


class TestNeo4jVsMemoryConsistency:
    """Testy consistency między Neo4j a memory analytics."""

    async def test_analytics_results_consistent_neo4j_vs_memory(
        self, graph_service_with_mocks, db_session
    ):
        """
        Test: Wyniki analytics są consistent między Neo4j i memory.

        Gdy Neo4j unavailable, memory fallback powinien zwrócić
        te same results (dla tych samych danych).
        """
        service = await graph_service_with_mocks

        # Populate memory with test data
        focus_group_id = "fg123"
        test_data = {
            "concept_aggregates": {
                "Quality": {"mentions": 5, "sentiments": [0.7], "personas": set()}
            },
            "persona_metadata": {"p1": {"name": "Test"}},
            "persona_connections": {"p1": 5},
            "persona_sentiments": {"p1": 0.5}
        }
        GraphService._memory_metrics_cache[focus_group_id] = test_data

        # Get results with memory fallback
        service.driver = None
        memory_results = await service.get_key_concepts(focus_group_id, db=db_session)

        # Verify: Sensible results
        assert len(memory_results) > 0
        assert memory_results[0]["name"] == "Quality"

    async def test_empty_graph_edge_case(
        self, graph_service_with_mocks, db_session
    ):
        """
        Test: Analytics działa gracefully dla empty graph.

        Edge case: Focus group bez responses (empty graph).
        Nie powinno crashnąć, zwrócić puste wyniki.
        """
        service = await graph_service_with_mocks
        service.driver = None

        focus_group_id = "empty_fg"
        GraphService._memory_metrics_cache[focus_group_id] = {
            "concept_aggregates": {},
            "persona_metadata": {},
            "persona_connections": {},
            "persona_sentiments": {}
        }

        # Execute all analytics
        concepts = await service.get_key_concepts(focus_group_id, db=db_session)
        controversial = await service.get_controversial_concepts(focus_group_id, db=db_session)
        influential = await service.get_influential_personas(focus_group_id, db=db_session)
        emotions = await service.get_emotion_distribution(focus_group_id, db=db_session)

        # Verify: All return empty but valid structures
        assert concepts == []
        assert controversial == []
        assert influential == []
        assert emotions == []
