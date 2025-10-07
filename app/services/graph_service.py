"""
Serwis Analizy Grafowej oparty na Neo4j

Zarządza grafem wiedzy łączącym persony, koncepcje i emocje.
Umożliwia analizę relacji między uczestnikami focus groups i ich opiniami.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import logging

from neo4j import AsyncGraphDatabase, AsyncDriver
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models import PersonaResponse, Persona, FocusGroup

settings = get_settings()
logger = logging.getLogger(__name__)


class GraphService:
    """
    Zarządza grafem wiedzy w Neo4j

    Graf zawiera:
    - Persony (nodes typu :Persona)
    - Koncepcje/tematy (nodes typu :Concept)
    - Emocje (nodes typu :Emotion)
    - Relacje: MENTIONS, AGREES_WITH, DISAGREES_WITH, FEELS
    """

    def __init__(self):
        """Inicjalizuj połączenie z Neo4j"""
        self.driver: Optional[AsyncDriver] = None
        self.settings = settings

    async def connect(self):
        """Nawiąż połączenie z Neo4j"""
        if not self.driver:
            self.driver = AsyncGraphDatabase.driver(
                self.settings.NEO4J_URI,
                auth=(self.settings.NEO4J_USER, self.settings.NEO4J_PASSWORD)
            )
            logger.info(f"Connected to Neo4j at {self.settings.NEO4J_URI}")

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
        await self.connect()

        # Fetch focus group data
        result = await db.execute(
            select(FocusGroup).where(FocusGroup.id == focus_group_id)
        )
        focus_group = result.scalar_one_or_none()

        if not focus_group or focus_group.status != "completed":
            raise ValueError("Focus group not found or not completed")

        # Fetch responses
        result = await db.execute(
            select(PersonaResponse)
            .where(PersonaResponse.focus_group_id == focus_group_id)
        )
        responses = result.scalars().all()

        # Fetch personas
        persona_ids = list(set(str(r.persona_id) for r in responses))
        result = await db.execute(
            select(Persona).where(Persona.id.in_(persona_ids))
        )
        personas = {str(p.id): p for p in result.scalars().all()}

        stats = {
            "personas_added": 0,
            "concepts_extracted": 0,
            "relationships_created": 0,
            "emotions_created": 0
        }

        async with self.driver.session() as session:
            # 1. Create persona nodes
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
                stats["personas_added"] += 1

            # 2. Extract concepts and create relationships
            concept_mentions = {}  # Track concept frequency

            for response in responses:
                persona_id = str(response.persona_id)

                # Simple keyword extraction (top concepts)
                concepts = self._extract_concepts(response.response)
                sentiment = self._analyze_sentiment(response.response)

                for concept in concepts:
                    # Create/update concept node
                    await session.run(
                        """
                        MERGE (c:Concept {name: $name})
                        ON CREATE SET c.frequency = 1, c.created_at = datetime()
                        ON MATCH SET c.frequency = c.frequency + 1
                        """,
                        name=concept
                    )

                    # Create MENTIONS relationship
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
                    stats["relationships_created"] += 1

                    concept_mentions[concept] = concept_mentions.get(concept, 0) + 1

                # 3. Create emotion nodes based on sentiment
                emotion = self._sentiment_to_emotion(sentiment)
                if emotion:
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
                        ON CREATE SET r.intensity = $sentiment
                        ON MATCH SET r.intensity = (r.intensity + $sentiment) / 2
                        """,
                        persona_id=persona_id,
                        emotion=emotion,
                        sentiment=abs(sentiment)
                    )
                    stats["emotions_created"] += 1

            # 4. Create inter-persona relationships (agrees/disagrees)
            # Based on concept overlap and sentiment similarity
            for p1_id in persona_ids:
                for p2_id in persona_ids:
                    if p1_id >= p2_id:
                        continue

                    # Calculate similarity
                    similarity = await self._calculate_persona_similarity(
                        session, p1_id, p2_id
                    )

                    if similarity > 0.5:
                        await session.run(
                            """
                            MATCH (p1:Persona {id: $p1_id})
                            MATCH (p2:Persona {id: $p2_id})
                            MERGE (p1)-[r:AGREES_WITH]->(p2)
                            SET r.strength = $similarity
                            """,
                            p1_id=p1_id,
                            p2_id=p2_id,
                            similarity=similarity
                        )
                        stats["relationships_created"] += 1
                    elif similarity < -0.3:
                        await session.run(
                            """
                            MATCH (p1:Persona {id: $p1_id})
                            MATCH (p2:Persona {id: $p2_id})
                            MERGE (p1)-[r:DISAGREES_WITH]->(p2)
                            SET r.strength = $similarity
                            """,
                            p1_id=p1_id,
                            p2_id=p2_id,
                            similarity=abs(similarity)
                        )
                        stats["relationships_created"] += 1

            stats["concepts_extracted"] = len(concept_mentions)

        return stats

    async def get_graph_data(
        self,
        focus_group_id: str,
        filter_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Pobiera dane grafu dla wizualizacji

        Args:
            focus_group_id: ID grupy fokusowej
            filter_type: Typ filtra ('positive', 'negative', 'influence', None)

        Returns:
            {
                "nodes": [{"id": str, "name": str, "type": str, "group": int, ...}],
                "links": [{"source": str, "target": str, "type": str, "strength": float}]
            }
        """
        await self.connect()

        nodes = []
        links = []

        async with self.driver.session() as session:
            # Fetch personas
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

                # Apply filters
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

            # Fetch concepts
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

            # Fetch emotions
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

            # Fetch relationships
            # Persona -> Concept
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

            # Persona -> Emotion
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

            # Persona <-> Persona (agreements/disagreements)
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

    def _extract_concepts(self, text: str) -> List[str]:
        """
        Prosta ekstrakcja kluczowych konceptów z tekstu

        W pełnej implementacji użyj NLP (spaCy, NLTK) lub LLM
        """
        # Simple keyword extraction - words that appear frequently
        keywords = [
            "price", "cost", "pricing", "expensive", "affordable",
            "design", "interface", "ui", "ux", "visual",
            "usability", "ease", "simple", "intuitive",
            "features", "functionality", "capability",
            "performance", "speed", "fast", "slow",
            "security", "privacy", "safe", "trust",
            "support", "help", "service",
            "quality", "value", "worth"
        ]

        text_lower = text.lower()
        found = []

        for keyword in keywords:
            if keyword in text_lower:
                # Capitalize first letter
                found.append(keyword.capitalize())

        return list(set(found))[:5]  # Max 5 concepts per response

    def _analyze_sentiment(self, text: str) -> float:
        """
        Prosta analiza sentymentu
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

        # Similarity = (shared concepts / 10) - sentiment difference
        similarity = (record["shared_concepts"] / 10.0) - record["sentiment_diff"]
        return max(-1.0, min(1.0, similarity))

    async def get_influential_personas(
        self,
        focus_group_id: str
    ) -> List[Dict[str, Any]]:
        """
        Znajduje najbardziej wpływowe persony w grafie
        Na podstawie liczby połączeń i siły relacji
        """
        await self.connect()

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

    async def get_key_concepts(
        self,
        focus_group_id: str
    ) -> List[Dict[str, Any]]:
        """Pobiera najczęściej wspominane koncepcje"""
        await self.connect()

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
                    "personas": record["personas"][:5]  # Top 5 personas
                })

            return concepts
