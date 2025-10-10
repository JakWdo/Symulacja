"""
Serwis Analizy Grafowej oparty na Neo4j

Zarządza grafem wiedzy łączącym persony, koncepcje i emocje.
Umożliwia analizę relacji między uczestnikami focus groups i ich opiniami.
"""

from typing import List, Dict, Any, Optional, Tuple, Iterable
from datetime import datetime
from collections import Counter, defaultdict
from statistics import mean, pstdev, StatisticsError
import logging
import json
import re

from neo4j import AsyncGraphDatabase, AsyncDriver
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.models import PersonaResponse, Persona, FocusGroup

settings = get_settings()
logger = logging.getLogger(__name__)

STOPWORDS = {
    "the", "and", "for", "with", "that", "from", "this", "have", "will", "your",
    "about", "there", "which", "their", "would", "could", "should", "much",
    "very", "just", "when", "they", "them", "what", "like", "been", "were",
    "being", "into", "than", "then", "because", "while", "after", "before",
    "need", "more", "also", "really", "maybe", "even", "some", "make", "made",
    "still", "does", "done", "cant", "don't", "cant", "can't", "didnt", "didn't",
    "its", "it's", "im", "i'm", "but", "our", "ours", "your", "you're", "youre",
    "has", "had", "those", "these", "get", "got", "onto", "per", "each", "most",
    "such", "though", "over", "under", "across", "again", "ever", "seen", "many"
}

EMOTION_KEYWORDS = {
    "Excited": {"excited", "thrilled", "love", "amazing", "awesome", "great"},
    "Satisfied": {"happy", "satisfied", "pleased", "glad", "good", "enjoy"},
    "Concerned": {"concerned", "worried", "uncertain", "hesitant", "doubt"},
    "Frustrated": {"frustrated", "angry", "annoyed", "hate", "upset", "issue", "problem"},
}


# Modele Pydantic opisujące strukturę odpowiedzi LLM
class ConceptExtraction(BaseModel):
    """Strukturalizowane wyniki ekstrakcji konceptów przez LLM"""
    concepts: List[str] = Field(description="Lista kluczowych konceptów/tematów (max 5)")
    emotions: List[str] = Field(description="Lista wykrytych emocji")
    sentiment: float = Field(description="Ogólny sentiment od -1.0 do 1.0")
    key_phrases: List[str] = Field(description="Najważniejsze frazy z wypowiedzi (max 3)")


class GraphService:
    """
    Zarządza grafem wiedzy w Neo4j

    Graf zawiera:
    - Persony (nodes typu :Persona)
    - Koncepcje/tematy (nodes typu :Concept)
    - Emocje (nodes typu :Emotion)
    - Relacje: MENTIONS, AGREES_WITH, DISAGREES_WITH, FEELS
    """

    # Pamięci podręczne w RAM używane, gdy Neo4j jest niedostępny
    _memory_graph_cache: Dict[str, Dict[str, Any]] = {}
    _memory_stats_cache: Dict[str, Dict[str, Any]] = {}
    _memory_metrics_cache: Dict[str, Dict[str, Any]] = {}

    def __init__(self):
        """Inicjalizuj połączenie z Neo4j i LLM do ekstrakcji konceptów"""
        self.driver: Optional[AsyncDriver] = None
        self.settings = settings

        self.llm: Optional[ChatGoogleGenerativeAI] = None
        self.extraction_prompt: Optional[ChatPromptTemplate] = None

        if self.settings.GOOGLE_API_KEY:
            try:
                # Inicjalizujemy model LLM do ekstrakcji konceptów
                self.llm = ChatGoogleGenerativeAI(
                    model=settings.PERSONA_GENERATION_MODEL,  # Szybszy wariant Flash
                    google_api_key=settings.GOOGLE_API_KEY,
                    temperature=0.3,  # Niższa temperatura dla spójnego wydobycia
                    max_tokens=500,
                )

                # Tworzymy szablon promptu do ekstrakcji
                self.extraction_prompt = ChatPromptTemplate.from_messages([
                    ("system", """Jesteś ekspertem od analizy tekstu. Wyekstraktuj z podanej wypowiedzi:
1. Kluczowe koncepty/tematy (max 5) - rzeczowniki lub frazy opisujące główne zagadnienia
2. Emocje wyrażone w tekście (np. 'Satisfied', 'Frustrated', 'Neutral', 'Excited', 'Concerned')
3. Sentiment jako liczba od -1.0 (bardzo negatywny) do 1.0 (bardzo pozytywny)
4. Najważniejsze frazy cytowane bezpośrednio z tekstu (max 3)

Zwróć wynik jako JSON w formacie:
{{
  "concepts": ["koncept1", "koncept2"],
  "emotions": ["emocja1"],
  "sentiment": 0.5,
  "key_phrases": ["fraza1", "fraza2"]
}}

Koncepty powinny być ogólne i wielokrotnego użytku (np. 'Price', 'Usability', 'Design').
Emocje w języku angielskim."""),
                    ("human", "{text}")
                ])
            except Exception as exc:
                logger.warning(
                    "Gemini LLM initialisation failed (%s). Falling back to keyword-only extraction.",
                    exc
                )
                self.llm = None
                self.extraction_prompt = None
        else:
            logger.info(
                "GOOGLE_API_KEY not configured. Graph analysis will use keyword-based extraction."
            )

        # Parser JSON odpowiedzialny za walidację struktury
        self.json_parser = JsonOutputParser(pydantic_object=ConceptExtraction)

    async def connect(self):
        """Nawiąż połączenie z Neo4j"""
        if not self.driver:
            try:
                self.driver = AsyncGraphDatabase.driver(
                    self.settings.NEO4J_URI,
                    auth=(self.settings.NEO4J_USER, self.settings.NEO4J_PASSWORD)
                )
                # Sprawdzamy, czy połączenie działa
                async with self.driver.session() as session:
                    await session.run("RETURN 1")
                logger.info(f"Connected to Neo4j at {self.settings.NEO4J_URI}")
            except Exception as e:
                logger.error(f"Failed to connect to Neo4j at {self.settings.NEO4J_URI}: {e}")
                self.driver = None
                raise ConnectionError(f"Cannot connect to Neo4j: {e}")

    async def close(self):
        """Zamknij połączenie"""
        if self.driver:
            await self.driver.close()
            self.driver = None

    async def build_graph_from_focus_group(
        self,
        db: AsyncSession,
        focus_group_id: str
    ) -> Dict[str, Any]:
        """
        Buduje graf wiedzy z danych focus group

        Proces:
        1. Ładuje wszystkie odpowiedzi z focus group
        2. Tworzy nodes dla person
        3. Ekstraktuje koncepcje/tematy z odpowiedzi (keyword extraction)
        4. Tworzy relationships między personami a konceptami
        5. Analizuje sentiment i tworzy emotion nodes

        Args:
            db: Sesja bazy danych
            focus_group_id: ID grupy fokusowej

        Returns:
            Statystyki: {
                "personas_added": int,
                "concepts_extracted": int,
                "relationships_created": int
            }
        """
        focus_group, responses, personas = await self._load_focus_group_entities(
            db, focus_group_id
        )

        try:
            await self.connect()
            neo4j_available = True
        except ConnectionError:
            neo4j_available = False

        processed = await self._prepare_graph_snapshot(responses, personas)
        stats = processed["stats"]
        graph_data = processed["graph_data"]
        metrics = processed["metrics"]
        entries = processed["entries"]

        if neo4j_available and self.driver:
            async with self.driver.session() as session:
                for persona_id, persona in personas.items():
                    await session.run(
                        """
                        MERGE (p:Persona {id: $id})
                        SET p.name = $name,
                            p.age = $age,
                            p.gender = $gender,
                            p.occupation = $occupation,
                            p.focus_group_id = $focus_group_id,
                            p.updated_at = datetime()
                        """,
                        id=persona_id,
                        name=persona.full_name,
                        age=persona.age,
                        gender=persona.gender,
                        occupation=persona.occupation,
                        focus_group_id=focus_group_id
                    )

                for entry in entries:
                    persona_id = entry["persona_id"]
                    sentiment = entry["sentiment"]

                    for concept in entry["concepts"]:
                        await session.run(
                            """
                            MERGE (c:Concept {name: $name})
                            ON CREATE SET c.frequency = 1, c.created_at = datetime()
                            ON MATCH SET c.frequency = c.frequency + 1
                            """,
                            name=concept
                        )

                        await session.run(
                            """
                            MATCH (p:Persona {id: $persona_id})
                            MATCH (c:Concept {name: $concept})
                            MERGE (p)-[r:MENTIONS]->(c)
                            ON CREATE SET r.count = 1, r.sentiment = $sentiment
                            ON MATCH SET r.count = r.count + 1,
                                         r.sentiment = (r.sentiment + $sentiment) / 2
                            """,
                            persona_id=persona_id,
                            concept=concept,
                            sentiment=sentiment
                        )

                    for emotion in entry["emotions"]:
                        await session.run(
                            """
                            MERGE (e:Emotion {name: $emotion})
                            ON CREATE SET e.count = 1
                            ON MATCH SET e.count = e.count + 1
                            """,
                            emotion=emotion
                        )

                        await session.run(
                            """
                            MATCH (p:Persona {id: $persona_id})
                            MATCH (e:Emotion {name: $emotion})
                            MERGE (p)-[r:FEELS]->(e)
                            ON CREATE SET r.intensity = $intensity
                            ON MATCH SET r.intensity = (r.intensity + $intensity) / 2
                            """,
                            persona_id=persona_id,
                            emotion=emotion,
                            intensity=abs(sentiment)
                        )

                for edge in metrics["persona_edges"]:
                    if edge["type"] == "agrees":
                        await session.run(
                            """
                            MATCH (p1:Persona {id: $p1_id})
                            MATCH (p2:Persona {id: $p2_id})
                            MERGE (p1)-[r:AGREES_WITH]->(p2)
                            SET r.strength = $strength
                            """,
                            p1_id=edge["source"],
                            p2_id=edge["target"],
                            strength=edge["strength"]
                        )
                    else:
                        await session.run(
                            """
                            MATCH (p1:Persona {id: $p1_id})
                            MATCH (p2:Persona {id: $p2_id})
                            MERGE (p1)-[r:DISAGREES_WITH]->(p2)
                            SET r.strength = $strength
                            """,
                            p1_id=edge["source"],
                            p2_id=edge["target"],
                            strength=edge["strength"]
                        )
        else:
            logger.info("Neo4j unavailable. Graph data stored in memory cache.")

        self._memory_graph_cache[focus_group_id] = graph_data
        self._memory_stats_cache[focus_group_id] = stats
        self._memory_metrics_cache[focus_group_id] = metrics

        return stats

    async def get_graph_data(
        self,
        focus_group_id: str,
        filter_type: Optional[str] = None,
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """
        Pobiera dane grafu dla wizualizacji.

        Przy niedostępności Neo4j korzysta z pamięciowego grafu zbudowanego na
        podstawie danych z bazy Postgres.
        """
        try:
            await self.connect()
            neo4j_available = True
        except ConnectionError:
            neo4j_available = False

        if not neo4j_available or not self.driver:
            graph_data, metrics = await self._ensure_memory_graph(
                focus_group_id, db
            )
            if filter_type:
                return self._apply_filter(graph_data, metrics, filter_type)
            return self._copy_graph(graph_data)

        nodes: List[Dict[str, Any]] = []
        links: List[Dict[str, Any]] = []

        async with self.driver.session() as session:
            result = await session.run(
                """
                MATCH (p:Persona {focus_group_id: $focus_group_id})
                OPTIONAL MATCH (p)-[m:MENTIONS]->(c:Concept)
                WITH p, AVG(m.sentiment) as avg_sentiment, COUNT(m) as connections
                RETURN p.id as id, p.name as name, p.age as age,
                       p.occupation as occupation, avg_sentiment, connections
                """,
                focus_group_id=focus_group_id
            )

            async for record in result:
                sentiment = record["avg_sentiment"] or 0.0

                if filter_type == 'positive' and sentiment < 0.6:
                    continue
                if filter_type == 'negative' and sentiment > -0.3:
                    continue

                nodes.append({
                    "id": record["id"],
                    "name": record["name"],
                    "type": "persona",
                    "group": 1,
                    "size": min(20, 10 + record["connections"]),
                    "sentiment": sentiment,
                    "metadata": {
                        "age": record["age"],
                        "occupation": record["occupation"]
                    }
                })

            result = await session.run(
                """
                MATCH (c:Concept)<-[m:MENTIONS]-(p:Persona {focus_group_id: $focus_group_id})
                WITH c, COUNT(m) as mentions, AVG(m.sentiment) as avg_sentiment
                WHERE mentions >= 2
                RETURN c.name as name, mentions, avg_sentiment
                ORDER BY mentions DESC
                LIMIT 10
                """,
                focus_group_id=focus_group_id
            )

            async for record in result:
                nodes.append({
                    "id": f"concept_{record['name']}",
                    "name": record["name"],
                    "type": "concept",
                    "group": 2,
                    "size": min(25, 8 + record["mentions"] * 2),
                    "sentiment": record["avg_sentiment"]
                })

            result = await session.run(
                """
                MATCH (e:Emotion)<-[f:FEELS]-(p:Persona {focus_group_id: $focus_group_id})
                WITH e, COUNT(f) as count
                RETURN e.name as name, count
                """,
                focus_group_id=focus_group_id
            )

            async for record in result:
                nodes.append({
                    "id": f"emotion_{record['name']}",
                    "name": record["name"],
                    "type": "emotion",
                    "group": 3,
                    "size": min(15, 5 + record["count"])
                })

            result = await session.run(
                """
                MATCH (p:Persona {focus_group_id: $focus_group_id})-[m:MENTIONS]->(c:Concept)
                WHERE c.frequency >= 2
                RETURN p.id as source, c.name as target, m.sentiment as sentiment, m.count as strength
                """,
                focus_group_id=focus_group_id
            )

            async for record in result:
                if filter_type == 'influence' and record["strength"] < 2:
                    continue

                links.append({
                    "source": record["source"],
                    "target": f"concept_{record['target']}",
                    "type": "mentions",
                    "strength": min(1.0, record["strength"] / 5.0),
                    "sentiment": record["sentiment"]
                })

            result = await session.run(
                """
                MATCH (p:Persona {focus_group_id: $focus_group_id})-[f:FEELS]->(e:Emotion)
                RETURN p.id as source, e.name as target, f.intensity as intensity
                """,
                focus_group_id=focus_group_id
            )

            async for record in result:
                links.append({
                    "source": record["source"],
                    "target": f"emotion_{record['target']}",
                    "type": "feels",
                    "strength": record["intensity"]
                })

            result = await session.run(
                """
                MATCH (p1:Persona {focus_group_id: $focus_group_id})-[r:AGREES_WITH|DISAGREES_WITH]->(p2:Persona)
                RETURN p1.id as source, p2.id as target,
                       type(r) as rel_type, r.strength as strength
                """,
                focus_group_id=focus_group_id
            )

            async for record in result:
                rel_type = "agrees" if "AGREES" in record["rel_type"] else "disagrees"
                links.append({
                    "source": record["source"],
                    "target": record["target"],
                    "type": rel_type,
                    "strength": record["strength"]
                })

        return {
            "nodes": nodes,
            "links": links
        }

    async def _load_focus_group_entities(
        self,
        db: AsyncSession,
        focus_group_id: str
    ) -> Tuple[FocusGroup, List[PersonaResponse], Dict[str, Persona]]:
        """Ładuje dane grupy fokusowej, odpowiedzi i persony."""
        result = await db.execute(
            select(FocusGroup).where(FocusGroup.id == focus_group_id)
        )
        focus_group = result.scalar_one_or_none()

        if not focus_group or focus_group.status != "completed":
            raise ValueError("Focus group not found or not completed")

        result = await db.execute(
            select(PersonaResponse).where(
                PersonaResponse.focus_group_id == focus_group_id
            )
        )
        responses = result.scalars().all()

        persona_ids = sorted({str(response.persona_id) for response in responses})
        personas: Dict[str, Persona] = {}
        if persona_ids:
            result = await db.execute(
                select(Persona).where(Persona.id.in_(persona_ids))
            )
            personas = {str(persona.id): persona for persona in result.scalars().all()}

        return focus_group, responses, personas

    async def _prepare_graph_snapshot(
        self,
        responses: List[PersonaResponse],
        personas: Dict[str, Persona]
    ) -> Dict[str, Any]:
        """
        Buduje strukturę grafu w pamięci na podstawie odpowiedzi i dostępnych person.
        """
        persona_concepts: Dict[str, Dict[str, List[float]]] = defaultdict(
            lambda: defaultdict(list)
        )
        persona_emotions: Dict[str, Dict[str, List[float]]] = defaultdict(
            lambda: defaultdict(list)
        )
        concept_aggregates: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {"mentions": 0, "sentiments": [], "personas": set()}
        )
        emotion_aggregates: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {"count": 0, "intensities": [], "personas": set()}
        )
        persona_sentiment_totals: Dict[str, Dict[str, float]] = defaultdict(
            lambda: {"total": 0.0, "count": 0}
        )

        entries: List[Dict[str, Any]] = []
        total_emotion_links = 0

        for response in responses:
            text = response.response or ""
            persona_id = str(response.persona_id)
            extraction = await self._extract_concepts_with_llm(text)

            normalized_concepts = self._normalize_concepts(extraction.concepts)
            normalized_emotions = self._normalize_emotions(extraction.emotions)

            sentiment_total = persona_sentiment_totals[persona_id]
            sentiment_total["total"] += extraction.sentiment
            sentiment_total["count"] += 1

            for concept in normalized_concepts:
                persona_concepts[persona_id][concept].append(extraction.sentiment)
                aggregate = concept_aggregates[concept]
                aggregate["mentions"] += 1
                aggregate["sentiments"].append(extraction.sentiment)
                aggregate["personas"].add(persona_id)

            for emotion in normalized_emotions:
                intensity = abs(extraction.sentiment)
                persona_emotions[persona_id][emotion].append(intensity)
                aggregate = emotion_aggregates[emotion]
                aggregate["count"] += 1
                aggregate["intensities"].append(intensity)
                aggregate["personas"].add(persona_id)
                total_emotion_links += 1

            entries.append({
                "persona_id": persona_id,
                "concepts": normalized_concepts,
                "emotions": normalized_emotions,
                "sentiment": extraction.sentiment
            })

        persona_sentiments = {
            persona_id: (
                totals["total"] / totals["count"] if totals["count"] else 0.0
            )
            for persona_id, totals in persona_sentiment_totals.items()
        }

        for persona_id in personas.keys():
            persona_sentiments.setdefault(persona_id, 0.0)

        persona_edges = self._compute_persona_edges(persona_concepts)

        concept_aggregates = {
            concept: {
                "mentions": data["mentions"],
                "sentiments": list(data["sentiments"]),
                "personas": set(data["personas"])
            }
            for concept, data in concept_aggregates.items()
        }

        emotion_aggregates = {
            emotion: {
                "count": data["count"],
                "intensities": list(data["intensities"]),
                "personas": set(data["personas"])
            }
            for emotion, data in emotion_aggregates.items()
        }

        persona_concepts = {
            persona_id: dict(concepts)
            for persona_id, concepts in persona_concepts.items()
        }
        persona_emotions = {
            persona_id: dict(emotions)
            for persona_id, emotions in persona_emotions.items()
        }

        persona_metadata = {
            persona_id: {
                "name": persona.full_name,
                "age": persona.age,
                "occupation": persona.occupation
            }
            for persona_id, persona in personas.items()
        }

        metrics = {
            "persona_concepts": persona_concepts,
            "persona_emotions": persona_emotions,
            "concept_aggregates": concept_aggregates,
            "emotion_aggregates": emotion_aggregates,
            "persona_sentiments": persona_sentiments,
            "persona_metadata": persona_metadata,
            "persona_edges": persona_edges
        }

        graph_data, persona_connections = self._build_graph_from_metrics(
            personas, metrics
        )
        metrics["persona_connections"] = persona_connections

        stats = {
            "personas_added": len(personas),
            "concepts_extracted": len(concept_aggregates),
            "relationships_created": len(graph_data["links"]),
            "emotions_created": total_emotion_links
        }

        return {
            "stats": stats,
            "graph_data": graph_data,
            "metrics": metrics,
            "entries": entries
        }

    async def _ensure_memory_graph(
        self,
        focus_group_id: str,
        db: Optional[AsyncSession]
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Zapewnia, że graf dla danej grupy jest dostępny w pamięci."""
        if focus_group_id not in self._memory_graph_cache:
            if db is None:
                raise ValueError(
                    "Graph not built yet and database session is required for fallback"
                )

            _, responses, personas = await self._load_focus_group_entities(db, focus_group_id)
            processed = await self._prepare_graph_snapshot(responses, personas)
            self._memory_graph_cache[focus_group_id] = processed["graph_data"]
            self._memory_stats_cache[focus_group_id] = processed["stats"]
            self._memory_metrics_cache[focus_group_id] = processed["metrics"]

        return (
            self._memory_graph_cache[focus_group_id],
            self._memory_metrics_cache[focus_group_id]
        )

    def _apply_filter(
        self,
        graph_data: Dict[str, Any],
        metrics: Dict[str, Any],
        filter_type: str
    ) -> Dict[str, Any]:
        """Zastosuj filtr do pamięciowego grafu."""
        persona_sentiments = metrics.get("persona_sentiments", {})
        persona_connections = metrics.get("persona_connections", {})
        persona_metadata = metrics.get("persona_metadata", {})

        if filter_type == "positive":
            allowed_personas = {
                persona_id for persona_id, sentiment in persona_sentiments.items()
                if sentiment >= 0.6
            }
        elif filter_type == "negative":
            allowed_personas = {
                persona_id for persona_id, sentiment in persona_sentiments.items()
                if sentiment <= -0.3
            }
        elif filter_type == "influence":
            allowed_personas = {
                persona_id for persona_id, connections in persona_connections.items()
                if connections >= 3
            }
        else:
            allowed_personas = set(persona_metadata.keys())

        if not allowed_personas:
            return {"nodes": [], "links": []}

        filtered_links: List[Dict[str, Any]] = []
        for link in graph_data.get("links", []):
            source = str(link.get("source"))
            target = str(link.get("target"))
            link_type = link.get("type")

            if link_type == "mentions":
                if source not in allowed_personas:
                    continue
                if filter_type == "influence" and link.get("strength", 0.0) < 0.4:
                    continue
            elif link_type == "feels":
                if source not in allowed_personas:
                    continue
            else:
                if source not in allowed_personas or target not in allowed_personas:
                    continue

            filtered_links.append(self._copy_link(link))

        connected_nodes = set()
        for link in filtered_links:
            connected_nodes.add(str(link["source"]))
            connected_nodes.add(str(link["target"]))

        filtered_nodes: List[Dict[str, Any]] = []
        for node in graph_data.get("nodes", []):
            node_id = str(node.get("id"))
            node_type = node.get("type")

            if node_type == "persona":
                if node_id in allowed_personas:
                    filtered_nodes.append(self._copy_node(node))
            else:
                if node_id in connected_nodes:
                    filtered_nodes.append(self._copy_node(node))

        return {
            "nodes": filtered_nodes,
            "links": filtered_links
        }

    def _copy_graph(self, graph_data: Dict[str, Any]) -> Dict[str, Any]:
        """Tworzy płytką kopię struktur grafu, aby nie modyfikować cache."""
        return {
            "nodes": [self._copy_node(node) for node in graph_data.get("nodes", [])],
            "links": [self._copy_link(link) for link in graph_data.get("links", [])]
        }

    def _copy_node(self, node: Dict[str, Any]) -> Dict[str, Any]:
        copied = dict(node)
        metadata = copied.get("metadata")
        if isinstance(metadata, dict):
            copied["metadata"] = dict(metadata)
        return copied

    def _copy_link(self, link: Dict[str, Any]) -> Dict[str, Any]:
        return dict(link)

    def _build_graph_from_metrics(
        self,
        personas: Dict[str, Persona],
        metrics: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], Dict[str, int]]:
        """Na podstawie metryk buduje listę nodes/links."""
        persona_concepts = metrics["persona_concepts"]
        persona_emotions = metrics["persona_emotions"]
        persona_sentiments = metrics["persona_sentiments"]
        concept_aggregates = metrics["concept_aggregates"]
        emotion_aggregates = metrics["emotion_aggregates"]
        persona_edges = metrics["persona_edges"]

        connections_counter: Counter = Counter()
        for edge in persona_edges:
            connections_counter[edge["source"]] += 1
            connections_counter[edge["target"]] += 1

        nodes: List[Dict[str, Any]] = []
        persona_connections: Dict[str, int] = {}

        for persona_id, persona in personas.items():
            concept_connections = sum(
                len(values) for values in persona_concepts.get(persona_id, {}).values()
            )
            emotion_connections = sum(
                len(values) for values in persona_emotions.get(persona_id, {}).values()
            )
            total_connections = (
                concept_connections + emotion_connections + connections_counter.get(persona_id, 0)
            )
            persona_connections[persona_id] = total_connections

            nodes.append({
                "id": persona_id,
                "name": persona.full_name,
                "type": "persona",
                "group": 1,
                "size": min(20, 10 + total_connections),
                "sentiment": persona_sentiments.get(persona_id, 0.0),
                "metadata": {
                    "age": persona.age,
                    "occupation": persona.occupation
                }
            })

        for concept, data in concept_aggregates.items():
            mentions = data["mentions"]
            avg_sentiment = mean(data["sentiments"]) if data["sentiments"] else 0.0
            nodes.append({
                "id": f"concept_{concept}",
                "name": concept,
                "type": "concept",
                "group": 2,
                "size": min(25, 8 + mentions * 2),
                "sentiment": avg_sentiment
            })

        for emotion, data in emotion_aggregates.items():
            nodes.append({
                "id": f"emotion_{emotion}",
                "name": emotion,
                "type": "emotion",
                "group": 3,
                "size": min(15, 5 + len(data["personas"]))
            })

        links: List[Dict[str, Any]] = []

        for persona_id, concepts in persona_concepts.items():
            for concept, sentiments in concepts.items():
                if not sentiments:
                    continue
                links.append({
                    "source": persona_id,
                    "target": f"concept_{concept}",
                    "type": "mentions",
                    "strength": min(1.0, len(sentiments) / 5.0),
                    "sentiment": mean(sentiments)
                })

        for persona_id, emotions in persona_emotions.items():
            for emotion, intensities in emotions.items():
                if not intensities:
                    continue
                links.append({
                    "source": persona_id,
                    "target": f"emotion_{emotion}",
                    "type": "feels",
                    "strength": mean(intensities)
                })

        for edge in persona_edges:
            links.append({
                "source": edge["source"],
                "target": edge["target"],
                "type": edge["type"],
                "strength": edge["strength"]
            })

        return {"nodes": nodes, "links": links}, persona_connections

    def _compute_persona_edges(
        self,
        persona_concepts: Dict[str, Dict[str, List[float]]]
    ) -> List[Dict[str, Any]]:
        """Wyznacza relacje między personami na podstawie wspólnych konceptów."""
        edges: List[Dict[str, Any]] = []
        persona_ids = sorted(persona_concepts.keys())

        for idx, persona_id in enumerate(persona_ids):
            for other_id in persona_ids[idx + 1:]:
                concepts_a = persona_concepts.get(persona_id, {})
                concepts_b = persona_concepts.get(other_id, {})
                shared = set(concepts_a.keys()) & set(concepts_b.keys())
                if not shared:
                    continue

                diffs = []
                for concept in shared:
                    values_a = concepts_a.get(concept, [])
                    values_b = concepts_b.get(concept, [])
                    avg_a = mean(values_a) if values_a else 0.0
                    avg_b = mean(values_b) if values_b else 0.0
                    diffs.append(abs(avg_a - avg_b))

                avg_diff = mean(diffs) if diffs else 0.0
                similarity = (len(shared) / 10.0) - avg_diff
                similarity = max(-1.0, min(1.0, similarity))

                if similarity > 0.5:
                    edges.append({
                        "source": persona_id,
                        "target": other_id,
                        "type": "agrees",
                        "strength": similarity
                    })
                elif similarity < -0.3:
                    edges.append({
                        "source": persona_id,
                        "target": other_id,
                        "type": "disagrees",
                        "strength": abs(similarity)
                    })

        return edges

    def _normalize_concepts(self, concepts: Iterable[str]) -> List[str]:
        """Czyści i normalizuje nazwy konceptów."""
        normalized: List[str] = []
        seen = set()
        for concept in concepts:
            if not concept:
                continue
            cleaned = re.sub(r"\s+", " ", concept).strip()
            if not cleaned:
                continue
            formatted = cleaned.title()
            if formatted not in seen:
                seen.add(formatted)
                normalized.append(formatted)
        return normalized

    def _normalize_emotions(self, emotions: Iterable[str]) -> List[str]:
        """Czyści i normalizuje nazwy emocji."""
        normalized: List[str] = []
        seen = set()
        for emotion in emotions:
            if not emotion:
                continue
            cleaned = re.sub(r"\s+", " ", emotion).strip()
            if not cleaned:
                continue
            formatted = cleaned.title()
            if formatted not in seen:
                seen.add(formatted)
                normalized.append(formatted)
        return normalized

    async def _extract_concepts_with_llm(self, text: str) -> ConceptExtraction:
        """
        Ekstrakcja konceptów przy użyciu Gemini LLM

        Używa structured output do wyekstraktowania:
        - Kluczowych konceptów/tematów
        - Emocji
        - Sentymentu
        - Najważniejszych fraz

        Args:
            text: Tekst odpowiedzi persony

        Returns:
            ConceptExtraction object z wyekstraktowanymi danymi
        """
        if not self.llm or not self.extraction_prompt:
            return self._fallback_concept_extraction(text)

        try:
            # Tworzymy łańcuch: prompt -> LLM -> parser JSON
            chain = self.extraction_prompt | self.llm | self.json_parser
            result = await chain.ainvoke({"text": text})

            # Walidujemy wynik i zwracamy strukturę
            return ConceptExtraction(**result)

        except Exception as e:
            logger.warning("LLM concept extraction failed (%s). Switching to fallback.", e)
            return self._fallback_concept_extraction(text)

    def _fallback_concept_extraction(self, text: str) -> ConceptExtraction:
        """Fallback pipeline when LLM is unavailable."""
        sentiment = self._analyze_sentiment(text)
        concepts = self._simple_keyword_extraction(text)
        key_phrases = self._extract_key_phrases(text, concepts)
        emotions = self._infer_emotions(text, sentiment)

        return ConceptExtraction(
            concepts=concepts,
            emotions=emotions,
            sentiment=sentiment,
            key_phrases=key_phrases
        )

    def _simple_keyword_extraction(self, text: str, max_keywords: int = 5) -> List[str]:
        """Fallback: prosta ekstrakcja słów kluczowych bez LLM z użyciem częstotliwości wyrazów."""
        tokens = [
            token.strip("'").lower()
            for token in re.findall(r"[A-Za-z][A-Za-z'\\-]+", text)
        ]
        filtered = [
            token for token in tokens
            if len(token) > 2 and token not in STOPWORDS and not any(char.isdigit() for char in token)
        ]

        if not filtered:
            return []

        word_counts = Counter(filtered)
        bigrams = [
            f"{filtered[idx]} {filtered[idx + 1]}"
            for idx in range(len(filtered) - 1)
            if filtered[idx] != filtered[idx + 1]
        ]
        bigram_counts = Counter(bigrams)

        candidates: List[str] = []

        for phrase, _ in bigram_counts.most_common(max_keywords * 2):
            formatted = " ".join(part.capitalize() for part in phrase.split())
            if formatted not in candidates:
                candidates.append(formatted)
            if len(candidates) >= max_keywords:
                break

        if len(candidates) < max_keywords:
            for word, _ in word_counts.most_common(max_keywords * 3):
                formatted = word.capitalize()
                if formatted not in candidates:
                    candidates.append(formatted)
                if len(candidates) >= max_keywords:
                    break

        return candidates[:max_keywords]

    def _analyze_sentiment(self, text: str) -> float:
        """
        Fallback: prosta analiza sentymentu
        Returns: -1.0 (negative) to 1.0 (positive)
        """
        positive = ["good", "great", "love", "excellent", "amazing", "like", "helpful", "useful", "easy"]
        negative = ["bad", "terrible", "hate", "poor", "awful", "difficult", "hard", "confusing", "expensive"]

        text_lower = text.lower()
        pos_count = sum(1 for word in positive if word in text_lower)
        neg_count = sum(1 for word in negative if word in text_lower)

        total = pos_count + neg_count
        if total == 0:
            return 0.0

        return (pos_count - neg_count) / total

    def _extract_key_phrases(
        self,
        text: str,
        concepts: Optional[List[str]] = None,
        max_phrases: int = 3
    ) -> List[str]:
        """Próbuje wyłuskać najważniejsze frazy do kontekstu konceptów."""
        phrases: List[str] = []
        lowered = text.lower()

        if concepts:
            for concept in concepts:
                if not concept:
                    continue
                idx = lowered.find(concept.lower())
                if idx == -1:
                    continue

                start = lowered.rfind(".", 0, idx)
                start = 0 if start == -1 else start + 1
                end = lowered.find(".", idx)
                end = len(text) if end == -1 else end

                snippet = text[start:end].strip()
                if snippet and snippet not in phrases:
                    phrases.append(snippet)

                if len(phrases) >= max_phrases:
                    return phrases[:max_phrases]

        tokens = [
            token.strip("'").lower()
            for token in re.findall(r"[A-Za-z][A-Za-z'\\-]+", text)
        ]
        filtered = [
            token for token in tokens
            if len(token) > 2 and token not in STOPWORDS and not any(char.isdigit() for char in token)
        ]

        if not filtered:
            return phrases[:max_phrases]

        ngrams = []
        for idx in range(len(filtered) - 1):
            bigram = f"{filtered[idx]} {filtered[idx + 1]}"
            ngrams.append(bigram)
            if idx < len(filtered) - 2:
                trigram = f"{filtered[idx]} {filtered[idx + 1]} {filtered[idx + 2]}"
                ngrams.append(trigram)

        for phrase, _ in Counter(ngrams).most_common(max_phrases * 2):
            formatted = " ".join(part.capitalize() for part in phrase.split())
            if formatted not in phrases:
                phrases.append(formatted)
            if len(phrases) >= max_phrases:
                break

        return phrases[:max_phrases]

    def _infer_emotions(self, text: str, sentiment: float) -> List[str]:
        """Próbuje odgadnąć emocje na podstawie słów kluczowych i sentymentu."""
        lowered = text.lower()
        detected: List[str] = []

        for emotion, keywords in EMOTION_KEYWORDS.items():
            if any(keyword in lowered for keyword in keywords):
                detected.append(emotion)

        if detected:
            # Zachowujemy kolejność wykrycia i usuwamy duplikaty
            seen = set()
            unique = []
            for emotion in detected:
                if emotion not in seen:
                    seen.add(emotion)
                    unique.append(emotion)
            return unique

        mapped = self._sentiment_to_emotion(sentiment)
        if mapped:
            return [mapped]

        return ["Neutral"]

    def _sentiment_to_emotion(self, sentiment: float) -> Optional[str]:
        """Mapuje sentiment score na emocję"""
        if sentiment > 0.6:
            return "Satisfied"
        elif sentiment > 0.3:
            return "Pleased"
        elif sentiment > -0.3:
            return "Neutral"
        elif sentiment > -0.6:
            return "Concerned"
        else:
            return "Frustrated"

    async def _calculate_persona_similarity(
        self,
        session,
        persona1_id: str,
        persona2_id: str
    ) -> float:
        """
        Oblicza podobieństwo między dwiema personami
        Na podstawie wspólnych konceptów i zgodności sentimentu
        """
        result = await session.run(
            """
            MATCH (p1:Persona {id: $p1_id})-[m1:MENTIONS]->(c:Concept)<-[m2:MENTIONS]-(p2:Persona {id: $p2_id})
            WITH COUNT(c) as shared_concepts,
                 AVG(ABS(m1.sentiment - m2.sentiment)) as sentiment_diff
            RETURN shared_concepts, sentiment_diff
            """,
            p1_id=persona1_id,
            p2_id=persona2_id
        )

        record = await result.single()
        if not record or record["shared_concepts"] == 0:
            return 0.0

        # Wzór: podobieństwo = (liczba wspólnych konceptów / 10) - różnica sentymentów
        similarity = (record["shared_concepts"] / 10.0) - record["sentiment_diff"]
        return max(-1.0, min(1.0, similarity))

    async def get_influential_personas(
        self,
        focus_group_id: str,
        db: Optional[AsyncSession] = None
    ) -> List[Dict[str, Any]]:
        """
        Znajduje najbardziej wpływowe persony w grafie
        Na podstawie liczby połączeń i siły relacji
        """
        try:
            await self.connect()
            neo4j_available = True
        except ConnectionError:
            neo4j_available = False

        if not neo4j_available or not self.driver:
            _, metrics = await self._ensure_memory_graph(focus_group_id, db)
            persona_metadata = metrics.get("persona_metadata", {})
            persona_connections = metrics.get("persona_connections", {})
            persona_sentiments = metrics.get("persona_sentiments", {})

            personas = [
                {
                    "id": persona_id,
                    "name": meta["name"],
                    "influence": min(100, persona_connections.get(persona_id, 0) * 5),
                    "connections": persona_connections.get(persona_id, 0),
                    "sentiment": persona_sentiments.get(persona_id, 0.0)
                }
                for persona_id, meta in persona_metadata.items()
            ]

            personas.sort(key=lambda item: item["connections"], reverse=True)
            return personas[:10]

        async with self.driver.session() as session:
            result = await session.run(
                """
                MATCH (p:Persona {focus_group_id: $focus_group_id})
                OPTIONAL MATCH (p)-[r]-()
                WITH p, COUNT(r) as connections,
                     AVG(CASE WHEN r.sentiment IS NOT NULL THEN r.sentiment ELSE 0.5 END) as avg_sentiment
                RETURN p.id as id, p.name as name, connections, avg_sentiment
                ORDER BY connections DESC
                LIMIT 10
                """,
                focus_group_id=focus_group_id
            )

            personas = []
            async for record in result:
                personas.append({
                    "id": record["id"],
                    "name": record["name"],
                    "influence": min(100, record["connections"] * 5),
                    "connections": record["connections"],
                    "sentiment": record["avg_sentiment"]
                })

            return personas

    async def answer_question(
        self,
        focus_group_id: str,
        question: str,
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """
        Wykonuje proste zapytanie w języku naturalnym na podstawie metryk grafu.

        Analiza wykorzystuje heurystyki, aby dopasować pytanie do gotowych analiz:
        - Najbardziej wpływowe persony
        - Kontrowersyjne koncepty
        - Emocje powiązane z konkretnym tematem
        - Najbardziej pozytywne/negatywne koncepty
        - Ogólne podsumowanie top tematów
        """
        question_text = (question or "").strip()
        if not question_text:
            raise ValueError("Question cannot be empty")

        normalized = question_text.lower()

        # Zapewnij istnienie grafu w pamięci
        _, metrics = await self._ensure_memory_graph(focus_group_id, db)

        persona_metadata: Dict[str, Dict[str, Any]] = metrics.get("persona_metadata", {})
        persona_concepts: Dict[str, Dict[str, List[float]]] = metrics.get("persona_concepts", {})
        persona_emotions: Dict[str, Dict[str, List[float]]] = metrics.get("persona_emotions", {})
        concept_aggregates: Dict[str, Dict[str, Any]] = metrics.get("concept_aggregates", {})
        persona_sentiments: Dict[str, float] = metrics.get("persona_sentiments", {})

        influential_personas = await self.get_influential_personas(focus_group_id, db)
        key_concepts = await self.get_key_concepts(focus_group_id, db)
        controversial_concepts = await self.get_controversial_concepts(focus_group_id, db)
        emotion_distribution = await self.get_emotion_distribution(focus_group_id, db)

        suggested_questions = [
            "Who influences others the most?",
            "Show me controversial topics.",
            "Which emotions dominate the discussion?",
            "Which concepts are rated most positively?",
            "Where do participants disagree the most?"
        ]

        insights: List[Dict[str, Any]] = []

        concept_lookup = {concept.lower(): concept for concept in concept_aggregates.keys()}
        matched_concept: Optional[str] = None
        for key, original in concept_lookup.items():
            if key and key in normalized:
                matched_concept = original
                break

        influence_tokens = {"influence", "influences", "influential", "impact", "influencers", "connections"}
        controversial_tokens = {"controversial", "disagree", "disagreement", "polarized", "polarising", "conflict", "split"}
        emotion_tokens = {"emotion", "feel", "feeling", "feelings", "mood", "sentiment"}
        sentiment_tokens = {"sentiment", "positive", "negative", "happy", "unhappy", "satisfied", "satisfaction"}
        topic_tokens = {"topic", "topics", "concept", "concepts", "talking", "discussion", "discuss"}
        opinion_tokens = {"think", "opinion", "opinions", "feel", "view", "perceive", "perception", "feedback"}

        def persona_label(persona_id: str, fallback: str) -> str:
            meta = persona_metadata.get(persona_id)
            if not meta:
                return fallback
            name = meta.get("name") or fallback
            occupation = meta.get("occupation")
            age = meta.get("age")
            if occupation and age:
                return f"{name} ({occupation}, {age}y)"
            if occupation:
                return f"{name} ({occupation})"
            if age:
                return f"{name} ({age}y)"
            return name

        def format_percentage(value: float) -> str:
            return f"{value * 100:.0f}%" if abs(value) <= 1 else f"{value:.1f}"

        # === 1. Pytania o wpływ ===
        if "who" in normalized and any(token in normalized for token in influence_tokens):
            if not influential_personas:
                answer = "I couldn't find influence metrics yet. Build the graph after the focus group completes."
            else:
                top_persona = influential_personas[0]
                answer = (
                    f"{top_persona['name']} is the most influential persona with "
                    f"{top_persona['connections']} connections and an influence score of "
                    f"{top_persona['influence']}/100."
                )
                for persona in influential_personas[:3]:
                    insights.append({
                        "title": persona["name"],
                        "detail": (
                            f"Influence {persona['influence']}/100 • "
                            f"Connections {persona['connections']} • "
                            f"Avg sentiment {persona['sentiment']:.2f}"
                        ),
                        "metadata": {"persona_id": persona["id"]}
                    })
            return {
                "answer": answer,
                "insights": insights,
                "suggested_questions": suggested_questions,
            }

        # === 2. Kontrowersyjne tematy ===
        if any(token in normalized for token in controversial_tokens):
            if not controversial_concepts:
                answer = "I didn't detect any highly polarized topics yet. Most discussions stayed aligned."
            else:
                top_concept = controversial_concepts[0]
                supporters = ", ".join(top_concept["supporters"][:3]) or "no clear supporters"
                critics = ", ".join(top_concept["critics"][:3]) or "no strong critics"
                answer = (
                    f"'{top_concept['concept']}' is the most controversial topic with high sentiment variance "
                    f"({top_concept['polarization']:.2f}). Supporters include {supporters}, while critics highlight {critics}."
                )
                for concept in controversial_concepts[:3]:
                    insights.append({
                        "title": concept["concept"],
                        "detail": (
                            f"Polarization {concept['polarization']:.2f} • Avg sentiment {concept['avg_sentiment']:.2f} • "
                            f"Mentions {concept['total_mentions']}"
                        ),
                        "metadata": {
                            "supporters": concept["supporters"],
                            "critics": concept["critics"],
                        }
                    })
            return {
                "answer": answer,
                "insights": insights,
                "suggested_questions": suggested_questions,
            }

        # === 3. Emocje ===
        if any(token in normalized for token in emotion_tokens):
            if matched_concept:
                emotion_totals: Dict[str, List[float]] = defaultdict(list)
                emotion_personas: Dict[str, set] = defaultdict(set)

                for persona_id, concepts in persona_concepts.items():
                    if matched_concept not in concepts:
                        continue
                    for emotion, intensities in persona_emotions.get(persona_id, {}).items():
                        if not intensities:
                            continue
                        emotion_totals[emotion].extend(intensities)
                        emotion_personas[emotion].add(persona_id)

                if not emotion_totals:
                    answer = f"Personas talking about {matched_concept} did not express strong emotional cues."
                else:
                    emotion_rank = sorted(
                        (
                            (
                                emotion,
                                mean(intensities) if intensities else 0.0,
                                len(emotion_personas[emotion])
                            )
                            for emotion, intensities in emotion_totals.items()
                        ),
                        key=lambda item: item[1],
                        reverse=True
                    )
                    top_emotion, top_intensity, persona_count = emotion_rank[0]
                    answer = (
                        f"The dominant emotion around {matched_concept} is {top_emotion} "
                        f"(intensity {top_intensity:.2f}) expressed by {persona_count} personas."
                    )
                    for emotion, avg_intensity, count in emotion_rank[:3]:
                        insights.append({
                            "title": emotion,
                            "detail": (
                                f"Average intensity {avg_intensity:.2f} • {count} personas referencing {matched_concept}"
                            ),
                            "metadata": {"personas": [persona_label(pid, pid) for pid in emotion_personas[emotion]]}
                        })
                return {
                    "answer": answer,
                    "insights": insights,
                    "suggested_questions": suggested_questions,
                }

            if not emotion_distribution:
                answer = "I couldn't derive an emotion distribution yet."
            else:
                top_emotion = emotion_distribution[0]
                answer = (
                    f"{top_emotion['emotion']} is the leading emotion, expressed by "
                    f"{top_emotion['personas_count']} personas (avg intensity {top_emotion['avg_intensity']:.2f})."
                )
                for emotion in emotion_distribution[:3]:
                    insights.append({
                        "title": emotion["emotion"],
                        "detail": (
                            f"{emotion['personas_count']} personas • Avg intensity {emotion['avg_intensity']:.2f}"
                        ),
                        "metadata": {"percentage": emotion.get("percentage", 0)}
                    })
            return {
                "answer": answer,
                "insights": insights,
                "suggested_questions": suggested_questions,
            }

        # === 4. Opinie o konkretnym koncepcie ===
        if matched_concept and any(token in normalized for token in opinion_tokens):
            concept_data = concept_aggregates.get(matched_concept)
            if not concept_data or concept_data["mentions"] == 0:
                answer = f"I don't have enough mentions about {matched_concept} yet."
            else:
                avg_sentiment = mean(concept_data["sentiments"]) if concept_data["sentiments"] else 0.0
                supporters: List[str] = []
                critics: List[str] = []

                for persona_id, concepts in persona_concepts.items():
                    values = concepts.get(matched_concept, [])
                    if not values:
                        continue
                    persona_avg = mean(values)
                    label = persona_label(persona_id, persona_id)
                    if persona_avg > 0.3:
                        supporters.append(label)
                    elif persona_avg < -0.3:
                        critics.append(label)

                supporters_display = ", ".join(supporters[:3]) or "nobody strongly in favour yet"
                critics_display = ", ".join(critics[:3]) or "nobody strongly opposed yet"
                answer = (
                    f"Overall sentiment toward {matched_concept} is {avg_sentiment:.2f}. "
                    f"Supporters include {supporters_display}, while critics mention {critics_display}."
                )
                insights.append({
                    "title": matched_concept,
                    "detail": (
                        f"Mentions {concept_data['mentions']} • Avg sentiment {avg_sentiment:.2f}"
                    ),
                    "metadata": {
                        "supporters": supporters[:5],
                        "critics": critics[:5]
                    }
                })
            return {
                "answer": answer,
                "insights": insights,
                "suggested_questions": suggested_questions,
            }

        # === 5. Zapytania o ogólną polaryzację / sentyment ===
        if any(token in normalized for token in sentiment_tokens):
            if not key_concepts:
                answer = "I don't have sentiment data yet. Run and build the graph first."
            else:
                positive = [concept for concept in key_concepts if concept["sentiment"] >= 0.3]
                negative = [concept for concept in key_concepts if concept["sentiment"] <= -0.2]

                if positive:
                    best = positive[0]
                    positive_msg = (
                        f"Most positive concept: {best['name']} ({best['sentiment']:.2f} sentiment across "
                        f"{best['frequency']} mentions)."
                    )
                    insights.append({
                        "title": f"Positive · {best['name']}",
                        "detail": f"Sentiment {best['sentiment']:.2f} • Mentions {best['frequency']}",
                        "metadata": {"personas": best["personas"]}
                    })
                else:
                    positive_msg = "No strongly positive concepts detected."

                if negative:
                    worst = sorted(negative, key=lambda item: item["sentiment"])[0]
                    negative_msg = (
                        f"Biggest pain point: {worst['name']} ({worst['sentiment']:.2f} sentiment)."
                    )
                    insights.append({
                        "title": f"Negative · {worst['name']}",
                        "detail": f"Sentiment {worst['sentiment']:.2f} • Mentions {worst['frequency']}",
                        "metadata": {"personas": worst["personas"]}
                    })
                else:
                    negative_msg = "No strongly negative concepts detected."

                answer = f"{positive_msg} {negative_msg}"
            return {
                "answer": answer,
                "insights": insights,
                "suggested_questions": suggested_questions,
            }

        # === 6. Tematy / top koncepcje ===
        if any(token in normalized for token in topic_tokens):
            if not key_concepts:
                answer = "No dominant topics yet. Once personas respond, I'll highlight the main themes."
            else:
                top_items = key_concepts[:3]
                topics = ", ".join(f"{item['name']} ({format_percentage(item['sentiment'])})" for item in top_items)
                answer = f"Top themes right now: {topics}."
                for concept in top_items:
                    insights.append({
                        "title": concept["name"],
                        "detail": (
                            f"Mentions {concept['frequency']} • Avg sentiment {concept['sentiment']:.2f}"
                        ),
                        "metadata": {"personas": concept["personas"]}
                    })
            return {
                "answer": answer,
                "insights": insights,
                "suggested_questions": suggested_questions,
            }

        # === 7. Domyślna odpowiedź - syntetyczne podsumowanie ===
        if key_concepts:
            top_concept = key_concepts[0]
            top_concept_text = (
                f"The discussion centers on {top_concept['name']} "
                f"(sentiment {top_concept['sentiment']:.2f}, {top_concept['frequency']} mentions)."
            )
            insights.append({
                "title": f"Focus · {top_concept['name']}",
                "detail": (
                    f"Mentions {top_concept['frequency']} • Avg sentiment {top_concept['sentiment']:.2f}"
                ),
                "metadata": {"personas": top_concept["personas"]}
            })
        else:
            top_concept_text = "I couldn't determine a dominant concept yet."

        if influential_personas:
            top_persona = influential_personas[0]
            influence_text = (
                f"{top_persona['name']} leads the conversation with "
                f"{top_persona['connections']} connections (influence {top_persona['influence']}/100)."
            )
            insights.append({
                "title": f"Leader · {top_persona['name']}",
                "detail": (
                    f"Influence {top_persona['influence']}/100 • Connections {top_persona['connections']} • "
                    f"Avg sentiment {top_persona['sentiment']:.2f}"
                ),
                "metadata": {"persona_id": top_persona["id"]}
            })
        else:
            influence_text = "I have limited information about persona influence so far."

        negative_concepts = [
            concept for concept in key_concepts if concept["sentiment"] <= -0.2
        ]
        if negative_concepts:
            worst = sorted(negative_concepts, key=lambda item: item["sentiment"])[0]
            risk_text = f"Watch out for {worst['name']} (sentiment {worst['sentiment']:.2f})."
            insights.append({
                "title": f"Risk · {worst['name']}",
                "detail": (
                    f"{worst['frequency']} mentions • Avg sentiment {worst['sentiment']:.2f}"
                ),
                "metadata": {"personas": worst["personas"]}
            })
        else:
            risk_text = ""

        answer_parts = [part for part in [top_concept_text, influence_text, risk_text] if part]
        answer = " ".join(answer_parts) if answer_parts else "I need more data before I can summarize this focus group."

        return {
            "answer": answer,
            "insights": insights,
            "suggested_questions": suggested_questions,
        }
    async def get_key_concepts(
        self,
        focus_group_id: str,
        db: Optional[AsyncSession] = None
    ) -> List[Dict[str, Any]]:
        """Pobiera najczęściej wspominane koncepcje"""
        try:
            await self.connect()
            neo4j_available = True
        except ConnectionError:
            neo4j_available = False

        if not neo4j_available or not self.driver:
            _, metrics = await self._ensure_memory_graph(focus_group_id, db)
            persona_metadata = metrics.get("persona_metadata", {})
            concept_aggregates = metrics.get("concept_aggregates", {})

            concepts = []
            for concept, data in concept_aggregates.items():
                if data["mentions"] == 0:
                    continue
                avg_sentiment = mean(data["sentiments"]) if data["sentiments"] else 0.0
                persona_names = [
                    persona_metadata.get(persona_id, {}).get("name", persona_id)
                    for persona_id in list(data["personas"])
                ]
                concepts.append({
                    "name": concept,
                    "frequency": data["mentions"],
                    "sentiment": avg_sentiment,
                    "personas": persona_names[:5]
                })

            concepts.sort(key=lambda item: item["frequency"], reverse=True)
            return concepts[:10]

        async with self.driver.session() as session:
            result = await session.run(
                """
                MATCH (c:Concept)<-[m:MENTIONS]-(p:Persona {focus_group_id: $focus_group_id})
                WITH c, COUNT(m) as frequency, AVG(m.sentiment) as avg_sentiment,
                     COLLECT(DISTINCT p.name) as personas
                RETURN c.name as name, frequency, avg_sentiment, personas
                ORDER BY frequency DESC
                LIMIT 10
                """,
                focus_group_id=focus_group_id
            )

            concepts = []
            async for record in result:
                concepts.append({
                    "name": record["name"],
                    "frequency": record["frequency"],
                    "sentiment": record["avg_sentiment"],
                    "personas": record["personas"][:5]
                })

            return concepts

    async def get_controversial_concepts(
        self,
        focus_group_id: str,
        db: Optional[AsyncSession] = None
    ) -> List[Dict[str, Any]]:
        """
        Znajduje koncepcje polaryzujące - te, które wywołują skrajne opinie

        Zwraca koncepcje z dużym rozrzutem sentymentu (jedni kochają, inni nienawidzą)
        """
        try:
            await self.connect()
            neo4j_available = True
        except ConnectionError:
            neo4j_available = False

        if not neo4j_available or not self.driver:
            _, metrics = await self._ensure_memory_graph(focus_group_id, db)
            concept_aggregates = metrics.get("concept_aggregates", {})
            persona_concepts = metrics.get("persona_concepts", {})
            persona_metadata = metrics.get("persona_metadata", {})

            controversial: List[Dict[str, Any]] = []
            for concept, data in concept_aggregates.items():
                sentiments = data["sentiments"]
                if len(sentiments) < 3:
                    continue
                try:
                    std_dev = pstdev(sentiments)
                except StatisticsError:
                    continue
                if std_dev <= 0.4:
                    continue
                avg_sentiment = mean(sentiments) if sentiments else 0.0
                supporters: List[str] = []
                critics: List[str] = []

                for persona_id in data["personas"]:
                    persona_values = persona_concepts.get(persona_id, {}).get(concept, [])
                    if not persona_values:
                        continue
                    persona_avg = mean(persona_values)
                    name = persona_metadata.get(persona_id, {}).get("name", persona_id)
                    if persona_avg > 0.5:
                        supporters.append(name)
                    elif persona_avg < -0.3:
                        critics.append(name)

                controversial.append({
                    "concept": concept,
                    "avg_sentiment": avg_sentiment,
                    "polarization": std_dev,
                    "supporters": supporters,
                    "critics": critics,
                    "total_mentions": len(sentiments)
                })

            controversial.sort(key=lambda item: item["polarization"], reverse=True)
            return controversial[:10]

        async with self.driver.session() as session:
            result = await session.run(
                """
                MATCH (c:Concept)<-[m:MENTIONS]-(p:Persona {focus_group_id: $focus_group_id})
                WITH c,
                     COLLECT(m.sentiment) as sentiments,
                     COLLECT({name: p.name, sentiment: m.sentiment}) as persona_sentiments
                WHERE size(sentiments) >= 3
                WITH c,
                     sentiments,
                     persona_sentiments,
                     reduce(s = 0.0, x IN sentiments | s + x) / size(sentiments) as avg_sentiment,
                     reduce(s = 0.0, x IN sentiments | s + (x * x)) / size(sentiments) as variance
                WITH c, avg_sentiment, variance, persona_sentiments,
                     sqrt(variance - (avg_sentiment * avg_sentiment)) as std_dev
                WHERE std_dev > 0.4
                RETURN c.name as concept,
                       avg_sentiment,
                       std_dev as polarization,
                       [ps IN persona_sentiments WHERE ps.sentiment > 0.5 | ps.name] as supporters,
                       [ps IN persona_sentiments WHERE ps.sentiment < -0.3 | ps.name] as critics,
                       size(persona_sentiments) as total_mentions
                ORDER BY std_dev DESC
                LIMIT 10
                """,
                focus_group_id=focus_group_id
            )

            controversial = []
            async for record in result:
                controversial.append({
                    "concept": record["concept"],
                    "avg_sentiment": record["avg_sentiment"],
                    "polarization": record["polarization"],
                    "supporters": record["supporters"],
                    "critics": record["critics"],
                    "total_mentions": record["total_mentions"]
                })

            return controversial

    async def get_trait_opinion_correlations(
        self,
        focus_group_id: str,
        db: Optional[AsyncSession] = None
    ) -> List[Dict[str, Any]]:
        """
        Znajduje korelacje między cechami demograficznymi/psychologicznymi a opiniami

        Przykład: "Osoby młodsze (<30) są bardziej pozytywne wobec 'Innovation'"
        """
        try:
            await self.connect()
            neo4j_available = True
        except ConnectionError:
            neo4j_available = False

        if not neo4j_available or not self.driver:
            _, metrics = await self._ensure_memory_graph(focus_group_id, db)
            concept_aggregates = metrics.get("concept_aggregates", {})
            persona_concepts = metrics.get("persona_concepts", {})
            persona_metadata = metrics.get("persona_metadata", {})

            correlations: List[Dict[str, Any]] = []
            for concept, data in concept_aggregates.items():
                if data["mentions"] < 3:
                    continue

                young: List[float] = []
                mid: List[float] = []
                senior: List[float] = []

                for persona_id, concepts in persona_concepts.items():
                    if concept not in concepts:
                        continue
                    meta = persona_metadata.get(persona_id)
                    if not meta or meta.get("age") is None:
                        continue
                    avg_sentiment = mean(concepts[concept]) if concepts[concept] else 0.0
                    age = meta["age"]
                    if age < 30:
                        young.append(avg_sentiment)
                    elif age < 50:
                        mid.append(avg_sentiment)
                    else:
                        senior.append(avg_sentiment)

                if not (young or mid or senior):
                    continue

                young_avg = mean(young) if young else None
                mid_avg = mean(mid) if mid else None
                senior_avg = mean(senior) if senior else None
                base_young = young_avg if young_avg is not None else 0.0
                base_senior = senior_avg if senior_avg is not None else 0.0
                age_gap = abs(base_young - base_senior)

                if age_gap <= 0.3:
                    continue

                correlations.append({
                    "concept": concept,
                    "young_sentiment": young_avg,
                    "mid_sentiment": mid_avg,
                    "senior_sentiment": senior_avg,
                    "age_gap": age_gap,
                    "mentions": data["mentions"]
                })

            correlations.sort(key=lambda item: item["age_gap"], reverse=True)
            return correlations[:10]

        async with self.driver.session() as session:
            result = await session.run(
                """
                MATCH (p:Persona {focus_group_id: $focus_group_id})-[m:MENTIONS]->(c:Concept)
                WITH c.name as concept,
                     AVG(CASE WHEN p.age < 30 THEN m.sentiment ELSE null END) as young_sentiment,
                     AVG(CASE WHEN p.age >= 30 AND p.age < 50 THEN m.sentiment ELSE null END) as mid_sentiment,
                     AVG(CASE WHEN p.age >= 50 THEN m.sentiment ELSE null END) as senior_sentiment,
                     COUNT(m) as mentions
                WHERE mentions >= 3
                WITH concept, young_sentiment, mid_sentiment, senior_sentiment, mentions,
                     ABS(coalesce(young_sentiment, 0.0) - coalesce(senior_sentiment, 0.0)) as age_gap
                WHERE age_gap > 0.3
                RETURN concept,
                       young_sentiment,
                       mid_sentiment,
                       senior_sentiment,
                       age_gap,
                       mentions
                ORDER BY age_gap DESC
                LIMIT 10
                """,
                focus_group_id=focus_group_id
            )

            correlations = []
            async for record in result:
                correlations.append({
                    "concept": record["concept"],
                    "young_sentiment": record["young_sentiment"],
                    "mid_sentiment": record["mid_sentiment"],
                    "senior_sentiment": record["senior_sentiment"],
                    "age_gap": record["age_gap"],
                    "mentions": record["mentions"]
                })

            return correlations

    async def get_emotion_distribution(
        self,
        focus_group_id: str,
        db: Optional[AsyncSession] = None
    ) -> List[Dict[str, Any]]:
        """
        Pobiera rozkład emocji w grupie fokusowej

        Zwraca agregację: jakie emocje dominują, ilu uczestników je wyraża
        """
        try:
            await self.connect()
            neo4j_available = True
        except ConnectionError:
            neo4j_available = False

        if not neo4j_available or not self.driver:
            _, metrics = await self._ensure_memory_graph(focus_group_id, db)
            emotion_aggregates = metrics.get("emotion_aggregates", {})

            emotions = []
            for emotion, data in emotion_aggregates.items():
                personas_count = len(data["personas"])
                avg_intensity = mean(data["intensities"]) if data["intensities"] else 0.0
                emotions.append({
                    "emotion": emotion,
                    "personas_count": personas_count,
                    "avg_intensity": avg_intensity,
                    "percentage": 0
                })

            total_personas = sum(item["personas_count"] for item in emotions)
            if total_personas > 0:
                for emotion in emotions:
                    emotion["percentage"] = (emotion["personas_count"] / total_personas) * 100

            emotions.sort(key=lambda item: item["personas_count"], reverse=True)
            return emotions

        async with self.driver.session() as session:
            result = await session.run(
                """
                MATCH (e:Emotion)<-[f:FEELS]-(p:Persona {focus_group_id: $focus_group_id})
                WITH e.name as emotion,
                     COUNT(DISTINCT p) as personas_count,
                     AVG(f.intensity) as avg_intensity
                RETURN emotion, personas_count, avg_intensity
                ORDER BY personas_count DESC
                """,
                focus_group_id=focus_group_id
            )

            emotions = []
            async for record in result:
                emotions.append({
                    "emotion": record["emotion"],
                    "personas_count": record["personas_count"],
                    "avg_intensity": record["avg_intensity"],
                    "percentage": 0
                })

            total_personas = sum(e["personas_count"] for e in emotions)
            if total_personas > 0:
                for emotion in emotions:
                    emotion["percentage"] = (emotion["personas_count"] / total_personas) * 100

            return emotions
