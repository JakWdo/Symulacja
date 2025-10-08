"""
Serwis Analizy Grafowej oparty na Neo4j

Zarządza grafem wiedzy łączącym persony, koncepcje i emocje.
Umożliwia analizę relacji między uczestnikami focus groups i ich opiniami.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import logging
import json

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


# Pydantic models for LLM structured output
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

    def __init__(self):
        """Inicjalizuj połączenie z Neo4j i LLM do ekstrakcji konceptów"""
        self.driver: Optional[AsyncDriver] = None
        self.settings = settings

        # Initialize LLM for concept extraction
        self.llm = ChatGoogleGenerativeAI(
            model=settings.PERSONA_GENERATION_MODEL,  # Use Flash for speed
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.3,  # Lower temperature for consistent extraction
            max_tokens=500,
        )

        # Create extraction prompt template
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

        # JSON output parser
        self.json_parser = JsonOutputParser(pydantic_object=ConceptExtraction)

    async def connect(self):
        """Nawiąż połączenie z Neo4j"""
        if not self.driver:
            try:
                self.driver = AsyncGraphDatabase.driver(
                    self.settings.NEO4J_URI,
                    auth=(self.settings.NEO4J_USER, self.settings.NEO4J_PASSWORD)
                )
                # Verify connection works
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

            # 2. Extract concepts and create relationships using LLM
            concept_mentions = {}  # Track concept frequency

            logger.info(f"Processing {len(responses)} responses with LLM extraction...")

            for idx, response in enumerate(responses):
                persona_id = str(response.persona_id)

                # LLM-powered extraction
                extraction = await self._extract_concepts_with_llm(response.response)

                if (idx + 1) % 10 == 0:
                    logger.info(f"Processed {idx + 1}/{len(responses)} responses")

                # Create concept nodes and relationships
                for concept in extraction.concepts:
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
                        sentiment=extraction.sentiment
                    )
                    stats["relationships_created"] += 1
                    concept_mentions[concept] = concept_mentions.get(concept, 0) + 1

                # 3. Create emotion nodes from LLM extraction
                for emotion in extraction.emotions:
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
                        intensity=abs(extraction.sentiment)
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
        try:
            await self.connect()
        except ConnectionError as e:
            logger.error(f"Cannot connect to Neo4j: {e}")
            return {"nodes": [], "links": [], "error": "Graph database unavailable"}

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
        try:
            # Create chain: prompt -> LLM -> JSON parser
            chain = self.extraction_prompt | self.llm | self.json_parser
            result = await chain.ainvoke({"text": text})

            # Validate and return
            return ConceptExtraction(**result)

        except Exception as e:
            logger.warning(f"LLM concept extraction failed: {e}, falling back to defaults")
            # Fallback to simple extraction
            return ConceptExtraction(
                concepts=self._simple_keyword_extraction(text),
                emotions=["Neutral"],
                sentiment=0.0,
                key_phrases=[]
            )

    def _simple_keyword_extraction(self, text: str) -> List[str]:
        """Fallback: prosta ekstrakcja słów kluczowych bez LLM"""
        keywords = [
            "Price", "Cost", "Design", "Interface", "Usability",
            "Features", "Performance", "Security", "Support", "Quality"
        ]
        text_lower = text.lower()
        found = [kw for kw in keywords if kw.lower() in text_lower]
        return list(set(found))[:5]

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
        try:
            await self.connect()
        except ConnectionError:
            return []

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
        try:
            await self.connect()
        except ConnectionError:
            return []

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

    async def get_controversial_concepts(
        self,
        focus_group_id: str
    ) -> List[Dict[str, Any]]:
        """
        Znajduje koncepcje polaryzujące - te, które wywołują skrajne opinie

        Zwraca koncepcje z dużym rozrzutem sentymentu (jedni kochają, inni nienawidzą)
        """
        try:
            await self.connect()
        except ConnectionError:
            return []

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
        focus_group_id: str
    ) -> List[Dict[str, Any]]:
        """
        Znajduje korelacje między cechami demograficznymi/psychologicznymi a opiniami

        Przykład: "Osoby młodsze (<30) są bardziej pozytywne wobec 'Innovation'"
        """
        try:
            await self.connect()
        except ConnectionError:
            return []

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
        focus_group_id: str
    ) -> List[Dict[str, Any]]:
        """
        Pobiera rozkład emocji w grupie fokusowej

        Zwraca agregację: jakie emocje dominują, ilu uczestników je wyraża
        """
        try:
            await self.connect()
        except ConnectionError:
            return []

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
                    "percentage": 0  # Will be calculated by caller
                })

            # Calculate percentages
            total_personas = sum(e["personas_count"] for e in emotions)
            if total_personas > 0:
                for emotion in emotions:
                    emotion["percentage"] = (emotion["personas_count"] / total_personas) * 100

            return emotions
