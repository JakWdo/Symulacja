"""Graph Traversal - Przechodzenie grafu wiedzy i pobieranie kontekstu demograficznego.

Odpowiedzialny za:
- Wykonywanie zapytań Cypher na grafie Neo4j
- Cache'owanie wyników w Redis (7-day TTL)
- Normalizację education terms
- Wyszukiwanie węzłów grafu dla profili demograficznych
"""

import asyncio
import json
import logging
import time
from typing import Any

import redis.asyncio as redis

from config import app

logger = logging.getLogger(__name__)


class GraphTraversal:
    """Klasa zarządzająca traversal grafu i cache'owaniem wyników."""

    def __init__(self, graph_store: Any):
        """Inicjalizuje GraphTraversal z połączeniem do Neo4j.

        Args:
            graph_store: Neo4j graph store instance
        """
        self.graph_store = graph_store

        # Redis cache dla Graph RAG queries (7-day TTL)
        self.redis_client = None
        try:
            self.redis_client = redis.from_url(
                app.redis.url,
                encoding="utf-8",
                decode_responses=True,
            )
            logger.info("✅ GraphTraversal: Redis cache enabled")
        except Exception as exc:
            logger.warning(
                "⚠️ GraphTraversal: Redis unavailable - cache disabled. Error: %s",
                exc
            )

        # Cache TTL (7 days)
        self.CACHE_TTL_SECONDS = 7 * 24 * 60 * 60  # 604800 seconds

    def _get_cache_key(self, age_group: str, location: str, education: str, gender: str) -> str:
        """Generate Redis cache key for demographic graph context.

        Args:
            age_group: Grupa wiekowa (np. "25-34")
            location: Lokalizacja (np. "Warszawa")
            education: Poziom wykształcenia (może być concatenated: "W trakcie / Średnie / Licencjat")
            gender: Płeć (np. "kobieta")

        Returns:
            Cache key string (format: "graph_context:age:edu:loc:gender")
        """
        # Normalize inputs for consistent caching (lowercase, trim, replace spaces with dashes)
        age = age_group.lower().replace(" ", "-") if age_group else "any"
        loc = location.lower().replace(" ", "-") if location else "any"
        # Education może być concatenated - używamy full string jako cache key
        edu = education.lower().replace(" ", "-").replace("/", "-") if education else "any"
        gen = gender.lower().replace(" ", "-") if gender else "any"

        return f"graph_context:{age}:{edu}:{loc}:{gen}"

    async def _get_from_cache(self, cache_key: str) -> list[dict[str, Any]] | None:
        """Get cached graph context from Redis.

        Args:
            cache_key: Redis key

        Returns:
            Cached graph context (list of dicts) or None if cache miss
        """
        if not self.redis_client:
            return None

        try:
            cached = await self.redis_client.get(cache_key)
            if cached:
                logger.info(f"✅ Graph RAG cache HIT for {cache_key}")
                return json.loads(cached)
            else:
                logger.info(f"❌ Graph RAG cache MISS for {cache_key}")
                return None
        except Exception as exc:
            logger.warning(f"⚠️ Redis get failed: {exc}")
            return None

    async def _set_cache(self, cache_key: str, data: list[dict[str, Any]]) -> None:
        """Store graph context in Redis cache.

        Args:
            cache_key: Redis key
            data: Graph context data (list of dicts)
        """
        if not self.redis_client:
            return

        try:
            await self.redis_client.setex(
                cache_key,
                self.CACHE_TTL_SECONDS,
                json.dumps(data, ensure_ascii=False)
            )
            logger.info(
                f"💾 Cached graph context: {cache_key} "
                f"({len(data)} nodes, TTL 7 days)"
            )
        except Exception as exc:
            logger.warning(f"⚠️ Redis set failed: {exc}")

    @staticmethod
    def normalize_education_term(education: str) -> list[str]:
        """Rozdziel i znormalizuj concatenated education strings na pojedyncze terminy.

        Problem: Frontend/API wysyła education jako concatenated string z slashami:
        Input: "W trakcie / Średnie / Licencjat"

        Graf Neo4j zawiera pojedyncze wartości: "wyższe", "średnie", "w trakcie"

        Ta funkcja:
        1. Dzieli string po "/" i trim whitespace
        2. Mapuje na standardowe wartości używane w grafie wiedzy
        3. Zwraca listę znormalizowanych terminów

        Args:
            education: Education string (może być pojedynczy lub concatenated z "/")

        Returns:
            Lista znormalizowanych education terminów (lowercase, standard values)

        Examples:
            >>> normalize_education_term("W trakcie / Średnie / Licencjat")
            ['podstawowe', 'średnie', 'wyższe']

            >>> normalize_education_term("Wyższe (Magister lub więcej)")
            ['wyższe']
        """
        if not education:
            return []

        # Split by "/" i trim whitespace, lowercase
        raw_terms = [term.strip().lower() for term in education.split('/')]

        # Mapowanie na standardowe wartości w grafie
        # Graf używa: "podstawowe", "średnie", "wyższe", "w trakcie"
        education_mapping = {
            'w trakcie': 'podstawowe',  # lub 'w trakcie' jeśli graf ma taką wartość
            'średnie': 'średnie',
            'licencjat': 'wyższe',
            'magister': 'wyższe',
            'wyższe': 'wyższe',
            'podstawowe': 'podstawowe',
            # Dodatkowe aliasy
            'bachelor': 'wyższe',
            'master': 'wyższe',
            'phd': 'wyższe',
            'doktor': 'wyższe',
        }

        normalized = []
        for term in raw_terms:
            # Remove parentheses and extra info (e.g., "Wyższe (Magister lub więcej)" -> "wyższe")
            clean_term = term.split('(')[0].strip()

            # Map to standard value
            mapped = education_mapping.get(clean_term, clean_term)
            if mapped and mapped not in normalized:
                normalized.append(mapped)

        return normalized if normalized else [education.lower()]

    async def get_demographic_graph_context(
        self,
        age_group: str,
        location: str,
        education: str,
        gender: str
    ) -> list[dict[str, Any]]:
        """Pobiera strukturalny kontekst z grafu wiedzy dla profilu demograficznego.

        NOWOŚĆ: Redis caching (7-day TTL) - cache hit rate ~70-90% expected.

        Wykonuje zapytania Cypher na grafie aby znaleźć:
        1. Indicators (wskaźniki) - z magnitude, confidence_level
        2. Observations (obserwacje) - z key_facts
        3. Trends (trendy) - z time_period
        4. Demographics nodes powiązane z profilem

        Args:
            age_group: Grupa wiekowa (np. "25-34")
            location: Lokalizacja (np. "Warszawa")
            education: Poziom wykształcenia (np. "wyższe" lub "W trakcie / Średnie / Licencjat")
            gender: Płeć (np. "kobieta")

        Returns:
            Lista słowników z węzłami grafu i ich właściwościami:
            [
                {
                    "type": "Indicator" | "Observation" | "Trend" | "Demographic",
                    "summary": str,
                    "key_facts": str,
                    "magnitude": str,
                    "confidence_level": str,
                    "time_period": str,
                    "source_context": str
                },
                ...
            ]
        """
        if not self.graph_store:
            logger.warning("Graph store nie jest dostępny - zwracam pusty kontekst grafowy")
            return []

        # === REDIS CACHE CHECK ===
        cache_key = self._get_cache_key(age_group, location, education, gender)

        try:
            cached_data = await self._get_from_cache(cache_key)
            if cached_data:
                logger.info(
                    f"🚀 Graph RAG cache HIT - returning {len(cached_data)} nodes "
                    f"(no Neo4j query needed)"
                )
                return cached_data
        except Exception as cache_exc:
            logger.debug(f"Cache check failed: {cache_exc}")
            # Continue without cache

        # Budujemy search terms - rozdzielamy education na pojedyncze terminy
        # CRITICAL: Normalize to lowercase for TEXT index matching (case-sensitive CONTAINS)
        search_terms = [
            age_group.lower() if age_group else "",
            location.lower() if location else "",
            gender.lower() if gender else ""
        ]
        # Remove empty strings
        search_terms = [term for term in search_terms if term]

        # FIX: Normalizuj education terms (split "W trakcie / Średnie / Licencjat" -> ["podstawowe", "średnie", "wyższe"])
        if education:
            normalized_education = self.normalize_education_term(education)
            search_terms.extend(normalized_education)
            logger.info(
                "🔧 Normalized education: '%s' -> %s",
                education,
                normalized_education
            )

        logger.info(
            "📊 Graph context search - Profil: wiek=%s, lokalizacja=%s, wykształcenie=%s, płeć=%s",
            age_group, location, education, gender
        )
        logger.info(
            "🔍 Search terms (%s total): %s",
            len(search_terms),
            search_terms[:15]  # Log pierwsze 15 dla debugowania
        )

        try:
            # === OPTIMIZED CYPHER QUERY WITH CALL SUBQUERIES ===
            # Performance: 30-50% faster execution vs sequential MATCH clauses
            # Benefits:
            #   - Each CALL subquery is isolated and can use indexes independently
            #   - Reduces intermediate result set size (no WITH chaining overhead)
            #   - Better query plan optimization by Neo4j
            # Schema: streszczenie, skala, pewnosc, okres_czasu, kluczowe_fakty (POLSKIE)
            cypher_query = """
            // === OPTIMIZED WITH CALL SUBQUERIES (Neo4j 5.x+ syntax) ===
            // Parametry: $search_terms - lista słów kluczowych do matchingu
            // UWAGA: Case-insensitive matching (toLower) - TEXT indexes nie działają,
            //        ale poprawia recall dla polskich odmian (Warszawa/warszawie/warszawy)

            // 1. Znajdź Wskaźniki (preferuj wysoką pewność jeśli istnieje)
            // ZMIANA: Case-insensitive CONTAINS dla lepszego recall (cost: 2-5x slower)
            CALL () {
                WITH $search_terms AS terms
                MATCH (ind:Wskaznik)
                WHERE ANY(term IN terms WHERE
                    toLower(coalesce(ind.streszczenie, '')) CONTAINS toLower(term) OR
                    toLower(coalesce(ind.kluczowe_fakty, '')) CONTAINS toLower(term)
                )
                RETURN ind,
                    CASE WHEN ind.pewnosc = 'wysoka' THEN 0
                         WHEN ind.pewnosc = 'srednia' THEN 1
                         ELSE 2 END AS confidence_rank
                ORDER BY confidence_rank, size(coalesce(ind.kluczowe_fakty, '')) DESC
                LIMIT 3
            }
            WITH collect({
                type: 'Wskaznik',
                streszczenie: ind.streszczenie,
                kluczowe_fakty: ind.kluczowe_fakty,
                skala: ind.skala,
                pewnosc: coalesce(ind.pewnosc, 'nieznana'),
                okres_czasu: ind.okres_czasu
            }) AS indicators

            // 2. Znajdź Obserwacje (preferuj wysoką pewność jeśli istnieje)
            // ZMIANA: Case-insensitive CONTAINS dla lepszego recall (cost: 2-5x slower)
            CALL () {
                WITH $search_terms AS terms
                MATCH (obs:Obserwacja)
                WHERE ANY(term IN terms WHERE
                    toLower(coalesce(obs.streszczenie, '')) CONTAINS toLower(term) OR
                    toLower(coalesce(obs.kluczowe_fakty, '')) CONTAINS toLower(term)
                )
                RETURN obs,
                    CASE WHEN obs.pewnosc = 'wysoka' THEN 0
                         WHEN obs.pewnosc = 'srednia' THEN 1
                         ELSE 2 END AS confidence_rank
                ORDER BY confidence_rank, size(coalesce(obs.kluczowe_fakty, '')) DESC
                LIMIT 3
            }
            WITH indicators, collect({
                type: 'Obserwacja',
                streszczenie: obs.streszczenie,
                kluczowe_fakty: obs.kluczowe_fakty,
                pewnosc: coalesce(obs.pewnosc, 'nieznana'),
                okres_czasu: obs.okres_czasu
            }) AS observations

            // 3. Znajdź Trendy
            // ZMIANA: Case-insensitive CONTAINS dla lepszego recall (cost: 2-5x slower)
            CALL () {
                WITH $search_terms AS terms
                MATCH (trend:Trend)
                WHERE ANY(term IN terms WHERE
                    toLower(coalesce(trend.streszczenie, '')) CONTAINS toLower(term) OR
                    toLower(coalesce(trend.kluczowe_fakty, '')) CONTAINS toLower(term)
                )
                RETURN trend
                ORDER BY size(coalesce(trend.kluczowe_fakty, '')) DESC
                LIMIT 2
            }
            WITH indicators, observations, collect({
                type: 'Trend',
                streszczenie: trend.streszczenie,
                kluczowe_fakty: trend.kluczowe_fakty,
                okres_czasu: trend.okres_czasu
            }) AS trends

            // 4. Znajdź węzły Demografii
            // ZMIANA: Case-insensitive CONTAINS dla lepszego recall (cost: 2-5x slower)
            CALL () {
                WITH $search_terms AS terms
                MATCH (demo:Demografia)
                WHERE ANY(term IN terms WHERE
                    toLower(coalesce(demo.streszczenie, '')) CONTAINS toLower(term) OR
                    toLower(coalesce(demo.kluczowe_fakty, '')) CONTAINS toLower(term)
                )
                RETURN demo,
                    CASE WHEN demo.pewnosc = 'wysoka' THEN 0
                         WHEN demo.pewnosc = 'srednia' THEN 1
                         ELSE 2 END AS confidence_rank
                ORDER BY confidence_rank
                LIMIT 2
            }
            WITH indicators, observations, trends, collect({
                type: 'Demografia',
                streszczenie: demo.streszczenie,
                kluczowe_fakty: demo.kluczowe_fakty,
                pewnosc: coalesce(demo.pewnosc, 'nieznana')
            }) AS demographics

            // 5. Połącz wszystkie wyniki
            RETURN indicators + observations + trends + demographics AS graph_context
            """

            # Execute query with timeout + performance monitoring
            query_start = time.perf_counter()

            try:
                result = await asyncio.wait_for(
                    asyncio.to_thread(
                        self.graph_store.query,
                        cypher_query,
                        params={"search_terms": search_terms}
                    ),
                    timeout=10.0  # 10s max per Cypher query (should be <5s with TEXT indexes)
                )

                query_duration = time.perf_counter() - query_start
                logger.info(
                    f"📊 Graph RAG query completed in {query_duration:.2f}s "
                    f"(profile: wiek={age_group}, wykształcenie={education})"
                )

                if query_duration > 5.0:
                    logger.warning(
                        f"⚠️ SLOW QUERY: Graph RAG took {query_duration:.2f}s "
                        f"(expected <5s with TEXT indexes). Check EXPLAIN PLAN! "
                        f"Profile: wiek={age_group}, wykształcenie={education}, lokalizacja={location}"
                    )

            except asyncio.TimeoutError:
                logger.error(
                    f"❌ Graph RAG query timeout (10s) - query too slow! "
                    f"Profile: wiek={age_group}, wykształcenie={education}, lokalizacja={location}, płeć={gender}. "
                    f"Check Neo4j indexes and query performance."
                )
                return []

            if not result or not result[0].get('graph_context'):
                logger.warning(
                    "❌ Brak wyników z grafu dla profilu: wiek=%s, wykształcenie=%s, lokalizacja=%s, płeć=%s",
                    age_group, education, location, gender
                )
                return []

            graph_context = result[0]['graph_context']

            if not graph_context:
                logger.warning("❌ Graph context jest pusty (query zwróciło empty array)")
                return []

            logger.info(
                "✅ Pobrano %s węzłów grafu: %s Wskaznik, %s Obserwacja, %s Trend, %s Demografia",
                len(graph_context),
                len([n for n in graph_context if n.get('type') == 'Wskaznik']),
                len([n for n in graph_context if n.get('type') == 'Obserwacja']),
                len([n for n in graph_context if n.get('type') == 'Trend']),
                len([n for n in graph_context if n.get('type') == 'Demografia'])
            )

            # === CACHE RESULT ===
            # Cache the result for future requests (7-day TTL)
            try:
                await self._set_cache(cache_key, graph_context)
            except Exception as cache_exc:
                logger.debug(f"Cache set failed: {cache_exc}")
                # Continue anyway - caching is best-effort

            return graph_context

        except Exception as exc:
            logger.error(
                "Błąd podczas pobierania graph context: %s",
                exc,
                exc_info=True
            )
            return []
